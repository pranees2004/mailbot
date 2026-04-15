# gmail_service.py - Gmail Integration Service

import smtplib
import imaplib
import email
import sqlite3
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, DATABASE_FILE, LOG_FILE
from models import EmailLog, Subscriber, SubscriptionStatus

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database for subscribers and email logs."""

    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self.init_database()

    def init_database(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                email TEXT PRIMARY KEY,
                name TEXT DEFAULT '',
                tags TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                subscribed_date TEXT DEFAULT '',
                last_engaged TEXT DEFAULT '',
                engagement_score REAL DEFAULT 0.0,
                timezone TEXT DEFAULT 'UTC',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT DEFAULT '',
                recipient TEXT,
                subject TEXT,
                status TEXT DEFAULT 'pending',
                sent_at TEXT,
                opened INTEGER DEFAULT 0,
                clicked INTEGER DEFAULT 0,
                error TEXT DEFAULT '',
                campaign_name TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                goal TEXT,
                subject TEXT,
                recipients_count INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT DEFAULT ''
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    # ----- Subscriber Management -----

    def add_subscriber(self, subscriber: Subscriber) -> bool:
        """Add a new subscriber."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO subscribers 
                (email, name, tags, status, subscribed_date, last_engaged, engagement_score, timezone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                subscriber.email,
                subscriber.name,
                ",".join(subscriber.tags),
                subscriber.status.value if isinstance(subscriber.status, SubscriptionStatus) else subscriber.status,
                subscriber.subscribed_date or datetime.now().isoformat(),
                subscriber.last_engaged,
                subscriber.engagement_score,
                subscriber.timezone
            ))
            conn.commit()
            conn.close()
            logger.info(f"Subscriber added: {subscriber.email}")
            return True
        except Exception as e:
            logger.error(f"Error adding subscriber {subscriber.email}: {e}")
            return False

    def remove_subscriber(self, email_addr: str) -> bool:
        """Unsubscribe (soft delete) a subscriber."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE subscribers SET status = 'unsubscribed' WHERE email = ?",
                (email_addr,)
            )
            conn.commit()
            conn.close()
            logger.info(f"Subscriber unsubscribed: {email_addr}")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing {email_addr}: {e}")
            return False

    def get_active_subscribers(self) -> List[Dict]:
        """Get all active subscribers."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subscribers WHERE status = 'active'")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def get_all_subscribers(self) -> List[Dict]:
        """Get all subscribers."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subscribers")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def get_subscriber_count(self) -> Dict:
        """Get subscriber count by status."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM subscribers GROUP BY status")
        result = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return result

    # ----- Email Logs -----

    def log_email(self, log: EmailLog, campaign_name: str = "") -> bool:
        """Log a sent email."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO email_logs 
                (message_id, recipient, subject, status, sent_at, opened, clicked, error, campaign_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.message_id, log.recipient, log.subject,
                log.status, log.sent_at, log.opened, log.clicked,
                log.error, campaign_name
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error logging email: {e}")
            return False

    def get_campaign_stats(self, campaign_name: str = "") -> Dict:
        """Get email stats for a campaign."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        if campaign_name:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(opened) as opened,
                    SUM(clicked) as clicked
                FROM email_logs WHERE campaign_name = ?
            """, (campaign_name,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(opened) as opened,
                    SUM(clicked) as clicked
                FROM email_logs
            """)
        row = cursor.fetchone()
        conn.close()
        return {
            "total": row[0] or 0,
            "sent": row[1] or 0,
            "failed": row[2] or 0,
            "opened": row[3] or 0,
            "clicked": row[4] or 0
        }


