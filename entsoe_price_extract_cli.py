"""
Main script for testing and running functions in utils.py. Featch and plot
day-ahead prices from ENTSO-E.

This file contains the following functions:

    * main - script for testing and running
"""
import os
import argparse
import logging
import pandas as pd
from dotenv import dotenv_values
import core_functions


pd.options.plotting.backend = "plotly"

# Load the environmental variables from the .env file
env_vars = dotenv_values(".env")

# Access the token value from the loaded environmental variables
entso_e_token = env_vars.get("MY_ENTSOE_TOKEN")

# Configure the root logger
logging_format = "%(asctime)s[%(name)s][%(levelname)s]: %(message)s"
logging.basicConfig(level=logging.INFO, format=logging_format)
logger = logging.getLogger(__name__)


def main():
    """
    Main function used to exectue when calling python

        Args:
            No arguments

        Returns:
            No return value
    """

    parser = argparse.ArgumentParser(
        description="Script to extract prices from entso-e transparancy platform.")
    parser.add_argument('-a', '--bidding_zone', type=str,
                        help='Name of bidding zones or keywords all, nordics or norway', default='norway', nargs='?')
    parser.add_argument('-s', '--start', type=str,
                        help='Start date. Format "yyyy-mm-dd". Example "2024-01-01".', default="2024-12-12", nargs='?')
    parser.add_argument('-e', '--end', type=str,
                        help='End date. Format "yyyy-mm-dd". Example "2024-02-01".', default="2024-12-13", nargs='?')
    parser.add_argument('-nok', '--convert_to_nok', action='store_true',
                        help='Fetch EUR->NOK conversion rates and return prices as NOK/kWh.')
    parser.add_argument('-p', '--plot', action='store_true',
                        help='Make an interactive plot using the plotly package')
    parser.add_argument('-o', '--output', type=str, default="", nargs='?',
                        help='Path of output file. Example ./output/prices.csv')
    args = parser.parse_args()

    convert_to_nok = args.convert_to_nok
    plot_prices = args.plot
    start_time = args.start
    end_time = args.end
    bidding_zone_input = args.bidding_zone.split(',')
    output_file_path = args.output

    bidding_zones = core_functions.get_valid_bidding_zones(bidding_zone_input)

    if len(bidding_zones) == 0:
        logger.warning("No valid bidding zones fetched. Exiting.")
        return

    prices = core_functions.fetch_day_ahead_prices(
        bidding_zones, start_time, end_time, entso_e_token, convert_to_nok=convert_to_nok
    )

    if prices is None:
        logger.warning("No prices fetched. Exiting.")
        return

    if len(output_file_path) > 0:
        if os.path.exists(os.path.dirname(output_file_path)):
            logger.info(f"Saving results to file at {output_file_path}")
            prices.to_csv(output_file_path, sep=';')
        else:
            logger.warning(f"Folder {os.path.dirname(output_file_path)} does not exists. No file stored.")

    if plot_prices:
        logger.info("Plotting results")
        plot = prices.plot()
        plot.update_layout(
            yaxis_range=[prices.min().min() - 0.1, prices.max().max() + 0.1]
        )
        plot.show()


if __name__ == "__main__":
    main()
