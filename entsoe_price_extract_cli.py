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
import core_functions, utils


pd.options.plotting.backend = "plotly"

# Load the environmental variables from the .env file
env_vars = dotenv_values(".env")

# Access the token value from the loaded environmental variables
entso_e_token = env_vars.get("MY_ENTSOE_TOKEN")

# Configure the root logger
logging_format = "%(asctime)s [%(levelname)s][%(name)s] %(message)s"
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
                        help='Name of bidding zones or keywords all, nordics or norway', default='norway', nargs='*')
    parser.add_argument('-s', '--start', type=str,
                        help='Start date. Optional (default: "DAY"). Format "yyyy-mm-dd" or BASE +/- RELATVE. Example "2024-01-01", "DAY-2D", "YEAR", "WEEK-D".', default="DAY", nargs='?')
    parser.add_argument('-e', '--end', type=str,
                        help='End date. Optional (default: "LAST_SDAC"). Format "yyyy-mm-dd" or BASE +/- RELATVE. Example "2024-01-01", "DAY-2D", "YEAR", "WEEK-W". Also supports special "LAST_SDAC"', default="LAST_SDAC", nargs='?')
    parser.add_argument('-nok', '--convert_to_nok', action='store_true',
                        help='Fetch EUR->NOK conversion rates and return prices as NOK/kWh.')
    parser.add_argument('-p', '--plot', action='store_true',
                        help='Make an interactive plot using the plotly package')
    parser.add_argument('-o', '--output', type=str, default="", nargs='?',
                        help='Path of output file. Example ./output/prices.csv')
    parser.add_argument('-t', '--time', type=str, default="SDAC_MTU", nargs='?',
                        help='Time resolution. Valid options are "15min", "60min", "SDAC_MTU" or any other valid resolution string. Default is "SDAC_MTU".', 
                        choices=list(utils.get_valid_time_resolution()))
    args = parser.parse_args()

    convert_to_nok = args.convert_to_nok
    plot_prices = args.plot
    start_date, end_date = utils.convert_date_range(args.start, args.end)
    bidding_zone_input = args.bidding_zone
    output_file_path = args.output
    resolution = args.time

    bidding_zones = utils.get_valid_bidding_zones(bidding_zone_input)

    if len(bidding_zones) == 0:
        logger.error("No valid bidding zones fetched. Exiting.")
        return

    prices = core_functions.fetch_day_ahead_prices(
        bidding_zones, 
        start_date, 
        end_date, 
        entso_e_token, 
        resolution=resolution, 
        convert_to_nok=convert_to_nok
    )

    if prices is None:
        logger.error("No prices fetched. Exiting.")
        return

    if len(output_file_path) > 0:
        if os.path.exists(os.path.dirname(output_file_path)):
            logger.info(f"Saving results to file at {output_file_path}")
            prices.to_csv(output_file_path, sep=';')
        else:
            logger.warning(f"Folder {os.path.dirname(output_file_path)} does not exists. No file stored.")

    if plot_prices:
        price_min = prices.min().min()
        price_max = prices.max().max()
        logger.info("Plotting results")

        # Extend the prices DataFrame by repeating the last value for an additional hour
        last_index = prices.index[-1]
        new_index = last_index + pd.Timedelta(hours=1)
        last_row = prices.iloc[-1]
        extended_prices = pd.concat([prices, pd.DataFrame([last_row], index=[new_index])])

        plot = extended_prices.plot(kind='line', line_shape='hv')
        plot.update_layout(
            title='Day ahead clearing price',
            xaxis_title='',
            yaxis_title=f'{prices.attrs["unit"]}',
            font=dict(
                family="Arial, sans-serif",
                size=16,  # Increase the font size
                color="#4d4d4d"
            ),
            legend_title_text='Bidding Zone',
            # Adding a band to the prices
            yaxis_range=[
                min(0, price_min - abs(price_min) * 0.02),
                price_max + abs(price_max) * 0.02
            ],
            xaxis_range=[
                prices.index.min(),
                new_index
            ]
        )
        plot.show()


if __name__ == "__main__":
    main()
