"""
Utility functions for extracting prices from ENTSO-E using their Rest API

This file contains the following functions:
    * get_valid_bidding_zones       - helper function to validate bidding zones
    * fetch_day_ahead_prices        - Wrapper function for fetch_day_ahead_prices_api.
                                      To get right time range, time zone and currency.
    * fetch_day_ahead_prices_api    - fetches DA electricity prices from ENTOS-E Restful API.
                                      Results in EUR/MWh and time zone is UTC.
    * fetch_conversion_rates        - fetches EUR to NOK conversion rates from Norges Bank
"""
# Standard Library Imports
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import requests
import pandas as pd
import pytz
import ext_api_config


logger = logging.getLogger(__name__)


def get_valid_bidding_zones(bidding_zone_input: list[str]):
    """'
    Retrieves valid bidding zones from a list of strings.

    Possible inputs include valid bidding zone names as defined in the bidding_zone_to_eic_code_map
    of ext_api_config.py. Additionally, the keywords 'nordics' and 'norway' can be used to extract
    the Nordic and Norwegian bidding zones, respectively. The keyword 'all' can be used to retrieve
    all valid bidding zones.

    Args:
        bidding_zone_input (list[str]): A list of bidding zones to validate.

    Returns:
        list[str]: A list of valid bidding zones. If no valid zones are provided,
                   an empty list is returned and a message is printed.
    """
    # Support bidding zone input as ["BZ1,BZ2","BZ3"], in addition to reglar list
    # Relevant for command line client which can get both comma and space separated arguments
    bidding_zone_input_split = [bz for sublist in bidding_zone_input for bz in sublist.split(",")]

    # Convert the input list to a set for efficient operations
    use_bidding_zone_set = set(bidding_zone_input_split)

    # Create an instance of the ExternalApiConfig class
    ext_api_config_obj = ext_api_config.ExternalApiConfig()

    # Define the bidding zones configuration
    bidding_zones_config = {
        "all": set(ext_api_config_obj.get_bidding_zone_to_eic_code_map().keys()),
        "nordics": set(["NO1", "NO2", "NO3", "NO4", "NO5", "SE1", "SE2", "SE3", "SE4", "DK1", "DK2", "FI"]),
        "norway": set(["NO1", "NO2", "NO3", "NO4", "NO5"]),
        "baltics": set(["EE", "LT", "LV"]),
        "cwe": set(["DE", "AT", "BE", "FR", "NL", "PL"])
    }

    # Include all Norwegian bidding zones if "norway" is in the input set
    if "norway" in use_bidding_zone_set:
        use_bidding_zone_set = bidding_zones_config["norway"] | use_bidding_zone_set

    # Include all Nordic bidding zones if "nordics" is in the input set
    if "nordics" in use_bidding_zone_set:
        use_bidding_zone_set = bidding_zones_config["nordics"] | use_bidding_zone_set

    # Include all bidding zones if "all" is in the input set
    if "all" in use_bidding_zone_set:
        use_bidding_zone_set = bidding_zones_config["all"] | use_bidding_zone_set

    # Ensure the final set only contains valid bidding zones
    use_bidding_zone_set = bidding_zones_config["all"] & use_bidding_zone_set

    # Check if the resulting set is empty and print a message if so
    if len(use_bidding_zone_set) == 0:
        logger.warning(
            f"No valid bidding zones provided (input: {bidding_zone_input})")
        logger.info(f"Please use at least one of the following: {bidding_zones_config['all']}")

    # Return the list of valid bidding zones
    return list(use_bidding_zone_set)


