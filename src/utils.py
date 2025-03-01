from loguru import logger
import random
import time
from config import MIN_DELAY, MAX_DELAY, LOG_FILE

# Configure logging
logger.add(LOG_FILE, rotation="1 MB")

def log(message):
    """Log a message to the log file."""
    logger.info(message)

def random_delay():
    """Add a random delay to mimic human behavior."""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    log(f"Delaying for {delay:.2f} seconds")
    time.sleep(delay)

def random_action(reddit, submission):
    """Perform a random action to mimic human behavior."""
    actions = [
        ("upvote", lambda: submission.upvote()),
        ("downvote", lambda: submission.downvote()),
        ("scroll", lambda: None),  # Simulate scrolling (no action)
    ]
    action_name, action_func = random.choice(actions)
    log(f"Performing random action: {action_name}")
    try:
        action_func()
    except Exception as e:
        log(f"Error during random action {action_name}: {e}")
