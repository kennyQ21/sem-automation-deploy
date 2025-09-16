"""
Core prompt templates for the SEM automation system.
Each prompt includes few-shot examples for consistent output.
"""

# Enrichment Prompt
ENRICHMENT_SYSTEM = """You are an expert SEM strategist. For each keyword, provide:
- 4 long-tail expansions (buyer-intent variants)
- Intent classification (transactional/commercial/informational/brand/competitor)
- 2-3 headlines (≤30 chars) and 2 descriptions (≤90 chars)
- Suggested landing page from crawled content
- Confidence score (0-1)

Output in JSON format. Do not invent prices or make unsupported claims."""

ENRICHMENT_FEW_SHOT = """
Input: "running shoes"
Output: {
    "expansions": [
        "best running shoes for marathon training",
        "cushioned running shoes for long distance",
        "professional running shoes with support",
        "running shoes for everyday training"
    ],
    "intent": "commercial",
    "headlines": [
        "Pro Running Shoes In Stock",
        "Top-Rated Running Footwear",
        "Running Shoes - All Sizes"
    ],
    "descriptions": [
        "Find your perfect running shoes. Expert fitting & free returns.",
        "Premium running shoes for every training goal. Shop now."
    ],
    "landing_candidate": "/running-shoes/catalog",
    "confidence": 0.95
}

Input: "nike zoom vs brooks ghost"
Output: {
    "expansions": [
        "nike zoom vs brooks ghost cushioning",
        "nike zoom vs brooks ghost for marathons",
        "brooks ghost or nike zoom for running",
        "compare nike zoom brooks ghost reviews"
    ],
    "intent": "commercial",
    "headlines": [
        "Nike vs Brooks - Compare Now",
        "Running Shoe Face-Off",
        "Top Running Shoes Compared"
    ],
    "descriptions": [
        "Expert comparison of Nike Zoom & Brooks Ghost. See which fits your needs.",
        "Detailed running shoe comparison. Find your perfect match today."
    ],
    "landing_candidate": "/running-shoes/compare",
    "confidence": 0.85
}"""

# Clustering Justifier Prompt
CLUSTER_JUSTIFY_SYSTEM = """Analyze this keyword cluster and provide:
1. A 2-sentence justification for the grouping
2. A 1-2 word ad group name that captures the theme"""

CLUSTER_JUSTIFY_FEW_SHOT = """
Input: ["stability running shoes", "motion control shoes", "running shoes overpronation"]
Output: {
    "justification": "These keywords all target runners who need extra stability and motion control. The cluster focuses on corrective footwear for overpronation, making it a cohesive group for targeted ads.",
    "ad_group_name": "Stability Runners"
}

Input: ["marathon training shoes", "long distance running shoes", "endurance running footwear"]
Output: {
    "justification": "This cluster centers on footwear specifically designed for long-distance running and marathon training. The keywords indicate high purchase intent from serious runners preparing for endurance events.",
    "ad_group_name": "Marathon Shoes"
}"""

# Title Rewriter Prompt
TITLE_REWRITE_SYSTEM = """Optimize product titles for search. Maximum 150 characters.
Include key product attributes and target keywords while maintaining readability."""

TITLE_REWRITE_FEW_SHOT = """
Input: 
Product: "BrandX Zoom Elite Running Shoe"
Keyword: "mens stability running shoes"

Output: "BrandX Zoom Elite Men's Stability Running Shoes - Professional Grade Support & Cushioning"

Input:
Product: "UltraBoost Performance Runner"
Keyword: "marathon training shoes"

Output: "UltraBoost Performance Marathon Training Shoes - Long Distance Running with Energy Return"
"""

# PMax Creative Prompt
PMAX_CREATIVE_SYSTEM = """Generate Performance Max asset group content. Flag any claims that require verification.
Include:
- 5 headlines (≤30 chars)
- 4 descriptions (≤90 chars)
- 3 image suggestions
- Audience signals

Mark claims needing proof with [VERIFY]"""

PMAX_CREATIVE_FEW_SHOT = """
Input: "Stability Running Shoes"
Output: {
    "headlines": [
        "Premium Stability Shoes",
        "Run with Confidence",
        "Expert-Designed Support",
        "[VERIFY] #1 in Stability",
        "Perfect Your Running Form"
    ],
    "descriptions": [
        "Engineered stability features for a controlled, comfortable running experience",
        "Advanced support system helps prevent overpronation while running",
        "[VERIFY] Recommended by professional trainers worldwide",
        "Find your perfect fit with our stability running collection"
    ],
    "image_captions": [
        "Side view highlighting stability features",
        "Runner showing proper form with shoes",
        "Close-up of support technology"
    ],
    "audience_signals": [
        "running enthusiasts",
        "users who viewed stability shoes",
        "marathon training researchers",
        "overpronation related searches"
    ]
}

Input: "Carbon Plate Racing Shoes"
Output: {
    "headlines": [
        "Elite Racing Shoes",
        "Break Your Record",
        "Carbon-Powered Speed",
        "Racing Innovation",
        "Podium-Ready Performance"
    ],
    "descriptions": [
        "Carbon plate technology for explosive energy return on race day",
        "[VERIFY] Fastest racing shoe in independent tests",
        "Engineered for PR-breaking race performance",
        "Ultra-lightweight design meets racing power"
    ],
    "image_captions": [
        "Side profile with visible carbon plate",
        "Action shot during race",
        "Weight comparison visualization"
    ],
    "audience_signals": [
        "competitive runners",
        "marathon participants",
        "racing shoe researchers",
        "speed training enthusiasts"
    ]
}
"""