"""
LinkedIn Job Auto-Applier
=========================
Author  : Aditya Rai
Project : Demo API Assignment - Option 1 (LinkedIn + Gmail Automation)
Description:
    This module handles automated login to LinkedIn using Selenium WebDriver.
    It manages cookie-based sessions to avoid repeated logins and handles
    common LinkedIn security challenges.
"""

import time
import json
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

COOKIES_FILE = "linkedin_cookies.json"


def create_driver(headless: bool = False) -> webdriver.Chrome:
    """
    Create and configure a Chrome WebDriver instance.

    Args:
        headless: Run browser in headless mode (no UI window). Default False
                  so recruiter can visually verify automation.

    Returns:
        Configured Chrome WebDriver instance.
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")

    # Essential options to avoid detection and crashes
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Realistic user-agent to avoid LinkedIn bot detection
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Remove navigator.webdriver flag (anti-bot bypass)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def save_cookies(driver: webdriver.Chrome) -> None:
    """Save LinkedIn session cookies to disk for reuse."""
    cookies = driver.get_cookies()
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f, indent=2)
    logger.info(f"Saved {len(cookies)} cookies to {COOKIES_FILE}")


def load_cookies(driver: webdriver.Chrome) -> bool:
    """
    Load saved LinkedIn cookies if they exist.

    Returns:
        True if cookies were loaded successfully, False otherwise.
    """
    if not os.path.exists(COOKIES_FILE):
        return False

    try:
        driver.get("https://www.linkedin.com")
        time.sleep(2)
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
        driver.refresh()
        time.sleep(3)

        # Verify we are actually logged in
        if "feed" in driver.current_url or "mynetwork" in driver.current_url:
            logger.info("✅ Logged in via saved cookies")
            return True
        return False
    except Exception as e:
        logger.warning(f"Cookie load failed: {e}")
        return False


def linkedin_login(email: str, password: str, headless: bool = False) -> webdriver.Chrome:
    """
    Log into LinkedIn automatically.

    Attempts cookie-based login first; falls back to credential login.

    Args:
        email:    LinkedIn account email address.
        password: LinkedIn account password.
        headless: Run without a visible browser window.

    Returns:
        Authenticated Chrome WebDriver instance.

    Raises:
        RuntimeError: If login fails after all attempts.
    """
    driver = create_driver(headless=headless)

    # --- Attempt 1: Cookie-based session restore ---
    if load_cookies(driver):
        return driver

    logger.info("🔑 Logging in with credentials...")
    driver.get("https://www.linkedin.com/login")

    try:
        wait = WebDriverWait(driver, 15)

        # Enter email
        email_field = wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_field.clear()
        for char in email:           # Type character by character to appear human
            email_field.send_keys(char)
            time.sleep(0.05)

        # Enter password
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        for char in password:
            password_field.send_keys(char)
            time.sleep(0.04)

        time.sleep(0.5)
        password_field.send_keys(Keys.RETURN)

        # Wait for feed page
        wait.until(
            EC.any_of(
                EC.url_contains("feed"),
                EC.url_contains("checkpoint"),
                EC.url_contains("mynetwork"),
            )
        )
        time.sleep(3)

        if "checkpoint" in driver.current_url:
            logger.warning(
                "⚠️  LinkedIn security checkpoint detected. "
                "Please complete verification manually in the browser."
            )
            input("Press ENTER after completing the LinkedIn verification...")

        save_cookies(driver)
        logger.info("✅ LinkedIn login successful")
        return driver

    except TimeoutException:
        driver.save_screenshot("login_error.png")
        driver.quit()
        raise RuntimeError(
            "LinkedIn login timed out. Check credentials in .env file."
        )
