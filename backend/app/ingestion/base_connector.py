"""Base connector for all data sources"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import re


class RawEvent:
    """Standard raw event schema"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.source = kwargs.get('source', '')
        self.domain = kwargs.get('domain', '')
        self.title = kwargs.get('title', '')
        self.text = kwargs.get('text', '')
        self.url = kwargs.get('url', '')
        self.published_at = kwargs.get('published_at', '')
        self.language = kwargs.get('language', 'en')
        self.raw_data = kwargs.get('raw_data', {})
        self.seed_type = kwargs.get('seed_type', 'breaking_event')  # MiroFish integration
        self.importance = kwargs.get('importance', 5)
        self.entities = kwargs.get('entities', [])
        self.sentiment = kwargs.get('sentiment', 0.0)


class BaseConnector(ABC):
    """Base class for all data source connectors"""
    
    def __init__(self):
        self.source_id: str = ""
        self.domain: str = ""
        self.update_interval: int = 3600  # Default 1 hour
        self.rate_limit: int = 60  # Default 60 requests per minute
        self.seed_type: str = "breaking_event"  # MiroFish seed type
        
    @abstractmethod
    async def fetch(self) -> List[RawEvent]:
        """Fetch raw data from source"""
        pass
    
    def normalize(self, raw: Dict[str, Any]) -> RawEvent:
        """Normalize to common RawEvent schema"""
        return RawEvent(
            id=str(uuid.uuid4()),
            source=self.source_id,
            domain=self.domain,
            title=raw.get('title', ''),
            text=raw.get('text', raw.get('description', '')),
            url=raw.get('url', raw.get('link', '')),
            published_at=self.parse_date(raw),
            language=raw.get('language', 'en'),
            raw_data=raw,
            seed_type=self.seed_type
        )
    
    def parse_date(self, raw: Dict[str, Any]) -> str:
        """Parse date from various formats"""
        date_fields = ['published_at', 'publishedDate', 'date', 'pubDate', 'created_at', 'timestamp']
        for field in date_fields:
            if field in raw and raw[field]:
                return str(raw[field])
        return datetime.now().isoformat()
    
    def clean_text(self, text: str) -> str:
        """Clean text content"""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        return text.strip()
    
    def parse_rss(self, xml_content: str) -> List[RawEvent]:
        """Parse RSS feed content"""
        try:
            import feedparser
            feed = feedparser.parse(xml_content)
            events = []
            for entry in feed.entries:
                event = RawEvent(
                    id=str(uuid.uuid4()),
                    source=self.source_id,
                    domain=self.domain,
                    title=getattr(entry, 'title', ''),
                    text=self.clean_text(getattr(entry, 'summary', '')),
                    url=getattr(entry, 'link', ''),
                    published_at=getattr(entry, 'published', ''),
                    language='en',
                    raw_data={'entry': entry},
                    seed_type=self.seed_type
                )
                events.append(event)
            return events
        except Exception as e:
            print(f"RSS parsing error for {self.source_id}: {e}")
            return []
    
    def parse_json_api(self, json_content: Dict[str, Any]) -> List[RawEvent]:
        """Parse JSON API response"""
        events = []
        # Override in specific connectors
        return events
