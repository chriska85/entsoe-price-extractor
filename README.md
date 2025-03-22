# entsoe-price-extractor
Simple python script for extracting day ahead prices from the Entso-e Transparency Platform using its Restful API

# Setup
There are two steps needed to use this package.

## Step 1: Setup a Virtual Environment with Dependencies
1. **Make a virtual environment**:
   - Open a command line window.
   - Navigate to this project's folder.
   - Type: `python -m venv venv`
2. **Activate the new environment**:
   - In the command line window, type: `.\venv\Scripts\activate`
3. **Install pip-tools**:
   - In the command line window, type: `pip install pip-tools`
4. **Install dependencies**:
   - In the command line window, type: `pip-sync`
   - This will install packages found in `requirements.txt` in the active environment.

## Step 2: Generate an ENTSO-E Security Token and Save it in the `.env` File
1. **Generate a security token**:
   - Follow this guide: [How to get a security token](https://uat-transparency.entsoe.eu/content/static_content/Static%20content/web%20api/how_to_get_security_token.html)
2. **Store in `.env`**:
   - In the `.env-sample` file, replace the placeholder with your token (removing the `<>` brackets): `MY_ENTSOE_TOKEN='<Insert your token here>'`
   - Rename the file as `.env`
   - Note: The ENTSO-E security token is personal and should not be committed to a git repository.


# Price Extraction Script `entsoe_price_extract_cli`
This script extracts day-ahead electricity prices from the ENTSO-E transparency platform for specified bidding zones and date ranges. It can also convert prices to NOK and generate interactive plots.

## Usage
### Command Line Arguments
- `-a`, `--bidding_zone`: Name of bidding zones or keywords (`all`, `nordics`, `norway`, `baltics` and/or `cwe`). Default is `norway`.
- `-s`, `--start`: Start date. Optional (default: "DAY"). Format "yyyy-mm-dd" or BASE +/- RELATIVE. Examples:
  - `"2025-03-23"`: Specific date
  - `"2025-03"`: Specific date (first day of month)
  - `"2025"`: Specific date (first day of year)
  - `"DAY"`: Today.
  - `"DAY+2D"`: Day after tomorrow.
  - `"YEAR"`: January 1st of the current year.
  - `"YEAR+W"`: January 8th of the current year.
  - `"YEAR-W"`: Seven days into the previous year.
  - `"YEAR-2Y"`: January 1st two years ago.
- `-e`, `--end`: End date. Optional (default: "LAST_SDAC"). Format "yyyy-mm-dd" or BASE +/- RELATIVE. Examples:
  - `"2024-01-01"`: Specific date.
  - `"DAY"`: Today.
  - `"DAY+2D"`: Day after tomorrow.
  - `"YEAR"`: January 1st of the current year.
  - `"YEAR+W"`: January 8th of the current year.
  - `"YEAR-W"`: Seven days into the previous year.
  - `"YEAR-2Y"`: January 1st two years ago.
  - `"LAST_SDAC"`: Special keyword for the last Single Day-Ahead Coupling auction.
- `-nok`, `--convert_to_nok`: Fetch EUR to NOK conversion rates and return prices as NOK/kWh (optional).
- `-p`, `--plot`: Generate an interactive plot using the Plotly package (optional).
- `-o`, `--output`: Path of the output file, including filename. Example: `./output/prices.csv` (optional).

### Example Command 
Retriving day-ahead prices for Norway's bidding zones NO1 and NO2, and Germany for today until the wnd of the last Single Day-Ahead Couling auction, and plotting results.
```sh
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s DAY -e LAST_SDAC -p
```
Retriving day-ahead prices for Norway's bidding zones NO1 and NO2, and Germany from January 1st this year until the start if this month, and plotting results.
```sh
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s YEAR -e MONTH -p
```
Retriving day-ahead prices for Norway's bidding zones and Germany on December 12, 2024, converting to NOK/kWh, and plotting results.
```sh
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s 2024-12-12 -e 2024-12-13 -p -nok
```
Retriving day-ahead prices for Norway's bidding zones in December 2024, and storing results (current folder).
```sh
python entsoe_price_extract_cli.py -a norway -s 2024-12 -e 2025-01 -o ./norway_Dec_2024_DAprices_EURMWh.csv
```

### Notes
- The bidding zone argument accepts various combinations of keywords and bidding zone names. These are validated before they are passed to the core fuction communicating with the ENTSO-E rest API.
- The output directory must exist if an output file path is specified. If writing to the current folder add the prefix `./` to the `-o` argument.

# Use of the `fetch_day_ahead_prices` function (see `entsoe_price_extract_demo`)
The main function used to collect prices is the `fetch_day_ahead_prices` found in `core_functions`. The script `entsoe_price_extract_demo` showcase the use of this function.