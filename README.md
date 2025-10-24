# entsoe-price-extractor
Simple Python tool to download day‑ahead electricity prices from the [ENTSO‑E Transparency Platform](https://newtransparency.entsoe.eu/) powered by [entsoe-py](https://github.com/EnergieID/entsoe-py/). This tool is designed to make it easy to retrieve day‑ahead electricity prices without writing Python code. It provides a user‑friendly command‑line interface for quick and efficient data extraction.

This README explains how to set up the project, obtain the required security token, run the command‑line script, and use the core function. Step‑by‑step examples are included to help users get started.

## ✅ Prerequisites
- Python 3.9+ installed and on PATH. Check with:
   ```sh
   python --version
   ```
- A free ENTSO‑E API token (
Simple Python tool to download day‑ahead electricity prices from the [ENTSO‑E Transparency Platform](https://newtransparency.entsoe.eu/) powered by [entsoe-py](https://github.com/EnergieID/entsoe-py/). The aim of this tool is simply to allow easy extraction of day-ahead prices without having to progam in python by exposing it thourgh an easy to use commandline client.

This README explains how to set up the project, obtain the required security token, run the command‑line script, and use the core function — with step‑by‑step examples for users new to Python.

## ✅ Prerequisites
- Python 3.9+ installed and on PATH. Check with:
   ```sh
   python --version
   ```
- A free ENTSO‑E API token (see below).

## 🚀 Setup
1) Create and activate a virtual environment

- Windows (PowerShell, CMD)
   ```cmd
   python -m venv venv
   .\venv\Scripts\activate
   ```
- macOS / Linux
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2) Install dependencies
- If requirements.txt is included:
   ```bash
   pip install -r requirements.txt
   ```

3) Generate and store your ENTSO‑E token 🔒
- Follow: https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token
- Create a file named `.env` in the project root with this line (replace with your token; no angle brackets):
   ```
   MY_ENTSOE_TOKEN=your_actual_token_here
   ```
- Important: Do not commit `.env` to version control. Keep the token private.

## ▶️ Basic usage
Activate the virtual environment before running commands (see step 1).

Command-line script: `entsoe_price_extract_cli.py`  
- Script purpose: download day‑ahead prices for one or more bidding zones, optionally convert to NOK and/or generate interactive plots.

General options (common)
- `-a`, `--bidding_zone` : bidding zone names or keywords (examples: NO1, NO2, DE) or keyword groups: `all`, `nordics`, `norway`, `baltics`, `cwe`. Default: `norway`.
- `-s`, `--start` : start date. Default: `DAY`. See date formats below.
- `-e`, `--end` : end date. Default: `LAST_SDAC` (last Single Day‑Ahead Coupling auction). See date formats below.
- `-nok`, `--convert_to_nok` : convert EUR to NOK (requires currency rates).
- `-p`, `--plot` : show an interactive Plotly plot (requires plotly).
- `-o`, `--output` : output file path (directory must exist). Example: `./output/prices.csv`

## 📅 Date formats and keywords
- Exact dates:
   - `YYYY-MM-DD` e.g. `2024-12-12`
   - `YYYY-MM` (interpreted as the first day of month)
   - `YYYY` (first day of year)
- Relative / keywords:
   - `DAY` — today
   - `DAY+2D` — two days from today
   - `YEAR` — January 1 of the current year
   - `YEAR+W` — January 8 of the current year
   - `YEAR-W` — seven days before Jan 1 of current year
   - `YEAR-2Y` — Jan 1 two years ago
   - `LAST_SDAC` — last Single Day-Ahead Coupling auction (special endpoint keyword)

Combine these examples as start/end values when calling the CLI.

## 💡 Examples
1) Today for Norway (NO1 and NO2) and Germany (DE), plot results:
```bash
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s DAY -e LAST_SDAC -p
```

2) From start of the year to start of this month, plot:
```bash
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s YEAR -e MONTH -p
```

3) Single day, convert to NOK and plot:
```bash
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s 2024-12-12 -e 2024-12-13 -p -nok
```

4) Norway for December 2024 and save CSV in current folder:
```bash
python entsoe_price_extract_cli.py -a norway -s 2024-12 -e 2025-01 -o ./norway_Dec_2024_DA_prices_EURMWh.csv
```

## 📝 Notes and tips
- Always activate the virtual environment before running the script so installed dependencies are used.
- If currency conversion (-nok) fails, check network access and that any external conversion service used by the script is reachable.
- Output directory must exist beforehand. Use `mkdir output` or create your desired folder.

## 🧰 Using the core function in Python
- The package exposes a function (from core_functions) named `fetch_day_ahead_prices`. A simple Python example:
   ```python
   from core_functions import fetch_day_ahead_prices

   # Example: fetch Norway (NO1) prices for a single day
   df = fetch_day_ahead_prices(bidding_zones=["NO1"], start="2024-12-12", end="2024-12-13", convert_to_nok=False)
   print(df.head())
   ```
