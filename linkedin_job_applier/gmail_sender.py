"""
Gmail Email Sender
==================
Author  : Aditya Rai
Project : Demo API Assignment - Option 1
Description:
    Uses the Gmail API (via OAuth 2.0) to compose and send professional
    job application emails to recruiters found on LinkedIn, attaching
    the candidate's resume automatically.

Setup (one-time):
    1. Go to Google Cloud Console → APIs & Services → Gmail API → Enable
    2. Create OAuth 2.0 credentials → Desktop App → Download as credentials.json
    3. Place credentials.json in the project root
    4. Run this script once manually — a browser window will ask you to
       authorize Gmail access. After that, token.json is saved for reuse.
"""

import os
import base64
import logging
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Gmail API scope — only sending permission needed
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def _get_gmail_service():
    """
    Authenticate with Gmail API and return a service object.

    Uses OAuth 2.0 flow:
      - First run: opens browser for user authorization → saves token.json
      - Subsequent runs: loads token.json (refreshes if expired)

    Returns:
        Authenticated Gmail API service object.

    Raises:
        FileNotFoundError: If credentials.json is missing.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"'{CREDENTIALS_FILE}' not found. "
            "Please download OAuth 2.0 credentials from Google Cloud Console "
            "and save as 'credentials.json' in the project root directory."
        )

    creds = None

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refresh or re-authorize
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            logger.info("✅ Gmail token refreshed")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            logger.info("✅ Gmail authorization complete")

        # Save for next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def build_email_body(
    candidate_name: str,
    candidate_email: str,
    candidate_phone: str,
    job_title: str,
    recruiter_name: str = "Hiring Manager",
    post_context: str = "",
) -> str:
    """
    Build a professional, personalized job application email body.

    Args:
        candidate_name:  Full name of the candidate (Aditya Rai).
        candidate_email: Candidate's email address.
        candidate_phone: Candidate's phone number.
        job_title:       The job title being applied for.
        recruiter_name:  Recruiter's name (if known, else "Hiring Manager").
        post_context:    Brief snippet from the LinkedIn post for personalization.

    Returns:
        HTML-formatted email body string.
    """
    context_paragraph = ""
    if post_context:
        preview = post_context[:200].replace("\n", " ").strip()
        context_paragraph = f"""
        <p>I came across your recent LinkedIn post regarding the <strong>{job_title}</strong> 
        opportunity — specifically your mention of: "<em>{preview}...</em>" — and I am very 
        excited to express my interest.</p>"""
    else:
        context_paragraph = f"""
        <p>I recently came across your LinkedIn post regarding the <strong>{job_title}</strong> 
        opportunity and am very excited to express my strong interest in this position.</p>"""

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.7;">

        <p>Dear {recruiter_name},</p>

        {context_paragraph}

        <p>I am <strong>Aditya Rai</strong>, a Computer Science student at <strong>Guru Tegh 
        Bahadur 4 Centenary Engineering College</strong>, with hands-on experience in 
        <strong>Java, JavaScript, HTML/CSS, C/C++, and SQL</strong>. I am actively seeking 
        a <strong>{job_title}</strong> contract/full-time opportunity where I can contribute 
        meaningfully from day one.</p>

        <p><strong>Why I am a strong candidate:</strong></p>
        <ul>
            <li>🎯 Strong foundation in OOP, Data Structures, and Java basics</li>
            <li>💻 Built real-world projects: a Money Management Web App and an Amazon Clone</li>
            <li>🏆 Qualified for Smart India Hackathon (SIH) Pre-Qualifiers 2024 & 2025 
                — selected among top college teams</li>
            <li>🥇 Winner of college tech fest BITS 'N' Bytes 2024</li>
            <li>🤝 Strong communication and leadership skills — led logistics/stage 
                coordination for a major college event</li>
        </ul>

        <p>I am a quick learner with a passion for full-stack development and emerging 
        technologies, including Artificial Intelligence. I am available immediately and 
        open to contract, C2C, or W2 arrangements.</p>

        <p>I have attached my resume for your review. I would welcome the opportunity for 
        a brief conversation to discuss how I can contribute to your team.</p>

        <p>Thank you sincerely for your time and consideration.</p>

        <p>
            Warm regards,<br/>
            <strong>Aditya Rai</strong><br/>
            📧 {candidate_email}<br/>
            📞 {candidate_phone}<br/>
            🔗 <a href="https://www.linkedin.com/in/aditya-rai-92873235a">LinkedIn Profile</a><br/>
            💻 <a href="https://github.com/Aditya-rai206">GitHub Portfolio</a>
        </p>

        <hr style="border: 1px solid #eee; margin-top: 20px;"/>
        <p style="font-size: 11px; color: #999;">
            This email was sent as part of a professional job application. 
            If you are not the intended recipient, please disregard this message.
        </p>
    </body>
    </html>
    """


