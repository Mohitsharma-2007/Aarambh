"""utils/text_filter.py — News categorization, keyword filtering, deduplication"""
import re
from typing import List, Dict, Optional

# ── Category keyword maps ──────────────────────────────────────────────────────
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "finance": [
        "stock", "market", "trade", "economy", "gdp", "inflation", "interest rate",
        "federal reserve", "rbi", "sensex", "nifty", "nasdaq", "dow", "s&p",
        "equity", "bond", "crypto", "bitcoin", "ipo", "earnings", "revenue",
        "profit", "loss", "investment", "fund", "portfolio", "rupee", "dollar",
        "forex", "commodity", "oil", "gold", "silver",
    ],
    "health": [
        "health", "hospital", "disease", "virus", "covid", "vaccine", "pandemic",
        "medicine", "drug", "fda", "who", "cdc", "outbreak", "infection", "cancer",
        "diabetes", "mental health", "surgery", "treatment", "clinical", "medical",
        "epidemic", "pathogen", "antibody", "immunity", "quarantine", "symptom",
        "healthcare", "pharmaceutical", "biotech", "patient", "doctor", "nurse",
    ],
    "geopolitical": [
        "war", "conflict", "sanction", "diplomacy", "military", "nato", "un",
        "treaty", "election", "protest", "coup", "border", "refugee", "missile",
        "nuclear", "alliance", "summit", "ceasefire", "invasion", "occupation",
        "geopolitical", "tension", "crisis", "security", "terrorism", "extremist",
        "foreign policy", "bilateral", "multilateral", "un security council",
    ],
    "technology": [
        "ai", "artificial intelligence", "machine learning", "tech", "software",
        "hardware", "startup", "silicon valley", "apple", "google", "microsoft",
        "meta", "amazon", "nvidia", "chip", "semiconductor", "cloud", "data",
        "cyber", "hack", "privacy", "5g", "quantum", "robot", "automation",
    ],
    "politics": [
        "government", "parliament", "congress", "senate", "president", "prime minister",
        "minister", "party", "vote", "poll", "policy", "law", "bill", "supreme court",
        "constitution", "democrat", "republican", "bjp", "congress india", "modi",
        "biden", "trump", "election", "cabinet", "legislation",
    ],
    "sports": [
        "cricket", "football", "soccer", "tennis", "basketball", "olympics",
        "ipl", "world cup", "championship", "tournament", "league", "match",
        "player", "team", "coach", "trophy", "medal", "athlete", "sport",
    ],
    "science": [
        "science", "research", "study", "nasa", "space", "climate", "environment",
        "carbon", "renewable", "energy", "physics", "chemistry", "biology",
        "discovery", "experiment", "scientist", "journal", "university",
    ],
    "world": [
        "international", "global", "world", "foreign", "abroad", "overseas",
        "united nations", "european union", "g7", "g20", "brics",
    ],
}

# ── Health sub-categories ──────────────────────────────────────────────────────
HEALTH_SUBCATEGORIES: Dict[str, List[str]] = {
    "infectious_disease":  ["virus", "bacteria", "infection", "outbreak", "epidemic", "pandemic", "pathogen", "covid", "flu", "dengue", "malaria"],
    "mental_health":       ["mental health", "depression", "anxiety", "suicide", "psychiatric", "psychology", "stress", "burnout", "therapy"],
    "cancer":              ["cancer", "tumor", "oncology", "chemotherapy", "radiation", "biopsy", "carcinoma"],
    "cardiovascular":      ["heart", "cardiac", "stroke", "blood pressure", "hypertension", "cholesterol", "artery"],
    "nutrition":           ["diet", "nutrition", "obesity", "weight", "food", "vitamin", "supplement", "calorie"],
    "pharmaceutical":      ["drug", "medicine", "fda", "approval", "clinical trial", "vaccine", "dosage", "side effect"],
    "public_health":       ["who", "cdc", "health ministry", "public health", "policy", "healthcare", "insurance"],
    "medical_research":    ["study", "research", "trial", "discovery", "treatment", "cure", "breakthrough"],
}

