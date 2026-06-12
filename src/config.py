BASE_URL = "https://www.goldenpages.uz"
PHONE_API_URL = BASE_URL + "/scripts/company_data/"

CITY_IDS: dict[str, int] = {
    "tashkent": 296,
    "samarkand": 322,
}

REGION_IDS: dict[str, int] = {
    "samarkand_region": 333,
}

DEFAULT_DELAY_MIN: float = 1.5
DEFAULT_DELAY_MAX: float = 3.5

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
