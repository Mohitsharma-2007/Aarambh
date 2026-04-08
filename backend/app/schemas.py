"""
AARAMBH API Schemas - Pydantic models for request/response validation
"""

from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== AUTH ====================

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class AuthResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ==================== MARKET DATA ====================

class StockQuote(BaseModel):
    ticker: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: int
    marketCap: Optional[float] = None
    pe: Optional[float] = None
    eps: Optional[float] = None
    beta: Optional[float] = None
    dividend: Optional[float] = None
    high52: Optional[float] = None
    low52: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None


class CandleData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketIndex(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    changePercent: float


class MarketHeatmapItem(BaseModel):
    ticker: str
    name: str
    price: float
    priceChange: float
    volume: int
    marketCap: float
    sector: Optional[str] = None


# ==================== NEWS ====================

class NewsItem(BaseModel):
    id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    source: str
    publishedAt: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    sentiment: Optional[str] = None


class NewsHeadlinesResponse(BaseModel):
    success: bool
    data: List[NewsItem]
    total: int


# ==================== SIGNALS ====================

class Signal(BaseModel):
    id: str
    ticker: str
    type: str
    direction: str
    confidence: float
    price_target: Optional[float] = None
    timeframe: Optional[str] = None
    created_at: datetime
    status: str = "active"


class SignalsResponse(BaseModel):
    success: bool
    data: List[Signal]
    total: int


# ==================== AI ====================

class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    provider: Optional[str] = "openai"
    model: Optional[str] = None
    tools: Optional[List[str]] = None
    agent_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    conversation_id: Optional[str] = None
    error: Optional[str] = None


# ==================== GRAPH/ONTOLOGY ====================

class CreateGraphRequest(BaseModel):
    name: str
    description: Optional[str] = None


class BuildGraphRequest(BaseModel):
    project_id: str
    graph_name: Optional[str] = None


class GraphData(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


# ==================== SIMULATION ====================

class CreateSimulationRequest(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Simulation(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    parameters: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None


# ==================== REPORT ====================

class GenerateReportRequest(BaseModel):
    simulation_id: str


class Report(BaseModel):
    id: str
    simulation_id: str
    status: str
    created_at: datetime
    content: Optional[str] = None


# ==================== INVESTORS ====================

class FundHolding(BaseModel):
    ticker: str
    name: str
    shares: int
    value: float
    weight: float


class Fund(BaseModel):
    cik: str
    name: str
    holdings_count: int
    total_value: float


class CongressTrade(BaseModel):
    representative: str
    ticker: str
    type: str
    amount: str
    date: str


# ==================== ECONOMY ====================

class TreasuryYield(BaseModel):
    maturity: str
    rate: float
    change: float


class EconomicIndicator(BaseModel):
    name: str
    value: float
    change: Optional[float] = None
    unit: str
    date: str


# ==================== STOCK RESEARCH ====================

class CompanyProfile(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    exchange: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[int] = None
    marketCap: Optional[float] = None
    pe: Optional[float] = None
    eps: Optional[float] = None
    beta: Optional[float] = None
    dividend: Optional[float] = None
    revenue: Optional[float] = None
    netIncome: Optional[float] = None
    price: Optional[float] = None
    change: Optional[float] = None
    changePercent: Optional[float] = None


class StockResearchResponse(BaseModel):
    success: bool
    quote: Optional[StockQuote] = None
    profile: Optional[CompanyProfile] = None
    financials: Optional[Dict[str, Any]] = None
    ownership: Optional[Dict[str, Any]] = None
    ratings: Optional[List[Dict[str, Any]]] = None


# ==================== DATA BRIDGE ====================

class DataStatus(BaseModel):
    last_update: str
    sources: Dict[str, Any]
    status: str


class MarketDashboard(BaseModel):
    indices: List[MarketIndex]
    movers: Optional[Dict[str, List[StockQuote]]] = None
    trending: Optional[List[str]] = None
    last_updated: str
