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
- `-s`, `--start`: Start date in the format `yyyy-mm-dd`. Example: `2024-01-01`. Default is `2024-12-12`.
- `-e`, `--end`: End date in the format `yyyy-mm-dd`. Example: `2024-02-01`. Default is `2024-12-13`.
- `-nok`, `--convert_to_nok`: Fetch EUR to NOK conversion rates and return prices as NOK/kWh (optional).
- `-p`, `--plot`: Generate an interactive plot using the Plotly package (optional).
- `-o`, `--output`: Path of the output file. Example: `./output/prices.csv` (optional).

### Example Command (Retriving day-ahead prices for Norway's bidding zones and Germany on December 12, 2024. Results are plotted and stored to file.)

```sh
python entsoe_price_extract_cli.py -a norway,DE -s 2024-12-12 -e 2024-12-13 -p -o ./output/norway_Dec12_2024_DAprices_EURMWh.csv
```

### Notes

- The bidding zone argument accepts various combinations of keywords and bidding zone names. These are validated before they are passed to the core fuction communicating with the ENTSO-E rest API.
- The output directory must exist if an output file path is specified.

# Use of the `fetch_day_ahead_prices` function (see `entsoe_price_extract_demo`)
The main function used to collect prices is the `fetch_day_ahead_prices` found in `core_functions`. The script `entsoe_price_extract_demo` showcase the use of this function.