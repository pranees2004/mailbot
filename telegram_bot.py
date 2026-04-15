
import re
import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, AZURE_AI_ENDPOINT, AZURE_AI_API_KEY
from models import (
    CampaignBrief, CampaignGoal, Tone, TelegramCommand
)
from content_optimizer import ContentOptimizer
from gmail_service import GmailService, DatabaseManager
from models import Subscriber

logger = logging.getLogger(__name__)


class NaturalLanguageParser:
    """Parses natural language commands into structured campaign briefs."""

    # Email pattern
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    # Date patterns
    DATE_PATTERNS = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:\s*,?\s*\d{4})?',
        r'(\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+\d{4})?)',
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:\s*,?\s*\d{4})?',
    ]

    # Goal keywords
    GOAL_KEYWORDS = {
        CampaignGoal.EVENT: ["event", "invite", "invitation", "rsvp", "attend", "conference", "meetup", "webinar", "party", "celebration", "ceremony"],
        CampaignGoal.PROMOTION: ["sale", "discount", "offer", "deal", "coupon", "promo", "promotion", "save", "off"],
        CampaignGoal.ANNOUNCEMENT: ["announce", "announcement", "launching", "launch", "introducing", "new product", "release", "update"],
        CampaignGoal.WELCOME: ["welcome", "onboard", "new member", "joined", "signup"],
        CampaignGoal.ENGAGEMENT: ["feedback", "survey", "poll", "opinion", "thoughts", "engage"],
        CampaignGoal.CONVERSION: ["buy", "purchase", "subscribe", "sign up", "convert", "trial", "demo"],
        CampaignGoal.NURTURE: ["tips", "newsletter", "educational", "learn", "guide", "how to"],
        CampaignGoal.REENGAGEMENT: ["miss you", "come back", "inactive", "re-engage", "been a while"]
    }

    # Tone keywords
    TONE_KEYWORDS = {
        Tone.PROFESSIONAL: ["professional", "formal", "business", "corporate"],
        Tone.CASUAL: ["casual", "relaxed", "chill", "informal"],
        Tone.URGENT: ["urgent", "asap", "immediately", "hurry", "last chance"],
        Tone.FRIENDLY: ["friendly", "warm", "nice", "kind"],
        Tone.FORMAL: ["formal", "official", "traditional"],
        Tone.PLAYFUL: ["playful", "fun", "exciting", "energetic"]
    }

    def parse(self, text: str) -> TelegramCommand:
        """Parse natural language into a structured command."""
        # Try AI parsing first if credentials are available
        if AZURE_AI_ENDPOINT and AZURE_AI_API_KEY:
            ai_cmd = self._ai_parse(text)
            if ai_cmd:
                return ai_cmd

        # Fallback to RegEx parsing
        text_lower = text.lower()
        cmd = TelegramCommand(raw_text=text)

        # Extract emails
        cmd.recipients = re.findall(self.EMAIL_PATTERN, text)

        # Extract dates
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                cmd.event_date = match.group(0).strip()
                break

        # Detect goal
        cmd.goal = self._detect_goal(text_lower)

        # Detect tone
        cmd.tone = self._detect_tone(text_lower)

        # Extract event name
        cmd.event_name = self._extract_event_name(text_lower)

        # Detect command type
        cmd.command = self._detect_command(text_lower)

        return cmd

    def _detect_goal(self, text: str) -> CampaignGoal:
        """Detect campaign goal from text."""
        scores = {}
        for goal, keywords in self.GOAL_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[goal] = score

        if scores:
            return max(scores, key=scores.get)
        return CampaignGoal.ENGAGEMENT

    def _detect_tone(self, text: str) -> Tone:
        """Detect desired tone from text."""
        for tone, keywords in self.TONE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return tone
        return Tone.PROFESSIONAL

    def _extract_event_name(self, text: str) -> str:
        """Try to extract event name from text."""
        # Look for "regarding the X" or "about the X" or "for X event"
        patterns = [
            r'regarding\s+(?:the\s+)?(.+?)(?:\s+on\s+|\s+event|\s+at\s+|$)',
            r'about\s+(?:the\s+)?(.+?)(?:\s+on\s+|\s+event|\s+at\s+|$)',
            r'for\s+(?:the\s+)?(.+?)(?:\s+on\s+|\s+event|\s+at\s+|$)',
            r'invite.*?to\s+(?:the\s+)?(.+?)(?:\s+on\s+|\s+at\s+|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # Clean up - remove trailing prepositions and common words
                name = re.sub(r'\s+(the|a|an|to|for|on|at|in)\s*$', '', name)
                # Remove email addresses from the name
                name = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', name).strip()
                name = re.sub(r'\s*,\s*', ' ', name).strip()
                if len(name) > 3:
                    return name.title()

        return ""

    def _detect_command(self, text: str) -> str:
        """Detect the type of command."""
        if any(word in text for word in ["send", "mail", "email", "deliver"]):
            return "send_email"
        elif any(word in text for word in ["subscribe", "add subscriber", "add contact"]):
            return "add_subscriber"
        elif any(word in text for word in ["unsubscribe", "remove"]):
            return "remove_subscriber"
        elif any(word in text for word in ["list", "show subscribers", "contacts"]):
            return "list_subscribers"
        elif any(word in text for word in ["stats", "statistics", "report", "analytics"]):
            return "show_stats"
        elif any(word in text for word in ["inbox", "check mail", "new mail"]):
            return "check_inbox"
        elif any(word in text for word in ["help", "commands"]):
            return "help"
        elif any(word in text for word in ["draft", "preview", "compose"]):
            return "draft_email"
        return "send_email"
    
    def _ai_parse(self, text: str) -> Optional[TelegramCommand]:
        """Use Claude to parse the natural language command."""
        try:
            import json
            import requests

            prompt = f"""Parse the following user request for an email marketing agent:
"{text}"

Identify:
1. Command: (send_email, add_subscriber, remove_subscriber, list_subscribers, show_stats, check_inbox, help)
2. Recipients: List of email addresses
3. Goal: (event, promotion, announcement, welcome, engagement, conversion, nurture, reengagement)
4. Tone: (professional, casual, urgent, friendly, formal, playful)
5. Event Name: The name of any event mentioned
6. Event Date: The date of any event mentioned

Return ONLY a JSON object:
{{
  "command": "command_name",
  "recipients": ["email1", "email2"],
  "goal": "goal_name",
  "tone": "tone_name",
  "event_name": "event name",
  "event_date": "event date"
}}
"""
            url = AZURE_AI_ENDPOINT
            if not url.endswith("/v1/messages") and not url.endswith("/messages"):
                url = f"{url.rstrip('/')}/v1/messages"

            headers = {
                "api-key": AZURE_AI_API_KEY,
                "content-type": "application/json"
            }
            data = {
                "model": "claude-3-5-sonnet-20240620",
                "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt}]
            }

            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()
            if "content" not in response_json:
                return None
                
            ai_text = response_json["content"][0]["text"]
            
            import re
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                d = json.loads(json_match.group(0))
                
                # Map strings to Enums
                from models import CampaignGoal, Tone
                goal = CampaignGoal.ENGAGEMENT
                try: goal = CampaignGoal(d.get("goal", "engagement"))
                except: pass
                
                tone = Tone.PROFESSIONAL
                try: tone = Tone(d.get("tone", "professional"))
                except: pass

                return TelegramCommand(
                    command=d.get("command", "send_email"),
                    recipients=d.get("recipients", []),
                    goal=goal,
                    tone=tone,
                    event_name=d.get("event_name", ""),
                    event_date=d.get("event_date", ""),
                    raw_text=text
                )
            return None
        except Exception as e:
            print(f"AI Parsing Error: {e}")
            return None


class TelegramBot:
    """Telegram Bot that controls the Email Agent."""

    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.parser = NaturalLanguageParser()
        self.optimizer = ContentOptimizer()
        self.gmail = GmailService()
        self.db = DatabaseManager()
        self.pending_campaigns = {}  # Store campaigns awaiting approval
        self.last_update_id = 0

    # ==========================================
    # TELEGRAM API METHODS
    # ==========================================

    def send_message(self, text: str, chat_id: str = None,
                     reply_markup: Dict = None, parse_mode: str = "HTML") -> bool:
        """Send a message to Telegram."""
        try:
            payload = {
                "chat_id": chat_id or self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            if reply_markup:
                payload["reply_markup"] = json.dumps(reply_markup)

            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            return response.json().get("ok", False)
        except Exception as e:
            logger.error(f"Error sending Telegram message to {chat_id or self.chat_id}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return False

    def get_updates(self, offset: int = None) -> List[Dict]:
        """Get new messages from Telegram."""
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset

            response = requests.get(f"{self.base_url}/getUpdates", params=params)
            data = response.json()

            if data.get("ok"):
                return data.get("result", [])
            return []
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []

    def send_approval_request(self, campaign_id: str, preview: str,
                              recipients: List[str], chat_id: str = None):
        """Send campaign preview with approve/reject buttons."""
        message = f"""
📧 <b>New Email Campaign Ready</b>

{preview}

<b>Recipients:</b> {', '.join(recipients)}
<b>Total:</b> {len(recipients)} recipient(s)

<i>Reply with:</i>
✅ <code>/approve {campaign_id}</code> — to send
❌ <code>/reject {campaign_id}</code> — to cancel
✏️ <code>/edit {campaign_id}</code> — to modify
"""
        # Inline keyboard buttons
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve & Send", "callback_data": f"approve_{campaign_id}"},
                    {"text": "❌ Reject", "callback_data": f"reject_{campaign_id}"}
                ],
                [
                    {"text": "✏️ Edit", "callback_data": f"edit_{campaign_id}"},
                    {"text": "👁 Preview Full", "callback_data": f"preview_{campaign_id}"}
                ]
            ]
        }

        self.send_message(message, chat_id=chat_id, reply_markup=reply_markup)

    # ==========================================
    # COMMAND HANDLERS
    # ==========================================

    def handle_message(self, text: str, chat_id: str = None) -> str:
        """Process an incoming message and return response."""
        text = text.strip()
        chat_id = chat_id or self.chat_id

        # Handle direct commands
        if text.startswith("/"):
            return self._handle_slash_command(text, chat_id)

        # Handle callback data (button presses)
        if text.startswith("approve_") or text.startswith("reject_"):
            return self._handle_callback(text, chat_id)

        # Parse natural language
        cmd = self.parser.parse(text)

        handlers = {
            "send_email": self._handle_send_email,
            "draft_email": self._handle_draft_email,
            "add_subscriber": self._handle_add_subscriber,
            "remove_subscriber": self._handle_remove_subscriber,
            "list_subscribers": self._handle_list_subscribers,
            "show_stats": self._handle_show_stats,
            "check_inbox": self._handle_check_inbox,
            "help": self._handle_help
        }

        handler = handlers.get(cmd.command, self._handle_send_email)
        return handler(cmd, chat_id)

    def _handle_slash_command(self, text: str, chat_id: str) -> str:
        """Handle /slash commands."""
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "/start" or command == "/help":
            return self._get_help_text()

        elif command == "/approve":
            return self._approve_campaign(args.strip(), chat_id)

        elif command == "/reject":
            return self._reject_campaign(args.strip(), chat_id)

        elif command == "/stats":
            stats = self.gmail.get_send_stats()
            return f"""📊 <b>Email Statistics</b>

Total Sent: {stats['sent']}
Failed: {stats['failed']}
Opened: {stats['opened']}
Clicked: {stats['clicked']}"""

        elif command == "/subscribers":
            subs = self.db.get_subscriber_count()
            total = sum(subs.values())
            active = subs.get("active", 0)
            unsub = subs.get("unsubscribed", 0)
            return f"""👥 <b>Subscribers</b>

Total: {total}
Active: {active}
Unsubscribed: {unsub}"""

        elif command == "/add":
            if args:
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', args)
                for em in emails:
                    self.db.add_subscriber(Subscriber(email=em, status=SubscriptionStatus.ACTIVE))
                return f"✅ Added {len(emails)} subscriber(s)"
            return "❌ Usage: /add email@example.com"

        elif command == "/remove":
            if args:
                self.db.remove_subscriber(args.strip())
                return f"✅ Unsubscribed: {args.strip()}"
            return "❌ Usage: /remove email@example.com"

        elif command == "/inbox":
            emails = self.gmail.check_inbox(limit=5)
            if not emails:
                return "📭 No new emails"
            result = "📬 <b>Recent Emails:</b>\n\n"
            for em in emails:
                result += f"From: {em['from']}\nSubject: {em['subject']}\n\n"
            return result

        elif command == "/checkunsub":
            unsubs = self.gmail.check_for_unsubscribes()
            if unsubs:
                return f"🔄 Auto-unsubscribed: {', '.join(unsubs)}"
            return "✅ No unsubscribe requests found"

        return "❓ Unknown command. Type /help for available commands."

    def _handle_send_email(self, cmd: TelegramCommand, chat_id: str) -> str:
        """Handle email sending request."""
        if not cmd.recipients:
            return "❌ No email addresses found in your message. Please include recipient emails."

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
        spam_result = self.optimizer.check_spam(email_content)

        # Create campaign ID
        campaign_id = f"camp_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Store pending campaign
        self.pending_campaigns[campaign_id] = {
            "brief": brief,
            "email_content": email_content,
            "spam_check": spam_result,
            "recipients": cmd.recipients,
            "created_at": datetime.now().isoformat()
        }

        # Build preview
        preview = f"""
<b>Subject:</b> {email_content.subject_lines[0]}

<b>Preview:</b>
{email_content.greeting}

{email_content.body_paragraphs[0][:200]}...

<b>CTA:</b> [{email_content.cta_text}]

<b>Spam Score:</b> {spam_result.grade} ({spam_result.score}/100)
<b>Alt Subjects:</b>
"""
        for i, subj in enumerate(email_content.subject_lines[1:4], 1):
            preview += f"  {i}. {subj}\n"

        # Send approval request
        self.send_approval_request(campaign_id, preview, cmd.recipients, chat_id)

        return "📝 Campaign generated! Review the preview above and approve to send."

    def _handle_draft_email(self, cmd: TelegramCommand, chat_id: str) -> str:
        """Handle draft/preview request without sending."""
        brief = CampaignBrief(
            goal=cmd.goal,
            tone=cmd.tone,
            event_name=cmd.event_name,
            event_date=cmd.event_date,
            recipients=cmd.recipients,
            audience_description=cmd.raw_text
        )

        email_content = self.optimizer.generate_email(brief)
        spam_result = self.optimizer.check_spam(email_content)

        response = f"""📝 <b>Email Draft</b>

<b>Subject Options:</b>
"""
        for i, subj in enumerate(email_content.subject_lines, 1):
            response += f"  {i}. {subj}\n"

        response += f"""
<b>Content:</b>
{email_content.greeting}

{chr(10).join(email_content.body_paragraphs[:3])}

[{email_content.cta_text}]

{email_content.closing}

<b>Spam Check:</b> {spam_result.grade} ({spam_result.score}/100)
"""
        if spam_result.issues:
            response += "\n<b>Issues:</b>\n"
            for issue in spam_result.issues[:3]:
                response += f"  ⚠️ {issue}\n"

        return response

    def _handle_add_subscriber(self, cmd: TelegramCommand, chat_id: str) -> str:
        """Add subscribers from the message."""
        if not cmd.recipients:
            return "❌ No email addresses found. Usage: 'add subscriber user@email.com'"

        added = 0
        for email_addr in cmd.recipients:
            sub = Subscriber(email=email_addr, status=SubscriptionStatus.ACTIVE)
            if self.db.add_subscriber(sub):
                added += 1

        return f"✅ Added {added} subscriber(s) to the list"

    def _handle_remove_subscriber(self, cmd: TelegramCommand, chat_id: str) -> str:
        """Remove/unsubscribe contacts."""
        if not cmd.recipients:
            return "❌ No email addresses found. Usage: 'unsubscribe user@email.com'"

        removed = 0
        for email_addr in cmd.recipients:
            if self.db.remove_subscriber(email_addr):
                removed += 1

        return f"✅ Unsubscribed {removed} contact(s)"

    def _handle_list_subscribers(self, cmd: TelegramCommand, chat_id: str) -> str:
        """List all subscribers."""
        subs = self.db.get_active_subscribers()
        if not subs:
            return "📭 No active subscribers yet."

        response = f"👥 <b>Active Subscribers ({len(subs)})</b>\n\n"
        for i, sub in enumerate(subs[:20], 1):
            name = sub.get('name', '') or 'No name'
            response += f"{i}. {sub['email']} ({name})\n"

        if len(subs) > 20:
            response += f"\n... and {len(subs) - 20} more"

        return response

    def _handle_show_stats(self, cmd: TelegramCommand, chat_id: str) -> str:
        """Show email statistics."""
        stats = self.gmail.get_send_stats()
        sub_count = self.db.get_subscriber_count()

        return f"""📊 <b>Email Agent Statistics</b>

<b>Emails:</b>
  Total Sent: {stats['sent']}
  Failed: {stats['failed']}
  Opened: {stats['opened']}
  Clicked: {stats['clicked']}

<b>Subscribers:</b>
  Active: {sub_count.get('active', 0)}
  Unsubscribed: {sub_count.get('unsubscribed', 0)}
  Total: {sum(sub_count.values())}"""

    def _handle_check_inbox(self, cmd: TelegramCommand, chat_id: str) -> str:
        """Check inbox for new emails."""
        emails = self.gmail.check_inbox(limit=5)
        if not emails:
            return "📭 No new unread emails."

        response = "📬 <b>Unread Emails:</b>\n\n"
        for em in emails:
            response += f"<b>From:</b> {em['from']}\n"
            response += f"<b>Subject:</b> {em['subject']}\n"
            response += f"<b>Date:</b> {em['date']}\n\n"

        return response

    def _handle_help(self, cmd: TelegramCommand, chat_id: str) -> str:
        """Show help."""
        return self._get_help_text()

    # ==========================================
    # CAMPAIGN APPROVAL
    # ==========================================

    def _approve_campaign(self, campaign_id: str, chat_id: str) -> str:
        """Approve and send a pending campaign."""
        campaign = self.pending_campaigns.get(campaign_id)
        if not campaign:
            return f"❌ Campaign '{campaign_id}' not found or expired."

        email_content = campaign["email_content"]
        recipients = campaign["recipients"]

        # Send emails
        logs = self.gmail.send_bulk(
            recipients=recipients,
            subject=email_content.subject_lines[0],
            html_body=email_content.get_full_html(),
            plain_body=email_content.get_plain_text(),
            campaign_name=campaign_id
        )

        # Count results
        sent = sum(1 for log in logs if log.status == "sent")
        failed = sum(1 for log in logs if log.status == "failed")

        # Clean up
        del self.pending_campaigns[campaign_id]

        result = f"""✅ <b>Campaign Sent!</b>

<b>Campaign:</b> {campaign_id}
<b>Sent:</b> {sent} ✅
<b>Failed:</b> {failed} ❌
<b>Subject:</b> {email_content.subject_lines[0]}"""

        if failed > 0:
            result += "\n\n<b>Failed Recipients:</b>\n"
            for log in logs:
                if log.status == "failed":
                    result += f"  ❌ {log.recipient}: {log.error}\n"

        return result

    def _reject_campaign(self, campaign_id: str, chat_id: str) -> str:
        """Reject/cancel a pending campaign."""
        if campaign_id in self.pending_campaigns:
            del self.pending_campaigns[campaign_id]
            return f"❌ Campaign '{campaign_id}' has been cancelled."
        return f"❌ Campaign '{campaign_id}' not found."

    def _handle_callback(self, data: str, chat_id: str) -> str:
        """Handle inline button callback data."""
        if data.startswith("approve_"):
            campaign_id = data.replace("approve_", "")
            return self._approve_campaign(campaign_id, chat_id)
        elif data.startswith("reject_"):
            campaign_id = data.replace("reject_", "")
            return self._reject_campaign(campaign_id, chat_id)
        return ""

    # ==========================================
    # HELP TEXT
    # ==========================================

    def _get_help_text(self) -> str:
        return """🤖 <b>AI Email Agent — Help</b>

<b>📧 Send Emails (Natural Language):</b>
Just describe what you want! Examples:
• "Send mail to john@email.com, jane@email.com regarding the New Year event on April 4"
• "Email alice@email.com about our product launch, casual tone"
• "Send an urgent promotion to bob@email.com"

<b>📋 Commands:</b>
/help — Show this help
/stats — Email statistics
/subscribers — List subscribers
/add email@example.com — Add subscriber
/remove email@example.com — Unsubscribe
/inbox — Check new emails
/checkunsub — Auto-process unsubscribe requests
/approve [id] — Approve pending campaign
/reject [id] — Cancel pending campaign

<b>🗣 Natural Language:</b>
• "Add subscriber user@email.com"
• "Show me the stats"
• "Check my inbox"
• "List all subscribers"
• "Draft an email about..."

<b>🎯 Supported Goals:</b>
Event, Promotion, Announcement, Welcome, Engagement, Conversion

<b>🎨 Supported Tones:</b>
Professional, Casual, Urgent, Friendly, Formal, Playful"""

    # ==========================================
    # POLLING LOOP
    # ==========================================

    def start_polling(self):
        """Start listening for Telegram messages (long polling)."""
        logger.info("Telegram bot started polling...")
        print("🤖 AI Email Agent Bot is running! Send a message on Telegram.")
        print("Press Ctrl+C to stop.\n")

        loop_count = 0
        while True:
            try:
                loop_count += 1
                if loop_count % 10 == 0:
                    logger.info("Bot is still polling... (Heartbeat)")

                updates = self.get_updates(offset=self.last_update_id + 1)

                for update in updates:
                    self.last_update_id = update["update_id"]

                    # Handle text messages
                    if "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        text = update["message"]["text"]
                        user = update["message"]["from"].get("first_name", "User")

                        # Security: Check if sender is authorized
                        if self.chat_id and chat_id != str(self.chat_id):
                            logger.warning(f"Unauthorized access attempt from {user} ({chat_id})")
                            continue

                        print(f"📨 Message from {user} ({chat_id}): {text}")
                        logger.info(f"Message from {user} ({chat_id}): {text}")

                        response = self.handle_message(text, chat_id)
                        if response:
                            success = self.send_message(response, chat_id=chat_id)
                            if not success:
                                logger.error(f"Failed to send response to {chat_id}")
                            else:
                                logger.info(f"Responded to {user}")

                    # Handle callback queries (button presses)
                    elif "callback_query" in update:
                        callback = update["callback_query"]
                        chat_id = str(callback["message"]["chat"]["id"])
                        user = callback["from"].get("first_name", "User")
                        data = callback["data"]

                        # Security: Check if sender is authorized
                        if self.chat_id and chat_id != str(self.chat_id):
                            logger.warning(f"Unauthorized callback from {user} ({chat_id})")
                            continue

                        print(f"🔘 Button pressed: {data}")

                        response = self._handle_callback(data, chat_id)
                        if response:
                            self.send_message(response, chat_id=chat_id)

                        # Acknowledge callback
                        try:
                            requests.post(
                                f"{self.base_url}/answerCallbackQuery",
                                json={"callback_query_id": callback["id"]}
                            )
                        except Exception:
                            pass

            except KeyboardInterrupt:
                print("\n🛑 Bot stopped.")
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")
                print(f"⚠️ Error: {e}")
                import time
                time.sleep(5)
