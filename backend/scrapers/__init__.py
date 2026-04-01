from .shopify import ShopifyScraper
from .vegnonveg import VegNonVegScraper
from .culturecircle import CultureCircleScraper
from .hiyest import HiyestScraper

# ====== BRAND REGISTRY ======
# All Shopify-based brands use the generic ShopifyScraper
SHOPIFY_BRANDS = [
    {"key": "crepdog_crew", "name": "Crep Dog Crew", "store_key": "CREPDOG_CREW", "url": "https://crepdogcrew.com"},
    {"key": "almost_gods", "name": "Almost Gods", "store_key": "ALMOST_GODS", "url": "https://almostgods.com"},
    {"key": "code_brown", "name": "Code Brown", "store_key": "CODE_BROWN", "url": "https://codebrwn.com"},
    {"key": "jaywalking", "name": "Jaywalking", "store_key": "JAYWALKING", "url": "https://jaywalking.in"},
    {"key": "huemn", "name": "Huemn", "store_key": "HUEMN", "url": "https://huemn.in"},
    {"key": "noughtone", "name": "Noughtone", "store_key": "NOUGHTONE", "url": "https://noughtone.in"},
    {"key": "bluorng", "name": "Bluorng", "store_key": "BLUORNG", "url": "https://bluorng.com"},
    {"key": "capsul", "name": "Capsul", "store_key": "CAPSUL", "url": "https://shopcapsul.com"},
    {"key": "urban_monkey", "name": "Urban Monkey", "store_key": "URBAN_MONKEY", "url": "https://urbanmonkey.com"},
    {"key": "house_of_koala", "name": "House of Koala", "store_key": "HOUSE_OF_KOALA", "url": "https://houseofkoala.com"},
    {"key": "farak", "name": "Farak", "store_key": "FARAK", "url": "https://farak.co"},
]

# Build SCRAPERS dict
SCRAPERS: dict = {}

for brand in SHOPIFY_BRANDS:
    SCRAPERS[brand["key"]] = lambda b=brand: ShopifyScraper(b["name"], b["store_key"], b["url"])

# Non-Shopify scrapers
SCRAPERS["veg_non_veg"] = VegNonVegScraper
SCRAPERS["culture_circle"] = CultureCircleScraper
SCRAPERS["hiyest"] = HiyestScraper