def send_application_email(
    sender_email: str,
    recipient_email: str,
    candidate_name: str,
    candidate_email: str,
    candidate_phone: str,
    job_title: str,
    resume_path: str,
    recruiter_name: str = "Hiring Manager",
    post_context: str = "",
) -> Dict:
    """
    Send a professional job application email via Gmail API.

    Args:
        sender_email:    Authorized Gmail address used to send from.
        recipient_email: Recruiter's email address.
        candidate_name:  Candidate's full name.
        candidate_email: Candidate's contact email.
        candidate_phone: Candidate's phone number.
        job_title:       Job title being applied for.
        resume_path:     Absolute or relative path to the resume PDF.
        recruiter_name:  Recruiter's name for salutation.
        post_context:    Snippet from LinkedIn post for personalization.

    Returns:
        Dict with keys 'success' (bool), 'message_id' (str), 'error' (str or None).
    """
    result = {"success": False, "message_id": None, "error": None}

    try:
        service = _get_gmail_service()

        # Build the email
        message = MIMEMultipart("alternative" if not resume_path else "mixed")
        message["Subject"] = f"Application for {job_title} Position — Aditya Rai"
        message["From"] = sender_email
        message["To"] = recipient_email

        # Attach HTML body
        html_body = build_email_body(
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone,
            job_title=job_title,
            recruiter_name=recruiter_name,
            post_context=post_context,
        )
        message.attach(MIMEText(html_body, "html"))

        # Attach resume PDF
        if resume_path and os.path.exists(resume_path):
            mime_type, _ = mimetypes.guess_type(resume_path)
            mime_main, mime_sub = (mime_type or "application/octet-stream").split("/", 1)

            with open(resume_path, "rb") as f:
                attachment = MIMEBase(mime_main, mime_sub)
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)

            filename = os.path.basename(resume_path)
            attachment.add_header(
                "Content-Disposition", "attachment", filename=filename
            )
            message.attach(attachment)
            logger.info(f"📎 Resume attached: {filename}")
        else:
            logger.warning(f"⚠️  Resume not found at: {resume_path}")

        # Encode message to bytes
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Send via Gmail API
        sent_msg = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )

        result["success"] = True
        result["message_id"] = sent_msg.get("id")
        logger.info(
            f"✉️  Email sent to {recipient_email} | Message ID: {result['message_id']}"
        )

    except HttpError as e:
        result["error"] = f"Gmail API error: {e}"
        logger.error(result["error"])
    except FileNotFoundError as e:
        result["error"] = str(e)
        logger.error(result["error"])
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        logger.error(result["error"])

    return result


def send_bulk_applications(
    sender_email: str,
    candidate_name: str,
    candidate_email: str,
    candidate_phone: str,
    resume_path: str,
    jobs: List[Dict],
    delay_seconds: int = 10,
) -> List[Dict]:
    """
    Send job application emails to multiple recruiters.

    Adds a delay between sends to avoid Gmail rate limits.

    Args:
        sender_email:    Authorized Gmail sender address.
        candidate_name:  Candidate name.
        candidate_email: Candidate email.
        candidate_phone: Candidate phone.
        resume_path:     Path to resume file.
        jobs:            List of job dicts (from linkedin_search.py).
        delay_seconds:   Seconds to wait between each email.

    Returns:
        List of result dicts for each send attempt.
    """
    import time

    all_results = []

    for i, job in enumerate(jobs, 1):
        emails = job.get("emails", [])
        if not emails:
            logger.info(f"  [{i}] No email found for post by {job.get('author')} — skipping")
            all_results.append({
                "job": job,
                "result": {"success": False, "error": "No recruiter email found", "message_id": None},
            })
            continue

        for email in emails:
            logger.info(f"  [{i}] Sending to {email} for '{job['title']}'...")
            result = send_application_email(
                sender_email=sender_email,
                recipient_email=email,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone,
                job_title=job.get("title", "Java Developer"),
                resume_path=resume_path,
                recruiter_name=job.get("author", "Hiring Manager"),
                post_context=job.get("post_text", ""),
            )
            all_results.append({"job": job, "email": email, "result": result})

            if i < len(jobs):
                logger.info(f"  ⏳ Waiting {delay_seconds}s before next email...")
                time.sleep(delay_seconds)

    return all_results
