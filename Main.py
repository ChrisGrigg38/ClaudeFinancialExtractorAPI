from App.ConfigManager import ConfigManager
from App.FinancialAnalyzer import FinancialAnalyzer

def main():
    config = ConfigManager("config.enc")
    analyzer = FinancialAnalyzer(config)
    
    print("=== Financial Analysis Scheduler ===")
    print("1. Create new configuration")
    print("2. Run scheduled analysis")
    print("3. Run manual analysis (for testing)")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        config.create_config()
    
    elif choice == "2":
        if config.load_config():
            print("Starting scheduled analysis. Press Ctrl+C to stop.")
            try:
                analyzer.schedule_analysis()
            except KeyboardInterrupt:
                print("\nScheduled analysis stopped.")
    
    elif choice == "3":
        if config.load_config():
            analyzer.run_manual_analysis()
    
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
