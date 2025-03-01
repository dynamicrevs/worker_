import random
import requests
import time
from config import CAPTCHA_SERVICES
from utils import log

class CaptchaSolver:
    def __init__(self):
        self.services = list(CAPTCHA_SERVICES.keys())
        self.current_service = random.choice(self.services)
        self.api_keys = CAPTCHA_SERVICES

    def solve(self, captcha_data):
        """Attempt to solve a captcha using the current service."""
        log(f"Attempting to solve captcha with {self.current_service}")
        try:
            if self.current_service == "capmonster":
                return self._solve_capmonster(captcha_data)
            elif self.current_service == "twocaptcha":
                return self._solve_twocaptcha(captcha_data)
            elif self.current_service == "anticaptcha":
                return self._solve_anticaptcha(captcha_data)
            elif self.current_service == "deathbycaptcha":
                return self._solve_deathbycaptcha(captcha_data)
            elif self.current_service == "solvecaptcha":
                return self._solve_solvecaptcha(captcha_data)
            elif self.current_service == "azcaptcha":
                return self._solve_azcaptcha(captcha_data)
            else:
                raise ValueError("Unsupported captcha service")
        except Exception as e:
            log(f"Captcha solving failed with {self.current_service}: {e}")
            self.rotate_service()
            return self.solve(captcha_data)  # Retry with next service

    def _solve_capmonster(self, captcha_data):
        """Solve captcha using CapMonster."""
        api_key = self.api_keys["capmonster"]
        response = requests.post(
            "https://api.capmonster.cloud/createTask",
            json={
                "clientKey": api_key,
                "task": {
                    "type": "NoCaptchaTaskProxyless",
                    "websiteURL": captcha_data["url"],
                    "websiteKey": captcha_data["sitekey"]
                }
            }
        )
        response.raise_for_status()
        task_id = response.json().get("taskId")
        for _ in range(30):  # Poll for up to 30 seconds
            time.sleep(1)
            result = requests.post(
                "https://api.capmonster.cloud/getTaskResult",
                json={"clientKey": api_key, "taskId": task_id}
            ).json()
            if result.get("status") == "ready":
                return result.get("solution", {}).get("gRecaptchaResponse")
        raise Exception("CapMonster timeout")

    def _solve_twocaptcha(self, captcha_data):
        """Solve captcha using 2Captcha."""
        api_key = self.api_keys["twocaptcha"]
        response = requests.get(
            f"http://2captcha.com/in.php?key={api_key}&method=userrecaptcha&googlekey={captcha_data['sitekey']}&pageurl={captcha_data['url']}"
        )
        response.raise_for_status()
        request_id = response.text.split("|")[1]
        for _ in range(30):  # Poll for up to 30 seconds
            time.sleep(1)
            result = requests.get(f"http://2captcha.com/res.php?key={api_key}&action=get&id={request_id}")
            if "OK" in result.text:
                return result.text.split("|")[1]
        raise Exception("2Captcha timeout")

    def _solve_anticaptcha(self, captcha_data):
        """Solve captcha using Anti-Captcha."""
        api_key = self.api_keys["anticaptcha"]
        response = requests.post(
            "https://api.anti-captcha.com/createTask",
            json={
                "clientKey": api_key,
                "task": {
                    "type": "NoCaptchaTaskProxyless",
                    "websiteURL": captcha_data["url"],
                    "websiteKey": captcha_data["sitekey"]
                }
            }
        )
        response.raise_for_status()
        task_id = response.json().get("taskId")
        for _ in range(30):  # Poll for up to 30 seconds
            time.sleep(1)
            result = requests.post(
                "https://api.anti-captcha.com/getTaskResult",
                json={"clientKey": api_key, "taskId": task_id}
            ).json()
            if result.get("status") == "ready":
                return result.get("solution", {}).get("gRecaptchaResponse")
        raise Exception("Anti-Captcha timeout")

    def _solve_deathbycaptcha(self, captcha_data):
        """Solve captcha using DeathByCaptcha."""
        api_key = self.api_keys["deathbycaptcha"]
        username, password = api_key.split(":")  # Format: username:password
        response = requests.post(
            "http://api.dbcapi.me/api/captcha",
            data={
                "username": username,
                "password": password,
                "type": 4,  # reCAPTCHA v2
                "token_params": f'{{"googlekey": "{captcha_data["sitekey"]}", "pageurl": "{captcha_data["url"]}"}}'
            }
        )
        response.raise_for_status()
        captcha_id = response.json().get("captcha")
        for _ in range(30):  # Poll for up to 30 seconds
            time.sleep(1)
            result = requests.get(f"http://api.dbcapi.me/api/captcha/{captcha_id}").json()
            if result.get("status") == 0 and result.get("text"):
                return result.get("text")
        raise Exception("DeathByCaptcha timeout")

    def _solve_solvecaptcha(self, captcha_data):
        """Solve captcha using SolveCaptcha."""
        api_key = self.api_keys["solvecaptcha"]
        response = requests.post(
            "https://api.solvecaptcha.com/in.php",
            data={
                "key": api_key,
                "method": "userrecaptcha",
                "googlekey": captcha_data["sitekey"],
                "pageurl": captcha_data["url"]
            }
        )
        response.raise_for_status()
        request_id = response.text.split("|")[1]
        for _ in range(30):  # Poll for up to 30 seconds
            time.sleep(1)
            result = requests.get(f"https://api.solvecaptcha.com/res.php?key={api_key}&action=get&id={request_id}")
            if "OK" in result.text:
                return result.text.split("|")[1]
        raise Exception("SolveCaptcha timeout")

    def _solve_azcaptcha(self, captcha_data):
        """Solve captcha using AZCaptcha."""
        api_key = self.api_keys["azcaptcha"]
        response = requests.post(
            "http://azcaptcha.com/in.php",
            data={
                "key": api_key,
                "method": "userrecaptcha",
                "googlekey": captcha_data["sitekey"],
                "pageurl": captcha_data["url"]
            }
        )
        response.raise_for_status()
        request_id = response.text.split("|")[1]
        for _ in range(30):  # Poll for up to 30 seconds
            time.sleep(1)
            result = requests.get(f"http://azcaptcha.com/res.php?key={api_key}&action=get&id={request_id}")
            if "OK" in result.text:
                return result.text.split("|")[1]
        raise Exception("AZCaptcha timeout")

    def rotate_service(self):
        """Rotate to the next captcha service."""
        current_idx = self.services.index(self.current_service)
        next_idx = (current_idx + 1) % len(self.services)
        self.current_service = self.services[next_idx]
        log(f"Rotated to captcha service: {self.current_service}")
