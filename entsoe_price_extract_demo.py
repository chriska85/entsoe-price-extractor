import logging
from dotenv import dotenv_values
import pandas as pd
import core_functions
import utils


# Load the environmental variables from the .env file
env_vars = dotenv_values(".env")

# Access the token value from the loaded environmental variables
entso_e_token = env_vars.get("MY_ENTSOE_TOKEN")

# Configure the root logger
logging_format = "%(asctime)s [%(levelname)s][%(name)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=logging_format)
logger = logging.getLogger(__name__)


# Set the basic input to be used by fetch_day_ahead_prices
#start_time = "2024-12-12"
#end_time = "2024-12-13"
start_time = "DAY"
end_time = "LAST_SDAC" #"DAY+D"

start_date, end_date = utils.convert_date_range(start_time, end_time)

bidding_zones = ["DE", "nordics"]
convert_to_nok = False

# Validate the bidding zone list (not strictly nessecary)
bidding_zones_valid = utils.get_valid_bidding_zones(bidding_zones)

# Run the fetch_day_ahead_prices method and store results in the pandas dataframe prices
prices = core_functions.fetch_day_ahead_prices(
    bidding_zones_valid, start_date, end_date, entso_e_token, convert_to_nok=convert_to_nok, resolution="15min"
)

def print_price_analysis(prices):
    # Ensure a DatetimeIndex, get the calendar date of the last timestamp,
    # and select all rows for that date.
    prices.index = pd.to_datetime(prices.index)
    last_date = prices.index[-1].date()
    prices_last_24h = prices[prices.index.date == last_date]

    # Print header
    print(f"\nPrices on {prices.index[-1].strftime('%Y-%m-%d')}:")
    col_width = 12
    left_label_width = 23
    separator = "-" * (left_label_width + col_width * (len(prices.columns)+1))
    print(separator)

    # Header row with fixed-width columns
    header = "Delivery period".ljust(left_label_width) + " ".join(col.center(col_width) for col in prices.columns)
    unit_row = "".ljust(left_label_width) + " ".join(f"[{prices.attrs['unit']}]".ljust(col_width) for _ in prices.columns)
    print(header)
    print(unit_row)
    print(separator)

     # Print hourly/15-min values
    for i in range(len(prices_last_24h)):
        start_time = f"{prices_last_24h.index[i].hour:02.0f}:{prices_last_24h.index[i].minute:02.0f}"
        next_time = prices_last_24h.index[i] + pd.Timedelta(minutes=15 if len(prices) >= 96 else 60)
        end_time = f"{next_time.hour:02.0f}:{next_time.minute:02.0f}"
        values = "     ".join(f"{prices_last_24h[col].iloc[i]:8.2f}" for col in prices_last_24h.columns)
        print(f"{start_time} - {end_time}".ljust(left_label_width) + f"{values}")


    # Print statistics
    print(separator)

    print(f"Statistics full period {prices.index[0].strftime('%Y-%m-%d')} - {prices.index[-1].strftime('%Y-%m-%d')}:")
    header2= "".ljust(left_label_width) + " ".join(col.center(col_width) for col in prices.columns)
    unit_row2 = "".ljust(left_label_width) + " ".join(f"[{prices.attrs['unit']}]".ljust(col_width) for _ in prices.columns)
    print(header2)
    print(unit_row2)
    print(separator)
    
    stats = prices.agg(['min', 'max', 'mean'])
    print("Min:".ljust(left_label_width) + "     ".join(f"{stats.at['min', col]:8.2f}" for col in prices.columns))
    print("Max:".ljust(left_label_width) + "     ".join(f"{stats.at['max', col]:8.2f}" for col in prices.columns))
    print("Average:".ljust(left_label_width) + "     ".join(f"{stats.at['mean', col]:8.2f}" for col in prices.columns))

# Call the function with the prices dataframe
print_price_analysis(prices)