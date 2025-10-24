from datetime import datetime, timedelta
import re
import logging
import pytz

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
    # Support bidding zone input as ["BZ1,BZ2","BZ3"], in addition to regular list
    bidding_zone_input_split = [bz for sublist in bidding_zone_input for bz in sublist.split(",")]
    use_bidding_zone_set = set(bidding_zone_input_split)

    # Define the bidding zones configuration
    bidding_zones_config = {
        "norway": {"NO_1", "NO_2", "NO_3", "NO_4", "NO_5"},
        "denmark": {"DK_1", "DK_2"},
        "sweden": {"SE_1", "SE_2", "SE_3", "SE_4"},
        "nordics": {"NO_1", "NO_2", "NO_3", "NO_4", "NO_5", "DK_1", "DK_2", "SE_1", "SE_2", "SE_3", "SE_4", "FI"},
        "baltics": {"EE", "LT", "LV"},
        "DE": {"DE_LU"},
        "cwe": {"DE_LU", "AT", "BE", "FR", "NL", "PL"},
        "nsl": {"NO_2_NSL"},
    }
    bidding_zones_config["all"] = set().union(*bidding_zones_config.values())

    # Add support for shorthand inputs like "NO2", "DK1", "SE3" and plain "DE" -> "DE_LU"
    use_bidding_zone_set.update({
        f"{m.group(1)}_{int(m.group(2))}" 
        for bz in {bz.strip().upper() for bz in use_bidding_zone_set} 
        if (m := re.match(r'^(NO|DK|SE)(\d+)$', bz))
    })
    if 'DE' in use_bidding_zone_set:
        use_bidding_zone_set.add('DE_LU')

    # Include all relevant bidding zones based on input
    for key in ["norway", "nordics", "DE", "cwe", "all"]:
        if key in use_bidding_zone_set:
            use_bidding_zone_set.update(bidding_zones_config[key])

    # Ensure the final set only contains valid bidding zones
    use_bidding_zone_set &= bidding_zones_config["all"]

    # Check if the resulting set is empty and print a message if so
    if len(use_bidding_zone_set) == 0:
        logger.warning(
            f"No valid bidding zones provided (input: {bidding_zone_input})")
        logger.info(f"Please use at least one of the following: {bidding_zones_config['all']}")

    # Return the list of (sorted) valid bidding zones
    use_bidding_zone_list = list(use_bidding_zone_set)
    use_bidding_zone_list.sort()
    return use_bidding_zone_list