# ── Geopolitical sub-categories ───────────────────────────────────────────────
GEO_SUBCATEGORIES: Dict[str, List[str]] = {
    "conflicts":    ["war", "battle", "attack", "missile", "airstrike", "troops", "military", "ceasefire", "invasion"],
    "diplomacy":    ["summit", "treaty", "agreement", "bilateral", "talks", "negotiation", "embassy", "ambassador"],
    "sanctions":    ["sanction", "ban", "embargo", "restriction", "tariff", "freeze", "asset"],
    "elections":    ["election", "vote", "ballot", "poll", "referendum", "candidate", "campaign"],
    "terrorism":    ["terror", "terrorist", "extremist", "attack", "bomb", "isis", "al-qaeda", "jihad"],
    "human_rights": ["refugee", "asylum", "protest", "rights", "freedom", "censorship", "oppression"],
    "economy":      ["trade war", "import", "export", "wto", "tariff", "economic", "gdp", "growth"],
}


def categorize(title: str, description: str = "") -> List[str]:
    """Return list of matching categories for an article."""
    text = (title + " " + description).lower()
    found = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(cat)
    return found or ["world"]


def health_subcategory(title: str, description: str = "") -> List[str]:
    text = (title + " " + description).lower()
    return [sub for sub, kws in HEALTH_SUBCATEGORIES.items()
            if any(kw in text for kw in kws)]


def geo_subcategory(title: str, description: str = "") -> List[str]:
    text = (title + " " + description).lower()
    return [sub for sub, kws in GEO_SUBCATEGORIES.items()
            if any(kw in text for kw in kws)]


def keyword_filter(articles: List[Dict], keywords: List[str],
                   require_all: bool = False) -> List[Dict]:
    """Filter articles by keywords (OR logic by default, AND if require_all)."""
    result = []
    for a in articles:
        text = (a.get("title","") + " " + a.get("summary","")).lower()
        matches = [kw.lower() in text for kw in keywords]
        if (require_all and all(matches)) or (not require_all and any(matches)):
            result.append(a)
    return result


def deduplicate(articles: List[Dict], key: str = "title",
                threshold: int = 20) -> List[Dict]:
    """Remove near-duplicate articles by title similarity."""
    seen_words: List[set] = []
    unique = []
    for a in articles:
        title = a.get(key, "").lower()
        words = set(re.findall(r'\w{4,}', title))
        if not words:
            continue
        is_dup = any(len(words & s) >= min(threshold, len(words)//2+1)
                     for s in seen_words)
        if not is_dup:
            unique.append(a)
            seen_words.append(words)
    return unique


def sentiment_score(text: str) -> Dict:
    """Simple rule-based sentiment (positive/negative/neutral word counts)."""
    pos = ["surge", "gain", "rise", "growth", "up", "profit", "win", "record",
           "strong", "positive", "boost", "rally", "recovery", "improve", "advance",
           "breakthrough", "success", "peace", "deal", "agreement"]
    neg = ["fall", "drop", "crash", "loss", "down", "crisis", "war", "attack",
           "decline", "negative", "fear", "risk", "cut", "fail", "collapse",
           "recession", "inflation", "conflict", "sanction", "ban", "protest"]
    txt = text.lower()
    pos_count = sum(1 for w in pos if w in txt)
    neg_count = sum(1 for w in neg if w in txt)
    total     = pos_count + neg_count or 1
    score     = (pos_count - neg_count) / total
    label     = "positive" if score > 0.1 else ("negative" if score < -0.1 else "neutral")
    return {"label": label, "score": round(score, 3),
            "positive_signals": pos_count, "negative_signals": neg_count}


def extract_entities(text: str) -> Dict:
    """Extract country, company, and person mentions using simple pattern matching."""
    COUNTRIES = [
        "India", "USA", "China", "Russia", "UK", "Germany", "France", "Japan",
        "Brazil", "Australia", "Canada", "Israel", "Iran", "Pakistan", "Ukraine",
        "Saudi Arabia", "Turkey", "South Korea", "Italy", "Spain", "Mexico",
    ]
    ORGS = [
        "Fed", "RBI", "NATO", "UN", "EU", "WHO", "IMF", "World Bank", "OPEC",
        "Apple", "Google", "Microsoft", "Tesla", "Amazon", "Meta", "Nvidia",
        "Goldman Sachs", "JPMorgan", "BlackRock",
    ]
    countries = [c for c in COUNTRIES if c in text]
    orgs      = [o for o in ORGS if o in text]
    return {"countries": countries, "organizations": orgs}
