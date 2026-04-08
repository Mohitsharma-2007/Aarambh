"""
AI Service for News Analysis using OpenRouter
Supports multiple AI models running in parallel for news analysis
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from dataclasses import dataclass

@dataclass
class AIAnalysisResult:
    """Result from AI analysis"""
    sentiment: str
    sentiment_score: float
    categories: List[str]
    entities: Dict[str, List[str]]
    summary: str
    source_confidence: float
    model_used: str
    processing_time: float

class AIService:
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Free models that work well for news analysis
        self.models = [
            "google/gemma-2-9b-it:free",
            "meta-llama/llama-3.1-8b-instruct:free", 
            "microsoft/wizardlm-2-8x22b:free",
            "anthropic/claude-3-haiku:free"
        ]
        
        if not self.openrouter_api_key:
            print("⚠️  OPENROUTER_API_KEY not found in environment variables")
            print("AI features will be limited")

    async def analyze_article(self, article: Dict[str, Any]) -> AIAnalysisResult:
        """
        Analyze a news article using multiple AI models in parallel
        """
        if not self.openrouter_api_key:
            return self._fallback_analysis(article)
        
        title = article.get('title', '')
        summary = article.get('summary', article.get('description', ''))
        source = article.get('source', '')
        
        if not title:
            return self._empty_analysis()
        
        # Prepare analysis prompt
        prompt = self._create_analysis_prompt(title, summary, source)
        
        # Run multiple models in parallel
        tasks = []
        for model in self.models[:2]:  # Use first 2 models for speed
            task = self._analyze_with_model(prompt, model)
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results from multiple models
            combined_result = self._combine_results(results, article)
            return combined_result
            
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            return self._fallback_analysis(article)

    def _create_analysis_prompt(self, title: str, summary: str, source: str) -> str:
        """Create a comprehensive prompt for news analysis"""
        return f"""
Analyze this news article and provide a structured JSON response:

Title: {title}
Summary: {summary}
Source: {source}

Please provide the following analysis in JSON format:
{{
    "sentiment": "positive/negative/neutral",
    "sentiment_score": 0.0-1.0,
    "categories": ["category1", "category2", ...],
    "entities": {{
        "people": ["person1", "person2", ...],
        "organizations": ["org1", "org2", ...],
        "countries": ["country1", "country2", ...],
        "topics": ["topic1", "topic2", ...]
    }},
    "summary": "Brief 1-2 sentence summary",
    "source_confidence": 0.0-1.0
}}

Categories to consider: politics, business, finance, technology, health, science, sports, entertainment, world, crime, environment.