- The demo script `entsoe_price_extract_demo.py` shows common usage patterns; run it to see sample code.

## 🐞 Troubleshooting
- "403 / unauthorized": check your ENTSO‑E token in `.env` and ensure it's valid and active.
- "ModuleNotFoundError": ensure you activated the venv and installed requirements into it.
- "No data returned": verify the date range and bidding zone identifiers, and that the API supports the requested range.

## 🤝 Contributing and license
- Treat your ENTSO‑E token as secret; never commit it.
- If you modify the repo, follow the project's contribution guidelines (if present) and add tests where applicable.

If you want, provide the OS you use and any errors you see and an example command you tried; guidance can be tailored to that environment.
e below).

## 🚀 Setup
1) Create and activate a virtual environment

- Windows (PowerShell, CMD)
   ```cmd
   python -m venv venv
   .\venv\Scripts\activate
   ```
- macOS / Linux
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2) Install dependencies
- If requirements.txt is included:
   ```bash
   pip install -r requirements.txt
   ```

3) Generate and store your ENTSO‑E token 🔒
- Follow: https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token
- Create a file named `.env` in the project root with this line (replace with your token; no angle brackets):
   ```
   MY_ENTSOE_TOKEN=your_actual_token_here
   ```
- Important: Do not commit `.env` to version control. Keep the token private.

## ▶️ Basic usage
Activate the virtual environment before running commands (see step 1).

Command-line script: `entsoe_price_extract_cli.py`  
- Script purpose: download day‑ahead prices for one or more bidding zones, optionally convert to NOK and/or generate interactive plots.

General options (common)
- `-a`, `--bidding_zone` : bidding zone names or keywords (examples: NO1, NO2, DE) or keyword groups: `all`, `nordics`, `norway`, `baltics`, `cwe`. Default: `norway`.
- `-s`, `--start` : start date. Default: `DAY`. See date formats below.
- `-e`, `--end` : end date. Default: `LAST_SDAC` (last Single Day‑Ahead Coupling auction). See date formats below.
- `-nok`, `--convert_to_nok` : convert EUR to NOK (requires currency rates).
- `-p`, `--plot` : show an interactive Plotly plot (requires plotly).
- `-o`, `--output` : output file path (directory must exist). Example: `./output/prices.csv`

## 📅 Date formats and keywords
- Exact dates:
   - `YYYY-MM-DD` e.g. `2024-12-12`
   - `YYYY-MM` (interpreted as the first day of month)
   - `YYYY` (first day of year)
- Relative / keywords:
   - `DAY` — today
   - `DAY+2D` — two days from today
   - `YEAR` — January 1 of the current year
   - `YEAR+W` — January 8 of the current year
   - `YEAR-W` — seven days before Jan 1 of current year
   - `YEAR-2Y` — Jan 1 two years ago
   - `LAST_SDAC` — last Single Day-Ahead Coupling auction (special endpoint keyword)

Combine these examples as start/end values when calling the CLI.

## 💡 Examples
1) Today for Norway (NO1 and NO2) and Germany (DE), plot results:
```bash
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s DAY -e LAST_SDAC -p
```

2) From start of the year to start of this month, plot:
```bash
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s YEAR -e MONTH -p
```

3) Single day, convert to NOK and plot:
```bash
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s 2024-12-12 -e 2024-12-13 -p -nok
```

4) Norway for December 2024 and save CSV in current folder:
```bash
python entsoe_price_extract_cli.py -a norway -s 2024-12 -e 2025-01 -o ./norway_Dec_2024_DA_prices_EURMWh.csv
```

## 📝 Notes and tips
- Always activate the virtual environment before running the script so installed dependencies are used.
- If currency conversion (-nok) fails, check network access and that any external conversion service used by the script is reachable.
- Output directory must exist beforehand. Use `mkdir output` or create your desired folder.

## 🧰 Using the core function in Python
- The package exposes a function (from core_functions) named `fetch_day_ahead_prices`. A simple Python example:
   ```python
   from core_functions import fetch_day_ahead_prices

   # Example: fetch Norway (NO1) prices for a single day
   df = fetch_day_ahead_prices(bidding_zones=["NO1"], start="2024-12-12", end="2024-12-13", convert_to_nok=False)
   print(df.head())
   ```
- The demo script `entsoe_price_extract_demo.py` shows common usage patterns; run it to see sample code.

## 🐞 Troubleshooting
- "403 / unauthorized": check your ENTSO‑E token in `.env` and ensure it's valid and active.
- "ModuleNotFoundError": ensure you activated the venv and installed requirements into it.
- "No data returned": verify the date range and bidding zone identifiers, and that the API supports the requested range.

## 🤝 Contributing and license
- Treat your ENTSO‑E token as secret; never commit it.
- If you modify the repo, follow the project's contribution guidelines (if present) and add tests where applicable.

If you want, provide the OS you use and any errors you see and an example command you tried; guidance can be tailored to that environment.
