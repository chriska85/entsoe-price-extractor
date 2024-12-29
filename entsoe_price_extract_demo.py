import logging
from dotenv import dotenv_values
import core_functions


# Load the environmental variables from the .env file
env_vars = dotenv_values(".env")

# Access the token value from the loaded environmental variables
entso_e_token = env_vars.get("MY_ENTSOE_TOKEN")

# Configure the root logger
logging_format = "%(asctime)s[%(name)s][%(levelname)s]: %(message)s"
logging.basicConfig(level=logging.INFO, format=logging_format)
logger = logging.getLogger(__name__)


# Set the basic input to be used by fetch_day_ahead_prices
start_time = "2024-12-12"
end_time = "2024-12-13"
bidding_zones = ["NO1", "NO2", "DE"]
convert_to_nok = False

# Validate the bidding zone list (not strictly nessecary)
bidding_zones_valid = core_functions.get_valid_bidding_zones(bidding_zones)

# Run the fetch_day_ahead_prices method and store results in the pandas dataframe prices
prices = core_functions.fetch_day_ahead_prices(
    bidding_zones, start_time, end_time, entso_e_token, convert_to_nok=convert_to_nok
)

# Do analysis on results
print(f"Mean price between {start_time} and {end_time}:")
print(prices.mean())
