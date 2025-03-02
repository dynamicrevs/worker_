import praw
import requests
import threading
import time
from config import *
from utils import log, random_delay, random_action
from captcha_solver import CaptchaSolver
from engagement_tracker import EngagementTracker
from huggingface_hub import InferenceClient

class RedditBot:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
            user_agent="reddit-super-manager-bot"
        )
        self.captcha_solver = CaptchaSolver()
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

    def post_comment(self, submission, comment_text):
        """Post a comment on Reddit, handling captchas if needed."""
        try:
            comment = submission.reply(comment_text)
            log(f"Posted comment ID: {comment.id}")
            self.tracker.add_comment(comment.id)
            self.report_status("comment_posted", {"comment_id": comment.id})
        except praw.exceptions.APIException as e:
            if "CAPTCHA" in str(e):
                log("Captcha required, attempting to solve")
                captcha_solution = self.captcha_solver.solve({"url": submission.permalink, "sitekey": "reddit-sitekey"})
                log(f"Captcha solution: {captcha_solution}")
                # PRAW doesn't support captcha submission natively; this is a limitation
                # In practice, you'd need to use Reddit's raw API or manual intervention
                raise Exception("Captcha solving not implemented in PRAW")
            else:
                log(f"Failed to post comment: {e}")
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
