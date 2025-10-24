"""
Utility functions for extracting prices from ENTSO-E using their Rest API

This file contains the following functions:
    * get_valid_bidding_zones       - helper function to validate bidding zones
    * fetch_day_ahead_prices        - Wrapper function for EntsoePandasClient's query_day_ahead_prices.
                                      To get multiple bidding zones and convert currency if requested.
    * fetch_conversion_rates        - fetches EUR to NOK conversion rates from Norges Bank
"""
# Standard Library Imports
import logging
# Imports for fetching data from ENTSO-E
from entsoe import EntsoePandasClient
import pandas as pd
# Imports for fetching data from Norges Bank
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def fetch_day_ahead_prices(
        bidding_zone_list: list[str],
        start_time: str,
        end_time: str,
        token: str,
        convert_to_nok: bool = False,
        resolution: str = "SDAC_MTU",
):
    """
    Wrapper function to fetches day-ahead electricity prices from ENTSO-E.
    Uses the entsoe-py library to fetch data from ENTSO-E's Restful API.
    Results in EUR/MWh by default, but can be converted to NOK/kWh using exhange rates
    from Norges Bank.

    Args:
        bidding_zone_list (list[str]): 
            A list of bidding zones to query for data. 
            Needs to correspond to the list of valid bidding zones in entsoe-py/entsoe/mappings.py
        start_date (str): 
            The start date of the interval to request data. 
        end_date (str): 
            The end date  (non inclusive) of the interval to request data. 
        token (str): 
            The token used for authorizing requests to ENTSO-E.
        convert_to_nok (bool): 
            A boolean controlling conversion to NOK/kWh.

    Returns:
        pd.DataFrame: A Pandas DataFrame (time-indexed, "Europe/Oslo" time zone) containing
        hourly day-ahead prices for the specified bidding zones and date range.
    """

    client = EntsoePandasClient(api_key=token)

    start_dt_cet = pd.Timestamp(start_time, tz="Europe/Oslo")
    end_dt_cet   = pd.Timestamp(end_time, tz="Europe/Oslo")

    if end_dt_cet < start_dt_cet:
        logger.warning(
            f"End time ({end_dt_cet}) is set prior to start time ({start_dt_cet}).")
        logger.info("Returning without value.")
        return

    datetime_index = pd.date_range(start=start_dt_cet, end=end_dt_cet, freq='15min', inclusive='left')
    # Dataframe to store the prices. Timeseries from ENTSO-E are breakpoint like, meaning they are
    # easily aggergated and filled with forward fill if needed
    full_price_df = pd.DataFrame(index=datetime_index)

    for bidding_zone in bidding_zone_list:
        entsoe_py_df = client.query_day_ahead_prices(bidding_zone, start=start_dt_cet, end=end_dt_cet)
        full_price_df[f"{bidding_zone}"] = entsoe_py_df

    if resolution != "SDAC_MTU":
        full_price_df = full_price_df.ffill()
        logger.info(f"Resampling prices to resolution {resolution}")
        if resolution == "60min":
            full_price_df = full_price_df.resample('h').mean()
        else:
            logger.warning(f"Resolution {resolution} not supported. Continuing with SDAC_MTU")


    # ENTSO-E prices are in EUR/MWh. Conversion to NOK/kWh possible using
    # EUR -> NOK exchange rates from Norges Bank
    if convert_to_nok:
        logger.info(
            "Conversion to NOK/kWh requested. Fetching currency conversion rates from Norges Bank.")
        exchange_rates = fetch_conversion_rates(start_time, end_time)

        if exchange_rates is None or len(exchange_rates) == 0:
            logger.warning(
                "Problems retriving currency conversion rates from Norges Bank. Continuing using EUR/MWh.")
            convert_to_nok = False
        else:
            logger.info("Currency conversion rates succesfully retrived.")
            exchange_rates_sdac_mtu = exchange_rates.reindex(full_price_df.index, method='ffill')
            full_price_df = full_price_df.mul(exchange_rates_sdac_mtu, axis=0) / 1000

    full_price_df.attrs['unit'] = 'EUR/MWh' if not convert_to_nok else 'NOK/kWh'

    return full_price_df

