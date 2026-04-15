
"""
AI Email Agent - Main Orchestrator
===================================
This is the main entry point that ties all modules together.

Usage:
    from email_agent import EmailAgent
    agent = EmailAgent()
    
    # Generate a full campaign from natural language
    agent.process_command("send mail to user@email.com regarding the product launch")
    
    # Or use individual modules
    agent.generate_email(brief)
    agent.check_spam(email_content)
"""

from models import (
    CampaignBrief, EmailContent, SpamCheckResult,
    CampaignGoal, Tone, Subscriber, CampaignPackage
)
from content_optimizer import ContentOptimizer
from gmail_service import GmailService, DatabaseManager
from telegram_bot import TelegramBot, NaturalLanguageParser
from config import *

from datetime import datetime
from typing import List, Dict, Optional


class EmailAgent:
    """Master orchestrator for the AI Email Agent system."""

    def __init__(self):
        self.optimizer = ContentOptimizer()
        self.gmail = GmailService()
        self.db = DatabaseManager()
        self.parser = NaturalLanguageParser()
        self.bot = None  # Initialized when start_bot() is called

    # ==========================================
    # HIGH-LEVEL METHODS
    # ==========================================

    def process_command(self, text: str) -> Dict:
        """
        Process a natural language command and return results.
        
        Example: "send mail to john@email.com, jane@email.com regarding 
                  the new year event on april 4"
        """
        # Parse the command
        cmd = self.parser.parse(text)

        # Create campaign brief
        brief = CampaignBrief(
            goal=cmd.goal,
            tone=cmd.tone,
            event_name=cmd.event_name,
            event_date=cmd.event_date,
            recipients=cmd.recipients,
            audience_description=cmd.raw_text
        )

        # Generate email content
        email_content = self.optimizer.generate_email(brief)

        # Run spam check
        spam_check = self.optimizer.check_spam(email_content)

        return {
            "command": cmd,
            "brief": brief,
            "email_content": email_content,
            "spam_check": spam_check,
            "recipients": cmd.recipients,
            "ready_to_send": spam_check.passed
        }

    def generate_email(self, brief: CampaignBrief) -> EmailContent:
        """Generate email content from a campaign brief."""
        return self.optimizer.generate_email(brief)

    def check_spam(self, email_content: EmailContent) -> SpamCheckResult:
        """Run spam/deliverability check on email content."""
        return self.optimizer.check_spam(email_content)

    def send_campaign(self, email_content: EmailContent,
                      recipients: List[str],
                      campaign_name: str = "") -> Dict:
        """Send an email campaign to multiple recipients."""
        if not campaign_name:
            campaign_name = f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logs = self.gmail.send_bulk(
            recipients=recipients,
            subject=email_content.subject_lines[0],
            html_body=email_content.get_full_html(),
            plain_body=email_content.get_plain_text(),
            campaign_name=campaign_name
        )

        sent = sum(1 for log in logs if log.status == "sent")
        failed = sum(1 for log in logs if log.status == "failed")

        return {
            "campaign_name": campaign_name,
            "total": len(recipients),
            "sent": sent,
            "failed": failed,
            "logs": logs
        }

    # ==========================================
    # SUBSCRIBER MANAGEMENT
    # ==========================================

    def add_subscriber(self, email: str, name: str = "", tags: List[str] = None) -> bool:
        """Add a new subscriber."""
        sub = Subscriber(email=email, name=name, tags=tags or [])
        return self.db.add_subscriber(sub)

    def remove_subscriber(self, email: str) -> bool:
        """Unsubscribe a contact."""
        return self.db.remove_subscriber(email)

    def get_subscribers(self, active_only: bool = True) -> List[Dict]:
        """Get subscriber list."""
        if active_only:
            return self.db.get_active_subscribers()
        return self.db.get_all_subscribers()

    def get_subscriber_stats(self) -> Dict:
        """Get subscriber statistics."""
        return self.db.get_subscriber_count()

    # ==========================================
    # MONITORING
    # ==========================================

    def check_inbox(self, limit: int = 10) -> List[Dict]:
        """Check Gmail inbox for new emails."""
        return self.gmail.check_inbox(limit=limit)

    def process_unsubscribes(self) -> List[str]:
        """Check inbox for unsubscribe requests and process them."""
        return self.gmail.check_for_unsubscribes()

    def get_campaign_stats(self, campaign_name: str = "") -> Dict:
        """Get email sending statistics."""
        return self.gmail.get_send_stats(campaign_name)

    # ==========================================
    # TELEGRAM BOT
    # ==========================================

    def start_bot(self):
        """Start the Telegram bot for remote control."""
        self.bot = TelegramBot()
        print("=" * 50)
        print("🤖 AI Email Agent — Telegram Bot")
        print("=" * 50)
        print(f"📧 Gmail: {GMAIL_ADDRESS}")
        print(f"💬 Telegram Chat ID: {TELEGRAM_CHAT_ID}")
        print("=" * 50)
        self.bot.start_polling()

    # ==========================================
    # QUICK CAMPAIGN GENERATOR
    # ==========================================

    def quick_campaign(self, prompt: str) -> str:
        """
        Generate a full campaign report from a single prompt.
        Returns formatted text output.
        """
        result = self.process_command(prompt)
        email = result["email_content"]
        spam = result["spam_check"]
        cmd = result["command"]

        report = []
        report.append("=" * 60)
        report.append("📧 AI EMAIL AGENT — CAMPAIGN REPORT")
        report.append("=" * 60)

        report.append(f"\n🎯 Detected Goal: {cmd.goal.value}")
        report.append(f"🎨 Tone: {cmd.tone.value}")
        if cmd.event_name:
            report.append(f"📅 Event: {cmd.event_name}")
        if cmd.event_date:
            report.append(f"📆 Date: {cmd.event_date}")
        report.append(f"👥 Recipients: {', '.join(cmd.recipients) if cmd.recipients else 'None specified'}")

        report.append(f"\n{'─' * 60}")
        report.append("📨 SUBJECT LINE OPTIONS:")
        report.append(f"{'─' * 60}")
        for i, subj in enumerate(email.subject_lines, 1):
            report.append(f"  {i}. {subj}")

        report.append(f"\n{'─' * 60}")
        report.append("📝 EMAIL CONTENT:")
        report.append(f"{'─' * 60}")
        report.append(f"Preheader: {email.preheader}")
        report.append(f"\n{email.greeting}\n")
        for para in email.body_paragraphs:
            report.append(f"{para}\n")
        report.append(f"[{email.cta_text}]")
        report.append(f"\n{email.closing}")
        if email.ps_line:
            report.append(f"\nP.S. {email.ps_line}")

        report.append(f"\n{'─' * 60}")
        report.append("🛡️ SPAM CHECK:")
        report.append(f"{'─' * 60}")
        report.append(f"  Grade: {spam.grade} ({spam.score}/100)")
        report.append(f"  Status: {'✅ PASSED' if spam.passed else '❌ FAILED'}")
        if spam.issues:
            report.append("  Issues:")
            for issue in spam.issues:
                report.append(f"    ⚠️ {issue}")
        if spam.suggestions:
            report.append("  Suggestions:")
            for sug in spam.suggestions:
                report.append(f"    💡 {sug}")

        report.append(f"\n{'=' * 60}")
        return "\n".join(report)


