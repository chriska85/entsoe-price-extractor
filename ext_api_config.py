class ExternalApiConfig:

    def __init__(self):
        self.bidding_zone_to_eic_code_map = {
            "NO1": "10YNO-1--------2",
            "NO2": "10YNO-2--------T",
            "NO3": "10YNO-3--------J",
            "NO4": "10YNO-4--------9",
            "NO5": "10Y1001A1001A48H",
            "SE1": "10Y1001A1001A44P",
            "SE2": "10Y1001A1001A45N",
            "SE3": "10Y1001A1001A46L",
            "SE4": "10Y1001A1001A47J",
            "DK1": "10YDK-1--------W",
            "DK2": "10YDK-2--------M",
            "FI": "10YFI-1--------U",
            "NL": "10YNL----------L",
            'DE': '10Y1001A1001A82H',
            "FR": "10YFR-RTE------C",
            "BE": "10YBE----------2",
            "AT": "10YAT-APG------L",
            "EE": "10Y1001A1001A39I",
            "LT": "10YLT-1001A0008Q",
            "LV": "10YLV-1001A00074",
            "PL": "10YPL-AREA-----S",
        }
        # 'DE': '10Y1001A1001A82H', 'UK':'10YGB----------A', # DE in 15 min resolution, UK no data
        # ENTSO-E api codes available here:
        # https://www.entsoe.eu/data/energy-identification-codes-eic/eic-approved-codes/

        self.entsoe_url = "https://web-api.tp.entsoe.eu/api"

        self.entsoe_price_ns_conf = {
            "ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"
        }

        self.norgesbank_eur_to_nok_url = "https://data.norges-bank.no/api/data/EXR/B.EUR.NOK.SP"

    def get_bidding_zone_to_eic_code_map(self):
        return self.bidding_zone_to_eic_code_map

    def get_entsoe_web_url(self):
        return self.entsoe_url

    def get_entsoe_price_namespace_conf(self):
        return self.entsoe_price_ns_conf

    def get_norgesbank_eur_to_nok_url(self):
        return self.norgesbank_eur_to_nok_url
