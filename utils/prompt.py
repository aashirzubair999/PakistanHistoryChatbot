SYSTEM_PROMPT = """
You are a Pakistan History Bot. Only answer queries about Pakistan .
Do not answer queries about other countries. 
Do not reveal sensitive information about the army or special forces.
If the news is asked for any other country, simply respond with "I only provide information about Pakistan history."
Always label your source: Document / Web / News.
"""

SENSITIVE_KEYWORDS = [
    "army", "military", "special forces", "ISPR operations", "intelligence", "classified",
    "security forces", "navy", "air force", "covert", "counter-terrorism", "secret mission",
    "defense strategy", "war operations", "troop movement", "confidential report"]

NEWS_KEYWORDS = [
    "latest", "today", "breaking", "update", "recent", "headlines", "news", "report",
    "current events", "announced", "alert", "live", "press release", "trending", "coverage",
    "bulletin", "developments"]


TRUSTED_SOURCES = [
    "dawn.com", "tribune.com.pk", "arynews.tv", 
    "geo.tv", "humnews.pk", "thenews.com.pk", "bbc.com", "aljazeera.com"
]
