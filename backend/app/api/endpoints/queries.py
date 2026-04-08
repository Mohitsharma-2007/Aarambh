from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.database import get_session, Query as QueryModel, User
from app.api.deps import get_current_user

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    context: dict = {}


class QueryResponse(BaseModel):
    id: str
    query: str
    response: str
    tokens_used: int
    created_at: datetime

    class Config:
        from_attributes = True


class QueryHistoryItem(BaseModel):
    id: str
    query: str
    created_at: datetime


@router.post("/", response_model=QueryResponse)
async def execute_query(
    query_data: QueryRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Execute an AI query"""
    # Check usage limit
    if user.query_usage >= user.query_limit:
        raise HTTPException(
            status_code=429,
            detail="Query limit exceeded. Please upgrade your plan."
        )

    # TODO: Integrate with AI service (OpenAI/Anthropic)
    # For now, return mock response
    mock_response = f"Analysis of '{query_data.query}': Based on available intelligence data, this query relates to geopolitical developments in the Indo-Pacific region. Key entities identified include India, China, and relevant organizations. Sentiment analysis suggests neutral-to-positive outlook."

    # Save query
    query_record = QueryModel(
        user_id=user.id,
        query=query_data.query,
        response=mock_response,
        tokens_used=len(query_data.query.split()) + len(mock_response.split()),
    )

    session.add(query_record)

    # Update usage
    user.query_usage += 1

    await session.commit()
    await session.refresh(query_record)

    return QueryResponse.model_validate(query_record)


@router.get("/history", response_model=List[QueryHistoryItem])
async def get_query_history(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Get user's query history"""
    query = (
        select(QueryModel)
        .where(QueryModel.user_id == user.id)
        .order_by(QueryModel.created_at.desc())
        .limit(limit)
    )

    result = await session.execute(query)
    queries = result.scalars().all()

    return [QueryHistoryItem.model_validate(q) for q in queries]


@router.get("/usage")
async def get_query_usage(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Get user's query usage stats"""
    return {
        "used": user.query_usage,
        "limit": user.query_limit,
        "remaining": user.query_limit - user.query_usage,
    }