def parse_date_reference(reference):
    """
    Parses a date reference string and returns a formatted date string.
    The function supports the following date formats:
    - "yyyy"
    - "yyyy-mm"
    - "yyyy-mm-dd"
    - "yyyy-mm-dd hh:mm"
    Additionally, it supports special date references:
    - "LAST_SDAC": Returns the next day if the current time is before 13:00, otherwise returns the day after tomorrow.
    - "DAY": Returns today's date.
    - "MONTH": Returns the first day of the current month.
    - "WEEK": Returns the first day of the current week (Monday).
    - "YEAR": Returns the first day of the current year.
    The function also supports relative date references with increments:
    - "DAY+N" or "DAY-N": Adds or subtracts N days from today.
    - "WEEK+N" or "WEEK-N": Adds or subtracts N weeks from today.
    - "MONTH+N" or "MONTH-N": Adds or subtracts N months from today.
    - "YEAR+N" or "YEAR-N": Adds or subtracts N years from today.
    N can be either xD, xW, xM or xY, where x is either "" or an integer.
    Examples: "DAY+2D", "WEEK-2W", "MONTH+3W", "YEAR-Y"

    Args:
        reference (str): The date reference string to parse.
    Returns:
        str: The parsed date in the format 'yyyy-mm-dd'.
    Raises:
        ValueError: If the reference string does not match any valid format or special reference.
    """
    today = datetime.now(pytz.timezone("Europe/Oslo"))
    
    # Define regex patterns for valid date formats
    valid_formats = [
        r"^\d{4}$",  # yyyy
        r"^\d{4}-\d{2}$",  # yyyy-mm
        r"^\d{4}-\d{2}-\d{2}$",  # yyyy-mm-dd
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$"  # yyyy-mm-dd hh:mm
    ]

    # Check if the reference matches any of the valid formats
    for pattern in valid_formats:
        if re.match(pattern, reference):
            # Parse the date based on the matched format
            if pattern == valid_formats[0]:
                return datetime.strptime(reference, "%Y").strftime('%Y-%m-%d')
            elif pattern == valid_formats[1]:
                return datetime.strptime(reference, "%Y-%m").strftime('%Y-%m-%d')
            elif pattern == valid_formats[2]:
                return datetime.strptime(reference, "%Y-%m-%d").strftime('%Y-%m-%d')
            elif pattern == valid_formats[3]:
                return datetime.strptime(reference, "%Y-%m-%d %H:%M").strftime('%Y-%m-%d')

    # Check for special date references 
    base_date = None
    if reference == 'LAST_SDAC':
        # If the current time is before 13:00, return the next day
        # Otherwise, return the day after tomorrow
        if today.hour < 13:
            base_date = today + timedelta(days=1)
        else:
            base_date = today + timedelta(days=2)
        return base_date.strftime('%Y-%m-%d')
    elif reference.startswith('DAY'):
        # Return today's date
        base_date = today
    elif reference.startswith('MONTH'):
        # Return the first day of the current month
        base_date = today.replace(day=1)
    elif reference.startswith('WEEK'):
        # Return the first day of the current week (Monday)
        base_date = today - timedelta(days=today.weekday())
    elif reference.startswith('YEAR'):
        # Return the first day of the current year
        base_date = today.replace(month=1, day=1)
    else:
        raise ValueError(f"Invalid date reference: {reference}")

    if '+' in reference or '-' in reference:
        # Split the reference into base and increment parts
        parts = re.split(r'(\+|-)', reference)
        increment = parts[-1]
        sign = 1 if '+' in reference else -1

        if increment.endswith('D'):
            # Add or subtract days
            days = int(increment[:-1]) if increment[:-1] != '' else 1
            base_date += timedelta(days=days * sign)
        elif increment.endswith('W'):
            # Add or subtract weeks
            weeks = int(increment[:-1]) if increment[:-1] else 1
            base_date += timedelta(weeks=weeks * sign)
        elif increment.endswith('M'):
            # Add or subtract months
            months = int(increment[:-1]) if increment[:-1] else 1
            for _ in range(abs(months)):
                if sign == 1:
                    if base_date.month == 12:
                        base_date = base_date.replace(year=base_date.year + 1, month=1)
                    else:
                        base_date = base_date.replace(month=base_date.month + 1)
                else:
                    if base_date.month == 1:
                        base_date = base_date.replace(year=base_date.year - 1, month=12)
                    else:
                        base_date = base_date.replace(month=base_date.month - 1)
        elif increment.endswith('Y'):
            # Add or subtract years
            years = int(increment[:-1]) if increment[:-1] else 1
            base_date = base_date.replace(year=base_date.year + (years * sign))

    return base_date.strftime('%Y-%m-%d')

def convert_date_range(start, end):
    """
    Converts a date range from string references to date objects.

    Args:
        start (str): The start date reference in string format.
        end (str): The end date reference in string format.

    Returns:
        tuple: A tuple containing the start and end dates as date objects.
    
    Raises:
        ValueError: If the start date is not before the end date or if they are not at least one day apart.
    """
    start_date = parse_date_reference(start)
    end_date = parse_date_reference(end)

    # Convert the dates to datetime objects for comparison
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    # Check if the start date is before the end date and at least one day apart
    if start_date_obj >= end_date_obj:
        raise ValueError("The start date must be before the end date and at least one day apart.")
    if (end_date_obj - start_date_obj).days < 1:
        raise ValueError("The start date must be before the end date and at least one day apart.")

    return start_date, end_date