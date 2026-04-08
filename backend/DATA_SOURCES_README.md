# AARAMBH Data Sources & API Setup

## Overview

This document explains how to set up and use the comprehensive data sources and APIs integrated into AARAMBH, inspired by the MiroFish swarm intelligence architecture.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 Data Sources Architecture

### Free Data Sources (No API Keys Required)

#### Geopolitics (15 sources)
- **GDELT**: Global news events (15min updates)
- **PIB**: India government press releases (15min updates)  
- **MEA**: India foreign policy statements (30min updates)
- **UN News**: United Nations announcements (1h updates)
- **Reuters World**: Global breaking news (15min updates)
- **BBC World**: International news (15min updates)
- **Al Jazeera**: Middle East & South Asia focus (15min updates)
- **ReliefWeb**: Humanitarian crises (6h updates)
- **GDACS**: Global disaster alerts (1h updates)

#### Economics (8 sources)
- **World Bank**: GDP, trade, development indicators (daily updates)
- **IMF**: Economic forecasts and balance of payments (monthly updates)
- **OECD**: Economic statistics for member countries (monthly updates)
- **WTO**: Global trade statistics (quarterly updates)
- **RBI DBIE**: Indian monetary policy (daily updates)
- **MOSPI**: Indian economic indicators (monthly/quarterly updates)
- **SEBI**: Market regulations and circulars (daily updates)

#### Defense & Security (6 sources)
- **ACLED**: Armed conflict events (daily updates)
- **SIPRI**: Military expenditure and arms transfers (annual updates)
- **GTD**: Terrorism incidents database (annual updates)
- **AlienVault OTX**: Cyber threat intelligence (real-time updates)
- **Shodan**: Internet-exposed devices (real-time updates)
- **NVD**: CVE vulnerability database (real-time updates)

#### Technology & Science (6 sources)
- **arXiv**: Research papers across multiple fields (daily updates)
- **GitHub**: Trending repositories and open source activity (daily updates)
- **Hacker News**: Tech community and security disclosures (30min updates)
- **PubMed**: Biomedical research literature (daily updates)
- **Semantic Scholar**: Cross-disciplinary research papers (daily updates)

#### Climate & Environment (6 sources)
- **NASA FIRMS**: Active fire detection (3h updates)
- **USGS**: Global earthquake data (real-time updates)
- **NOAA**: Weather station data and climate records (daily updates)
- **GDACS**: Disaster coordination system (1h updates)
- **CPCB**: India air quality monitoring (hourly updates)
- **IMD**: India weather and monsoon forecasts (3h updates)

## 🔄 Data Ingestion Pipeline

### Kafka Topics Architecture
```
raw.geopolitics     ← GDELT, PIB, MEA, Reuters, ACLED
raw.economics       ← World Bank, IMF, RBI, MOSPI
raw.defense         ← ACLED, SIPRI, GTD, AlienVault
raw.technology      ← arXiv, GitHub, Hacker News, PubMed
raw.climate         ← NASA FIRMS, USGS, NOAA, CPCB
raw.india-govt     ← data.gov.in, SEBI, MCA21, ECI
raw.society         ← WHO, UN Population, ReliefWeb
processed.events    ← Post-NLP normalized events
graph.updates        ← Neo4j write queue
alerts.evaluate     ← Events needing alert rule check
```

### MiroFish Integration

#### Seed Types for Swarm Intelligence
- `breaking_event`: News events, conflicts, disasters
- `policy_draft`: Government statements, policy documents
- `financial_signal`: Economic indicators, market data
- `diplomatic_signal`: Foreign policy, international relations
- `technology_signal`: Research papers, tech developments

#### Swarm Agent Types
- **Diplomatic Agents** (3): Specialize in geopolitics and international relations
- **Economic Agents** (3): Focus on macroeconomics and financial analysis
- **Defense Analysts** (3): Expertise in military strategy and security threats
- **Technology Analysts** (3): Track emerging tech and cybersecurity trends
- **Strategic Analysts** (3): Long-term trend analysis and planning

