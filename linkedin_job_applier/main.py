"""
Main Orchestrator
=================
Author  : Aditya Rai
Project : Demo API Assignment - Option 1 (LinkedIn + Gmail Automation)
Description:
    Main entry point that ties all modules together:
      Step 1 → LinkedIn auto-login
      Step 2 → Search LinkedIn Posts for job keywords (last 24h)
      Step 3 → Extract recruiter emails from posts
      Step 4 → Send professional application emails via Gmail API

Usage:
    python main.py                    # Full auto-run
    python main.py --demo             # Demo mode (uses mock data, no real login)
    python main.py --search-only      # Only search and print, don't send emails
    python main.py --headless         # Run browser in headless mode
"""

import os
import sys
# Force UTF-8 output on Windows to handle Unicode characters
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
import json
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# ── Local modules ──────────────────────────────────────────────────────────────
from linkedin_login import linkedin_login
from linkedin_search import search_linkedin_jobs
from gmail_sender import send_bulk_applications

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("run_log.txt", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ── Mock data for demo/testing ─────────────────────────────────────────────────
DEMO_JOBS = [
    {
        "title": "Java Developer (Contract)",
        "author": "Sarah Johnson",
        "author_profile": "https://www.linkedin.com/in/sarah-johnson-recruiter",
        "post_url": "https://www.linkedin.com/posts/demo1",
        "post_text": (
            "🚀 Urgent Hiring! Looking for a Java Developer for a 6-month CONTRACT role. "
            "Skills: Java, Spring Boot, Microservices. Location: Remote. "
            "C2C/W2 both ok. Please send resumes to demo.recruiter@techcorp.com"
        ),
        "emails": ["demo.recruiter@techcorp.com"],
        "timestamp": "2h ago",
        "keywords_found": ["JAVA DEVELOPER"],
    },
    {
        "title": "Java Backend Developer",
        "author": "Mike Chen",
        "author_profile": "https://www.linkedin.com/in/mike-chen-hiring",
        "post_url": "https://www.linkedin.com/posts/demo2",
        "post_text": (
            "Hiring Java Backend Developer | Contract role | 12 months | "
            "Must have: Java 11+, REST APIs, SQL. "
            "Contact: hiring@innovatetech.io"
        ),
        "emails": ["hiring@innovatetech.io"],
        "timestamp": "5h ago",
        "keywords_found": ["CONTRACT"],
    },
]


def print_banner():
    """Print a styled startup banner."""
    banner = """
=================================================================
  LinkedIn Auto Job Applier -- Aditya Rai
  Demo API Assignment | Option 1
-----------------------------------------------------------------
  Step 1: Login to LinkedIn automatically
  Step 2: Search Posts for JAVA DEVELOPER / CONTRACT (24h)
  Step 3: Extract recruiter email IDs
  Step 4: Send application emails via Gmail API
=================================================================
    """
    print(banner)


def save_results(jobs: list, email_results: list, output_file: str = "results.json"):
    """Save run results to a JSON file for review."""
    data = {
        "run_timestamp": datetime.now().isoformat(),
        "jobs_found": len(jobs),
        "emails_sent": sum(1 for r in email_results if r.get("result", {}).get("success")),
        "jobs": jobs,
        "email_results": email_results,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"📁 Results saved to {output_file}")


def main():
    """Main pipeline: LinkedIn login → Search → Extract emails → Send applications."""
    parser = argparse.ArgumentParser(
        description="LinkedIn Auto Job Applier — Aditya Rai"
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run in demo mode with mock data (no real LinkedIn login)"
    )
    parser.add_argument(
        "--search-only", action="store_true",
        help="Only search LinkedIn posts, do not send emails"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run Chrome in headless mode (no browser window)"
    )
    parser.add_argument(
        "--max-jobs", type=int, default=20,
        help="Maximum number of job posts to process (default: 20)"
    )
    args = parser.parse_args()

    print_banner()

    # ── Load environment variables ──────────────────────────────────────────────
    load_dotenv()

    LINKEDIN_EMAIL    = os.getenv("LINKEDIN_EMAIL", "")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")
    GMAIL_SENDER      = os.getenv("GMAIL_SENDER", "")
    CANDIDATE_NAME    = os.getenv("CANDIDATE_NAME", "Aditya Rai")
    CANDIDATE_EMAIL   = os.getenv("CANDIDATE_EMAIL", "raiaditya464@gmail.com")
    CANDIDATE_PHONE   = os.getenv("CANDIDATE_PHONE", "+91 9599052047")
    RESUME_PATH       = os.getenv("RESUME_PATH", "resume/Aditya_Rai_Resume.pdf")
    KEYWORDS          = os.getenv("JOB_KEYWORDS", "JAVA DEVELOPER,CONTRACT").split(",")
    MAX_HOURS         = int(os.getenv("MAX_HOURS_AGO", "24"))

    logger.info(f"Candidate : {CANDIDATE_NAME}")
    logger.info(f"Keywords  : {KEYWORDS}")
    logger.info(f"Max hours : {MAX_HOURS}h")
    logger.info(f"Max jobs  : {args.max_jobs}")
    logger.info(f"Demo mode : {args.demo}")

    # ════════════════════════════════════════════════════════════════════════════
    # STEP 1 & 2: LinkedIn Login + Job Search
    # ════════════════════════════════════════════════════════════════════════════
    if args.demo:
        logger.info("\n🎭 DEMO MODE — Using mock LinkedIn data\n")
        jobs = DEMO_JOBS
        logger.info(f"Loaded {len(jobs)} demo job posts")
    else:
        if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
            logger.error(
                "❌ LinkedIn credentials not set. "
                "Copy .env.example to .env and fill in your credentials."
            )
            sys.exit(1)

        driver = None
        try:
            # ── STEP 1: Login ──────────────────────────────────────────────────
            logger.info("\n━━━ STEP 1: LinkedIn Login ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            driver = linkedin_login(
                email=LINKEDIN_EMAIL,
                password=LINKEDIN_PASSWORD,
                headless=args.headless,
            )

            # ── STEP 2: Search + Extract ───────────────────────────────────────
            logger.info("\n━━━ STEP 2: Searching LinkedIn Posts ━━━━━━━━━━━━━━━━━━━━━━")
            jobs = search_linkedin_jobs(
                driver=driver,
                keywords=KEYWORDS,
                max_hours=MAX_HOURS,
                max_results=args.max_jobs,
            )

        finally:
            if driver:
                driver.quit()
                logger.info("Browser closed.")

    # ── STEP 3: Report extracted emails ────────────────────────────────────────
    logger.info("\n━━━ STEP 3: Recruiter Emails Extracted ━━━━━━━━━━━━━━━━━━━━━")
    total_emails = sum(len(j.get("emails", [])) for j in jobs)
    logger.info(f"Jobs found: {len(jobs)} | Emails extracted: {total_emails}")

    for i, job in enumerate(jobs, 1):
        print(
            f"  [{i}] {job['title']} | By: {job['author']} | "
            f"Emails: {job.get('emails', ['None found'])} | "
            f"Posted: {job.get('timestamp', 'unknown')}"
        )

    if not jobs:
        logger.warning("No qualifying jobs found. Try different keywords or increase --max-jobs.")
        return

    if args.search_only:
        logger.info("\nSearch-only mode — skipping email sending.")
        save_results(jobs, [])
        return

    # ════════════════════════════════════════════════════════════════════════════
    # STEP 4: Send Application Emails via Gmail API
    # ════════════════════════════════════════════════════════════════════════════
    logger.info("\n━━━ STEP 4: Sending Application Emails via Gmail API ━━━━━━━━")

    if not GMAIL_SENDER:
        logger.error("❌ GMAIL_SENDER not set in .env")
        sys.exit(1)

    if not os.path.exists(RESUME_PATH):
        logger.error(
            f"❌ Resume not found at: {RESUME_PATH}. "
            "Place your resume PDF in the 'resume/' folder."
        )
        sys.exit(1)

    email_results = send_bulk_applications(
        sender_email=GMAIL_SENDER,
        candidate_name=CANDIDATE_NAME,
        candidate_email=CANDIDATE_EMAIL,
        candidate_phone=CANDIDATE_PHONE,
        resume_path=RESUME_PATH,
        jobs=jobs,
        delay_seconds=10,
    )

    # ── Final Summary ──────────────────────────────────────────────────────────
    sent_ok = sum(1 for r in email_results if r.get("result", {}).get("success"))
    logger.info(f"\n✅ Pipeline complete!")
    logger.info(f"   Jobs found     : {len(jobs)}")
    logger.info(f"   Emails sent    : {sent_ok}")
    logger.info(f"   Failed/skipped : {len(email_results) - sent_ok}")

    save_results(jobs, email_results)
    logger.info("\nDone. Check results.json for the full report.")


if __name__ == "__main__":
    main()
