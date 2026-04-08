"""
AI Analysis Router for News Platform
Integrates AI service with database for news analysis
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from datetime import datetime

from database import db
from ai_service import ai_service, AIAnalysisResult

router = APIRouter()

class AnalysisRequest(BaseModel):
    article_id: int
    force_reanalyze: bool = False

class BatchAnalysisRequest(BaseModel):
    limit: int = 50
    category: Optional[str] = None
    force_reanalyze: bool = False

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    analysis_id: Optional[int] = None

@router.post("/analyze/{article_id}", summary="Analyze specific article with AI")
async def analyze_article(
    article_id: int, 
    background_tasks: BackgroundTasks,
    force_reanalyze: bool = False
):
    """Analyze a specific article using AI models"""
    try:
        # Get article from database
        async with db.get_session() as session:
            from database import NewsArticle
            article = await session.get(NewsArticle, article_id)
            
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")
            
            # Check if already analyzed
            if article.ai_processed and not force_reanalyze:
                return {
                    "success": True,
                    "message": "Article already analyzed",
                    "analysis": {
                        "sentiment": article.ai_sentiment,
                        "categories": article.ai_categories,
                        "entities": article.ai_entities,
                        "summary": article.ai_summary,
                        "source_confidence": article.ai_source_confidence
                    }
                }
            
            # Perform AI analysis
            article_data = {
                "title": article.title,
                "summary": article.summary,
                "source": article.source,
                "url": article.url
            }
            
            # Run AI analysis
            analysis_result = await ai_service.analyze_article(article_data)
            
            # Update database
            await db.update_ai_analysis(article_id, {
                "sentiment": analysis_result.sentiment,
                "sentiment_score": analysis_result.sentiment_score,
                "categories": analysis_result.categories,
                "entities": analysis_result.entities,
                "summary": analysis_result.summary,
                "source_confidence": analysis_result.source_confidence
            })
            
            return {
                "success": True,
                "message": "Analysis completed successfully",
                "analysis": {
                    "sentiment": analysis_result.sentiment,
                    "sentiment_score": analysis_result.sentiment_score,
                    "categories": analysis_result.categories,
                    "entities": analysis_result.entities,
                    "summary": analysis_result.summary,
                    "source_confidence": analysis_result.source_confidence,
                    "model_used": analysis_result.model_used,
                    "processing_time": analysis_result.processing_time
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/batch-analyze", summary="Batch analyze multiple articles")
async def batch_analyze(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Analyze multiple articles in the background"""
    try:
        # Get unanalyzed articles
        if request.category:
            articles = await db.get_articles_by_category(
                request.category, 
                limit=request.limit, 
                offset=0
            )
        else:
            articles = await db.get_headlines(limit=request.limit, offset=0)
        
        # Filter unanalyzed articles
        unanalyzed = [a for a in articles if not a.ai_processed or request.force_reanalyze]
        
        if not unanalyzed:
            return {
                "success": True,
                "message": "No articles to analyze",
                "total": 0,
                "analyzed": 0
            }
        
        # Run batch analysis in background
        background_tasks.add_task(
            run_batch_analysis, 
            unanalyzed[:10],  # Limit to 10 for performance
            request.force_reanalyze
        )
        
        return {
            "success": True,
            "message": f"Batch analysis started for {len(unanalyzed[:10])} articles",
            "total": len(unanalyzed),
            "analyzed": len(unanalyzed[:10])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.get("/stats", summary="Get AI analysis statistics")
async def get_analysis_stats():
    """Get statistics about AI analysis"""
    try:
        async with db.get_session() as session:
            from sqlalchemy import text
            
            # Get total articles
            total_result = await session.execute(text("SELECT COUNT(*) FROM news_articles"))
            total_articles = total_result.scalar()
            
            # Get analyzed articles
            analyzed_result = await session.execute(
                text("SELECT COUNT(*) FROM news_articles WHERE ai_processed = True")
            )
            analyzed_articles = analyzed_result.scalar()
            
            # Get sentiment distribution
            sentiment_result = await session.execute(text("""
                SELECT ai_sentiment, COUNT(*) as count 
                FROM news_articles 
                WHERE ai_processed = True AND ai_sentiment IS NOT NULL
                GROUP BY ai_sentiment
            """))
            sentiment_dist = {row[0]: row[1] for row in sentiment_result.fetchall()}
            
            # Get category distribution
            category_result = await session.execute(text("""
                SELECT json_extract(ai_categories, '$[0]') as category, COUNT(*) as count
                FROM news_articles 
                WHERE ai_processed = True AND ai_categories IS NOT NULL
                GROUP BY json_extract(ai_categories, '$[0]')
                ORDER BY count DESC
                LIMIT 10
            """))
            category_dist = {row[0]: row[1] for row in category_result.fetchall()}
            
            return {
                "total_articles": total_articles,
                "analyzed_articles": analyzed_articles,
                "analysis_coverage": round((analyzed_articles / total_articles * 100) if total_articles > 0 else 0, 2),
                "sentiment_distribution": sentiment_dist,
                "top_categories": category_dist,
                "unanalyzed_count": total_articles - analyzed_articles
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/models", summary="Get available AI models")
async def get_available_models():
    """Get list of available AI models"""
    return {
        "models": ai_service.models,
        "api_key_configured": bool(ai_service.openrouter_api_key),
        "service_status": "active" if ai_service.openrouter_api_key else "limited"
    }

async def run_batch_analysis(articles: List, force_reanalyze: bool = False):
    """Background task for batch analysis"""
    analyzed_count = 0
    
    for article in articles:
        try:
            if not article.ai_processed or force_reanalyze:
                article_data = {
                    "title": article.title,
                    "summary": article.summary,
                    "source": article.source,
                    "url": article.url
                }
                
                analysis_result = await ai_service.analyze_article(article_data)
                
                await db.update_ai_analysis(article.id, {
                    "sentiment": analysis_result.sentiment,
                    "sentiment_score": analysis_result.sentiment_score,
                    "categories": analysis_result.categories,
                    "entities": analysis_result.entities,
                    "summary": analysis_result.summary,
                    "source_confidence": analysis_result.source_confidence
                })
                
                analyzed_count += 1
                print(f"✅ Analyzed article: {article.title[:50]}...")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"❌ Failed to analyze article {article.id}: {e}")
    
    print(f"🎉 Batch analysis completed. Analyzed {analyzed_count} articles.")
