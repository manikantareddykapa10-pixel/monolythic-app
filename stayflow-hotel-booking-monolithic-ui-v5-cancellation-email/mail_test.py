import sys
from dotenv import load_dotenv
load_dotenv()
from email_service import smtp_test, smtp_configured

if not smtp_configured():
    raise SystemExit("SMTP is not configured. Fill SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_APP_PASSWORD and MAIL_FROM in .env")
recipient = sys.argv[1] if len(sys.argv) > 1 else input("Send test email to: ").strip()
try:
    if smtp_test(recipient):
        print(f"SMTP test sent successfully to {recipient}")
except Exception as exc:
    raise SystemExit(f"SMTP test failed: {exc}")
