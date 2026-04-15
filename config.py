import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ============================================
# API KEYS & CREDENTIALS (Set in .env file)
# ============================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
AZURE_AI_ENDPOINT = os.getenv("AZURE_AI_ENDPOINT", "")
AZURE_AI_API_KEY = os.getenv("AZURE_AI_API_KEY", "")

DATABASE_FILE = "email_agent.db"
LOG_FILE = "email_agent.log"

# ============================================
# EMAIL TEMPLATES BY GOAL
# ============================================
EMAIL_TEMPLATES = {
    "event": {
        "subject_templates": [
            "You're Invited: {event_name} on {event_date}",
            "🎉 {event_name} — Save the Date: {event_date}",
            "Don't Miss {event_name} | {event_date}",
            "Join Us for {event_name} — {event_date}",
            "{event_name}: An Event You Won't Want to Miss"
        ],
        "body_template": [
            "We're thrilled to invite you to {event_name}, happening on {event_date}.",
            "This is going to be an incredible experience, and we'd love to have you there.",
            "Here's what you can expect:",
            "• Engaging sessions and activities\n• Networking opportunities\n• Memorable experiences",
            "Seats are limited, so make sure to reserve your spot today."
        ],
        "cta": "Reserve Your Spot",
        "preheader": "You're invited to something special — {event_name}"
    },
    "promotion": {
        "subject_templates": [
            "🔥 Exclusive Deal Just for You",
            "Limited Time Offer — Don't Miss Out!",
            "Your Special Discount Awaits",
            "Act Now: This Deal Won't Last",
            "We've Got Something Special for You"
        ],
        "body_template": [
            "We've got an exclusive offer that we think you'll love.",
            "For a limited time, you can take advantage of this special deal.",
            "Here's what's included:",
            "• Premium features at a discounted price\n• Exclusive bonus content\n• Priority support",
            "This offer expires soon, so don't wait!"
        ],
        "cta": "Claim Your Offer",
        "preheader": "An exclusive offer is waiting for you"
    },
    "engagement": {
        "subject_templates": [
            "We'd Love to Hear From You",
            "Quick Question for You",
            "What Do You Think About This?",
            "Your Opinion Matters to Us",
            "Let's Stay Connected"
        ],
        "body_template": [
            "We value your input and would love to hear your thoughts.",
            "Your feedback helps us create better experiences for you.",
            "We'd really appreciate it if you could take a moment to share your thoughts.",
            "It only takes a minute and makes a huge difference.",
            "Thank you for being part of our community!"
        ],
        "cta": "Share Your Thoughts",
        "preheader": "We'd love your input"
    },
    "announcement": {
        "subject_templates": [
            "Big News: {product_or_service} is Here!",
            "Introducing Something New",
            "Exciting Update You Need to Know",
            "We've Been Working on Something Special",
            "The Wait is Over — Check This Out"
        ],
        "body_template": [
            "We're excited to share some big news with you!",
            "After months of hard work, we're thrilled to announce something special.",
            "Here's what's new:",
            "• Brand new features and improvements\n• Better experience for you\n• More value than ever",
            "We can't wait for you to try it out!"
        ],
        "cta": "Learn More",
        "preheader": "We have exciting news to share"
    },
    "welcome": {
        "subject_templates": [
            "Welcome to {company_name}! 🎉",
            "Great to Have You Aboard!",
            "You're In! Here's What's Next",
            "Welcome — Let's Get Started",
            "Thanks for Joining {company_name}"
        ],
        "body_template": [
            "Welcome! We're so glad you're here.",
            "You've made a great decision, and we're excited to have you on board.",
            "Here's how to get started:",
            "• Explore our features\n• Set up your profile\n• Connect with the community",
            "If you need any help, don't hesitate to reach out!"
        ],
        "cta": "Get Started",
        "preheader": "Welcome aboard — here's how to get started"
    },
    "nurture": {
        "subject_templates": ["Quick tip for {audience_description}", "How to master {product_or_service}"],
        "body_template": ["We want to make sure you get the most out of {product_or_service}.", "Here is a quick tip to get you started."],
        "cta": "Read More",
        "preheader": "Level up your skills"
    }
}

TONE_PROFILES = {
    "professional": {
        "greeting": "Dear {name}",
        "closing": "Best regards",
        "style_notes": "Formal language, clear structure",
        "emoji_allowed": False
    },
    "casual": {
        "greeting": "Hey {name}",
        "closing": "Cheers",
        "style_notes": "Conversational",
        "emoji_allowed": True
    },
    "urgent": {
        "greeting": "Attention {name}",
        "closing": "Act now",
        "style_notes": "High pressure",
        "emoji_allowed": True
    },
    "friendly": {
        "greeting": "Hi {name}!",
        "closing": "Warmly",
        "style_notes": "Warm and personal",
        "emoji_allowed": True
    }
}

SPAM_TRIGGERS = ["free", "buy now", "urgent", "congratulations", "winner", "cash", "money"]

# Add missing ones needed by audience_engine.py
OPTIMAL_SEND_TIMES = {
    "general": [{"day": "Tuesday", "time": "10:00 AM", "confidence": 0.85, "reasoning": "High engagement day"}],
    "b2b": [{"day": "Wednesday", "time": "10:00 AM", "confidence": 0.9, "reasoning": "Mid-week focus"}]
}

EMAIL_PLATFORMS = {
    "Mailchimp": {"deliverability_score": 88, "best_for": "Beginners", "price_range": "Free/Paid", "max_subscribers": "Unlimited", "pros": ["Easy"], "cons": ["Expensive"]},
    "SendGrid": {"deliverability_score": 92, "best_for": "Developers", "price_range": "Paid", "max_subscribers": "Unlimited", "pros": ["API"], "cons": ["Complex"]}
}

GROWTH_STRATEGIES = {
    "lead_magnet": {"name": "Lead Magnet", "description": "Freebie in exchange for email", "difficulty": "Medium", "expected_growth_rate": "High", "time_to_results": "Immediate", "steps": ["Create PDF", "Setup form"], "tools_needed": ["Canva"]}
}

CALENDAR_TEMPLATES = {
    "engagement": {"weekly_mix": [{"type": "educational"}, {"type": "interactive"}]}
}