def fetch_day_ahead_prices(
        bidding_zone_list: list[str],
        start_time: str,
        end_time: str,
        token: str,
        convert_to_nok: bool = False
):
    """
    Wrapper function to fetches day-ahead electricity prices from ENTSO-E.
    As the ENTSO-E API limits the time range of each request to 100 days this function
    breaks up the request into several between start_time and end_time.
    Results in EUR/MWh by default, but can be converted to NOK/kWh using exhange rates
    from Norges Bank.

    Args:
        bidding_zone_list (list[str]): A list of bidding zones to query for data.
        start_date (str): The start date of the interval to request data. Format '%Y-%m-%d'.
        end_date (str): The end date  (non inclusive) of the interval to request data. Format '%Y-%m-%d'.
        token (str): The token used for authorizing requests to ENTSO-E.
        convert_to_nok (bool): A boolean controlling conversion to NOK/kWh.

    Returns:
        pd.DataFrame: A Pandas DataFrame (time-indexed, "UTC" time zone) containing
        hourly day-ahead prices for the specified bidding zones and date range.
    """
    ext_api_config_obj = ext_api_config.ExternalApiConfig()

    cet_tz = pytz.timezone("Europe/Oslo")
    start_dt_cet = cet_tz.localize(datetime.strptime(start_time, "%Y-%m-%d"))
    end_dt_cet = cet_tz.localize(datetime.strptime(end_time, "%Y-%m-%d"))

    if end_dt_cet < start_dt_cet:
        logger.warning(
            f"End time ({end_dt_cet}) is set prior to start time ({start_dt_cet}).")
        logger.info("Returning without value.")
        return

    # Convert to UTC as this is the time index used
    start_dt_utc = start_dt_cet.astimezone(pytz.utc)
    end_dt_utc = end_dt_cet.astimezone(pytz.utc)

    full_price_df = pd.DataFrame()
    max_interval = timedelta(days=ext_api_config_obj.get_entsoe_max_days_per_request())
    current_start_utc = start_dt_utc

    while current_start_utc < end_dt_utc:
        current_end_utc = min(current_start_utc + max_interval, end_dt_utc)
        prices_chunk = fetch_day_ahead_prices_api(bidding_zone_list, current_start_utc, current_end_utc, token)
        full_price_df = pd.concat([full_price_df, prices_chunk])
        # fetch_day_ahead_prices_api works with 15 minutes time steps,
        # but is non-inclusive wrt end_dt_utc. Next start therefore does not have to be shifted.
        current_start_utc = current_end_utc

    # ENTSO-E return timeseries in UTC. Convert the index timezone to Europe/Oslo
    full_price_df = full_price_df.tz_convert('Europe/Oslo')

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
            exchange_rates_hourly = exchange_rates.resample('h').ffill()
            exchange_rates_hourly = exchange_rates_hourly[full_price_df.index]
            full_price_df = full_price_df.mul(exchange_rates_hourly, axis=0) / 1000

    full_price_df.attrs['unit'] = 'EUR/MWh' if not convert_to_nok else 'NOK/kWh'

    return full_price_df


