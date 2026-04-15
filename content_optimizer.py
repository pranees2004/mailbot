# content_optimizer.py - AI Content Generation & Optimization Engine

import re
import random
from typing import List, Dict, Optional
from models import (
    CampaignBrief, EmailContent, SpamCheckResult,
    CampaignGoal, Tone
)
import json
import requests
from config import (
    EMAIL_TEMPLATES, TONE_PROFILES, SPAM_TRIGGERS,
    AZURE_AI_ENDPOINT, AZURE_AI_API_KEY
)


class ContentOptimizer:
    """Generates and optimizes email content based on campaign briefs."""

    def __init__(self):
        self.spam_triggers = SPAM_TRIGGERS
        self.templates = EMAIL_TEMPLATES
        self.tone_profiles = TONE_PROFILES
        self.api_key = AZURE_AI_API_KEY
        self.endpoint = AZURE_AI_ENDPOINT

    def generate_email(self, brief: CampaignBrief) -> EmailContent:
        """Generate complete email content from a campaign brief."""
        # Try Claude if API key is available
        if self.api_key:
            ai_content = self._generate_with_claude(brief)
            if ai_content:
                return ai_content

        # Fallback to template-based generation
        goal_key = brief.goal.value if isinstance(brief.goal, CampaignGoal) else brief.goal
        tone_key = brief.tone.value if isinstance(brief.tone, Tone) else brief.tone

        template = self.templates.get(goal_key, self.templates["engagement"])
        tone = self.tone_profiles.get(tone_key, self.tone_profiles["professional"])

        # Generate subject lines
        subject_lines = self._generate_subject_lines(brief, template)

        # Generate preheader
        preheader = self._generate_preheader(brief, template)

        # Generate greeting
        greeting = tone["greeting"].replace("{name}", "{{first_name}}")

        # Generate body
        body_paragraphs = self._generate_body(brief, template, tone)

        # Generate CTA
        cta_text = self._generate_cta(brief, template)

        # Generate closing
        closing = self._generate_closing(brief, tone)

        # Generate signature
        signature = self._generate_signature(brief)

        # Generate PS line
        ps_line = self._generate_ps(brief, goal_key)

        return EmailContent(
            subject_lines=subject_lines,
            preheader=preheader,
            greeting=greeting,
            body_paragraphs=body_paragraphs,
            cta_text=cta_text,
            cta_url=brief.cta_url or "https://yourlink.com",
            closing=closing,
            signature=signature,
            ps_line=ps_line
        )

    def _generate_with_claude(self, brief: CampaignBrief) -> Optional[EmailContent]:
        """Generate email content using Claude API."""
        try:
            prompt = f"""Generate a professional email campaign based on the following brief:
AI Goal: {brief.goal.value if isinstance(brief.goal, CampaignGoal) else brief.goal}
Tone: {brief.tone.value if isinstance(brief.tone, Tone) else brief.tone}
Event Name: {brief.event_name}
Event Date: {brief.event_date}
Target Audience: {brief.audience_description}
Key Messages: {", ".join(brief.key_messages)}

Return ONLY a JSON object with this structure:
{{
  "subject_lines": ["Subject 1", "Subject 2", "Subject 3"],
  "preheader": "Short preview text",
  "greeting": "Greeting with {{first_name}}",
  "body_paragraphs": ["Para 1", "Para 2", "Para 3"],
  "cta_text": "Button Text",
  "closing": "Closing line",
  "ps_line": "Postscript (optional)"
}}
"""
            headers = {
                "api-key": self.api_key,
                "content-type": "application/json"
            }
            data = {
                "model": "claude-3-5-sonnet-20240620",  # Or whatever model is deployed on Azure
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}]
            }

            # Handle Azure API URL format - usually requires /v1/messages path
            url = self.endpoint
            if not url.endswith("/v1/messages") and not url.endswith("/messages"):
                url = f"{url.rstrip('/')}/v1/messages"

            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()
            
            if "content" in response_json:
                ai_text = response_json["content"][0]["text"]
                # Extract JSON from potential markdown blocks
                json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                if json_match:
                    content_dict = json.loads(json_match.group(0))
                    return EmailContent(
                        subject_lines=content_dict.get("subject_lines", []),
                        preheader=content_dict.get("preheader", ""),
                        greeting=content_dict.get("greeting", "Hello {{first_name}},"),
                        body_paragraphs=content_dict.get("body_paragraphs", []),
                        cta_text=content_dict.get("cta_text", "Learn More"),
                        cta_url=brief.cta_url or "https://yourlink.com",
                        closing=content_dict.get("closing", "Best regards,"),
                        signature=self._generate_signature(brief),
                        ps_line=content_dict.get("ps_line", "")
                    )
            return None
        except Exception as e:
            print(f"Claude API Error: {e}")
            return None

    def _generate_subject_lines(self, brief: CampaignBrief, template: Dict) -> List[str]:
        """Generate multiple subject line variations."""
        subjects = []
        for tmpl in template["subject_templates"]:
            subject = tmpl.format(
                event_name=brief.event_name or "Our Event",
                event_date=brief.event_date or "Coming Soon",
                product_or_service=brief.product_or_service or "Our Product",
                company_name=brief.company_name or "Our Team",
                audience_description=brief.audience_description or "You"
            )
            subjects.append(subject)

        # Add personalized variant
        if brief.event_name:
            subjects.append(f"{{{{first_name}}}}, you're invited to {brief.event_name}!")
        else:
            subjects.append(f"{{{{first_name}}}}, we have something special for you")

        return subjects[:6]

    def _generate_preheader(self, brief: CampaignBrief, template: Dict) -> str:
        """Generate preheader text."""
        preheader = template.get("preheader", "")
        return preheader.format(
            event_name=brief.event_name or "our event",
            product_or_service=brief.product_or_service or "this",
            company_name=brief.company_name or "us"
        )

    def _generate_body(self, brief: CampaignBrief, template: Dict, tone: Dict) -> List[str]:
        """Generate email body paragraphs."""
        paragraphs = []

        for tmpl in template["body_template"]:
            para = tmpl.format(
                event_name=brief.event_name or "our event",
                event_date=brief.event_date or "soon",
                product_or_service=brief.product_or_service or "our solution",
                company_name=brief.company_name or "our team",
                audience_description=brief.audience_description or "you"
            )
            paragraphs.append(para)

        # Add key messages if provided
        if brief.key_messages:
            key_points = "\n".join([f"✦ {msg}" for msg in brief.key_messages])
            paragraphs.insert(2, f"Here's what makes this special:\n{key_points}")

        return paragraphs

    def _generate_cta(self, brief: CampaignBrief, template: Dict) -> str:
        """Generate call-to-action text."""
        return template.get("cta", "Learn More")

    def _generate_closing(self, brief: CampaignBrief, tone: Dict) -> str:
        """Generate closing line."""
        closing_base = tone["closing"]
        if brief.sender_name:
            return f"{closing_base},\n{brief.sender_name}"
        elif brief.company_name:
            return f"{closing_base},\nThe {brief.company_name} Team"
        return f"{closing_base},\nThe Team"

    def _generate_signature(self, brief: CampaignBrief) -> str:
        """Generate email signature."""
        parts = []
        if brief.sender_name:
            parts.append(brief.sender_name)
        if brief.company_name:
            parts.append(brief.company_name)
        return " | ".join(parts) if parts else ""

    def _generate_ps(self, brief: CampaignBrief, goal: str) -> str:
        """Generate PS line based on campaign goal."""
        ps_options = {
            "event": f"Seats are filling up fast for {brief.event_name or 'this event'}. Don't wait!",
            "promotion": "This offer is only available for a limited time. Act now!",
            "conversion": "Join thousands of satisfied customers who made the switch.",
            "engagement": "Hit reply — we read every single response!",
            "announcement": "Stay tuned for more exciting updates coming soon.",
            "welcome": "Need help getting started? Just reply to this email!",
            "nurture": "Found this helpful? Forward it to a friend who might enjoy it too.",
            "re-engagement": "We miss you! Come back and see what's new."
        }
        return ps_options.get(goal, "")

    # ==========================================
    # SPAM CHECKER
    # ==========================================

    def check_spam(self, email_content: EmailContent) -> SpamCheckResult:
        """Run comprehensive spam and deliverability check."""
        issues = []
        suggestions = []
        score = 100.0

        full_text = " ".join([
            " ".join(email_content.subject_lines),
            email_content.preheader,
            " ".join(email_content.body_paragraphs),
            email_content.cta_text
        ]).lower()

        # Check 1: Spam trigger words
        found_triggers = []
        for trigger in self.spam_triggers:
            if trigger.lower() in full_text:
                found_triggers.append(trigger)
        if found_triggers:
            score -= len(found_triggers) * 3
            issues.append(f"Spam trigger words found: {', '.join(found_triggers[:5])}")
            suggestions.append("Replace spam trigger words with alternative phrasing")

        # Check 2: ALL CAPS in subject lines
        for subject in email_content.subject_lines:
            caps_words = re.findall(r'\b[A-Z]{3,}\b', subject)
            if caps_words:
                score -= 5
                issues.append(f"ALL CAPS detected in subject: {', '.join(caps_words)}")
                suggestions.append("Avoid using ALL CAPS — it triggers spam filters")
                break

        # Check 3: Excessive exclamation marks
        exclamation_count = full_text.count('!')
        if exclamation_count > 3:
            score -= (exclamation_count - 3) * 2
            issues.append(f"Too many exclamation marks: {exclamation_count}")
            suggestions.append("Limit exclamation marks to 1-2 per email")

        # Check 4: Subject line length
        for subject in email_content.subject_lines:
            if len(subject) > 60:
                score -= 3
                issues.append(f"Subject line too long ({len(subject)} chars): {subject[:40]}...")
                suggestions.append("Keep subject lines under 60 characters for mobile")
                break
            elif len(subject) < 10:
                score -= 5
                issues.append(f"Subject line too short ({len(subject)} chars)")
                suggestions.append("Subject lines under 10 chars look suspicious")
                break

        # Check 5: Has unsubscribe link placeholder
        html = email_content.get_full_html()
        if "unsubscribe" not in html.lower():
            score -= 15
            issues.append("No unsubscribe link found")
            suggestions.append("Always include an unsubscribe link — it's legally required")

        # Check 6: Image-to-text ratio (check for img tags)
        img_count = html.lower().count('<img')
        if img_count > 5:
            score -= 5
            issues.append(f"Too many images ({img_count}) — may trigger spam filters")
            suggestions.append("Keep images to 3-4 max and ensure good text-to-image ratio")

        # Check 7: Link count
        link_count = html.lower().count('<a ')
        if link_count > 8:
            score -= 5
            issues.append(f"Too many links ({link_count})")
            suggestions.append("Keep links to 3-5 per email for best deliverability")

        # Check 8: Personalization check
        if "{{first_name}}" not in html and "{name}" not in html:
            score -= 3
            issues.append("No personalization tokens found")
            suggestions.append("Add personalization (e.g., {{first_name}}) to improve engagement")

        # Check 9: Email length
        plain_text = email_content.get_plain_text()
        word_count = len(plain_text.split())
        if word_count > 500:
            score -= 3
            issues.append(f"Email is long ({word_count} words)")
            suggestions.append("Consider shorter emails (150-300 words) for better engagement")
        elif word_count < 50:
            score -= 5
            issues.append(f"Email is very short ({word_count} words)")
            suggestions.append("Emails under 50 words may look like spam")

        # Check 10: Has CTA
        if not email_content.cta_text:
            score -= 5
            issues.append("No clear call-to-action found")
            suggestions.append("Always include a clear, compelling CTA")

        # Check 11: Special characters in subject
        for subject in email_content.subject_lines:
            special_chars = re.findall(r'[💰🤑🔥💵$€£¥]', subject)
            if len(special_chars) > 2:
                score -= 3
                issues.append("Too many money/flashy emojis in subject line")
                suggestions.append("Limit flashy emojis — they trigger spam filters")
                break

        # Check 12: Reply-to check
        if not email_content.signature:
            score -= 2
            issues.append("No signature/sender identification")
            suggestions.append("Include sender name and company for trust")

        # Calculate grade
        score = max(0, min(100, score))
        if score >= 95:
            grade = "A+"
        elif score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        return SpamCheckResult(
            score=score,
            grade=grade,
            issues=issues if issues else ["No issues found — excellent!"],
            suggestions=suggestions if suggestions else ["Your email looks great!"],
            passed=score >= 70
        )

    def optimize_for_goal(self, email_content: EmailContent, goal: str) -> Dict:
        """Provide optimization suggestions based on campaign goal."""
        optimizations = {
            "conversion": {
                "structure": "Problem → Solution → Social Proof → CTA",
                "ideal_length": "200-300 words",
                "cta_style": "Action-oriented, specific benefit",
                "tips": [
                    "Lead with the pain point your audience faces",
                    "Include a testimonial or statistic for social proof",
                    "Make CTA button large and above the fold",
                    "Add urgency with a deadline or limited availability",
                    "Use 'you/your' more than 'we/our'"
                ]
            },
            "engagement": {
                "structure": "Hook → Value → Question → CTA",
                "ideal_length": "150-250 words",
                "cta_style": "Conversational, low commitment",
                "tips": [
                    "Ask a question in the subject line",
                    "Include interactive elements (polls, quizzes)",
                    "Write like you're talking to a friend",
                    "End with an open-ended question",
                    "Use 'Reply to this email' as a CTA"
                ]
            },
            "event": {
                "structure": "Invitation → Details → Benefits → RSVP CTA",
                "ideal_length": "200-350 words",
                "cta_style": "Clear RSVP/Register button",
                "tips": [
                    "Put the date and time in bold at the top",
                    "List 3-4 specific benefits of attending",
                    "Include speaker/host names if applicable",
                    "Add a calendar invite link",
                    "Create urgency with 'limited seats' if true"
                ]
            },
            "announcement": {
                "structure": "Big News → Details → Impact on Reader → CTA",
                "ideal_length": "150-300 words",
                "cta_style": "Learn more / Explore",
                "tips": [
                    "Lead with the most exciting detail",
                    "Explain how this benefits the reader specifically",
                    "Keep it focused on one announcement",
                    "Include a visual if possible",
                    "Tease future developments"
                ]
            }
        }

        return optimizations.get(goal, optimizations["engagement"])

    def rewrite_for_tone(self, text: str, target_tone: str) -> str:
        """Provide tone adjustment suggestions."""
        tone = self.tone_profiles.get(target_tone, self.tone_profiles["professional"])

        adjustments = {
            "professional": f"Rewrite in a formal, data-driven style. {tone['style_notes']}",
            "casual": f"Rewrite in a relaxed, conversational way. {tone['style_notes']}",
            "urgent": f"Rewrite with urgency and time-pressure. {tone['style_notes']}",
            "friendly": f"Rewrite warmly and personally. {tone['style_notes']}",
            "formal": f"Rewrite in highly formal corporate language. {tone['style_notes']}",
            "playful": f"Rewrite with energy and fun. {tone['style_notes']}"
        }

        return adjustments.get(target_tone, "Maintain current tone.")