class GmailService:
    """Handles sending and monitoring emails via Gmail."""

    def __init__(self):
        self.email_address = GMAIL_ADDRESS
        self.app_password = GMAIL_APP_PASSWORD
        self.db = DatabaseManager()
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.imap_server = "imap.gmail.com"

    def send_email(self, to_email: str, subject: str, html_body: str,
                   plain_body: str = "", campaign_name: str = "") -> EmailLog:
        """Send a single email via Gmail SMTP."""
        log = EmailLog(
            recipient=to_email,
            subject=subject,
            status="pending",
            sent_at=datetime.now().isoformat()
        )

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.email_address
            msg["To"] = to_email
            msg["Subject"] = subject

            # Add plain text version
            if plain_body:
                msg.attach(MIMEText(plain_body, "plain"))

            # Add HTML version
            msg.attach(MIMEText(html_body, "html"))

            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.app_password)
                server.sendmail(self.email_address, to_email, msg.as_string())

            log.status = "sent"
            log.message_id = msg["Message-ID"] or ""
            logger.info(f"Email sent successfully to {to_email}")

        except smtplib.SMTPAuthenticationError:
            log.status = "failed"
            log.error = "Authentication failed. Check Gmail address and App Password."
            logger.error(f"SMTP Auth Error for {to_email}")

        except smtplib.SMTPException as e:
            log.status = "failed"
            log.error = f"SMTP Error: {str(e)}"
            logger.error(f"SMTP Error for {to_email}: {e}")

        except Exception as e:
            log.status = "failed"
            log.error = f"Error: {str(e)}"
            logger.error(f"Error sending to {to_email}: {e}")

        # Log to database
        self.db.log_email(log, campaign_name)
        return log

    def send_bulk(self, recipients: List[str], subject: str,
                  html_body: str, plain_body: str = "",
                  campaign_name: str = "") -> List[EmailLog]:
        """Send emails to multiple recipients."""
        logs = []
        for recipient in recipients:
            # Personalize if possible
            personalized_html = html_body.replace("{{first_name}}",
                                                   recipient.split("@")[0].title())
            personalized_plain = plain_body.replace("{{first_name}}",
                                                     recipient.split("@")[0].title())

            log = self.send_email(
                to_email=recipient,
                subject=subject.replace("{{first_name}}", recipient.split("@")[0].title()),
                html_body=personalized_html,
                plain_body=personalized_plain,
                campaign_name=campaign_name
            )
            logs.append(log)

        return logs

    def check_inbox(self, folder: str = "INBOX", limit: int = 10) -> List[Dict]:
        """Check Gmail inbox for new emails (monitoring)."""
        emails = []
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.app_password)
            mail.select(folder)

            _, message_numbers = mail.search(None, "UNSEEN")
            msg_nums = message_numbers[0].split()

            for num in msg_nums[-limit:]:
                _, msg_data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])

                email_data = {
                    "from": msg["From"],
                    "to": msg["To"],
                    "subject": msg["Subject"],
                    "date": msg["Date"],
                    "body": ""
                }

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            email_data["body"] = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    email_data["body"] = msg.get_payload(decode=True).decode(errors="ignore")

                emails.append(email_data)

            mail.logout()
            logger.info(f"Checked inbox: found {len(emails)} unread emails")

        except Exception as e:
            logger.error(f"Error checking inbox: {e}")

        return emails

    def check_for_unsubscribes(self) -> List[str]:
        """Check inbox for unsubscribe requests."""
        unsubscribes = []
        emails = self.check_inbox(limit=50)

        for em in emails:
            subject = (em.get("subject") or "").lower()
            body = (em.get("body") or "").lower()

            if "unsubscribe" in subject or "unsubscribe" in body or "stop" in subject:
                sender = em.get("from", "")
                # Extract email from "Name <email>" format
                if "<" in sender:
                    sender = sender.split("<")[1].split(">")[0]
                unsubscribes.append(sender)
                self.db.remove_subscriber(sender)
                logger.info(f"Auto-unsubscribed: {sender}")

        return unsubscribes

    def get_send_stats(self, campaign_name: str = "") -> Dict:
        """Get sending statistics."""
        return self.db.get_campaign_stats(campaign_name)