# ==========================================
# MAIN ENTRY POINT
# ==========================================

if __name__ == "__main__":
    import sys

    agent = EmailAgent()

    if len(sys.argv) > 1:
        # Check for basic config
        if not GMAIL_ADDRESS or not TELEGRAM_BOT_TOKEN:
            print("⚠️ WARNING: GMAIL_ADDRESS or TELEGRAM_BOT_TOKEN not found in .env")
            print("Please configure your .env file before running.")
            print("-" * 40)

        if sys.argv[1] == "bot":
            # Start Telegram bot
            agent.start_bot()
        elif sys.argv[1] == "test":
            # Run a test campaign
            prompt = "send mail to test@example.com regarding the product launch event on May 15"
            try:
                print(agent.quick_campaign(prompt))
            except UnicodeEncodeError:
                # Fallback for Windows consoles that don't support emojis
                report = agent.quick_campaign(prompt)
                clean_report = report.encode('ascii', 'replace').decode('ascii')
                print(clean_report)
                print("\n[Note: Emojis were hidden because your console doesn't support UTF-8]")
        else:
            # Process the command from arguments
            prompt = " ".join(sys.argv[1:])
            try:
                print(agent.quick_campaign(prompt))
            except UnicodeEncodeError:
                report = agent.quick_campaign(prompt)
                print(report.encode('ascii', 'replace').decode('ascii'))
    else:
        print("AI Email Agent")
        print("=" * 40)
        print("Usage:")
        print("  python email_agent.py bot              — Start Telegram bot")
        print("  python email_agent.py test             — Run test campaign")
        print('  python email_agent.py "your prompt"    — Generate campaign')
        print()
        print("Or import in Python:")
        print("  from email_agent import EmailAgent")
        print("  agent = EmailAgent()")
        print('  print(agent.quick_campaign("your prompt here"))')
