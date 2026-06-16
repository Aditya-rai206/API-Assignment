"""
LinkedIn Job Searcher
=====================
Author  : Aditya Rai
Project : Demo API Assignment - Option 1
Description:
    Searches LinkedIn Posts section for jobs matching specified keywords
    posted within the last 24 hours. Extracts job details and any visible
    recruiter/contact email addresses from each post.
"""

import time
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)

logger = logging.getLogger(__name__)

# Regex to detect email addresses anywhere in post text
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+\-]+\s*[@＠]\s*[A-Za-z0-9.\-]+\s*\.\s*[A-Za-z]{2,}\b"
)

# Words that indicate a post is a job opportunity
JOB_SIGNAL_WORDS = [
    "hiring", "looking for", "job opportunity", "position", "role",
    "apply", "recruiter", "contract", "fulltime", "full-time",
    "java developer", "c2c", "w2", "urgent", "immediate",
]


def _clean_email(raw: str) -> str:
    """Normalize obfuscated emails like 'john . doe @ company . com'."""
    return re.sub(r"\s+", "", raw).lower()


def _extract_emails(text: str) -> List[str]:
    """Extract and deduplicate email addresses from text."""
    matches = EMAIL_REGEX.findall(text)
    return list({_clean_email(m) for m in matches})


def _is_recent(time_text: str, max_hours: int = 24) -> bool:
    """
    Determine if a LinkedIn post timestamp is within the allowed window.

    LinkedIn uses relative timestamps like "2h", "45m", "1d", "Just now".
    """
    if not time_text:
        return False

    text = time_text.lower().strip()

    if "just now" in text or "now" in text:
        return True
    if "second" in text or "minute" in text:
        return True
    if "hour" in text:
        match = re.search(r"(\d+)\s*h", text)
        hours = int(match.group(1)) if match else 1
        return hours <= max_hours
    if "day" in text:
        match = re.search(r"(\d+)\s*d", text)
        days = int(match.group(1)) if match else 99
        return days == 0  # Only "today" or "0d" (rare)

    return False


def _scroll_feed(driver: webdriver.Chrome, scrolls: int = 5) -> None:
    """Scroll the LinkedIn feed to load more posts."""
    for _ in range(scrolls):
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1.5)


def search_linkedin_jobs(
    driver: webdriver.Chrome,
    keywords: List[str],
    max_hours: int = 24,
    max_results: int = 20,
) -> List[Dict]:
    """
    Search LinkedIn Posts for jobs matching given keywords posted within max_hours.

    Strategy:
        1. Navigate to LinkedIn Posts search for each keyword
        2. Filter by "Posts" content type (not jobs board)
        3. Scroll to load posts
        4. Extract post text, author info, timestamps, and emails

    Args:
        driver:      Authenticated Selenium WebDriver.
        keywords:    List of keyword strings to search (e.g. ["JAVA DEVELOPER", "CONTRACT"]).
        max_hours:   Only include posts from the last N hours.
        max_results: Maximum number of job posts to return.

    Returns:
        List of dicts with keys:
            - title:          Inferred job title from post text
            - author:         Post author name
            - author_profile: LinkedIn profile URL of the author
            - post_url:       Direct URL to the post
            - post_text:      Full text content of the post
            - emails:         List of extracted email addresses
            - timestamp:      Raw timestamp string from LinkedIn
            - keywords_found: Which search keywords matched
    """
    results: List[Dict] = []
    seen_urls: set = set()

    for keyword in keywords:
        logger.info(f"🔍 Searching LinkedIn posts for: '{keyword}'")

        # Build LinkedIn search URL filtered to Posts
        search_url = (
            f"https://www.linkedin.com/search/results/content/"
            f"?keywords={keyword.replace(' ', '%20')}"
            f"&origin=SWITCH_SEARCH_VERTICAL"
            f"&sortBy=date_posted"
        )

        driver.get(search_url)
        time.sleep(3)

        # Scroll to load posts
        _scroll_feed(driver, scrolls=8)

        # Collect post containers
        try:
            wait = WebDriverWait(driver, 10)
            post_containers = driver.find_elements(
                By.CSS_SELECTOR,
                "div.search-results-container li.reusable-search__result-container",
            )

            if not post_containers:
                # Try alternative selector
                post_containers = driver.find_elements(
                    By.CSS_SELECTOR, "div[data-view-name='search-entity-result-universal-template']"
                )

            logger.info(f"  Found {len(post_containers)} post containers")
        except TimeoutException:
            logger.warning(f"  No posts found for keyword '{keyword}'")
            continue

        for container in post_containers:
            if len(results) >= max_results:
                break

            try:
                job_data = _parse_post_container(container, keyword, max_hours)
                if job_data and job_data["post_url"] not in seen_urls:
                    seen_urls.add(job_data["post_url"])
                    results.append(job_data)
                    logger.info(
                        f"  ✅ Post: {job_data['author']} | "
                        f"Emails: {job_data['emails']} | "
                        f"Time: {job_data['timestamp']}"
                    )
            except StaleElementReferenceException:
                continue
            except Exception as e:
                logger.debug(f"  Parse error: {e}")
                continue

    logger.info(f"📋 Total qualifying posts found: {len(results)}")
    return results


