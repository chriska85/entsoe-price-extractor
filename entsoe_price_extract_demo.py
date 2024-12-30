import logging
from dotenv import dotenv_values
import pandas as pd
import core_functions


# Load the environmental variables from the .env file
env_vars = dotenv_values(".env")

# Access the token value from the loaded environmental variables
entso_e_token = env_vars.get("MY_ENTSOE_TOKEN")

# Configure the root logger
logging_format = "%(asctime)s [%(levelname)s][%(name)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=logging_format)
logger = logging.getLogger(__name__)


# Set the basic input to be used by fetch_day_ahead_prices
start_time = "2024-12-1"
end_time = "2024-12-30"
bidding_zones = ["NO1", "NO2", "DE"]
convert_to_nok = True

# Validate the bidding zone list (not strictly nessecary)
bidding_zones_valid = core_functions.get_valid_bidding_zones(bidding_zones)

# Run the fetch_day_ahead_prices method and store results in the pandas dataframe prices
prices = core_functions.fetch_day_ahead_prices(
    bidding_zones, start_time, end_time, entso_e_token, convert_to_nok=convert_to_nok
)

# Do analysis on results
end_time_24h = prices.index.max()
start_time_24h = end_time_24h - pd.Timedelta(hours=24)
prices_last_24_hours = prices.loc[start_time_24h:end_time_24h]
print(f"\nPrices on {prices.index[-1].strftime('%Y-%m-%d')}:")
print("-" * (25 + 16*len(prices.columns)))  # Separator line for better readability
print("Delivey period\t\t" + "\t\t".join(prices.columns))
print("\t\t\t" + "\t".join([f"[{prices.attrs['unit']}]"] * len(prices.columns)))
print("-" * (25 + 16*len(prices.columns)))  # Separator line for better readability
for i in range(len(prices_last_24_hours) - 1):
    start_time = prices_last_24_hours.index[i].strftime('%H:%M')
    end_time = prices_last_24_hours.index[i + 1].strftime('%H:%M')
    values = "\t".join(f"{prices_last_24_hours[col].iloc[i]:8.2f}" for col in prices_last_24_hours.columns)
    print(f"{start_time} - {end_time}\t\t{values}")
# Print min, max, and average
print("-" * (25 + 16*len(prices.columns)))  # Separator line for better readability
print(f"Statistics full period {prices.index[0].strftime('%Y-%m-%d')} - {prices.index[-1].strftime('%Y-%m-%d')}:")
print("\t\t\t" + "\t\t".join(prices_last_24_hours.columns))
print("\t\t\t" + "\t".join([f"[{prices.attrs['unit']}]"] * len(prices_last_24_hours.columns)))
print("-" * (25 + 16*len(prices.columns)))  # Separator line for better readability
stats = prices.agg(['min', 'max', 'mean'])
print("Min:\t\t\t" + "\t".join(f"{stats.at['min', col]:8.2f}" for col in prices.columns))
print("Max:\t\t\t" + "\t".join(f"{stats.at['max', col]:8.2f}" for col in prices.columns))
print("Average:\t\t" + "\t".join(f"{stats.at['mean', col]:8.2f}" for col in prices.columns))

