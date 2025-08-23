//+------------------------------------------------------------------+
//|                                        ClaudeForecasterLib.mq4   |
//|                                   ClaudeForecaster Library Class |
//|                                   Handles Loading Claude Input   |
//+------------------------------------------------------------------+

#property library
#property copyright "ClaudeForecaster Library"
#property link      ""
#property version   "1.00"

//+------------------------------------------------------------------+
//| Structure to hold Claude data                                    |
//+------------------------------------------------------------------+
struct ClaudeData
{
   datetime timestamp;
   double   high;
   double   low;
   int      rating;
};

//+------------------------------------------------------------------+
//| Structure to hold cache entry                                    |
//+------------------------------------------------------------------+
struct CacheEntry
{
   string      time_key;
   ClaudeData  data;
   datetime    last_updated;
   bool        is_valid;
};

//+------------------------------------------------------------------+
//| ClaudeForecaster Library Class                                   |
//+------------------------------------------------------------------+
class ClaudeForecasterLib
{
private:
   CacheEntry cache_entries[];
   int        cache_size;
   
   // Private methods
   int        FindCacheIndex(string time_key);
   bool       IsMonday10AM();
   bool       ShouldUpdateCache(string time_key);
   bool       ReadCSVFile(string time_key, ClaudeData &data);
   string     BuildFileName(string time_key);
   bool       ParseCSVLine(string line, ClaudeData &data);
   datetime   StringToDateTime(string date_str);
   void       AddOrUpdateCache(string time_key, ClaudeData &data);
   datetime   GetLineDateTime(string line);

public:
   // Constructor
   ClaudeForecasterLib();
   
   // Destructor
   ~ClaudeForecasterLib();
   
   // Main public method
   ClaudeData   GetData(string time_key);
   
   // Utility methods
   void       ClearCache();
   int        GetCacheSize() { return cache_size; }
};

//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
ClaudeForecasterLib::ClaudeForecasterLib()
{
   cache_size = 0;
   ArrayResize(cache_entries, 0);
}

//+------------------------------------------------------------------+
//| Destructor                                                       |
//+------------------------------------------------------------------+
ClaudeForecasterLib::~ClaudeForecasterLib()
{
   ArrayFree(cache_entries);
}

//+------------------------------------------------------------------+
//| Main function to get data with caching logic                    |
//+------------------------------------------------------------------+
ClaudeData ClaudeForecasterLib::GetData(string time_key)
{
   ClaudeData result;
   
   // Initialize result structure
   result.timestamp = 0;
   result.high = 0.0;
   result.low = 0.0;
   result.rating = 0;
   
   // Check if we should update the cache
   if(ShouldUpdateCache(time_key))
   {
      ClaudeData new_data;
      if(ReadCSVFile(time_key, new_data))
      {
         AddOrUpdateCache(time_key, new_data);
      }
      else
      {
         Print("Error: Could not read CSV file for time_key: ", time_key);
      }
   }
   
   // Get data from cache
   int cache_index = FindCacheIndex(time_key);
   if(cache_index >= 0 && cache_entries[cache_index].is_valid)
   {
      result = cache_entries[cache_index].data;
   }
   else
   {
      Print("Warning: No valid cached data found for time_key: ", time_key);
   }
   
   return result;
}

//+------------------------------------------------------------------+
//| Find cache entry index by time_key                              |
//+------------------------------------------------------------------+
int ClaudeForecasterLib::FindCacheIndex(string time_key)
{
   for(int i = 0; i < cache_size; i++)
   {
      if(cache_entries[i].time_key == time_key)
         return i;
   }
   return -1;
}

//+------------------------------------------------------------------+
//| Check if current time is Monday 10:00 AM or later              |
//+------------------------------------------------------------------+
bool ClaudeForecasterLib::IsMonday10AM()
{
   datetime current_time = TimeCurrent();
   int day_of_week = TimeDayOfWeek(current_time);
   int hour = TimeHour(current_time);
   
   return (day_of_week == 1 && hour >= 10); // Monday = 1, hour >= 10
}

//+------------------------------------------------------------------+
//| Check if cache should be updated                                |
//+------------------------------------------------------------------+
bool ClaudeForecasterLib::ShouldUpdateCache(string time_key)
{
   // Only update on Monday at 10 AM or later
   if(!IsMonday10AM())
      return false;
   
   int cache_index = FindCacheIndex(time_key);
   
   // If no cache entry exists, we should update
   if(cache_index < 0)
      return true;
   
   // Check if we already updated this week
   datetime current_time = TimeCurrent();
   datetime last_update = cache_entries[cache_index].last_updated;
   
   // Calculate start of current week (Monday 00:00)
   datetime start_of_week = current_time;
   int day_of_week = TimeDayOfWeek(current_time);
   int seconds_since_monday = (day_of_week - 1) * 86400 + TimeHour(current_time) * 3600 + TimeMinute(current_time) * 60 + TimeSeconds(current_time);
   start_of_week -= seconds_since_monday;
   
   // If last update was before this week's Monday, we should update
   return (last_update < start_of_week);
}