Respond only with valid JSON.
"""

    async def _analyze_with_model(self, prompt: str, model: str) -> Dict[str, Any]:
        """Analyze with a specific model"""
        start_time = datetime.now()
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8001",
            "X-Title": "News Platform AI"
        }
        
        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        # Parse JSON response
                        try:
                            analysis = json.loads(content)
                            processing_time = (datetime.now() - start_time).total_seconds()
                            
                            return {
                                "success": True,
                                "model": model,
                                "analysis": analysis,
                                "processing_time": processing_time
                            }
                        except json.JSONDecodeError:
                            print(f"Failed to parse JSON from {model}")
                            return {"success": False, "model": model, "error": "Invalid JSON"}
                    else:
                        print(f"Error from {model}: {response.status}")
                        return {"success": False, "model": model, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            print(f"Exception with {model}: {e}")
            return {"success": False, "model": model, "error": str(e)}

    def _combine_results(self, results: List[Any], article: Dict[str, Any]) -> AIAnalysisResult:
        """Combine results from multiple AI models"""
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        if not successful_results:
            return self._fallback_analysis(article)
        
        # Average sentiment scores
        sentiment_scores = []
        sentiments = []
        categories_sets = []
        entities_lists = []
        summaries = []
        source_confidences = []
        total_processing_time = 0
        
        for result in successful_results:
            analysis = result["analysis"]
            sentiment_scores.append(analysis.get("sentiment_score", 0.5))
            sentiments.append(analysis.get("sentiment", "neutral"))
            categories_sets.append(set(analysis.get("categories", [])))
            
            # Merge entities
            entities = analysis.get("entities", {})
            entities_lists.append(entities)
            
            summaries.append(analysis.get("summary", ""))
            source_confidences.append(analysis.get("source_confidence", 0.5))
            total_processing_time += result.get("processing_time", 0)
        
        # Calculate combined sentiment
        avg_sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
        combined_sentiment = "neutral"
        if avg_sentiment_score > 0.6:
            combined_sentiment = "positive"
        elif avg_sentiment_score < 0.4:
            combined_sentiment = "negative"
        
        # Combine categories (union of all categories)
        all_categories = set()
        for cat_set in categories_sets:
            all_categories.update(cat_set)
        
        # Combine entities
        combined_entities = {
            "people": [],
            "organizations": [],
            "countries": [],
            "topics": []
        }
        
        for entities in entities_lists:
            for key in combined_entities:
                combined_entities[key].extend(entities.get(key, []))
        
        # Remove duplicates
        for key in combined_entities:
            combined_entities[key] = list(set(combined_entities[key]))
        
        # Choose best summary (longest one)
        best_summary = max(summaries, key=len) if summaries else ""
        
        # Average source confidence
        avg_source_confidence = sum(source_confidences) / len(source_confidences)
        
        model_used = ", ".join([r["model"] for r in successful_results])
        
        return AIAnalysisResult(
            sentiment=combined_sentiment,
            sentiment_score=avg_sentiment_score,
            categories=list(all_categories),
            entities=combined_entities,
            summary=best_summary,
            source_confidence=avg_source_confidence,
            model_used=model_used,
            processing_time=total_processing_time
        )

    def _fallback_analysis(self, article: Dict[str, Any]) -> AIAnalysisResult:
        """Fallback analysis when AI is unavailable"""
        title = article.get('title', '').lower()
        summary = article.get('summary', article.get('description', '')).lower()
        
        # Simple keyword-based sentiment analysis
        positive_words = ['good', 'great', 'success', 'growth', 'rise', 'win', 'positive', 'happy']
        negative_words = ['bad', 'terrible', 'fail', 'fall', 'crash', 'loss', 'negative', 'sad']
        
        text = f"{title} {summary}"
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(0.7, 0.5 + (positive_count * 0.1))
        elif negative_count > positive_count:
            sentiment = "negative"
            score = max(0.3, 0.5 - (negative_count * 0.1))
        else:
            sentiment = "neutral"
            score = 0.5
        
        # Simple category detection
        categories = []
        if any(word in text for word in ['business', 'finance', 'economy', 'market', 'stock']):
            categories.append('business')
        if any(word in text for word in ['tech', 'technology', 'software', 'ai', 'computer']):
            categories.append('technology')
        if any(word in text for word in ['health', 'medical', 'hospital', 'disease']):
            categories.append('health')
        
        return AIAnalysisResult(
            sentiment=sentiment,
            sentiment_score=score,
            categories=categories or ['general'],
            entities={"people": [], "organizations": [], "countries": [], "topics": []},
            summary=article.get('summary', article.get('description', ''))[:200] + "...",
            source_confidence=0.5,
            model_used="fallback",
            processing_time=0.1
        )

    def _empty_analysis(self) -> AIAnalysisResult:
        """Empty analysis for articles with no content"""
        return AIAnalysisResult(
            sentiment="neutral",
            sentiment_score=0.5,
            categories=["general"],
            entities={"people": [], "organizations": [], "countries": [], "topics": []},
            summary="No content available for analysis.",
            source_confidence=0.0,
            model_used="empty",
            processing_time=0.01
        )

# Global AI service instance
ai_service = AIService()
