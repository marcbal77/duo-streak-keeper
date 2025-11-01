# Duo Streak Keeper

Automatically protect your Duolingo streak by purchasing streak freezes when you need them.

> **⚠️ Important**: This uses Duolingo's unofficial API and may violate their Terms of Service. Use at your own risk.

## What Does This Do?

This tool checks your Duolingo account and automatically buys a streak freeze (costs 200 gems) if you don't already have one. This protects your streak if you miss a day.

You can run it manually whenever you want, or set it up to run automatically once a day.

## For Language Learners (Non-Coders)

Don't worry if you're not familiar with code! This guide will walk you through everything step-by-step.

### What You Need

- A Duolingo account with at least 200 gems
- A computer (Mac, Windows, or Linux)
- About 15 minutes to set up

### Quick Setup (Simplest Method)

1. **Install Python**
   - Mac: Python is already installed (open Terminal and type `python3 --version` to check)
   - Windows: Download from [python.org](https://www.python.org/downloads/)
   - Make sure you have Python 3.8 or newer

2. **Download This Project**
   ```bash
   git clone https://github.com/marcbal77/duo-streak-keeper.git
   cd duo-streak-keeper
   ```

   Or download as ZIP from GitHub and unzip it.

3. **Install Required Packages**
   ```bash
   pip install -r requirements.txt
   ```

   Or on Mac/Linux:
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Set Up Your Credentials**

   Copy the example file:
   ```bash
   cp .env.example .env
   ```

   Then open `.env` in any text editor and fill in your details:
   ```
   DUOLINGO_USERNAME=your_username
   DUOLINGO_PASSWORD=your_password
   ```

   **Optional**: Add email notifications so you get alerts when things happen:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   NOTIFICATION_EMAIL=your_email@gmail.com
   ```

   For Gmail, you'll need an [App Password](https://support.google.com/accounts/answer/185833?hl=en) (not your regular password).

5. **Test It**
   ```bash
   python main.py --dry-run
   ```

   This runs in test mode (won't actually buy anything). Make sure there are no errors.

6. **Run It For Real**
   ```bash
   python main.py
   ```

   That's it! It will check your account and buy a streak freeze if needed.

### Running It Automatically Every Day

The easiest way is to use your computer's built-in scheduler.

**Mac/Linux (cron):**

1. Open Terminal
2. Type: `crontab -e`
3. Add this line (change the path to match where you downloaded the project):
   ```
   0 9 * * * cd /path/to/duo-streak-keeper && python3 main.py
   ```
   This runs it at 9 AM every day.

**Windows (Task Scheduler):**

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 9 AM
4. Set action: Start a program
5. Program: `python`
6. Arguments: `main.py`
7. Start in: (path to your duo-streak-keeper folder)

### Using AI Tools (ChatGPT, Claude, etc.)

You can use AI assistants to help run this project! Here's how:

1. **Show the AI your setup:**
   - Share the error messages if something doesn't work
   - Copy the contents of your `.env` file (but hide your password!)
   - Show what happens when you run commands

2. **Ask for help like this:**
   - "I'm trying to run duo-streak-keeper but getting this error: [paste error]"
   - "How do I set up a cron job on Mac?"
   - "What's an App Password for Gmail?"
   - "Can you explain what this Python error means?"

3. **Let AI read the code:**
   - AI tools can read the source code files to understand what's happening
   - They can suggest fixes or explain how things work
   - They can help you customize settings

## For Developers

### Installation

```bash
git clone https://github.com/marcbal77/duo-streak-keeper.git
cd duo-streak-keeper
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required
DUOLINGO_USERNAME=your_username_or_email
DUOLINGO_PASSWORD=your_password

# Optional - Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_email@gmail.com

# Optional - Tuning
LOW_GEMS_THRESHOLD=600
MIN_GEMS_REQUIRED=200
LOG_LEVEL=INFO
```

### Usage

```bash
# Run once
python main.py

# Test mode (no purchases)
python main.py --dry-run

# Check status only
python main.py --status

# Disable email notifications
python main.py --no-email
```

### Automated Scheduling

**Cron (Linux/Mac):**
```bash
0 9 * * * cd /path/to/duo-streak-keeper && /path/to/venv/bin/python main.py
```

**systemd (Linux):**
```ini
[Unit]
Description=Duo Streak Keeper

[Service]
Type=oneshot
WorkingDirectory=/path/to/duo-streak-keeper
ExecStart=/path/to/venv/bin/python main.py
```

**Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**GitHub Actions (free, no server needed):**
```yaml
name: Duo Streak Keeper
on:
  schedule:
    - cron: '0 9 * * *'
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          DUOLINGO_USERNAME: ${{ secrets.DUOLINGO_USERNAME }}
          DUOLINGO_PASSWORD: ${{ secrets.DUOLINGO_PASSWORD }}
```

## How It Works

1. Logs into your Duolingo account using your credentials
2. Checks if you have a streak freeze equipped
3. Checks your gem balance
4. If you don't have a freeze and have enough gems (200+), it buys one
5. Sends you an email notification (if configured)

## Email Notifications

You'll get emails for:
- ✅ Successfully purchased a streak freeze
- ⚠️ Low gems warning (less than 600)
- 🚨 Out of gems (less than 200)
- 💔 Streak was broken
- ❌ System errors

## Troubleshooting

**"Authentication failed"**
- Check your username and password in `.env`
- Make sure there are no extra spaces
- Try logging into Duolingo's website to verify credentials

**"Insufficient gems"**
- You need at least 200 gems to buy a streak freeze
- Complete some lessons to earn more gems
- The tool will email you when you're low on gems

**"Already own maximum streak freezes"**
- Good news! You already have protection
- You can own up to 2 streak freezes at once

**Email notifications not working**
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password
- Make sure 2-Factor Authentication is enabled on your Google account
- Check that SMTP settings are correct

**Module import errors**
- Make sure you ran `pip install -r requirements.txt`
- Try: `pip3 install -r requirements.txt`
- Check you're in the right folder

## Project Structure

```
duo-streak-keeper/
├── main.py                           # Main entry point (what you run)
├── src/
│   ├── duolingo_api.py              # Talks to Duolingo's API
│   ├── streak_manager.py            # Decision logic
│   └── notifications.py             # Email alerts
├── .env                             # Your credentials (don't share!)
├── .env.example                     # Template
├── requirements.txt                 # Python packages needed
├── DUOLINGO_API_TECHNICAL_SPEC.md   # API documentation
└── README.md                        # This file
```

## Security & Privacy

- Your credentials stay on your computer in the `.env` file
- The `.env` file is in `.gitignore` (won't be uploaded to GitHub)
- No data is sent anywhere except directly to Duolingo's servers
- No telemetry or tracking
- Email notifications go directly through your email provider

## Important Legal Info

**This tool uses Duolingo's unofficial API** which is not publicly documented or officially supported.

### Risks:
- May violate Duolingo's Terms of Service
- Could result in account suspension (though unlikely for personal use)
- API may change without notice and break this tool
- No warranty or guarantee it will work

### Use Responsibly:
- Only use for your own account
- Don't abuse the API with too many requests
- Don't share your login credentials
- Consider supporting Duolingo by subscribing to Super if you use their service heavily

## License

MIT License - see [LICENSE](LICENSE) file.

This software is provided "as is" without warranty of any kind. Use at your own risk.

## Contributing

Found a bug? Have an improvement? Open an issue or pull request!

Please note:
- Keep it simple for non-technical users
- Document any changes clearly
- Test before submitting
- Respect Duolingo's systems

## Questions?

- Check the [DUOLINGO_API_TECHNICAL_SPEC.md](DUOLINGO_API_TECHNICAL_SPEC.md) for API details
- Open an issue on GitHub
- Ask an AI assistant (ChatGPT, Claude, etc.) - they can read the code and help!

## Alternatives

- **Duolingo Super**: Official subscription with automatic streak repair
- **Manual**: Just remember to buy a streak freeze yourself when you run low
- **Daily reminders**: Set a phone reminder to do your lessons

---

**Made by language learners, for language learners** 🦉
