
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
        self.symbols = ["EURUSD", "XAUUSD", "GBPUSD"]
        
        # Time periods for analysis
        self.time_periods = ["3 months", "1 week", "1 month"]
        
        # Mapping for filename formatting
        self.time_mapping = {
            "3 months": "3_months",
            "1 week": "1_week", 
            "1 month": "1_month"
        }

        self.parse_folders = [""]
        
        self.config = config
            
    def generate_prompt(self, symbol: str, time_period: str) -> str:
        """Generate the analysis prompt"""
        return f"""Given the state of the economy, where would you think the {symbol} is heading for in the next {time_period}? Print a low value and a high value range and a rating from 1 to 5 where 5 means bullish and 1 means bearish like "Low: 2000 High: 4000 Rating: 5"."""
    
    def query_anthropic(self, prompt: str) -> str:
        """Query Anthropic API with the given prompt"""
        try:
            message = self.config.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            logging.error(f"API query failed: {e}")
            raise
    
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
    
    def save_results(self, symbol: str, time_period: str, full_response: str, parsed_data: Optional[Dict]) -> None:
        """Save both full and parsed results to files"""
        time_key = self.time_mapping[time_period]
        timeNow = datetime.now()

        # Save full response
        full_filename = f"Full-{timeNow.year:04d}{timeNow.month:02d}{timeNow.day:02d}-{symbol}-{time_key}.json"
        full_data = {
            "timestamp": timeNow.isoformat(),
            "symbol": symbol,
            "time_period": time_period,
            "response": full_response
        }
        
        try:
            with open(full_filename, 'w', encoding='utf-8') as f:
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
            response = self.query_anthropic(prompt)
            parsed_data = self.parse_response(response)
            
            self.save_results(symbol, time_period, response, parsed_data)
            
            # Add small delay between API calls to be respectful
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"Failed to analyze {symbol} for {time_period}: {e}")
    
    def run_weekly_analysis(self) -> None:
        """Run analysis for all symbol-timeperiod combinations"""
        logging.info("Starting weekly analysis")
        
        if not self.config or not self.config.client:
            logging.error("API client not initialized")
            return
        
        for symbol in self.symbols:
            for time_period in self.time_periods:
                self.analyze_symbol_timeperiod(symbol, time_period)
        
        logging.info("Weekly analysis completed")
    
    def schedule_analysis(self) -> None:
        """Schedule the weekly analysis"""
        # Schedule for every Monday at 9 AM
        schedule.every().monday.at("09:00").do(self.run_weekly_analysis)
        
        logging.info("Analysis scheduled for every Monday at 9:00 AM")
        
        # Keep the program running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_manual_analysis(self) -> None:
        """Run analysis manually (for testing)"""
        print("Running manual analysis...")
        self.run_weekly_analysis()
        print("Manual analysis completed!")
