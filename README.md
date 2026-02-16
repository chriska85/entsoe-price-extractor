# entsoe-price-extractor
Simple Python tool to download day‑ahead electricity prices from the [ENTSO‑E Transparency Platform](https://newtransparency.entsoe.eu/) powered by [entsoe-py](https://github.com/EnergieID/entsoe-py/). This tool is designed to make it easy to retrieve day‑ahead electricity prices without writing Python code. It provides a user‑friendly command‑line interface for quick and efficient data extraction.

This README explains how to set up the project, obtain the required security token, run the command‑line script, and use the core function. Step‑by‑step examples are included to help users get started.

## ✅ Prerequisites

- Python 3.9+ installed and on PATH
   ```sh
   python --version
   ```
- A free ENTSO‑E API token (see [Setup](#-setup) section)

## 🚀 Setup

### 1. Create and activate a virtual environment

**Windows (PowerShell, CMD)**
```cmd
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```


### 2. Install dependencies
Install `uv` 
```bash
pip install uv
```

Maintaing dependencies using `uv` 
```bash
uv pip sync requirements.txt
```


### 3. Generate and store your ENTSO‑E token 🔒

- Follow: [How to get security token](https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token)
- Create a `.env` file in the project root:
   ```
   MY_ENTSOE_TOKEN=your_actual_token_here
   ```
- **Important:** Do not commit `.env` to version control. Keep the token private.

## ▶️ Basic usage

Activate the virtual environment before running commands (see [Setup](#-setup)).

### Command-line script: `entsoe_price_extract_cli.py`

Download day‑ahead prices for one or more bidding zones, optionally convert to NOK and/or generate interactive plots.

### General options

| Option | Short | Description |
|--------|-------|-------------|
| `--bidding_zone` | `-a` | Bidding zone names or keywords: `NO1`, `NO2`, `DE`, or groups: `all`, `nordics`, `norway`, `baltics`, `cwe` (default: `norway`) |
| `--start` | `-s` | Start date (default: `DAY`) |
| `--end` | `-e` | End date (default: `LAST_SDAC`) |
| `--convert_to_nok` | `-nok` | Convert EUR to NOK |
| `--plot` | `-p` | Show interactive Plotly plot |
| `--output` | `-o` | Output file path (directory must exist) |
| `--resolution` | `-r` | Price output time resolution, e.g. `15min` or `60min` (default: `SDAC_MTU`) |

## 📅 Date formats and keywords

**Exact dates:**
- `YYYY-MM-DD` – e.g., `2024-12-12`
- `YYYY-MM` – first day of month
- `YYYY` – first day of year

**Relative/keywords and offset:**
- `DAY` – today
- `DAY+2D` – two days from today
- `YEAR` – January 1 of current year
- `YEAR+W` – January 8 of current year
- `YEAR-W` – seven days before Jan 1
- `YEAR-2Y` – Jan 1 two years ago
- `LAST_SDAC` – last Single Day-Ahead Coupling auction (does not work with time offset)


## 💡 Examples

```bash
# Today for Norway and Germany with plot
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s DAY -e LAST_SDAC -p

# Year-to-date with plot
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s YEAR -e LAST_SDAC -p

# Single day, convert to NOK and plot
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s 2024-12-12 -e 2024-12-13 -nok -p

# Last ten days up until last SDAC plot
python entsoe_price_extract_cli.py -a NO1 NO2 DE -s DAYS-10D -e LAST_SDAC -p

# December 2024 data, save as CSV
python entsoe_price_extract_cli.py -a norway -s 2024-12 -e 2025-01 -o ./output/prices.csv
```

## 📝 Notes and tips

- Always activate the virtual environment before running the script
- If currency conversion fails, check network access and external service availability
- Output directory must exist beforehand (`mkdir output`)
- Treat your ENTSO‑E token as secret; never commit it

## 🧰 Using the core function in Python

The package exposes `fetch_day_ahead_prices` from `core_functions`:

```python
from core_functions import fetch_day_ahead_prices

# Fetch Norway (NO1) prices for a single day
df = fetch_day_ahead_prices(
      bidding_zones=["NO1"],
      start="2024-12-12",
      end="2024-12-13",
      convert_to_nok=False
)
print(df.head())
```

See `entsoe_price_extract_demo.py` for more usage patterns.

## 🐞 Troubleshooting

| Error | Solution |
|-------|----------|
| `requests.exceptions.HTTPError: 401` | Verify your ENTSO-E token in `.env` file: `MY_ENTSOE_TOKEN=<TOKEN>` |
| `NameResolutionError` | Check your internet connection and DNS resolution |
| `ModuleNotFoundError` | Activate the virtual environment and install requirements |
| `entsoe.exceptions.NoMatchingDataError` | Verify date range and bidding zone identifiers are correct |