## 🛠️ API Endpoints

### Data Ingestion
- `GET /api/v1/ingestion/status` - Pipeline status
- `POST /api/v1/ingestion/start` - Start ingestion
- `POST /api/v1/ingestion/stop` - Stop ingestion
- `GET /api/v1/ingestion/connectors` - Connector status
- `POST /api/v1/ingestion/fetch/{connector_id}` - Manual fetch
- `GET /api/v1/ingestion/sources` - Available sources

### Swarm Intelligence
- `POST /api/v1/swarm/simulate` - Run swarm simulation
- `GET /api/v1/swarm/status` - Swarm engine status
- `GET /api/v1/swarm/agents` - Agent list and status
- `GET /api/v1/swarm/predictions/{id}` - Historical predictions

## 🔧 Configuration

### Environment Variables
```bash
# Core Settings
ENV=development
DEBUG=true
SECRET_KEY=your-secret-key

# Database Connections
POSTGRES_URL=postgresql+asyncpg://aarambh:password@localhost:5432/aarambh
NEO4J_URI=bolt://localhost:7687
REDIS_URL=redis://localhost:6379

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
SWARM_ENGINE_ENABLED=true
AGENT_SIMULATION_COUNT=1000

# Free Data Source URLs (no keys required)
GDELT_API_URL=http://data.gdeltproject.org/gdeltv2/lastupdate.txt
PIB_RSS_URL=https://pib.gov.in/RssMain.aspx
MEA_RSS_URL=https://www.mea.gov.in/rss_feed.htm
WORLD_BANK_API=https://api.worldbank.org/v2/
ACLED_API=https://api.acleddata.com/acled/read

# AI Provider Keys (optional)
OPENROUTER_API_KEY=your-openrouter-key
ANTHROPIC_API_KEY=your-anthropic-key
GROQ_API_KEY=your-groq-key
```

## 📈 Monitoring & Testing

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Ingestion status
curl http://localhost:8000/api/v1/ingestion/status

# Swarm status
curl http://localhost:8000/api/v1/swarm/status
```

### Manual Data Fetch
```bash
# Fetch from specific connector
curl -X POST http://localhost:8000/api/v1/ingestion/fetch/pib_press_releases

# Start full ingestion
curl -X POST http://localhost:8000/api/v1/ingestion/start

# Run swarm simulation
curl -X POST http://localhost:8000/api/v1/swarm/simulate \
  -H "Content-Type: application/json" \
  -d '{"seed_data": {"event": "India-China border tension"}, "simulation_steps": 10}'
```

## 🚨 Production Deployment

### Scaling Considerations
1. **Kafka Cluster**: Deploy multiple brokers for high availability
2. **Database Pooling**: Configure connection pools for PostgreSQL and Neo4j
3. **Rate Limiting**: Implement proper rate limiting for external APIs
4. **Monitoring**: Set up comprehensive logging and metrics
5. **Error Handling**: Implement dead letter queues and retry mechanisms

### Security Best Practices
1. **API Keys**: Store in secure environment variables
2. **Network Security**: Use HTTPS for all external communications
3. **Input Validation**: Validate all incoming data and API requests
4. **Access Control**: Implement proper authentication and authorization

## 📚 Next Steps

1. **Add More Connectors**: Implement remaining 200+ data sources
2. **Enhance NLP Pipeline**: Improve entity resolution and relationship extraction
3. **Graph Analytics**: Add advanced graph traversal and pattern detection
4. **Real-time Alerts**: Implement sophisticated alerting system
5. **ML Models**: Train custom models for domain-specific predictions

## 🤝 Support

For issues and questions:
- Check the API documentation at `http://localhost:8000/docs`
- Review connector logs for specific errors
- Monitor Kafka topic lag and consumer health
- Validate Neo4j graph schema and relationships

---

*Last Updated: March 2026*
*AARAMBH Intelligence Terminal v2.0*
