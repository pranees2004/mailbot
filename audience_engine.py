"""
audience_engine.py - Module 1: Audience Expansion Engine
Handles segmentation, send time optimization, growth strategies, platform recommendations.
"""
import random
from typing import List, Dict, Optional
from models import (
    AudienceSegment, SendTimeRecommendation, GrowthStrategy, PlatformRecommendation, CampaignBrief
)
from config import OPTIMAL_SEND_TIMES, EMAIL_PLATFORMS, GROWTH_STRATEGIES


class AudienceEngine:
    """Analyzes audiences, recommends send times, growth strategies, and platforms."""

    def segment_audience(self, subscriber_data: Optional[Dict] = None) -> List[AudienceSegment]:
        """Analyze subscriber data and create audience segments."""
        segments = [
            AudienceSegment(
                name="Champions",
                description="Highly engaged subscribers who open and click consistently. They are your brand advocates.",
                size_percentage=8.0,
                engagement_level="Very High",
                recommended_frequency="2-3x per week",
                best_content_type="Exclusive content, early access, VIP offers",
                strategy="Reward loyalty with exclusive perks. Ask for referrals and reviews. Give them first access to new features or products."
            ),
            AudienceSegment(
                name="Active Engagers",
                description="Regular openers and occasional clickers. Engaged but not at champion level yet.",
                size_percentage=22.0,
                engagement_level="High",
                recommended_frequency="2x per week",
                best_content_type="Educational content, product updates, case studies",
                strategy="Nurture toward champion status with increasingly personalized content. Use dynamic content blocks to tailor messages."
            ),
            AudienceSegment(
                name="Casual Readers",
                description="Open emails occasionally but rarely click. They skim content and are passively interested.",
                size_percentage=30.0,
                engagement_level="Medium",
                recommended_frequency="1x per week",
                best_content_type="Newsletters, curated content, short tips",
                strategy="Focus on compelling subject lines to maintain opens. Test different content formats. Use re-engagement triggers."
            ),
            AudienceSegment(
                name="Window Shoppers",
                description="New subscribers who haven't established a pattern yet. Still evaluating your content.",
                size_percentage=15.0,
                engagement_level="Medium-Low",
                recommended_frequency="1x per week (welcome series first)",
                best_content_type="Welcome series, brand story, best-of content",
                strategy="Deploy a strong 5-7 email welcome series. Showcase your best content immediately. Set expectations clearly."
            ),
            AudienceSegment(
                name="Drifting Away",
                description="Previously active subscribers whose engagement has declined over the past 30-60 days.",
                size_percentage=18.0,
                engagement_level="Low",
                recommended_frequency="1x per week with re-engagement focus",
                best_content_type="Re-engagement campaigns, surveys, special offers",
                strategy="Launch a targeted re-engagement sequence. Ask what content they want. Offer incentive to re-engage. Set a sunset deadline."
            ),
            AudienceSegment(
                name="Inactive / At Risk",
                description="Haven't opened or clicked in 60+ days. At high risk of becoming dead weight on your list.",
                size_percentage=7.0,
                engagement_level="Very Low",
                recommended_frequency="Final re-engagement then remove",
                best_content_type="Win-back campaign, 'We miss you' emails",
                strategy="Send a final 3-email win-back sequence. If no engagement, move to suppression list to protect deliverability."
            ),
        ]
        return segments

    def get_send_times(self, business_type: str = "general", timezone: str = "US/Eastern") -> List[SendTimeRecommendation]:
        """Recommend optimal send times based on business type."""
        btype = business_type.lower()
        if btype not in OPTIMAL_SEND_TIMES:
            btype = "general"

        recommendations = []
        for slot in OPTIMAL_SEND_TIMES[btype]:
            rec = SendTimeRecommendation(
                day=slot["day"],
                time=f"{slot['time']} {timezone}",
                timezone=timezone,
                confidence=slot["confidence"],
                reasoning=slot["reasoning"]
            )
            recommendations.append(rec)
        return recommendations

    def get_growth_strategies(self, current_list_size: int = 0, budget: str = "low") -> List[GrowthStrategy]:
        """Recommend list growth strategies based on current situation."""
        strategies = []
        for key, data in GROWTH_STRATEGIES.items():
            if budget == "low" and data["difficulty"] == "Hard":
                continue
            strategy = GrowthStrategy(
                name=data["name"],
                description=data["description"],
                difficulty=data["difficulty"],
                expected_growth_rate=data["expected_growth_rate"],
                time_to_results=data["time_to_results"],
                steps=data["steps"],
                tools_needed=data["tools_needed"]
            )
            strategies.append(strategy)
        return strategies

    def recommend_platforms(self, list_size: int = 0, budget: str = "low", needs: str = "general") -> List[PlatformRecommendation]:
        """Score and rank email platforms based on user needs."""
        recommendations = []
        for name, data in EMAIL_PLATFORMS.items():
            score = data["deliverability_score"]

            # Adjust score based on needs
            if "developer" in needs.lower() and name == "SendGrid":
                score += 8
            elif "creator" in needs.lower() and name == "ConvertKit":
                score += 8
            elif "beginner" in needs.lower() and name == "Mailchimp":
                score += 8
            elif "budget" in needs.lower() and name == "Brevo (Sendinblue)":
                score += 10

            # Adjust for budget
            if budget == "low" and "Free" in data["price_range"]:
                score += 5

            rec = PlatformRecommendation(
                name=name,
                score=min(score, 100),
                best_for=data["best_for"],
                max_subscribers=data["max_subscribers"],
                price_range=data["price_range"],
                pros=data["pros"],
                cons=data["cons"]
            )
            recommendations.append(rec)

        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations

    def format_segments_report(self, segments: List[AudienceSegment]) -> str:
        """Format audience segments into a readable report."""
        lines = ["=" * 60, "AUDIENCE SEGMENTATION ANALYSIS", "=" * 60, ""]
        for i, seg in enumerate(segments, 1):
            lines.append(f"Segment {i}: {seg.name} ({seg.size_percentage}% of list)")
            lines.append(f"  Engagement: {seg.engagement_level}")
            lines.append(f"  Description: {seg.description}")
            lines.append(f"  Send Frequency: {seg.recommended_frequency}")
            lines.append(f"  Best Content: {seg.best_content_type}")
            lines.append(f"  Strategy: {seg.strategy}")
            lines.append("")
        return "\n".join(lines)

    def format_send_times_report(self, recommendations: List[SendTimeRecommendation]) -> str:
        """Format send time recommendations into a readable report."""
        lines = ["=" * 60, "OPTIMAL SEND TIME RECOMMENDATIONS", "=" * 60, ""]
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"Option {i}: {rec.day} at {rec.time}")
            lines.append(f"  Confidence: {rec.confidence * 100:.0f}%")
            lines.append(f"  Why: {rec.reasoning}")
            lines.append("")
        return "\n".join(lines)

    def format_growth_report(self, strategies: List[GrowthStrategy]) -> str:
        """Format growth strategies into a readable report."""
        lines = ["=" * 60, "LIST GROWTH STRATEGIES", "=" * 60, ""]
        for i, strat in enumerate(strategies, 1):
            lines.append(f"Strategy {i}: {strat.name}")
            lines.append(f"  Difficulty: {strat.difficulty}")
            lines.append(f"  Expected Growth: {strat.expected_growth_rate}")
            lines.append(f"  Time to Results: {strat.time_to_results}")
            lines.append(f"  Description: {strat.description}")
            lines.append(f"  Steps:")
            for j, step in enumerate(strat.steps, 1):
                lines.append(f"    {j}. {step}")
            lines.append(f"  Tools Needed: {', '.join(strat.tools_needed)}")
            lines.append("")
        return "\n".join(lines)

    def format_platform_report(self, platforms: List[PlatformRecommendation]) -> str:
        """Format platform recommendations into a readable report."""
        lines = ["=" * 60, "EMAIL PLATFORM RECOMMENDATIONS", "=" * 60, ""]
        for i, plat in enumerate(platforms, 1):
            lines.append(f"#{i}: {plat.name} (Score: {plat.score}/100)")
            lines.append(f"  Best For: {plat.best_for}")
            lines.append(f"  Max Subscribers: {plat.max_subscribers}")
            lines.append(f"  Pricing: {plat.price_range}")
            lines.append(f"  Pros: {', '.join(plat.pros)}")
            lines.append(f"  Cons: {', '.join(plat.cons)}")
            lines.append("")
        return "\n".join(lines)
