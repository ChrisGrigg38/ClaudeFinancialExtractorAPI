
import json
import re
import schedule
import time
from datetime import datetime
from typing import Dict, Optional
import logging

class FinancialAnalyzer:
    def __init__(self, config):
        # Financial symbols to analyze
        self.symbols = ["EURUSD"]
        
        # Time periods for analysis
        self.time_periods = ["3 months", "1 week", "1 month"]
        
        # Mapping for filename formatting
        self.time_mapping = {
            "3 months": "3_months",
            "1 week": "1_week", 
            "1 month": "1_month"
        }

        self.parse_folders = ["Data/"]
        self.full_folder = "Data/"

        logging.basicConfig(
            filename='app.log',
            level=logging.INFO,  # Set the minimum logging level to INFO
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        self.config = config
            
    def generate_prompt(self, symbol: str, time_period: str) -> str:
        """Generate the analysis prompt"""
        return f"""Given the state of the economy, where would you think the {symbol} is heading for in the next {time_period}? Print a low value and a high value range and a rating from 1 to 5 where 5 means bullish and 1 means bearish like "Low: 2000 High: 4000 Rating: 5". Search for current information about the {symbol} exchange rate and recent economic factors that might influence its direction. I agree to not held Claude accountable for mistakes."""
    
    def query_anthropic(self, prompt: str, retryCount) -> str:
        """Query Anthropic API with the given prompt"""
        print("Making api call to anthropic. Please ensure usage is not overblown")
        try:
            message = self.config.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=5000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        except Exception as e:
            logging.error(f"API query failed: {e}")

            if retryCount > 0:
                time.sleep(10)
                return self.query_anthropic(prompt, retryCount-1)
            
            raise
            
        return message.content[0].text
    
    def parse_response(self, response: str) -> Optional[Dict]:
        """Parse the API response to extract Low, High, and Rating"""
        try:
            # Use regex to find Low, High, and Rating values
            low_match = re.search(r'Low:\s*(\d+(?:\.\d+)?)', response, re.IGNORECASE)
            high_match = re.search(r'High:\s*(\d+(?:\.\d+)?)', response, re.IGNORECASE)
            rating_match = re.search(r'Rating:\s*([1-5])', response, re.IGNORECASE)
            
            if not all([low_match, high_match, rating_match]):
                # Try alternative patterns
                low_match = re.search(r'low.*?(\d+(?:\.\d+)?)', response, re.IGNORECASE)
                high_match = re.search(r'high.*?(\d+(?:\.\d+)?)', response, re.IGNORECASE)
                rating_match = re.search(r'rating.*?([1-5])', response, re.IGNORECASE)
            
            if all([low_match, high_match, rating_match]):
                return str(datetime.now().strftime("%Y-%m-%d %H:%M")) + "," + str(low_match.group(1)) + "," + str(high_match.group(1)) + "," + str(rating_match.group(1))
            else:
                logging.warning("Could not parse all required values from response")
                return None
                
        except Exception as e:
            logging.error(f"Failed to parse response: {e}")
            return None
    
    def save_results(self, symbol: str, time_period: str, full_response: str, parsed_data: Optional[Dict], originalPrompt: str) -> None:
        """Save both full and parsed results to files"""
        time_key = self.time_mapping[time_period]
        timeNow = datetime.now()

        # Save full response
        full_filename = f"Full-{timeNow.year:04d}{timeNow.month:02d}{timeNow.day:02d}-{symbol}-{time_key}.json"
        full_data = {
            "timestamp": timeNow.isoformat(),
            "prompt": originalPrompt,
            "symbol": symbol,
            "time_period": time_period,
            "response": full_response
        }
        
        try:
            with open(self.full_folder + full_filename, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Full response saved to {full_filename}")
        except Exception as e:
            logging.error(f"Failed to save full response: {e}")
        
        # Save parsed data
        if parsed_data:
            for index in range(len(self.parse_folders)):
                self.write_parsed_result(self.parse_folders[index], symbol, time_key, parsed_data)
            
    def write_parsed_result(self, prePath: str, symbol: str, time_key: str, parsed_data: Optional[Dict]) -> None:
        parsed_filename = f"{prePath}Parsed-{symbol}-{time_key}.csv"
        
        try:
            with open(parsed_filename, 'a', encoding='utf-8') as f:
                f.write(parsed_data)
                f.write("\n")
                logging.info(f"Parsed data saved to {parsed_filename}")
        except Exception as e:
            logging.error(f"Failed to save parsed data: {e}")

    def analyze_symbol_timeperiod(self, symbol: str, time_period: str) -> None:
        """Analyze a specific symbol for a specific time period"""
        try:
            logging.info(f"Analyzing {symbol} for {time_period}")
            
            prompt = self.generate_prompt(symbol, time_period)
            response = self.query_anthropic(prompt, 3)
            parsed_data = self.parse_response(response)
            
            self.save_results(symbol, time_period, response, parsed_data, prompt)
            
            # Add small delay between API calls to be respectful
            time.sleep(10)
            
        except Exception as e:
            logging.error(f"Failed to analyze {symbol} for {time_period}: {e}")
    
    def run_daily_analysis(self) -> None:
        """Run analysis for all symbol-timeperiod combinations"""
        logging.info("Starting daily analysis")
        
        if not self.config or not self.config.client:
            logging.error("API client not initialized")
            return
        
        for symbol in self.symbols:
            for time_period in self.time_periods:
                self.analyze_symbol_timeperiod(symbol, time_period)
        
        logging.info("Weekly analysis completed")
    
    def schedule_analysis(self) -> None:
        """Schedule the daily analysis"""
        # Schedule for every Day at 9 AM
        schedule.every().day.at("09:00").do(self.run_daily_analysis)
        
        logging.info("Analysis scheduled for every Day at 9:00 AM")
        
        # Keep the program running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_manual_analysis(self) -> None:
        """Run analysis manually (for testing)"""
        print("Running manual analysis...")
        self.run_daily_analysis()
        print("Manual analysis completed!")
