import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Reddit credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

# Hugging Face API
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_MODEL = "distilgpt2"  # Lightweight model for comment generation

# Captcha services with API keys
CAPTCHA_SERVICES = {
    "capmonster": os.getenv("CAPMONSTER_API_KEY"),
    "twocaptcha": os.getenv("TWOCAPTCHA_API_KEY"),
    "anticaptcha": os.getenv("ANTICAPTCHA_API_KEY"),
    "deathbycaptcha": os.getenv("DEATHBYCAPTCHA_API_KEY"),
    "solvecaptcha": os.getenv("SOLVECAPTCHA_API_KEY"),
    "azcaptcha": os.getenv("AZCAPTCHA_API_KEY"),
}

# Controller API
CONTROLLER_URL = os.getenv("CONTROLLER_URL")
WORKER_ID = os.getenv("WORKER_ID")

# Other settings
LOG_FILE = "logs/worker.log"
ENGAGEMENT_CHECK_INTERVAL = 3600  # Check engagement every hour (in seconds)
MIN_DELAY = 5  # Minimum delay in seconds
MAX_DELAY = 15  # Maximum delay in seconds
WARM_UP_DAYS = 4  # Days to perform only non-commenting actions
