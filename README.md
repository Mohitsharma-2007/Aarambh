# AARAMBH: AI-Powered Financial Intelligence Terminal

AARAMBH is a state-of-the-art financial intelligence and news orchestration engine, providing real-time insights, swarm-intelligence simulations, and a high-performance terminal experience.

## 🚀 Key Features

- **Swarm Intelligence Engine**: Inspired by MiroFish architecture, simulating complex scenarios across Geopolitics, Economics, Defense, and Technology.
- **Unified Data Ingestion**: Automated pipelines fetching data from 35+ global sources including GDELT, PIB, Reuters, IMF, and the World Bank.
- **Deep Market Analytics**: Real-time stock quotes, heatmaps, OHLCV charts, and comprehensive equity research.
- **News Intelligence**: Aggregated headlines from global sources with AI-driven sentiment analysis and entity extraction.
- **Interactive Dashboard**: Premium glassmorphism UI with responsive charts and real-time activity indicators.
- **AI Query Terminal**: Direct interaction with advanced LLMs for deep-dive research and data synthesis.

## 🛠️ Tech Stack

### Backend (FastAPI)
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (Relational), Neo4j (Knowledge Graph), Redis (Caching/Queues)
- **Messaging**: Kafka (Data Pipeline)
- **AI Integration**: OpenRouter, Anthropic, Groq
- **Scrapers**: Custom-built asynchronous scrapers for global news and economic data.

### Frontend (React & Vite)
- **Framework**: React 18, Vite
- **Styling**: Tailwind CSS, Framer Motion (Animations)
- **Charts**: Recharts, D3.js
- **Icons**: Lucide React
- **Data Management**: React Query, Zustand, localDB (IndexedDB wrapper)
- **Testing**: Vitest, Playwright

## 📂 Project Structure

```text
AARAMBH/
├── backend/            # FastAPI source code, routers, scrapers, and services
├── frontend/           # React frontend source code, components, and styles
├── data/               # Local data storage and databases
├── uploads/            # User-uploaded files for analysis
└── .gitignore          # Repository hygiene and secret protection
```

## 🚥 Getting Started

### Prerequisites
- Node.js (v20+)
- Python (v3.11+)
- PostgreSQL, Neo4j, Redis, and Kafka (for full production setup)

### 1. Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Add your API keys here
python main.py
```

### 2. Setup Frontend
```bash
cd frontend
npm install
cp .env.example .env      # Configure VITE_API_URL pointing to the backend
npm run dev
```

## 📄 Documentation

For more detailed information, please refer to:
- [Backend API Documentation](backend/API_DOCUMENTATION.md)
- [Data Sources & Setup Guide](backend/DATA_SOURCES_README.md)

## 🚢 Deployment

The project is optimized for deployment on **Vercel** (Frontend) and can be hosted on any cloud provider supporting Python/Docker for the backend.

- Ensure all environment variables are properly configured in your deployment settings.
- The `.gitignore` is pre-configured to prevent sensitive keys from being exposed.

---

*AARAMBH Intelligence Terminal v2.0*
*Last Updated: April 2026*
