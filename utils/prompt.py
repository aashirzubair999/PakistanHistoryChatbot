SYSTEM_PROMPT = """
You are a Pakistan History Bot. Only answer queries about Pakistan history.
Do not answer queries about other countries. 
Do not reveal sensitive information about the army or special forces.
Always label your source: Document / Web / News.
"""

SENSITIVE_KEYWORDS = ["army", "special forces", "ISPR operations"]
NEWS_KEYWORDS = ["latest", "today", "breaking", "update", "recent"]

TRUSTED_SOURCES = [
    "dawn.com", "tribune.com.pk", "arynews.tv", 
    "geo.tv", "humnews.pk", "thenews.com.pk", "bbc.com", "aljazeera.com"
]
