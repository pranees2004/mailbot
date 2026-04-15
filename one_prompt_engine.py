"""
one_prompt_engine.py - One-Prompt Campaign Generation Engine
Parses a single prompt and generates complete multi-channel campaign package
"""

import re
import random
from typing import List, Dict, Optional
from models import (
    CampaignBrief, FullCampaignPackage, SocialMediaAdaptation,
    SMSFollowUp, ABTestPlan, ContentCalendarEntry
)
from config import CALENDAR_TEMPLATES


class OnePromptEngine:
    """Module 3: Parse one prompt and generate everything"""

    # Keywords for parsing
    GOAL_KEYWORDS = {
        "conversion": ["sell", "convert", "purchase", "buy", "sign up", "signup", "register", "trial", "pricing", "offer", "discount", "sale", "revenue"],
        "engagement": ["engage", "read", "content", "blog", "newsletter", "educate", "inform", "share", "story", "update"],
        "announcement": ["announce", "launch", "new", "introduce", "release", "unveil", "reveal", "update", "feature", "just launched"],
        "retention": ["retain", "win back", "re-engage", "comeback", "miss you", "return", "reactivate", "churn", "inactive"],
        "nurture": ["nurture", "onboard", "welcome", "guide", "educate", "drip", "sequence", "learn", "course"],
        "referral": ["refer", "invite", "share with", "tell a friend", "word of mouth", "ambassador"]
    }

    TONE_KEYWORDS = {
        "professional": ["professional", "formal", "corporate", "business", "enterprise", "executive"],
        "casual": ["casual", "relaxed", "chill", "laid back", "conversational", "informal", "fun"],
        "urgent": ["urgent", "asap", "hurry", "limited time", "deadline", "last chance", "expires", "rush"],
        "friendly": ["friendly", "warm", "welcoming", "approachable", "kind", "personal", "human"],
        "inspirational": ["inspire", "motivate", "empower", "dream", "vision", "aspire", "transform"]
    }

    INDUSTRY_KEYWORDS = {
        "saas": ["saas", "software", "app", "platform", "tool", "api", "cloud", "subscription"],
        "ecommerce": ["ecommerce", "shop", "store", "product", "shipping", "cart", "retail", "buy"],
        "education": ["education", "course", "learn", "student", "teach", "school", "training", "academy"],
        "healthcare": ["health", "medical", "wellness", "fitness", "doctor", "patient", "care"],
        "finance": ["finance", "bank", "invest", "money", "fund", "trade", "crypto", "fintech"],
        "technology": ["tech", "ai", "machine learning", "developer", "code", "engineering", "data"],
        "marketing": ["marketing", "seo", "ads", "brand", "social media", "content", "growth"],
        "nonprofit": ["nonprofit", "charity", "donate", "volunteer", "cause", "community", "impact"]
    }

    def parse_prompt(self, prompt: str) -> CampaignBrief:
        """Parse a single natural language prompt into a structured campaign brief"""

        prompt_lower = prompt.lower()

        # Detect goal
        goal = "engagement"
        max_matches = 0
        for g, keywords in self.GOAL_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in prompt_lower)
            if matches > max_matches:
                max_matches = matches
                goal = g

        # Detect tone
        tone = "professional"
        max_matches = 0
        for t, keywords in self.TONE_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in prompt_lower)
            if matches > max_matches:
                max_matches = matches
                tone = t

        # Detect industry
        industry = "general"
        max_matches = 0
        for ind, keywords in self.INDUSTRY_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in prompt_lower)
            if matches > max_matches:
                max_matches = matches
                industry = ind

        # Extract audience
        audience = "general audience"
        audience_patterns = [
            r"(?:for|targeting|aimed at|to reach|audience[:\s]+)([^,.]+)",
            r"(?:developers|marketers|students|professionals|creators|founders|managers|executives|customers|users|subscribers|members)",
        ]
        for pattern in audience_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                audience = match.group(0).strip()
                break

        # Extract product name
        product_name = ""
        product_patterns = [
            r"(?:for|about|promoting|launching)\s+([A-Z][A-Za-z0-9\s]+?)(?:\s+targeting|\s+to|\s+for|,|\.)",
            r"(?:our|my|the)\s+(?:new\s+)?([A-Z][A-Za-z0-9\s]+?)(?:\s+is|\s+has|,|\.)"
        ]
        for pattern in product_patterns:
            match = re.search(pattern, prompt)
            if match:
                product_name = match.group(1).strip()
                break

        # Extract key messages
        key_messages = []
        sentences = re.split(r'[.!?,;]', prompt)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                key_messages.append(sentence)
        if not key_messages:
            key_messages = [prompt[:100]]

        # Detect urgency
        urgency = "normal"
        if any(w in prompt_lower for w in ["urgent", "asap", "immediately", "deadline", "today"]):
            urgency = "high"
        elif any(w in prompt_lower for w in ["soon", "upcoming", "next week"]):
            urgency = "medium"

        # Detect CTA type
        cta_type = "learn_more"
        cta_map = {
            "sign_up": ["sign up", "register", "join", "subscribe"],
            "buy_now": ["buy", "purchase", "order", "shop"],
            "download": ["download", "get the guide", "free resource"],
            "learn_more": ["learn", "read", "discover", "explore"],
            "start_trial": ["trial", "try", "test", "demo"]
        }
        for cta, keywords in cta_map.items():
            if any(kw in prompt_lower for kw in keywords):
                cta_type = cta
                break

        return CampaignBrief(
            goal=goal,
            audience=audience,
            key_messages=key_messages[:5],
            tone=tone,
            industry=industry,
            product_name=product_name,
            urgency=urgency,
            cta_type=cta_type,
            raw_prompt=prompt
        )

    def generate_social_media(self, brief: CampaignBrief) -> List[SocialMediaAdaptation]:
        """Generate social media adaptations from campaign brief"""

        topic = brief.product_name or brief.key_messages[0] if brief.key_messages else "our latest update"
        audience = brief.audience

        adaptations = []

        # Twitter/X
        twitter_texts = [
            f"Exciting news for {audience}! We just launched {topic}. Check it out and see how it can transform your workflow. Link in bio!",
            f"What if you could level up your {brief.industry} game? {topic} makes it possible. See for yourself.",
            f"We built {topic} because {audience} deserve better tools. The response has been incredible. Join the movement."
        ]
        twitter_text = random.choice(twitter_texts)
        twitter_hashtags = self._generate_hashtags(brief, "twitter")
        adaptations.append(SocialMediaAdaptation(
            platform="Twitter/X",
            text=twitter_text[:270],
            character_count=min(len(twitter_text), 270),
            hashtags=twitter_hashtags,
            has_emoji=True,
            post_type="text_with_link"
        ))

        # LinkedIn
        linkedin_texts = [
            f"Thrilled to announce that {topic} is now available for {audience}.\n\nAfter months of development and feedback from industry professionals, we have created something we believe will make a real difference in {brief.industry}.\n\nKey highlights:\n- {brief.key_messages[0] if brief.key_messages else 'Improved efficiency'}\n- Built specifically for {audience}\n- Designed with real user feedback\n\nI would love to hear your thoughts. What challenges are you facing in {brief.industry} today?\n\nLink in comments.",
        ]
        linkedin_text = linkedin_texts[0]
        linkedin_hashtags = self._generate_hashtags(brief, "linkedin")
        adaptations.append(SocialMediaAdaptation(
            platform="LinkedIn",
            text=linkedin_text[:2900],
            character_count=min(len(linkedin_text), 2900),
            hashtags=linkedin_hashtags,
            has_emoji=False,
            post_type="article_with_image"
        ))

        # Instagram
        instagram_texts = [
            f"Game changer alert! {topic} is HERE and it is everything {audience} have been asking for.\n\nSwipe to see the top features, tap the link in bio to get started.\n\nWho is ready to level up? Drop a emoji below!",
        ]
        instagram_text = instagram_texts[0]
        instagram_hashtags = self._generate_hashtags(brief, "instagram")
        adaptations.append(SocialMediaAdaptation(
            platform="Instagram",
            text=instagram_text[:2100],
            character_count=min(len(instagram_text), 2100),
            hashtags=instagram_hashtags,
            has_emoji=True,
            post_type="carousel_with_caption"
        ))

        # Facebook
        facebook_texts = [
            f"We are excited to share {topic} with our community!\n\n{brief.key_messages[0] if brief.key_messages else 'This is something special we have been working on'}.\n\nBuilt for {audience} who want better results without the complexity. We listened to your feedback and built exactly what you asked for.\n\nClick the link below to learn more and get started. We would love to hear what you think!",
        ]
        facebook_text = facebook_texts[0]
        adaptations.append(SocialMediaAdaptation(
            platform="Facebook",
            text=facebook_text[:2000],
            character_count=min(len(facebook_text), 2000),
            hashtags=self._generate_hashtags(brief, "facebook"),
            has_emoji=True,
            post_type="link_post"
        ))

        return adaptations

    def generate_sms_followup(self, brief: CampaignBrief) -> SMSFollowUp:
        """Generate SMS follow-up message"""

        topic = brief.product_name or "our update"

        sms_templates = {
            "conversion": f"Hi {{first_name}}! Did you see our email about {topic}? Your special offer is waiting. Tap here: [LINK]",
            "engagement": f"Hey {{first_name}}, new content about {topic} just dropped! Check your inbox or read here: [LINK]",
            "announcement": f"{{first_name}}, {topic} is LIVE! Be one of the first to check it out: [LINK]",
            "retention": f"We miss you, {{first_name}}! Come back and see what is new with {topic}. Special offer inside: [LINK]",
            "nurture": f"Hi {{first_name}}, your guide to {topic} is ready! Download it here: [LINK]",
            "referral": f"{{first_name}}, share {topic} with a friend and you both get rewarded! Details: [LINK]"
        }

        text = sms_templates.get(brief.goal, sms_templates["engagement"])

        delay_map = {
            "conversion": "24h",
            "engagement": "48h",
            "announcement": "12h",
            "retention": "72h",
            "nurture": "48h",
            "referral": "24h"
        }

        return SMSFollowUp(
            text=text[:160],
            character_count=min(len(text), 160),
            delay_after_email=delay_map.get(brief.goal, "24h"),
            includes_link=True
        )

    def generate_ab_tests(self, brief: CampaignBrief) -> List[ABTestPlan]:
        """Generate A/B testing suggestions"""

        topic = brief.product_name or "the campaign"

        tests = [
            ABTestPlan(
                test_name="Subject Line: Question vs Statement",
                variable="subject_line",
                variant_a=f"Are you ready to transform your {brief.industry} approach?",
                variant_b=f"Transform your {brief.industry} approach today",
                metric_to_track="open_rate",
                sample_size_recommendation="Min 1,000 per variant (2,000 total)",
                duration="4 hours, then send winner to remaining list"
            ),
            ABTestPlan(
                test_name="Subject Line: With vs Without Personalization",
                variable="subject_line_personalization",
                variant_a=f"{{first_name}}, check out {topic}",
                variant_b=f"Check out {topic} - you will love it",
                metric_to_track="open_rate",
                sample_size_recommendation="Min 1,000 per variant (2,000 total)",
                duration="4 hours, then send winner to remaining list"
            ),
            ABTestPlan(
                test_name="CTA: Action-Oriented vs Benefit-Oriented",
                variable="cta_button_text",
                variant_a="Get Started Now",
                variant_b=f"See How {topic} Helps You",
                metric_to_track="click_through_rate",
                sample_size_recommendation="Min 2,000 per variant (4,000 total)",
                duration="24 hours"
            ),
            ABTestPlan(
                test_name="Email Length: Short vs Detailed",
                variable="email_body_length",
                variant_a="Short version (~100 words): Key benefit + CTA only",
                variant_b="Detailed version (~300 words): Story + benefits + social proof + CTA",
                metric_to_track="click_through_rate, conversion_rate",
                sample_size_recommendation="Min 2,000 per variant (4,000 total)",
                duration="48 hours"
            ),
            ABTestPlan(
                test_name="Send Time: Morning vs Afternoon",
                variable="send_time",
                variant_a="9:00 AM recipient local time",
                variant_b="2:00 PM recipient local time",
                metric_to_track="open_rate, click_through_rate",
                sample_size_recommendation="Min 3,000 per variant (6,000 total)",
                duration="48 hours"
            )
        ]

        return tests

    def generate_content_calendar(self, brief: CampaignBrief,
                                    weeks: int = 4) -> List[ContentCalendarEntry]:
        """Generate a content calendar based on campaign goal"""

        template = CALENDAR_TEMPLATES.get(brief.goal, CALENDAR_TEMPLATES["engagement"])
        calendar = []
        topic = brief.product_name or brief.industry

        # Calendar content pools
        content_pools = {
            "conversion": {
                "value_content": [
                    ("Educational", f"5 Ways {topic} Saves You Time", "Build value before pitch"),
                    ("Case Study", f"How [Client] Achieved 3X Results", "Social proof"),
                    ("Tips", f"Quick Win: {topic} Pro Tips", "Demonstrate expertise"),
                ],
                "promotional": [
                    ("Offer", f"Special Launch Pricing for {topic}", "Direct conversion"),
                    ("Demo", f"See {topic} in Action (2-min video)", "Reduce friction"),
                    ("Comparison", f"{topic} vs Alternatives", "Handle objections"),
                ],
                "social_proof": [
                    ("Testimonial", f"What {brief.audience} Say About {topic}", "Build trust"),
                    ("Numbers", f"{topic} By The Numbers: Our Impact", "Credibility"),
                ],
                "urgency": [
                    ("Deadline", f"Last Day for {topic} Launch Pricing", "Create urgency"),
                    ("Scarcity", f"Only X Spots Left for {topic}", "FOMO"),
                ]
            },
            "engagement": {
                "educational": [
                    ("Guide", f"The Complete Guide to {topic}", "Deep value"),
                    ("Trends", f"2026 {brief.industry} Trends You Need to Know", "Thought leadership"),
                    ("How-To", f"How to Master {topic} in 5 Steps", "Practical value"),
                ],
                "interactive": [
                    ("Poll", f"Quick Poll: What is Your Biggest {brief.industry} Challenge?", "Drive replies"),
                    ("Quiz", f"Test Your {topic} Knowledge", "Fun engagement"),
                ],
                "story": [
                    ("Behind Scenes", f"How We Built {topic}: The Inside Story", "Humanize brand"),
                    ("Journey", f"From Idea to Impact: Our {topic} Journey", "Connection"),
                ],
                "community": [
                    ("Spotlight", f"Community Spotlight: {brief.audience} Success Stories", "Build community"),
                    ("AMA", f"Ask Us Anything About {topic}", "Accessibility"),
                ]
            }
        }

        pool = content_pools.get(brief.goal, content_pools["engagement"])
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        entry_id = 0
        for week in range(1, weeks + 1):
            for mix_item in template["weekly_mix"]:
                content_type = mix_item["type"]
                if content_type in pool and pool[content_type]:
                    item = pool[content_type][entry_id % len(pool[content_type])]
                    calendar.append(ContentCalendarEntry(
                        week=week,
                        day=days[entry_id % len(days)],
                        campaign_type=item[0],
                        subject_theme=item[1],
                        goal=brief.goal,
                        notes=item[2]
                    ))
                    entry_id += 1

        return calendar

    def _generate_hashtags(self, brief: CampaignBrief, platform: str) -> List[str]:
        """Generate relevant hashtags for social media"""

        base_hashtags = {
            "saas": ["#SaaS", "#Software", "#TechTools", "#Productivity"],
            "ecommerce": ["#Ecommerce", "#OnlineShopping", "#ShopNow", "#Retail"],
            "education": ["#Education", "#Learning", "#EdTech", "#OnlineLearning"],
            "healthcare": ["#Healthcare", "#Wellness", "#HealthTech", "#MedTech"],
            "finance": ["#FinTech", "#Finance", "#Investing", "#MoneyMatters"],
            "technology": ["#Tech", "#AI", "#Innovation", "#FutureTech"],
            "marketing": ["#Marketing", "#DigitalMarketing", "#Growth", "#MarTech"],
            "general": ["#Innovation", "#Business", "#Growth", "#Success"]
        }

        hashtags = base_hashtags.get(brief.industry, base_hashtags["general"])

        goal_tags = {
            "conversion": ["#Launch", "#NewProduct", "#GetStarted"],
            "engagement": ["#Community", "#JoinUs", "#LetsTalk"],
            "announcement": ["#BigNews", "#JustLaunched", "#Exciting"],
            "retention": ["#WelcomeBack", "#WeValue You", "#Community"],
        }
        hashtags.extend(goal_tags.get(brief.goal, ["#Update"]))

        if brief.product_name:
            hashtags.append(f"#{brief.product_name.replace(' ', '')}")

        max_tags = {"twitter": 3, "linkedin": 5, "instagram": 15, "facebook": 3}
        limit = max_tags.get(platform, 5)

        return hashtags[:limit]