def fetch_conversion_rates(start_date: str, end_date: str):
    """
    Fetches currency conversion rates from the Norges Bank API for a specified date range.

    Args:
        start_date (str): The start date in the format '%Y-%m-%d'.
        end_date (str): The end date in the format '%Y-%m-%d'.

    Returns:
        pd.Series: A Pandas Series containing daily exchange rates for the specified date range.
                Missing exchange rates are filled using the last available observation.
                If the start_date falls on a weekend, the previous Friday is included in the
                returned series. If the end_date falls on a weekend, the following Monday is
                included in the returned series.
    """

    # Specify the API endpoints and parameters
    norges_bank_base_url = "https://data.norges-bank.no/api/data/EXR/B.EUR.NOK.SP"
    norges_bank_payload = {"format": "sdmx-json"}

    # Check if start_date and end_date fall on a weekend
    start_datetime_query = datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime_query = datetime.strptime(end_date, "%Y-%m-%d")

    if end_datetime_query < start_datetime_query:
        logger.warning(
            f"End time ({end_datetime_query}) is set prior "
            f"to start time ({start_datetime_query})")
        logger.info("Returning without value.")
        return

    if start_datetime_query.weekday() >= 5:
        # Adjust start_date to the previous Friday
        start_datetime_query -= timedelta(days=start_datetime_query.weekday() - 4)

    max_attempts = 4
    success = False
    # Need to have data on the first date to aviod NaNs in the first part of the
    # returned pandas dataframe. Try 4 requests, extending one day into the past
    # for each try
    for attempt in range(max_attempts):
        if attempt > 0:
            start_datetime_query -= timedelta(days=1)

        # Updating API query parameters
        norges_bank_payload.update({
            "startPeriod": start_datetime_query.strftime("%Y-%m-%d"),
            "endPeriod": start_datetime_query.strftime("%Y-%m-%d"),
        })

        # Send a GET request to Norges Bank for currency conversion
        norges_bank_response = requests.get(
            norges_bank_base_url, params=norges_bank_payload, timeout=20
        )
        if norges_bank_response.status_code == 200:
            success = True
            break
        else:
            logger.warning(f"No valid exhange rates on day {start_datetime_query}. Trying one day prior.")

    if not success:
        logger.error(f"Not possible to retrive a first date with currency data starting from {start_date}. "
                     f"Returning None")
        logger.info(f"Last API Request: {norges_bank_response.url}")
        return None

    # Found a first day with valid exchange rate data. Now querying the full period
    start_date_query = start_datetime_query.strftime("%Y-%m-%d")
    end_datetime_query = datetime.strptime(end_date, "%Y-%m-%d")
    end_date_query = end_datetime_query.strftime("%Y-%m-%d")
    # Updating API query parameters
    norges_bank_payload.update({"startPeriod": start_date_query, "endPeriod": end_date_query})
    # Performing request
    norges_bank_response = requests.get(norges_bank_base_url, params=norges_bank_payload, timeout=20)

    if norges_bank_response.status_code == 200:
        logger.info(f"Successfully extracted conversion rates for period {start_date_query} and {end_date_query}")
    else:
        logger.error(f"Error code {norges_bank_response.status_code} from Norges Bank API request. Returning None")
        logger.info(f"API Request: {norges_bank_response.url}")
        return None

    # Unpacking the exhange rates from Norges Bank (if successful response)
    norges_bank_data = norges_bank_response.json()
    if "data" in norges_bank_data and "dataSets" in norges_bank_data["data"]:
        data_sets = norges_bank_data["data"]["dataSets"]

        if data_sets:
            # Data points and time index are stored in different part of the response structure
            # Extracting the currency exchange rate data:
            currency_exchange_data = data_sets[0]["series"]["0:0:0:0"]["observations"]

            # Extracting the time index:
            exchange_rate_dates = {
                value["id"]: value["name"] for value
                in norges_bank_data["data"]["structure"]["dimensions"]["observation"][0]["values"]
            }

            # Storing exchange rates into a pandas series
            exchange_rates = pd.Series(index=pd.date_range(start=start_date_query, end=end_date_query, freq="D"))
            # Combining rates data and obeservation time stamps
            for rate_key, rate_value in zip(
                exchange_rate_dates.keys(), currency_exchange_data.values()
            ):
                rate_date = exchange_rate_dates[rate_key]
                rate = float(rate_value[0])
                exchange_rates[rate_date] = rate

            if exchange_rates[start_date:end_date].isna().any():
                missing_data = exchange_rates[start_date:end_date].isna()
                missing_indexes = [date.strftime("%Y-%m-%d") for date in missing_data[missing_data].index]
                logger.warning(f"Missing exchange rate data, using previous days instead. Indexes: {missing_indexes}")

        # Use ffill to fill in missing observations with previous values
        exchange_rates = exchange_rates.ffill()

        exchange_rates.index = exchange_rates.index.tz_localize('Europe/Oslo')

        # Return values only for the originally requested time period
        return exchange_rates[start_date:end_date]
    else:
        logger.error("No data in Norges Bank API response (even with status code 200). Returning None")
        return None
