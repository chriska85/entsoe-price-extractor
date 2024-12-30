"""
Utility functions for extracting prices from ENTSO-E using their Rest API

This file contains the following functions:

    * fetch_day_ahead_prices - fetches DA electricity prices from ENTOS-E
    * fetch_conversion_rates - fetches EUR to NOK conversion rates fo
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
    # Convert the input list to a set for efficient operations
    use_bidding_zone_set = set(bidding_zone_input)

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
    Fetches day-ahead electricity prices from ENTSO-E using their Restful API.
    Results in EUR/MWh by default, but can be converted to NOK/kWh using exhange rates
    from Norges Bank.

    Args:
        bidding_zone_list (list[str]): A list of bidding zones to query for data.
        start_date (str): The start date in the format '%Y-%m-%d'.
        end_date (str): The end date in the format '%Y-%m-%d'.
        token (str): The token used for authorizing requests to ENTSO-E.
        convert_to_nok (bool): A boolean controlling conversion to NOK/kWh.

    Returns:
        pd.DataFrame: A Pandas DataFrame (time-indexed, "Europe/Oslo" time zone) containing
        hourly day-ahead prices for the specified bidding zones and date range.
    """
    # Convert start_time and end_time to UTC format expected by ENTSO-E
    cet_tz = pytz.timezone("Europe/Oslo")
    start_dt_cet = cet_tz.localize(datetime.strptime(start_time, "%Y-%m-%d"))
    end_dt_cet = cet_tz.localize(datetime.strptime(end_time, "%Y-%m-%d"))

    if end_dt_cet < start_dt_cet:
        logger.warning(
            f"End time ({end_dt_cet}) is set prior to start time ({start_dt_cet}).")
        logger.info("Returning without value.")
        return

    end_dt_cet_request = end_dt_cet - timedelta(hours=1)
    # Convert to UTC as this is the time index used
    start_dt_utc = start_dt_cet.astimezone(pytz.utc).strftime("%Y%m%d%H%M")
    end_dt_utc = end_dt_cet_request.astimezone(pytz.utc).strftime("%Y%m%d%H%M")

    data_frame = pd.DataFrame()

    entsoe_payload = {
        "securityToken": token,
        "documentType": "A44",
        "in_Domain": None,
        "out_Domain": None,
        "periodStart": start_dt_utc,
        "periodEnd": end_dt_utc,
    }

    ext_api_config_obj = ext_api_config.ExternalApiConfig()
    url = ext_api_config_obj.get_entsoe_web_url()

    logger.info("Fetching prices from ENTSO-E's Transparency Platform.")
    logger.info(f"ENTSO-E's API url: {url}")
    logger.info(f"Starting time: {start_dt_cet}")
    logger.info(f"End time: {end_dt_cet}")
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
                    resolution = period.find('ns:resolution', namespace).text

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
                            'resolution': resolution,
                            'position': position,
                            'price_amount': price_amount
                        })

            # Create a DataFrame from the list of dictionaries
            df = pd.DataFrame(data)

            # Filter data to include only PT60M resolution
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
            # Convert the timezone and append to data_frame
            df = df.tz_convert('Europe/Oslo')
            # Add data series for trade area to the dataframe
            data_frame[f"{bidding_zone}"] = df['price_amount']
        else:
            logger.error(
                f"Error code {response.status_code} from ENTOS-E API for bidding zone {bidding_zone}.")
            logger.info(f"API Request: {response.url}")

    # Check if data frame has data
    if len(data_frame) == 0:
        logger.warning(
            "No prices was collected from ENTSO-E. Review the status codes from the API calls.")
        return

    # In the entos-e time series, if consecutive time steps have repeated values,
    # only the first value is retained. Subsequent data points will have NaN values
    # in the dataframe. Applying forward fill should correctly handle these NaN values.
    data_frame = data_frame.ffill()

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
            exchange_rates_hourly = exchange_rates_hourly[data_frame.index]
            data_frame = data_frame.mul(exchange_rates_hourly, axis=0) / 1000

    data_frame.attrs['unit'] = 'EUR/MWh' if not convert_to_nok else 'NOK/kWh'
    # Sort columns alphabetically
    data_frame = data_frame[sorted(data_frame.columns)]

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

    # Check if start_date and end_date fall on a weekend
    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")

    if start_datetime.weekday() >= 5:
        # Adjust start_date to the previous Friday
        start_datetime -= timedelta(days=start_datetime.weekday() - 4)
    if end_datetime.weekday() >= 5:
        # Adjust end_date to the following Monday
        end_datetime += timedelta(days=7 - end_datetime.weekday())

    start_date = start_datetime.strftime("%Y-%m-%d")
    end_date = end_datetime.strftime("%Y-%m-%d")

    norges_bank_payload = {
        "format": "sdmx-json",
        "startPeriod": start_date,
        "endPeriod": end_date,
    }

    # Send a GET request to Norges Bank for currency conversion

    norges_bank_response = requests.get(
        norges_bank_base_url, params=norges_bank_payload, timeout=20
    )

    # Extract the exhange rates from Norges Bank (if successful response)
    if norges_bank_response.status_code == 200:
        norges_bank_data = norges_bank_response.json()

        if "data" in norges_bank_data and "dataSets" in norges_bank_data["data"]:
            data_sets = norges_bank_data["data"]["dataSets"]

            if data_sets:
                series = data_sets[0]["series"]["0:0:0:0"]["observations"]
                observation_values = norges_bank_data["data"]["structure"][
                    "dimensions"
                ]["observation"][0]["values"]
                exchange_rate_dates = {
                    value["id"]: value["name"] for value in observation_values
                }

                # Extract relevant exchange rates from Norges Bank response
                exchange_rates = {}

                for rate_key, rate_value in zip(
                    exchange_rate_dates.keys(), series.values()
                ):
                    rate_date = exchange_rate_dates[rate_key]
                    rate = float(rate_value[0])
                    exchange_rates[rate_date] = rate

        date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        series_data = []

        # Fill in missing values (weekend days do not have observations from Norges Bank)
        for date in date_range:
            date_str = date.strftime("%Y-%m-%d")

            if date_str in exchange_rates:
                rate = exchange_rates[date_str]
                series_data.append(rate)
                previous_rate = rate
            else:
                if previous_rate is not None:
                    series_data.append(previous_rate)

        # Return values as pandas series
        series = pd.Series(series_data, index=date_range)
        series.index = series.index.tz_localize('Europe/Oslo')
        return series
    else:
        logger.error(f"Error code {norges_bank_response.status_code} from Norges Bank API request")
        logger.info(f"API Request: {norges_bank_response.url}")
