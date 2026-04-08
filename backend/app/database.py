from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from datetime import datetime
import uuid

from app.config import Config

settings = Config()

# Use SQLite by default for development
# Only use Postgres if URL contains actual password (not default placeholder)
if settings.POSTGRES_URL and "password@localhost" not in settings.POSTGRES_URL:
    DATABASE_URL = settings.POSTGRES_URL
else:
    DATABASE_URL = "sqlite+aiosqlite:///./aarambh.db"

# Async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    future=True,
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def init_db():
    """Initialize database tables and seed data if empty"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()


async def seed_data():
    """Seed database with initial intelligence entities, relationships, and events if empty"""
    from loguru import logger

    async with async_session() as session:
        # Check if data already exists
        from sqlalchemy import select, func
        entity_count = await session.scalar(select(func.count(Entity.id)))
        if entity_count and entity_count > 0:
            logger.info(f"Database already has {entity_count} entities, skipping seed")
            return

        logger.info("Seeding database with initial intelligence data...")

        # ── Entities ──
        entities_data = [
            # Countries (GPE)
            {"id": "india", "name": "India", "type": "GPE", "domain": "geopolitics", "importance": 10, "attributes": {"capital": "New Delhi", "region": "South Asia", "population": "1.4B"}},
            {"id": "china", "name": "China", "type": "GPE", "domain": "geopolitics", "importance": 9, "attributes": {"capital": "Beijing", "region": "East Asia", "population": "1.4B"}},
            {"id": "usa", "name": "United States", "type": "GPE", "domain": "geopolitics", "importance": 9, "attributes": {"capital": "Washington DC", "region": "North America", "population": "330M"}},
            {"id": "russia", "name": "Russia", "type": "GPE", "domain": "geopolitics", "importance": 8, "attributes": {"capital": "Moscow", "region": "Eurasia", "population": "144M"}},
            {"id": "pakistan", "name": "Pakistan", "type": "GPE", "domain": "geopolitics", "importance": 7, "attributes": {"capital": "Islamabad", "region": "South Asia", "population": "230M"}},
            {"id": "japan", "name": "Japan", "type": "GPE", "domain": "geopolitics", "importance": 7, "attributes": {"capital": "Tokyo", "region": "East Asia", "population": "125M"}},
            {"id": "australia", "name": "Australia", "type": "GPE", "domain": "geopolitics", "importance": 6, "attributes": {"capital": "Canberra", "region": "Oceania", "population": "26M"}},
            {"id": "iran", "name": "Iran", "type": "GPE", "domain": "geopolitics", "importance": 6, "attributes": {"capital": "Tehran", "region": "Middle East", "population": "88M"}},
            {"id": "france", "name": "France", "type": "GPE", "domain": "geopolitics", "importance": 6, "attributes": {"capital": "Paris", "region": "Europe", "population": "68M"}},
            {"id": "uk", "name": "United Kingdom", "type": "GPE", "domain": "geopolitics", "importance": 6, "attributes": {"capital": "London", "region": "Europe", "population": "67M"}},
            {"id": "germany", "name": "Germany", "type": "GPE", "domain": "economics", "importance": 6, "attributes": {"capital": "Berlin", "region": "Europe", "population": "84M"}},
            {"id": "israel", "name": "Israel", "type": "GPE", "domain": "geopolitics", "importance": 6, "attributes": {"capital": "Jerusalem", "region": "Middle East", "population": "9.5M"}},
            {"id": "taiwan", "name": "Taiwan", "type": "GPE", "domain": "geopolitics", "importance": 7, "attributes": {"capital": "Taipei", "region": "East Asia", "population": "23M"}},
            # Persons
            {"id": "modi", "name": "Narendra Modi", "type": "PERSON", "domain": "geopolitics", "importance": 9, "attributes": {"role": "Prime Minister", "country": "India"}},
            {"id": "xi", "name": "Xi Jinping", "type": "PERSON", "domain": "geopolitics", "importance": 9, "attributes": {"role": "President", "country": "China"}},
            {"id": "trump", "name": "Donald Trump", "type": "PERSON", "domain": "geopolitics", "importance": 8, "attributes": {"role": "President", "country": "USA"}},
            {"id": "putin", "name": "Vladimir Putin", "type": "PERSON", "domain": "geopolitics", "importance": 8, "attributes": {"role": "President", "country": "Russia"}},
            {"id": "jaishankar", "name": "S. Jaishankar", "type": "PERSON", "domain": "geopolitics", "importance": 7, "attributes": {"role": "External Affairs Minister", "country": "India"}},
            {"id": "rajnath", "name": "Rajnath Singh", "type": "PERSON", "domain": "defense", "importance": 7, "attributes": {"role": "Defence Minister", "country": "India"}},
            # Organizations
            {"id": "quad", "name": "QUAD", "type": "ORG", "domain": "geopolitics", "importance": 7, "attributes": {"type": "Alliance", "members": ["India", "USA", "Japan", "Australia"]}},
            {"id": "brics", "name": "BRICS", "type": "ORG", "domain": "geopolitics", "importance": 7, "attributes": {"type": "Alliance", "members": ["Brazil", "Russia", "India", "China", "South Africa"]}},
            {"id": "asean", "name": "ASEAN", "type": "ORG", "domain": "geopolitics", "importance": 5, "attributes": {"type": "Regional Bloc"}},
            {"id": "g20", "name": "G20", "type": "ORG", "domain": "economics", "importance": 7, "attributes": {"type": "Economic Forum"}},
            {"id": "un", "name": "United Nations", "type": "ORG", "domain": "geopolitics", "importance": 6, "attributes": {"type": "International Organization"}},
            {"id": "nato", "name": "NATO", "type": "ORG", "domain": "defense", "importance": 7, "attributes": {"type": "Military Alliance"}},
            {"id": "isro", "name": "ISRO", "type": "ORG", "domain": "technology", "importance": 7, "attributes": {"type": "Space Agency", "country": "India"}},
            {"id": "drdo", "name": "DRDO", "type": "ORG", "domain": "defense", "importance": 7, "attributes": {"type": "Defence Research", "country": "India"}},
            {"id": "hal", "name": "HAL", "type": "ORG", "domain": "defense", "importance": 6, "attributes": {"type": "Defence Manufacturing", "country": "India"}},
            {"id": "rbi", "name": "RBI", "type": "ORG", "domain": "economics", "importance": 8, "attributes": {"type": "Central Bank", "country": "India"}},
            {"id": "sbi", "name": "SBI", "type": "ORG", "domain": "economics", "importance": 6, "attributes": {"type": "Bank", "country": "India"}},
            {"id": "reliance", "name": "Reliance Industries", "type": "ORG", "domain": "economics", "importance": 6, "attributes": {"type": "Conglomerate", "country": "India"}},
            {"id": "tata", "name": "Tata Group", "type": "ORG", "domain": "economics", "importance": 6, "attributes": {"type": "Conglomerate", "country": "India"}},
            {"id": "pla", "name": "PLA", "type": "ORG", "domain": "defense", "importance": 7, "attributes": {"type": "Military", "country": "China"}},
            {"id": "isi", "name": "ISI", "type": "ORG", "domain": "defense", "importance": 6, "attributes": {"type": "Intelligence Agency", "country": "Pakistan"}},
        ]

        entity_objects = []
        for e in entities_data:
            entity_objects.append(Entity(
                id=e["id"], name=e["name"], type=e["type"],
                domain=e["domain"], importance=e["importance"],
                attributes=e.get("attributes", {}),
            ))
        session.add_all(entity_objects)

        # ── Relationships ──
        relationships_data = [
            # Geopolitical alliances & rivalries
            {"source_id": "india", "target_id": "china", "relation_type": "OPPOSES", "weight": 0.9},
            {"source_id": "india", "target_id": "usa", "relation_type": "ALLIED_WITH", "weight": 0.85},
            {"source_id": "india", "target_id": "russia", "relation_type": "COOPERATES_WITH", "weight": 0.8},
            {"source_id": "india", "target_id": "pakistan", "relation_type": "OPPOSES", "weight": 0.95},
            {"source_id": "india", "target_id": "japan", "relation_type": "COOPERATES_WITH", "weight": 0.85},
            {"source_id": "india", "target_id": "australia", "relation_type": "COOPERATES_WITH", "weight": 0.8},
            {"source_id": "india", "target_id": "france", "relation_type": "COOPERATES_WITH", "weight": 0.75},
            {"source_id": "india", "target_id": "israel", "relation_type": "COOPERATES_WITH", "weight": 0.8},
            {"source_id": "china", "target_id": "pakistan", "relation_type": "ALLIED_WITH", "weight": 0.9},
            {"source_id": "china", "target_id": "russia", "relation_type": "COOPERATES_WITH", "weight": 0.75},
            {"source_id": "china", "target_id": "iran", "relation_type": "COOPERATES_WITH", "weight": 0.7},
            {"source_id": "china", "target_id": "taiwan", "relation_type": "OPPOSES", "weight": 0.9},
            {"source_id": "usa", "target_id": "china", "relation_type": "OPPOSES", "weight": 0.85},
            {"source_id": "usa", "target_id": "russia", "relation_type": "OPPOSES", "weight": 0.8},
            {"source_id": "usa", "target_id": "japan", "relation_type": "ALLIED_WITH", "weight": 0.95},
            {"source_id": "usa", "target_id": "australia", "relation_type": "ALLIED_WITH", "weight": 0.9},
            {"source_id": "usa", "target_id": "uk", "relation_type": "ALLIED_WITH", "weight": 0.95},
            {"source_id": "usa", "target_id": "israel", "relation_type": "ALLIED_WITH", "weight": 0.9},
            {"source_id": "usa", "target_id": "taiwan", "relation_type": "COOPERATES_WITH", "weight": 0.85},
            {"source_id": "russia", "target_id": "iran", "relation_type": "COOPERATES_WITH", "weight": 0.7},
            # Leaders
            {"source_id": "modi", "target_id": "india", "relation_type": "LEADS", "weight": 1.0},
            {"source_id": "xi", "target_id": "china", "relation_type": "LEADS", "weight": 1.0},
            {"source_id": "trump", "target_id": "usa", "relation_type": "LEADS", "weight": 1.0},
            {"source_id": "putin", "target_id": "russia", "relation_type": "LEADS", "weight": 1.0},
            {"source_id": "jaishankar", "target_id": "india", "relation_type": "SERVES", "weight": 0.9},
            {"source_id": "rajnath", "target_id": "india", "relation_type": "SERVES", "weight": 0.9},
            # Memberships
            {"source_id": "india", "target_id": "quad", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "usa", "target_id": "quad", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "japan", "target_id": "quad", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "australia", "target_id": "quad", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "india", "target_id": "brics", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "china", "target_id": "brics", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "russia", "target_id": "brics", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "india", "target_id": "g20", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "usa", "target_id": "g20", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "china", "target_id": "g20", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "india", "target_id": "un", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "usa", "target_id": "nato", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "uk", "target_id": "nato", "relation_type": "MEMBER_OF", "weight": 1.0},
            {"source_id": "france", "target_id": "nato", "relation_type": "MEMBER_OF", "weight": 1.0},
            # Ownership/Control
            {"source_id": "india", "target_id": "isro", "relation_type": "OWNS", "weight": 1.0},
            {"source_id": "india", "target_id": "drdo", "relation_type": "OWNS", "weight": 1.0},
            {"source_id": "india", "target_id": "hal", "relation_type": "OWNS", "weight": 1.0},
            {"source_id": "india", "target_id": "rbi", "relation_type": "OWNS", "weight": 1.0},
            {"source_id": "india", "target_id": "sbi", "relation_type": "OWNS", "weight": 0.9},
            {"source_id": "reliance", "target_id": "india", "relation_type": "BASED_IN", "weight": 1.0},
            {"source_id": "tata", "target_id": "india", "relation_type": "BASED_IN", "weight": 1.0},
            {"source_id": "china", "target_id": "pla", "relation_type": "OWNS", "weight": 1.0},
            {"source_id": "pakistan", "target_id": "isi", "relation_type": "OWNS", "weight": 1.0},
            # Tech/Defense cooperation
            {"source_id": "isro", "target_id": "usa", "relation_type": "COOPERATES_WITH", "weight": 0.7},
            {"source_id": "drdo", "target_id": "russia", "relation_type": "COOPERATES_WITH", "weight": 0.75},
            {"source_id": "drdo", "target_id": "israel", "relation_type": "COOPERATES_WITH", "weight": 0.8},
        ]

        rel_objects = []
        for r in relationships_data:
            rel_objects.append(Relationship(
                source_id=r["source_id"], target_id=r["target_id"],
                relation_type=r["relation_type"], weight=r["weight"],
            ))
        session.add_all(rel_objects)

        # ── Sample Events ──
        from datetime import timedelta
        import random
        now = datetime.utcnow()

        events_data = [
            {"title": "India-China LAC tensions escalate near Tawang sector", "summary": "Indian and Chinese troops face off at the Line of Actual Control near Tawang. Both sides have increased patrol activity.", "domain": "defense", "source": "PIB", "importance": 9, "sentiment": -0.7, "entities": ["India", "China", "PLA"]},
            {"title": "QUAD summit announces joint maritime surveillance initiative", "summary": "Leaders of India, US, Japan and Australia agree to enhanced maritime domain awareness in the Indo-Pacific.", "domain": "geopolitics", "source": "MEA", "importance": 8, "sentiment": 0.6, "entities": ["QUAD", "India", "USA", "Japan"]},
            {"title": "RBI holds repo rate steady at 6.5% amid inflation concerns", "summary": "The Reserve Bank of India maintains benchmark lending rate, citing persistent food inflation.", "domain": "economics", "source": "RBI", "importance": 7, "sentiment": 0.0, "entities": ["RBI", "India"]},
            {"title": "ISRO successfully launches GSLV-F15 with navigation satellite", "summary": "Indian Space Research Organisation achieves another milestone with the successful deployment of NVS-02.", "domain": "technology", "source": "ISRO", "importance": 8, "sentiment": 0.9, "entities": ["ISRO", "India"]},
            {"title": "Pakistan-China CPEC Phase 2 expansion announced", "summary": "Pakistan and China sign agreements for new economic corridor projects worth $15 billion.", "domain": "economics", "source": "Reuters", "importance": 7, "sentiment": -0.3, "entities": ["Pakistan", "China"]},
            {"title": "India signs defense deal with France for Rafale Marine jets", "summary": "India finalizes procurement of 26 Rafale-M fighters for INS Vikrant aircraft carrier.", "domain": "defense", "source": "PIB", "importance": 8, "sentiment": 0.5, "entities": ["India", "France", "HAL"]},
            {"title": "DRDO successfully tests hypersonic cruise missile", "summary": "Defence Research and Development Organisation conducts successful flight test of long-range hypersonic missile.", "domain": "defense", "source": "DRDO", "importance": 9, "sentiment": 0.8, "entities": ["DRDO", "India"]},
            {"title": "Russia-Ukraine conflict enters third year with no ceasefire in sight", "summary": "Diplomatic efforts stall as fighting intensifies in eastern Ukraine. NATO increases support.", "domain": "geopolitics", "source": "BBC", "importance": 8, "sentiment": -0.8, "entities": ["Russia", "NATO"]},
            {"title": "India GDP growth at 7.2% in Q3, fastest among major economies", "summary": "India maintains robust economic growth driven by services sector and domestic consumption.", "domain": "economics", "source": "Economic Times", "importance": 8, "sentiment": 0.7, "entities": ["India", "RBI"]},
            {"title": "China increases military activity around Taiwan Strait", "summary": "PLA conducts large-scale naval exercises near Taiwan, raising regional tensions.", "domain": "defense", "source": "Reuters", "importance": 9, "sentiment": -0.8, "entities": ["China", "Taiwan", "PLA"]},
            {"title": "BRICS expansion brings new members into fold", "summary": "BRICS alliance formally inducts new members, expanding its economic and geopolitical influence.", "domain": "geopolitics", "source": "UN News", "importance": 7, "sentiment": 0.3, "entities": ["BRICS", "India", "China", "Russia"]},
            {"title": "India-Japan semiconductor partnership deepens", "summary": "India and Japan announce joint venture for semiconductor fabrication plant in Gujarat.", "domain": "technology", "source": "PIB", "importance": 8, "sentiment": 0.7, "entities": ["India", "Japan"]},
            {"title": "Cyclone warning issued for Bay of Bengal coast", "summary": "IMD tracks severe cyclonic storm expected to make landfall in Odisha within 48 hours.", "domain": "climate", "source": "USGS", "importance": 7, "sentiment": -0.5, "entities": ["India"]},
            {"title": "India-Australia critical minerals agreement signed", "summary": "Both nations commit to supply chain resilience for lithium, cobalt and rare earth minerals.", "domain": "economics", "source": "MEA", "importance": 7, "sentiment": 0.6, "entities": ["India", "Australia"]},
            {"title": "Tata Group unveils AI chip design for defense applications", "summary": "Tata Electronics announces indigenous AI processor for military and surveillance systems.", "domain": "technology", "source": "The Hindu", "importance": 7, "sentiment": 0.6, "entities": ["Tata Group", "India"]},
            {"title": "Pakistan border tensions flare in Rajasthan sector", "summary": "BSF reports increased cross-border firing incidents along the international border.", "domain": "defense", "source": "PIB", "importance": 8, "sentiment": -0.7, "entities": ["India", "Pakistan"]},
            {"title": "India becomes world's third-largest solar power producer", "summary": "Installed solar capacity crosses 100 GW milestone, boosting clean energy transition.", "domain": "climate", "source": "Economic Times", "importance": 7, "sentiment": 0.8, "entities": ["India"]},
            {"title": "Reliance Jio launches satellite internet service", "summary": "Jio SpaceFiber begins commercial operations, competing with Starlink in Indian market.", "domain": "technology", "source": "Economic Times", "importance": 7, "sentiment": 0.5, "entities": ["Reliance Industries", "India"]},
            {"title": "India-USA 2+2 dialogue focuses on Indo-Pacific security", "summary": "Defense and foreign ministers meet to discuss strategic partnership and China containment.", "domain": "geopolitics", "source": "MEA", "importance": 8, "sentiment": 0.5, "entities": ["India", "USA", "S. Jaishankar"]},
            {"title": "Global ransomware attack targets Indian banking infrastructure", "summary": "Multiple Indian banks face coordinated cyber attack. CERT-In issues emergency advisory.", "domain": "technology", "source": "The Hindu", "importance": 9, "sentiment": -0.9, "entities": ["India", "SBI"]},
            {"title": "India ratifies deep-sea mining accord at International Seabed Authority", "summary": "India secures mining rights in Central Indian Ocean Basin for polymetallic nodules.", "domain": "economics", "source": "UN News", "importance": 6, "sentiment": 0.4, "entities": ["India", "United Nations"]},
            {"title": "HAL delivers first Tejas MK-1A to Indian Air Force", "summary": "Light Combat Aircraft production ramps up with 83 jets on order for IAF.", "domain": "defense", "source": "PIB", "importance": 8, "sentiment": 0.8, "entities": ["HAL", "India", "DRDO"]},
            {"title": "Iran nuclear talks collapse as IAEA finds enrichment violations", "summary": "Diplomatic efforts face setback as Iran accelerates uranium enrichment beyond agreed limits.", "domain": "geopolitics", "source": "BBC", "importance": 8, "sentiment": -0.6, "entities": ["Iran", "United Nations"]},
            {"title": "India-Israel joint counter-terrorism exercise begins", "summary": "Special forces from both nations conduct joint training focusing on urban warfare scenarios.", "domain": "defense", "source": "PIB", "importance": 7, "sentiment": 0.4, "entities": ["India", "Israel"]},
            {"title": "SBI reports record quarterly profit on loan growth", "summary": "State Bank of India posts highest-ever net profit driven by strong credit demand.", "domain": "economics", "source": "Economic Times", "importance": 6, "sentiment": 0.6, "entities": ["SBI", "India"]},
            {"title": "Major earthquake hits Hindu Kush region, tremors felt in Delhi", "summary": "6.2 magnitude earthquake strikes Afghanistan-Pakistan border region. No casualties in India.", "domain": "climate", "source": "USGS", "importance": 7, "sentiment": -0.4, "entities": ["India", "Pakistan"]},
            {"title": "India-UK Free Trade Agreement negotiations conclude", "summary": "After 14 rounds of talks, India and UK reach consensus on services and goods trade deal.", "domain": "economics", "source": "MEA", "importance": 7, "sentiment": 0.6, "entities": ["India", "United Kingdom"]},
            {"title": "China deploys new aircraft carrier in South China Sea", "summary": "PLA Navy's third carrier Fujian begins operational patrols, shifting regional naval balance.", "domain": "defense", "source": "Reuters", "importance": 9, "sentiment": -0.5, "entities": ["China", "PLA"]},
            {"title": "ASEAN-India maritime cooperation agreement signed", "summary": "India and ASEAN nations agree to joint patrols and information sharing in Malacca Strait.", "domain": "geopolitics", "source": "MEA", "importance": 7, "sentiment": 0.5, "entities": ["India", "ASEAN"]},
            {"title": "Hacker group targets Indian critical infrastructure", "summary": "APT group linked to nation-state actors attempts intrusion into Indian power grid systems.", "domain": "technology", "source": "NVD", "importance": 9, "sentiment": -0.9, "entities": ["India"]},
        ]

        event_objects = []
        for i, ev in enumerate(events_data):
            event_objects.append(Event(
                title=ev["title"],
                summary=ev["summary"],
                domain=ev["domain"],
                source=ev["source"],
                source_url=None,
                published_at=now - timedelta(hours=random.randint(1, 72)),
                importance=ev["importance"],
                sentiment=ev["sentiment"],
                entities=ev.get("entities", []),
                is_new=i < 15,
            ))
        session.add_all(event_objects)

        # ── Sample Signals ──
        signals_data = [
            {"name": "LAC Buildup Detection", "type": "pattern", "severity": "critical", "status": "active", "config": {"keywords": ["LAC", "Tawang", "Galwan", "buildup"], "threshold": 3}},
            {"name": "China Naval Movement", "type": "entity", "severity": "high", "status": "active", "config": {"entities": ["PLA", "China"], "pattern": "naval|carrier|south china sea"}},
            {"name": "Pakistan Border Activity", "type": "pattern", "severity": "high", "status": "active", "config": {"keywords": ["ceasefire violation", "cross-border", "LoC", "IB firing"], "threshold": 2}},
            {"name": "Cyber Threat Alert", "type": "keyword", "severity": "high", "status": "active", "config": {"keywords": ["ransomware", "APT", "cyber attack", "CERT-In"], "threshold": 1}},
            {"name": "Economic Shock Monitor", "type": "anomaly", "severity": "medium", "status": "active", "config": {"metrics": ["GDP", "inflation", "forex"], "deviation_threshold": 2.0}},
        ]

        from app.database import Signal as SignalModel
        for s in signals_data:
            session.add(SignalModel(
                name=s["name"], type=s["type"], severity=s["severity"],
                status=s["status"], config=s["config"],
            ))

        await session.commit()
        logger.info(f"Seeded {len(entities_data)} entities, {len(relationships_data)} relationships, {len(events_data)} events, {len(signals_data)} signals")


async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session() as session:
        yield session


# Models
class Entity(Base):
    """Entity model for tracked entities"""
    __tablename__ = "entities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)  # GPE, ORG, PERSON, etc.
    domain = Column(String(50), nullable=False, index=True)
    attributes = Column(JSON, default=dict)
    importance = Column(Integer, default=5)
    summary = Column(Text, nullable=True)  # AI-generated summary of the entity
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Event(Base):
    """Event model for intelligence events"""
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    domain = Column(String(50), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    source_url = Column(String(1000))
    published_at = Column(DateTime, nullable=False, index=True)
    importance = Column(Integer, default=5)
    sentiment = Column(Float, default=0.0)
    entities = Column(JSON, default=list)
    is_new = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Relationship(Base):
    """Relationship model for entity connections"""
    __tablename__ = "relationships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    target_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    relation_type = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)
    attributes = Column(JSON, default=dict)
    fact = Column(Text, nullable=True)  # Brief evidence text
    metadata_json = Column(JSON, default=dict)  # For episodes, full_evidence, temporal info
    valid_at = Column(DateTime, nullable=True)  # When relationship becomes valid
    invalid_at = Column(DateTime, nullable=True)  # When relationship becomes invalid
    created_at = Column(DateTime, default=datetime.utcnow)


class Signal(Base):
    """Signal model for alerts"""
    __tablename__ = "signals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # keyword, entity, pattern, anomaly
    status = Column(String(20), default="active")  # active, triggered, paused
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    config = Column(JSON, default=dict)
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255))
    tier = Column(String(50), default="free")  # free, basic, professional, enterprise
    query_usage = Column(Integer, default=0)
    query_limit = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Query(Base):
    """Query model for AI queries"""
    __tablename__ = "queries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ResearchRecord(Base):
    """Research model for deep ontology research history"""
    __tablename__ = "research_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(String(500), nullable=False, index=True)
    report = Column(Text)
    entities = Column(JSON, default=list)
    research_data = Column(JSON, default=list)  # Raw results from DDGS/Models
    simulation_results = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
