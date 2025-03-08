import praw
import requests
import threading
import time
from ./config/config import *
from utils import log, random_delay, random_action
from engagement_tracker import EngagementTracker
from huggingface_hub import InferenceClient
import pytesseract
from PIL import Image

class RedditBot:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
            user_agent="reddit-super-manager-bot"
        )
        self.tracker = EngagementTracker()
        self.hf_client = InferenceClient(model=HUGGINGFACE_MODEL, token=HUGGINGFACE_API_KEY)
        self.start_time = time.time()
        self.register_with_controller()
        threading.Thread(target=self.tracker.start, daemon=True).start()

    def register_with_controller(self):
        """Register the worker with the Controller."""
        try:
            response = requests.post(
                f"{CONTROLLER_URL}/register",
                json={"worker_id": WORKER_ID}
            )
            response.raise_for_status()
            log("Successfully registered with Controller")
        except Exception as e:
            log(f"Failed to register with Controller: {e}")
            raise

    def is_maintenance_mode(self):
        try:
            response = requests.get(f"{CONTROLLER_URL}/maintenance/status")
            return response.json().get("maintenance", False)
        except Exception as e:
            log(f"Error checking maintenance: {e}")
            return False

    def fetch_tasks(self):
        """Fetch tasks from the Controller."""
        try:
            response = requests.get(f"{CONTROLLER_URL}/tasks?worker_id={WORKER_ID}")
            response.raise_for_status()
            tasks = response.json()
            log(f"Fetched tasks: {tasks}")
            return tasks
        except Exception as e:
            log(f"Failed to fetch tasks: {e}")
            return []

    def generate_comment(self, post_content, promotion_link):
        """Generate a comment using Hugging Face API."""
        prompt = f"Generate a natural, casual Reddit comment based on this post content: '{post_content}'. Subtly include this promotion link: {promotion_link}."
        try:
            comment = self.hf_client.text_generation(prompt, max_length=100)
            log(f"Generated comment: {comment}")
            return comment.strip()
        except Exception as e:
            log(f"Failed to generate comment: {e}")
            return f"Nice post! Check this out: {promotion_link}"

    def solve_captcha_with_tesseract(self, image_path):
        """Solve a text-based CAPTCHA using Tesseract OCR."""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, config='--psm 8')  # Single word mode
            log(f"Tesseract CAPTCHA solution: {text.strip()}")
            return text.strip()
        except Exception as e:
            log(f"Failed to solve CAPTCHA with Tesseract: {e}")
            return ""

def post_comment(self, submission, comment_text):
    """Post a comment on Reddit, handling CAPTCHAs automatically if needed."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Attempt to post the comment using PRAW's reply method
            comment = submission.reply(comment_text)
            log(f"Posted comment ID: {comment.id}")
            self.tracker.add_comment(comment.id)
            self.report_status("comment_posted", {"comment_id": comment.id})
            return  # Success, exit the method
        except praw.exceptions.APIException as e:
            if "BAD_CAPTCHA" in str(e):
                log(f"CAPTCHA required, attempting to solve (Attempt {attempt + 1}/{max_retries})")
                try:
                    # Step 1: Fetch a new CAPTCHA ID from Reddit's API
                    captcha_response = self.reddit.request('POST', '/api/new_captcha')
                    captcha_id = captcha_response.get('json', {}).get('data', {}).get('iden')
                    if not captcha_id:
                        raise Exception("Failed to get CAPTCHA ID")

                    # Step 2: Download the CAPTCHA image in memory
                    captcha_url = f"https://www.reddit.com/captcha/{captcha_id}.png"
                    response = requests.get(captcha_url)
                    image_data = BytesIO(response.content)

                    # Step 3: Solve the CAPTCHA using Tesseract OCR
                    image = Image.open(image_data)
                    captcha_solution = pytesseract.image_to_string(image, config='--psm 8').strip()
                    if not captcha_solution:
                        log("Tesseract failed to extract text from CAPTCHA")
                        continue  # Retry if solution is empty

                    # Step 4: Submit the comment with CAPTCHA solution using raw API
                    comment_data = {
                        'thing_id': submission.fullname,
                        'text': comment_text,
                        'iden': captcha_id,
                        'captcha': captcha_solution
                    }
                    response = self.reddit.request('POST', '/api/comment', data=comment_data)
                    if response.get('json', {}).get('errors'):
                        raise Exception(f"Failed to post comment with CAPTCHA: {response['json']['errors']}")

                    # Step 5: Extract comment ID from the raw API response
                    comment_id = response.get('json', {}).get('data', {}).get('things', [{}])[0].get('id')
                    if comment_id:
                        self.tracker.add_comment(comment_id)
                        self.report_status("comment_posted", {"comment_id": comment_id})
                        return  # Success, exit the method
                except Exception as captcha_error:
                    log(f"CAPTCHA solving failed: {captcha_error}")
                    if attempt == max_retries - 1:
                        raise Exception("Failed to solve CAPTCHA after multiple attempts")
            else:
                # Handle non-CAPTCHA API exceptions
                log(f"Failed to post comment: {e}")
                self.report_status("comment_failed", {"error": str(e)})
                raise


    def report_status(self, status, data):
        """Report status to the Controller."""
        try:
            response = requests.post(
                f"{CONTROLLER_URL}/status",
                json={"worker_id": WORKER_ID, "status": status, "data": data}
            )
            response.raise_for_status()
            log("Status reported successfully")
        except Exception as e:
            log(f"Failed to report status: {e}")

    def is_warm_up_period(self):
        """Check if the worker is in the warm-up period."""
        elapsed_days = (time.time() - self.start_time) / (24 * 3600)
        return elapsed_days < WARM_UP_DAYS

    def run(self):
        """Main loop: fetch tasks, process them, and mimic human behavior."""
        log("Reddit Bot started")
        while True:
            if self.is_maintenance_mode():
                log("Maintenance mode enabled. Sleeping...")
                time.sleep(60)
                continue
            tasks = self.fetch_tasks()
            for task in tasks:
                subreddit_name = task.get("subreddit")
                promotion_link = task.get("promotion_link")
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    for submission in subreddit.hot(limit=5):  # Top 5 hot posts
                        random_delay()
                        random_action(self.reddit, submission)

                        if not self.is_warm_up_period():
                            post_content = submission.title + " " + (submission.selftext or "")
                            comment_text = self.generate_comment(post_content, promotion_link)
                            self.post_comment(submission, comment_text)
                        else:
                            log("In warm-up period, skipping comment posting")
                except Exception as e:
                    log(f"Error processing task {task}: {e}")
                    self.report_status("task_failed", {"task": task, "error": str(e)})
            random_delay()

if __name__ == "__main__":
    bot = RedditBot()
    bot.run()
