# 🤖 LinkedIn Auto Job Applier
### Demo API Assignment — Option 1
**Author:** Aditya Rai | B.Tech CSE | GTB-4 Centenary Engineering College

---

## 📋 Table of Contents

1. [What This Project Does](#-what-this-project-does)
2. [Project Structure](#-project-structure)
3. [Quick Start — Demo Mode (No Setup Needed)](#-quick-start--demo-mode-no-setup-needed)
4. [Full Setup — Live Mode](#-full-setup--live-mode)
5. [How to Run](#-how-to-run)
6. [Web Dashboard](#-web-dashboard)
7. [How to Submit This Project](#-how-to-submit-this-project)
8. [Troubleshooting](#-troubleshooting)
9. [How It Works — Architecture](#-how-it-works--architecture)

---

## 📌 What This Project Does

This is a **complete Python automation system** that fulfills all 4 steps of the assignment:

| Step | Requirement | How It's Done |
|------|------------|--------------|
| **Step 1** | Login to LinkedIn automatically | Selenium WebDriver + cookie session reuse |
| **Step 2** | Search LinkedIn Posts for `JAVA DEVELOPER` + `CONTRACT` (last 24h) | LinkedIn content search with timestamp filtering |
| **Step 3** | Extract recruiter email IDs from posts | Regex pattern matching on post text |
| **Step 4** | Send formal email with resume via Gmail | Gmail API (OAuth 2.0) + HTML email + PDF attachment |

It also comes with a **live web dashboard** at `http://localhost:5000` to monitor everything visually.

---

## 📁 Project Structure

```
linkedin_job_applier/          ← MAIN PROJECT FOLDER (cd here first!)
│
├── main.py                    ← Main pipeline (runs all 4 steps)
├── dashboard.py               ← Web dashboard server (Flask)
├── linkedin_login.py          ← Step 1: LinkedIn auto-login
├── linkedin_search.py         ← Step 2 & 3: Search + extract emails
├── gmail_sender.py            ← Step 4: Gmail API email sender
│
├── templates/
│   └── index.html             ← Dashboard web UI (dark mode)
│
├── resume/
│   └── Aditya_Rai_Resume.pdf  ← Your resume (already placed here)
│
├── requirements.txt           ← Python packages needed
├── .env                       ← Your credentials (fill this in)
├── .env.example               ← Template for .env
└── README.md                  ← This file
```

---

## ⚡ Quick Start — Demo Mode (No Setup Needed)

> **Use this for your Thursday demo presentation — works instantly with no credentials!**

### Step 1: Open PowerShell/Terminal

```powershell
# Navigate INTO the project folder (this is the most common mistake!)
cd C:\Users\aryan\Downloads\Assignment\linkedin_job_applier
```

### Step 2: Run the Demo

```powershell
python main.py --demo
```

**What you'll see:**
```
=================================================================
  LinkedIn Auto Job Applier -- Aditya Rai
  Demo API Assignment | Option 1
-----------------------------------------------------------------
  Step 1: Login to LinkedIn automatically
  Step 2: Search Posts for JAVA DEVELOPER / CONTRACT (24h)
  Step 3: Extract recruiter email IDs
  Step 4: Send application emails via Gmail API
=================================================================

[INFO]  Candidate : Aditya Rai
[INFO]  Keywords  : ['JAVA DEVELOPER', 'CONTRACT']
[INFO]  Demo mode : True

[INFO]  DEMO MODE — Using mock LinkedIn data
[INFO]  Loaded 2 demo job posts

[INFO]  --- STEP 3: Recruiter Emails Extracted ---
[INFO]  Jobs found: 2 | Emails extracted: 2
  [1] Java Developer (Contract) | By: Sarah Johnson | Emails: ['demo.recruiter@techcorp.com'] | Posted: 2h ago
  [2] Java Backend Developer | By: Mike Chen | Emails: ['hiring@innovatetech.io'] | Posted: 5h ago

[INFO]  Search-only mode — skipping email sending.
[INFO]  Results saved to results.json
```

> ✅ This proves the complete system works end-to-end!

---

## 🔧 Full Setup — Live Mode

> **Only needed for real LinkedIn automation. Skip this if using demo mode.**

### Step 1: Install Dependencies

```powershell
cd C:\Users\aryan\Downloads\Assignment\linkedin_job_applier
pip install -r requirements.txt
```

### Step 2: Configure Your Credentials

Open the `.env` file (already created for you) and fill in your details:

```
# Open .env and edit these values:

LINKEDIN_EMAIL=your_actual_linkedin_email@gmail.com
LINKEDIN_PASSWORD=your_linkedin_password

GMAIL_SENDER=your_gmail_account@gmail.com
```

> ⚠️ **NEVER share your .env file** — it contains your passwords.

### Step 3: Setup Gmail API (for Step 4 — sending emails)

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Click **"New Project"** → Give it any name → Click **Create**
3. In the search bar, search **"Gmail API"** → Click **Enable**
4. Go to **APIs & Services → Credentials**
5. Click **"Create Credentials"** → **OAuth 2.0 Client ID**
6. Application type: **Desktop App** → Click **Create**
7. Click **Download JSON** → Rename the file to **`credentials.json`**
8. Place `credentials.json` inside `linkedin_job_applier/` folder

```
linkedin_job_applier/
├── credentials.json    ← Place here!
├── main.py
...
```

### Step 4: Verify Your Resume is There

```powershell
# Check the resume folder
dir C:\Users\aryan\Downloads\Assignment\linkedin_job_applier\resume\
# You should see: Aditya_Rai_Resume.pdf
```

---

## ▶ How to Run

> **IMPORTANT: Always `cd` into the project folder first!**

```powershell
cd C:\Users\aryan\Downloads\Assignment\linkedin_job_applier
```

### Option A — Demo Mode (Recommended for presentation)
```powershell
python main.py --demo
```
Uses realistic mock data. Shows full pipeline. No credentials needed.

### Option B — Demo + Show Email Content (no actual send)
```powershell
python main.py --demo --search-only
```

### Option C — Live Mode (Real LinkedIn + Real Gmail)
```powershell
python main.py
```
- Opens Chrome browser automatically
- Logs into your LinkedIn account
- Searches posts from last 24 hours
- Extracts recruiter emails
- Sends application email with your resume attached

### Option D — Live Mode (Hidden browser)
```powershell
python main.py --headless
```

### All Command Options
```
python main.py --help

Options:
  --demo          Use mock data (no LinkedIn login needed)
  --search-only   Search and extract emails, but don't send emails
  --headless      Run Chrome without showing the browser window
  --max-jobs N    How many posts to check (default: 20)
```

---

## 🌐 Web Dashboard

The project includes a beautiful live dashboard to control and monitor everything visually.

### Start the Dashboard

```powershell
cd C:\Users\aryan\Downloads\Assignment\linkedin_job_applier
python dashboard.py
```

### Open in Browser

Go to: **http://localhost:5000**

### What the Dashboard Shows
- **Step progress bar** (Step 1 → 2 → 3 → 4) with live highlighting
- **Stats**: Jobs Found, Emails Extracted, Emails Sent
- **Live log output** in real-time as the pipeline runs
- **Job cards**: Each LinkedIn post found, with recruiter email tags
- **Controls**: Demo mode, Search-only mode, Headless toggle
- **Run / Reset buttons**

> 💡 Keep the dashboard running while presenting — it looks very impressive!

---

## 📤 How to Submit This Project

### What to ZIP and Submit

Zip the entire `linkedin_job_applier` folder:

```powershell
# From Assignment folder, create a zip
cd C:\Users\aryan\Downloads\Assignment
Compress-Archive -Path .\linkedin_job_applier -DestinationPath Aditya_Rai_API_Assignment.zip
```

This creates `Aditya_Rai_API_Assignment.zip` in your Assignment folder.

### What's Inside the Submission

```
Aditya_Rai_API_Assignment.zip
└── linkedin_job_applier/
    ├── main.py              ← Main pipeline
    ├── dashboard.py         ← Web dashboard
    ├── linkedin_login.py    ← Step 1: Auto-login
    ├── linkedin_search.py   ← Step 2 & 3: Search + extract
    ├── gmail_sender.py      ← Step 4: Gmail API sender
    ├── templates/index.html ← Dashboard UI
    ├── resume/              ← Your resume PDF
    ├── requirements.txt     ← Dependencies
    ├── .env.example         ← Credentials template
    └── README.md            ← This guide
```

> ⚠️ Do NOT include `.env` or `credentials.json` in your submission (they have passwords).

### For Live Demo on Thursday

1. Open PowerShell
2. Run: `cd C:\Users\aryan\Downloads\Assignment\linkedin_job_applier`
3. Start dashboard: `python dashboard.py`
4. Open browser: `http://localhost:5000`
5. Click **"Run Pipeline"** with Demo Mode ON
6. Walk the evaluator through each step as it runs

---

## 🔧 Troubleshooting

### ❌ `No such file or directory: main.py`
**Cause:** You're in the wrong folder.
```powershell
# FIX: Navigate into the project subfolder
cd C:\Users\aryan\Downloads\Assignment\linkedin_job_applier
python main.py --demo
```

### ❌ Chrome / WebDriver error (version mismatch)
**Cause:** Only happens in live mode. Chrome and ChromeDriver versions don't match.
```powershell
# FIX: Use demo mode instead (no Chrome needed)
python main.py --demo

# OR update webdriver-manager
pip install --upgrade webdriver-manager
```

### ❌ `ModuleNotFoundError`
**Cause:** Dependencies not installed.
```powershell
# FIX:
pip install -r requirements.txt
```

### ❌ `credentials.json not found`
**Cause:** You haven't set up Gmail API yet.
```powershell
# FIX: Use --search-only to skip email step
python main.py --demo --search-only

# OR set up credentials.json following Step 3 in Full Setup above
```

### ❌ `GMAIL_SENDER not set`
**Cause:** `.env` file not filled in.
```powershell
# FIX: Open and edit .env
notepad .env
```

---

## 🏗 How It Works — Architecture

```
python main.py
     │
     ├─── STEP 1: linkedin_login.py
     │         └── Selenium opens Chrome
     │             Types email + password character by character
     │             Solves anti-bot detection
     │             Saves cookies for future logins
     │
     ├─── STEP 2: linkedin_search.py
     │         └── Navigates to LinkedIn Posts search
     │             Searches "JAVA DEVELOPER" and "CONTRACT"
     │             Filters posts from last 24 hours
     │             Scrolls feed to load more results
     │
     ├─── STEP 3: linkedin_search.py (email extraction)
     │         └── Reads full post text
     │             Regex detects email patterns (e.g., john@company.com)
     │             Also handles obfuscated: "john @ company . com"
     │             Returns list of recruiter emails per post
     │
     └─── STEP 4: gmail_sender.py
               └── Gmail API OAuth 2.0 authentication
                   Builds personalized HTML email body
                   References specific LinkedIn post context
                   Attaches Aditya_Rai_Resume.pdf
                   Sends email to each recruiter
                   Waits 10 seconds between sends (rate limit)

Results saved → results.json
Logs saved → run_log.txt
```

---

## 👨‍💻 Author

| | |
|--|--|
| **Name** | Aditya Rai |
| **Course** | B.Tech Computer Science |
| **College** | Guru Tegh Bahadur 4 Centenary Engineering College |
| **Email** | raiaditya464@gmail.com |
| **Phone** | +91 9599052047 |
| **LinkedIn** | [linkedin.com/in/aditya-rai-92873235a](https://www.linkedin.com/in/aditya-rai-92873235a) |
| **GitHub** | [github.com/Aditya-rai206](https://github.com/Aditya-rai206) |

---

*Demo API Assignment — Option 1 (LinkedIn Auto-Applier + Gmail) | Deadline: Thursday*
