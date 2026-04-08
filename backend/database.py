"""
Database module for News Platform
Handles SQLite database operations for news articles, categories, and AI analysis
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager
import json

Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    summary = Column(Text)
    content = Column(Text)
    source = Column(String(100), nullable=False, index=True)
    url = Column(String(1000), unique=True, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    country = Column(String(10), index=True)
    published_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Media fields
    thumbnail_url = Column(String(1000))
    image_url = Column(String(1000))
    
    # AI Analysis fields
    ai_sentiment = Column(String(20))  # positive, negative, neutral
    ai_sentiment_score = Column(Float)
    ai_categories = Column(JSON)  # AI-detected categories
    ai_entities = Column(JSON)  # AI-detected entities
    ai_summary = Column(Text)  # AI-generated summary
    ai_source_confidence = Column(Float)  # AI confidence in source validity
    ai_processed = Column(Boolean, default=False)
    ai_processed_at = Column(DateTime)

class LiveTVChannel(Base):
    __tablename__ = "live_tv_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)
    country = Column(String(10), index=True)
    language = Column(String(10))
    thumbnail = Column(String(1000))
    embed_url = Column(String(1000))
    stream_key = Column(String(200), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NewsDatabase:
    def __init__(self, database_url: str = "sqlite+aiosqlite:///./news_platform.db"):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session_factory = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def init_db(self):
        """Initialize database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    # News Article operations
    async def create_article(self, article_data: Dict[str, Any]) -> NewsArticle:
        """Create a new news article"""
        async with self.get_session() as session:
            article = NewsArticle(**article_data)
            session.add(article)
            await session.commit()
            await session.refresh(article)
            return article
    
    async def get_article_by_url(self, url: str) -> Optional[NewsArticle]:
        """Get article by URL"""
        async with self.get_session() as session:
            result = await session.execute(
                "SELECT * FROM news_articles WHERE url = :url", {"url": url}
            )
            return result.scalar_one_or_none()
    
    async def get_articles_by_category(
        self, 
        category: str, 
        limit: int = 20, 
        offset: int = 0,
        country: Optional[str] = None
    ) -> List[NewsArticle]:
        """Get articles by category with pagination"""
        async with self.get_session() as session:
            query = text("SELECT * FROM news_articles WHERE category = :category")
            params = {"category": category, "limit": limit, "offset": offset}
            
            if country:
                query = text("SELECT * FROM news_articles WHERE category = :category AND country = :country ORDER BY published_at DESC LIMIT :limit OFFSET :offset")
                params["country"] = country
            else:
                query = text("SELECT * FROM news_articles WHERE category = :category ORDER BY published_at DESC LIMIT :limit OFFSET :offset")
            
            result = await session.execute(query, params)
            return result.scalars().all()
    
    async def get_headlines(
        self, 
        limit: int = 20, 
        offset: int = 0,
        country: Optional[str] = None
    ) -> List[NewsArticle]:
        """Get latest headlines with pagination"""
        async with self.get_session() as session:
            if country:
                query = text("SELECT * FROM news_articles WHERE country = :country ORDER BY published_at DESC LIMIT :limit OFFSET :offset")
                params = {"country": country, "limit": limit, "offset": offset}
            else:
                query = text("SELECT * FROM news_articles ORDER BY published_at DESC LIMIT :limit OFFSET :offset")
                params = {"limit": limit, "offset": offset}
            
            result = await session.execute(query, params)
            return result.scalars().all()
    
    async def search_articles(
        self, 
        query: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[NewsArticle]:
        """Search articles"""
        async with self.get_session() as session:
            search_query = """
                SELECT * FROM news_articles 
                WHERE title LIKE :query OR summary LIKE :query OR content LIKE :query
                ORDER BY published_at DESC LIMIT :limit OFFSET :offset
            """
            params = {
                "query": f"%{query}%", 
                "limit": limit, 
                "offset": offset
            }
            
            result = await session.execute(search_query, params)
            return result.scalars().all()
    
    async def update_ai_analysis(
        self, 
        article_id: int, 
        ai_data: Dict[str, Any]
    ) -> Optional[NewsArticle]:
        """Update AI analysis for an article"""
        async with self.get_session() as session:
            article = await session.get(NewsArticle, article_id)
            if article:
                article.ai_sentiment = ai_data.get("sentiment")
                article.ai_sentiment_score = ai_data.get("sentiment_score")
                article.ai_categories = ai_data.get("categories")
                article.ai_entities = ai_data.get("entities")
                article.ai_summary = ai_data.get("summary")
                article.ai_source_confidence = ai_data.get("source_confidence")
                article.ai_processed = True
                article.ai_processed_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(article)
            return article
    
    # Live TV Channel operations
    async def create_channel(self, channel_data: Dict[str, Any]) -> LiveTVChannel:
        """Create a new live TV channel"""
        async with self.get_session() as session:
            channel = LiveTVChannel(**channel_data)
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            return channel
    
    async def get_channels_by_category(
        self, 
        category: str, 
        limit: int = 50
    ) -> List[LiveTVChannel]:
        """Get channels by category"""
        async with self.get_session() as session:
            result = await session.execute(
                """
                SELECT * FROM live_tv_channels 
                WHERE category = :category AND is_active = True
                ORDER BY name ASC LIMIT :limit
                """,
                {"category": category, "limit": limit}
            )
            return result.scalars().all()
    
    async def get_all_channels(self, limit: int = 50) -> List[LiveTVChannel]:
        """Get all active channels"""
        async with self.get_session() as session:
            result = await session.execute(
                """
                SELECT * FROM live_tv_channels 
                WHERE is_active = True
                ORDER BY name ASC LIMIT :limit
                """,
                {"limit": limit}
            )
            return result.scalars().all()
    
    async def get_channel_by_stream_key(self, stream_key: str) -> Optional[LiveTVChannel]:
        """Get channel by stream key"""
        async with self.get_session() as session:
            result = await session.execute(
                "SELECT * FROM live_tv_channels WHERE stream_key = :stream_key",
                {"stream_key": stream_key}
            )
            return result.scalar_one_or_none()
    
    # Statistics and cleanup
    async def get_article_count(self, category: Optional[str] = None) -> int:
        """Get total article count"""
        async with self.get_session() as session:
            if category:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM news_articles WHERE category = :category"),
                    {"category": category}
                )
            else:
                result = await session.execute(text("SELECT COUNT(*) FROM news_articles"))
            return result.scalar()
    
    async def cleanup_old_articles(self, days: int = 30) -> int:
        """Remove articles older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        async with self.get_session() as session:
            result = await session.execute(
                "DELETE FROM news_articles WHERE created_at < :cutoff_date",
                {"cutoff_date": cutoff_date}
            )
            await session.commit()
            return result.rowcount

# Global database instance
db = NewsDatabase()
