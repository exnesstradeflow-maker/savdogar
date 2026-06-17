import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

ADMIN_USERNAME = os.environ.get("ADMIN", "@samir_axii")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0")) or None
STAR_TO_SOM = int(os.environ.get("STAR_TO_SOM", "195"))
CACHE_TTL = int(os.environ.get("CACHE_TTL", "60"))
