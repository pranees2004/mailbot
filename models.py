# models.py - Data Models for AI Email Agent

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class CampaignGoal(Enum):
    CONVERSION = "conversion"
    ENGAGEMENT = "engagement"
    ANNOUNCEMENT = "announcement"
    NURTURE = "nurture"
    REENGAGEMENT = "re-engagement"
    WELCOME = "welcome"
    EVENT = "event"
    PROMOTION = "promotion"


class Tone(Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    URGENT = "urgent"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    PLAYFUL = "playful"


class SubscriptionStatus(Enum):
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    PENDING = "pending"


@dataclass
class Subscriber:
    email: str
    name: str = ""
    tags: List[str] = field(default_factory=list)
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    subscribed_date: str = ""
    last_engaged: str = ""
    engagement_score: float = 0.0
    timezone: str = "UTC"
    metadata: Dict = field(default_factory=dict)


@dataclass
class CampaignBrief:
    goal: CampaignGoal = CampaignGoal.ENGAGEMENT
    audience_description: str = ""
    key_messages: List[str] = field(default_factory=list)
    tone: Tone = Tone.PROFESSIONAL
    product_or_service: str = ""
    cta_url: str = ""
    sender_name: str = ""
    company_name: str = ""
    event_name: str = ""
    event_date: str = ""
    recipients: List[str] = field(default_factory=list)


@dataclass
class EmailContent:
    subject_lines: List[str] = field(default_factory=list)
    preheader: str = ""
    greeting: str = ""
    body_paragraphs: List[str] = field(default_factory=list)
    cta_text: str = ""
    cta_url: str = ""
    closing: str = ""
    signature: str = ""
    ps_line: str = ""

    def get_full_html(self) -> str:
        body_html = ""
        for p in self.body_paragraphs:
            body_html += f"<p style='font-size:16px;line-height:1.6;color:#333;'>{p}</p>"

        return f"""
        <html>
        <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
            <h2 style="color:#2c3e50;">{self.subject_lines[0] if self.subject_lines else ''}</h2>
            <p style="font-size:16px;color:#333;">{self.greeting}</p>
            {body_html}
            <div style="text-align:center;margin:30px 0;">
                <a href="{self.cta_url}" style="background-color:#3498db;color:white;padding:14px 28px;
                text-decoration:none;border-radius:5px;font-size:16px;font-weight:bold;">{self.cta_text}</a>
            </div>
            <p style="font-size:16px;color:#333;">{self.closing}</p>
            <p style="font-size:14px;color:#666;">{self.signature}</p>
            {f'<p style="font-size:13px;color:#888;font-style:italic;">P.S. {self.ps_line}</p>' if self.ps_line else ''}
            <hr style="border:none;border-top:1px solid #eee;margin-top:30px;">
            <p style="font-size:11px;color:#999;text-align:center;">
                You received this because you subscribed. 
                <a href="{{unsubscribe_url}}">Unsubscribe</a>
            </p>
        </body>
        </html>"""

    def get_plain_text(self) -> str:
        body = "\n\n".join(self.body_paragraphs)
        return f"{self.greeting}\n\n{body}\n\n{self.cta_text}: {self.cta_url}\n\n{self.closing}\n{self.signature}"


@dataclass
class SpamCheckResult:
    score: float = 0.0
    grade: str = "A+"
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    passed: bool = True


@dataclass
class ABTest:
    test_name: str = ""
    variant_a: str = ""
    variant_b: str = ""
    hypothesis: str = ""
    metric: str = "open_rate"
    recommended_sample_size: int = 1000
    recommended_duration_hours: int = 4


@dataclass
class SocialAdaptation:
    platform: str = ""
    content: str = ""
    hashtags: List[str] = field(default_factory=list)
    char_limit: int = 0
    char_used: int = 0


@dataclass
class SMSFollowUp:
    message: str = ""
    char_count: int = 0
    delay_hours: int = 24
    trigger: str = "non-opener"


@dataclass
class CampaignPackage:
    brief: CampaignBrief = None
    email_content: EmailContent = None
    spam_check: SpamCheckResult = None
    ab_tests: List[ABTest] = field(default_factory=list)
    social_posts: List[SocialAdaptation] = field(default_factory=list)
    sms_followup: SMSFollowUp = None
    send_time_recommendation: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class EmailLog:
    message_id: str = ""
    recipient: str = ""
    subject: str = ""
    status: str = "pending"
    sent_at: str = ""
    opened: bool = False
    clicked: bool = False
    error: str = ""


@dataclass
class TelegramCommand:
    command: str = ""
    recipients: List[str] = field(default_factory=list)
    subject: str = ""
    event_name: str = ""
    event_date: str = ""
    tone: Tone = Tone.PROFESSIONAL
    goal: CampaignGoal = CampaignGoal.EVENT
    raw_text: str = ""