def fetch_day_ahead_prices_api(
        bidding_zone_list: list[str],
        start_dt_utc: datetime,
        end_dt_utc: datetime,
        token: str,
        resolution: str = '60min'
):
    """
    Fetches day-ahead electricity prices from ENTSO-E using their Restful API.
    Results in EUR/MWh and time zone is UTC.

    Args:
        bidding_zone_list (list[str]): A list of bidding zones to query for data.
        start_date (datetime): The start of the interval to request data, in UTC.
        end_date (datetime): The end of the interval to request data (non inclusive), in UTC.
        token (str): The token used for authorizing requests to ENTSO-E.
        resolution (str): Time resolution of data to return. Either hourly or quarterly. Default is '60min'.

    Returns:
        pd.DataFrame: A Pandas DataFrame (time-indexed, "UTC" time zone) containing
        day-ahead prices (either hourly or quarterly) for the specified bidding zones and date range.
    """
    # Define allowed resolutions
    allowed_resolutions = {'15min', '15T', '15t', 'quarter-hour', 'quarter_hour', '15minutes', '15m', '15M',
                           '60min', '60T', '60t', 'hour', '1H', '1h', '1hour', '1HOUR', 'h', 'H'}

    # Validate the resolution
    if resolution not in allowed_resolutions:
        raise ValueError(f"Invalid resolution '{resolution}'. "
                         f"Allowed values are '15min' and '60min' (or their variations).")

    # Create a datetime index with 15 minute intervals as this is the
    # smallest market time unit supported in the single day ahead market clearing
    datetime_index = pd.date_range(start=start_dt_utc, end=end_dt_utc, freq='15min', inclusive='left')
    # Dataframe to store the prices. Timeseries from ENTSO-E are breakpoint like, meaning they are
    # easily aggergated and filled with forward fill if needed
    data_frame = pd.DataFrame(index=datetime_index)

    start_dt_utc_str = start_dt_utc.strftime("%Y%m%d%H%M")
    end_dt_utc_str = end_dt_utc.strftime("%Y%m%d%H%M")

    entsoe_payload = {
        "securityToken": token,
        "documentType": "A44",
        "in_Domain": None,
        "out_Domain": None,
        "periodStart": start_dt_utc_str,
        "periodEnd": end_dt_utc_str,
    }

    ext_api_config_obj = ext_api_config.ExternalApiConfig()
    url = ext_api_config_obj.get_entsoe_web_url()

    logger.info("Fetching prices from ENTSO-E's Transparency Platform.")
    logger.debug(f"ENTSO-E's API url: {url}")
    logger.info(f"Starting time (UTC): {start_dt_utc_str}")
    logger.info(f"End time (UTC): {end_dt_utc_str}")
    logger.info(f"Bidding zones: {bidding_zone_list}")

    # ENTSO-E identifies bidding zones by so-called eic codes
    # The map between bidding zone and EIC codes are maintained in ext_api_confit.py
    bidding_zone_to_eic_code_dict = ext_api_config_obj.get_bidding_zone_to_eic_code_map()

    for bidding_zone in bidding_zone_list:
        # Set the bidding zone in the ENTSO-E api payload
        # (both in_Domain and out_Domain needed)
        entsoe_payload["in_Domain"] = bidding_zone_to_eic_code_dict[bidding_zone]
        entsoe_payload["out_Domain"] = bidding_zone_to_eic_code_dict[bidding_zone]
        # Request data from ENTSO-E
        response = requests.get(url, params=entsoe_payload, timeout=180)

        if response.status_code == 200:
            xml_data = response.content

            # Define the namespace prefix and URI
            namespace = ext_api_config_obj.get_entsoe_price_namespace_conf()

            # Parse the XML data
            root = ET.fromstring(xml_data)

            # Initialize an empty list to store the extracted data
            data = []

            # Iterate over each TimeSeries element in the XML
            for timeseries in root.findall('ns:TimeSeries', namespace):
                # Iterate over each Period element within the current TimeSeries
                for period in timeseries.findall('ns:Period', namespace):
                    # Extract the start time of the period
                    start_time_period = period.find(
                        'ns:timeInterval/ns:start', namespace).text
                    # Extract the resolution of the period (e.g., PT60M for 60 minutes)
                    data_resolution = period.find('ns:resolution', namespace).text

                    # Iterate over each Point element within the current Period
                    for point in period.findall('ns:Point', namespace):
                        # Extract the position of the point (e.g., 1, 2, 3, ...)
                        position = int(point.find(
                            'ns:position', namespace).text)
                        # Extract the price amount at the current point
                        price_amount = float(point.find(
                            'ns:price.amount', namespace).text)

                        # Append the extracted data as a dictionary to the data list
                        data.append({
                            'start_time': start_time_period,
                            'resolution': data_resolution,
                            'position': position,
                            'price_amount': price_amount
                        })

            # Create a DataFrame from the list of dictionaries
            df = pd.DataFrame(data)

            # Filter data to include only PT60M resolution
            if bidding_zone == 'DE':
                # In the ENTSO-E API transparancy platform, there are two auctions available for DE
                # The first is the 10:15 CE(S)T auction of EXAA and the second is the 12:00 CE(S)T D-1 SDAC
                # For all practical purposes, we will use the 12:00 CE(S)T D-1 SDAC auction, which is provided with
                # resolution PT60M (whereas the 10:15 CE(S)T auction is provided with resolution PT15M)
                df = df[df['resolution'] == 'PT60M']

            # Convert start_time to datetime
            df['start_time'] = pd.to_datetime(df['start_time'])

            # Calculate the timestamp for each data point using the resolution and position
            # Extract the number of minutes from the resolution string (e.g., 'PT60M' -> 60)
            # Multiply the position (adjusted by -1) by the extracted minutes to get the total
            # offset in minutes. Add this offset to the start_time to get the final timestamp
            df['timestamp'] = df['start_time'] + pd.to_timedelta(
                (df['position'] - 1) * df['resolution'].str.extract(r'(\d+)').astype(int)[0],
                unit='m'
            )

            # Set the timestamp as the index
            df.set_index('timestamp', inplace=True)

            # Add data series for trade area to the dataframe
            data_frame[f"{bidding_zone}"] = df['price_amount']
        else:
            logger.error(
                f"Error code {response.status_code} from ENTOS-E API for bidding zone {bidding_zone}.")
            logger.info(f"API Request: {response.url}")

    logger.info("Completed ENTSO-E API requests")
    # Check if data frame has data
    if len(data_frame) == 0:
        logger.warning(
            "No prices was collected from ENTSO-E. Review the status codes from the API calls.")
        return

    # In the entos-e time series, if consecutive time steps have repeated values,
    # only the first value is retained. Subsequent data points will have NaN values
    # in the dataframe. Applying forward fill should correctly handle these NaN values.
    data_frame = data_frame.ffill()

    # Sort columns alphabetically
    data_frame = data_frame[sorted(data_frame.columns)]

    if resolution in ['60min', '60T', '60t', 'hour', '1H', '1h', '1hour', '1HOUR', 'h', 'H']:
        # Resample to hourly data
        data_frame = data_frame.resample('60min').ffill()

    return data_frame


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
    ext_api_config_obj = ext_api_config.ExternalApiConfig()
    # Specify the API endpoints and parameters
    norges_bank_base_url = ext_api_config_obj.get_norgesbank_eur_to_nok_url()

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