//+------------------------------------------------------------------+
//| Read CSV file and get the last line data                        |
//+------------------------------------------------------------------+
bool ClaudeForecasterLib::ReadCSVFile(string time_key, ClaudeData &data)
{
   string filename = BuildFileName(time_key);
   int file_handle = FileOpen(filename, FILE_READ | FILE_CSV | FILE_ANSI);
   
   if(file_handle == INVALID_HANDLE)
   {
      Print("Error: Cannot open file ", filename, ". Error code: ", GetLastError());
      return false;
   }
   
   string last_line = "";
   string current_line = "";
   
   // Read all lines to get the last one
   while(!FileIsEnding(file_handle))
   {
      current_line = FileReadString(file_handle);
      if(StringLen(current_line) > 0)
         if(GetLineDateTime(current_line) < TimeCurrent())
             last_line = current_line;
   }
   
   FileClose(file_handle);
   
   if(StringLen(last_line) == 0)
   {
      Print("Error: CSV file is empty or could not read last line");
      return false;
   }
   
   return ParseCSVLine(last_line, data);
}

//+------------------------------------------------------------------+
//| Build filename based on current symbol and time_key             |
//+------------------------------------------------------------------+
string ClaudeForecasterLib::BuildFileName(string time_key)
{
   string symbol = Symbol();
   return StringFormat("Parsed-%s-%s.csv", symbol, time_key);
}

datetime ClaudeForecasterLib::GetLineDateTime(string line)
{
   string parts[];
   int count = StringSplit(line, ',', parts);
   
   if(count != 4)
   {
      Print("Error: Invalid CSV line format. Expected 4 columns, got ", count);
      return 0;
   }
   
   // Parse timestamp
   return StringToDateTime(parts[0]);
}

//+------------------------------------------------------------------+
//| Parse CSV line into ClaudeData structure                         |
//+------------------------------------------------------------------+
bool ClaudeForecasterLib::ParseCSVLine(string line, ClaudeData &data)
{
   string parts[];
   int count = StringSplit(line, ',', parts);
   
   if(count != 4)
   {
      Print("Error: Invalid CSV line format. Expected 4 columns, got ", count);
      return false;
   }
   
   // Parse timestamp
   data.timestamp = StringToDateTime(parts[0]);
   if(data.timestamp == 0)
   {
      Print("Error: Could not parse timestamp: ", parts[0]);
      return false;
   }
   
   // Parse high
   data.high = StringToDouble(parts[1]);
   
   // Parse low  
   data.low = StringToDouble(parts[2]);
   
   // Parse rating
   data.rating = (int)StringToInteger(parts[3]);
   
   return true;
}

//+------------------------------------------------------------------+
//| Convert date string to datetime                                 |
//+------------------------------------------------------------------+
datetime ClaudeForecasterLib::StringToDateTime(string date_str)
{
   // Expected format: YYYY-MM-DD
   string date_parts[];
   int count = StringSplit(date_str, '-', date_parts);
   
   if(count != 3)
      return 0;
   
   int year = (int)StringToInteger(date_parts[0]);
   int month = (int)StringToInteger(date_parts[1]);
   int day = (int)StringToInteger(date_parts[2]);
   
   // Create datetime (time set to 00:00:00)
   return StringToTime(StringFormat("%04d.%02d.%02d 00:00:00", year, month, day));
}

//+------------------------------------------------------------------+
//| Add or update cache entry                                       |
//+------------------------------------------------------------------+
void ClaudeForecasterLib::AddOrUpdateCache(string time_key, ClaudeData &data)
{
   int cache_index = FindCacheIndex(time_key);
   
   if(cache_index >= 0)
   {
      // Update existing entry
      cache_entries[cache_index].data = data;
      cache_entries[cache_index].last_updated = TimeCurrent();
      cache_entries[cache_index].is_valid = true;
   }
   else
   {
      // Add new entry
      cache_size++;
      ArrayResize(cache_entries, cache_size);
      
      cache_entries[cache_size - 1].time_key = time_key;
      cache_entries[cache_size - 1].data = data;
      cache_entries[cache_size - 1].last_updated = TimeCurrent();
      cache_entries[cache_size - 1].is_valid = true;
   }
   
   Print("Cache updated for time_key: ", time_key, " at ", TimeToString(TimeCurrent()));
}

//+------------------------------------------------------------------+
//| Clear all cache entries                                         |
//+------------------------------------------------------------------+
void ClaudeForecasterLib::ClearCache()
{
   cache_size = 0;
   ArrayResize(cache_entries, 0);
   Print("Cache cleared");
}