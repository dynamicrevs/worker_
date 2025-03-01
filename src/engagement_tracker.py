import schedule
import time
import praw
import requests
from config import ENGAGEMENT_CHECK_INTERVAL, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD, CONTROLLER_URL, WORKER_ID
from utils import log

class EngagementTracker:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
            user_agent="reddit-super-manager-bot"
        )
        self.comment_ids = []  # List to store comment IDs for tracking

    def add_comment(self, comment_id):
        """Add a comment ID to track."""
        self.comment_ids.append(comment_id)
        log(f"Tracking engagement for comment ID: {comment_id}")

    def check_engagement(self):
        """Check engagement metrics for tracked comments."""
        for comment_id in self.comment_ids:
            try:
                comment = self.reddit.comment(id=comment_id)
                engagement = {
                    "comment_id": comment_id,
                    "upvotes": comment.score,
                    "replies": len(comment.replies)
                }
                log(f"Engagement for {comment_id}: {engagement}")
                self.report_engagement(engagement)
            except Exception as e:
                log(f"Error checking engagement for {comment_id}: {e}")

    def report_engagement(self, engagement):
        """Send engagement data to the Controller."""
        try:
            response = requests.post(
                f"{CONTROLLER_URL}/engagement",
                json={"worker_id": WORKER_ID, "engagement": engagement}
            )
            response.raise_for_status()
            log("Engagement reported successfully")
        except Exception as e:
            log(f"Failed to report engagement: {e}")

    def start(self):
        """Start the engagement tracking schedule."""
        schedule.every(ENGAGEMENT_CHECK_INTERVAL).seconds.do(self.check_engagement)
        log("Engagement tracking started")
        while True:
            schedule.run_pending()
            time.sleep(1)