def _parse_post_container(
    container, keyword: str, max_hours: int
) -> Optional[Dict]:
    """
    Parse a single LinkedIn post container element.

    Returns a structured dict or None if the post doesn't qualify.
    """
    # --- Extract timestamp ---
    timestamp_text = ""
    try:
        ts_elem = container.find_element(
            By.CSS_SELECTOR, "span.search-entity-result__primary-subtitle time, time"
        )
        timestamp_text = ts_elem.get_attribute("aria-label") or ts_elem.text
    except NoSuchElementException:
        try:
            ts_elem = container.find_element(By.CSS_SELECTOR, "time")
            timestamp_text = ts_elem.get_attribute("datetime") or ts_elem.text
        except NoSuchElementException:
            timestamp_text = "recent"

    # Skip posts older than max_hours (be lenient if we can't parse)
    if timestamp_text and not _is_recent(timestamp_text, max_hours):
        return None

    # --- Extract post text ---
    post_text = ""
    try:
        text_elem = container.find_element(
            By.CSS_SELECTOR,
            "span.break-words, div.feed-shared-update-v2__description, "
            "p.feed-shared-text, div.update-components-text",
        )
        post_text = text_elem.text.strip()
    except NoSuchElementException:
        try:
            post_text = container.text.strip()
        except Exception:
            return None

    if not post_text:
        return None

    # Check if the post is actually job-related
    text_lower = post_text.lower()
    has_job_signal = any(word in text_lower for word in JOB_SIGNAL_WORDS)
    has_keyword = keyword.lower() in text_lower
    if not (has_job_signal or has_keyword):
        return None

    # --- Extract author name & profile URL ---
    author_name = "LinkedIn User"
    author_profile = ""
    try:
        author_elem = container.find_element(
            By.CSS_SELECTOR,
            "span.entity-result__title-text a, "
            "a.app-aware-link[href*='/in/'], "
            "span.feed-shared-actor__name",
        )
        author_name = author_elem.text.strip() or author_name
        author_profile = author_elem.get_attribute("href") or ""
    except NoSuchElementException:
        pass

    # --- Extract post URL ---
    post_url = ""
    try:
        link_elem = container.find_element(
            By.CSS_SELECTOR,
            "a[href*='/posts/'], a[href*='/feed/update/'], a[href*='activity']",
        )
        post_url = link_elem.get_attribute("href") or ""
    except NoSuchElementException:
        post_url = f"https://www.linkedin.com/search/results/content/?keywords={keyword}"

    # --- Extract emails ---
    emails = _extract_emails(post_text)

    # Also check "See more" expanded text if available
    try:
        see_more = container.find_element(By.CSS_SELECTOR, "button[aria-label*='more']")
        see_more.click()
        time.sleep(0.5)
        expanded_text = container.text
        emails = list(set(emails + _extract_emails(expanded_text)))
    except Exception:
        pass

    # Infer a job title from the post text
    title = _infer_job_title(post_text, keyword)

    return {
        "title": title,
        "author": author_name,
        "author_profile": author_profile,
        "post_url": post_url,
        "post_text": post_text[:1500],  # Trim very long posts
        "emails": emails,
        "timestamp": timestamp_text,
        "keywords_found": [keyword],
    }


def _infer_job_title(text: str, fallback_keyword: str) -> str:
    """
    Try to infer a job title from the post text using common patterns.
    Falls back to the search keyword if nothing is found.
    """
    patterns = [
        r"hiring\s+(?:a\s+)?(.{5,50}?)\s*[!\n\.]",
        r"looking\s+for\s+(?:a\s+)?(.{5,50}?)\s*[!\n\.]",
        r"position\s*[:\-]?\s*(.{5,50}?)\s*[!\n\.]",
        r"role\s*[:\-]?\s*(.{5,50}?)\s*[!\n\.]",
        r"job\s*[:\-]?\s*(.{5,50}?)\s*[!\n\.]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return fallback_keyword.title()
