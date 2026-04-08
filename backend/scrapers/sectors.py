"""
scrapers/sectors.py  —  31 Sector Data Aggregator
==================================================
Covers all sectors from the NDAP/India Data Portal image:
Agriculture, Animal Husbandry, Art & Culture, Chemicals, Coal, Commerce,
Communications, Defence, Education, Employment, Energy, Environment,
Finance, Food, Forestry, Governance, Health, Home Affairs, Housing,
Information, International Affairs, Law, Petroleum, Rural Dev, Science,
Social Justice, Socio-Economic, SDGs, Tourism, Transport, Youth/Sports
"""

import asyncio, re
from bs4 import BeautifulSoup
from utils.session import fetch, fetch_json
from utils.cache   import get as c_get, set as c_set

# ── Sector master registry ────────────────────────────────────────────────────
SECTORS = {
    "Agriculture-and-Cooperation": {
        "name":       "Agriculture and Cooperation",
        "ministries": ["Ministry of Agriculture & Farmers' Welfare"],
        "ndap_cat":   "Agriculture",
        "pib_key":    "agriculture",
        "rss":        ["https://pib.gov.in/RssMain.aspx?ModId=6&LangId=1",
                       "https://agricoop.nic.in/sites/default/files/rss.xml"],
        "apis": [
            {"name": "APEDA",       "url": "https://apeda.gov.in/apedawebsite/api/"},
            {"name": "AgriStack",   "url": "https://agristack.gov.in/"},
            {"name": "eNAM",        "url": "https://www.enam.gov.in/web/"},
            {"name": "PM Kisan",    "url": "https://pmkisan.gov.in/"},
        ],
        "indicators": ["crop_production", "msp_prices", "kharif_rabi", "agri_export"],
    },

    "Animal-Husbandary-and-Fishing": {
        "name":       "Animal Husbandary and Fishing",
        "ministries": ["Ministry of Fisheries, Animal Husbandry & Dairying"],
        "ndap_cat":   "Animal Husbandry",
        "pib_key":    "fisheries",
        "indicators": ["milk_production", "fish_production", "poultry"],
    },

    "Art-and-Culture": {
        "name":       "Art and Culture",
        "ministries": ["Ministry of Culture"],
        "pib_key":    "culture",
        "rss":        ["https://indiaculture.gov.in/rss"],
        "indicators": ["heritage_sites", "tourism_receipts"],
    },

    "Chemicals-and-Fertilizers": {
        "name":       "Chemicals and Fertilizers",
        "ministries": ["Ministry of Chemicals and Fertilizers"],
        "pib_key":    "chemicals",
        "apis": [
            {"name": "Fertilizer Dept", "url": "https://fert.nic.in/"},
        ],
        "indicators": ["fertilizer_production", "pharma_export", "chemical_output"],
    },

    "Coal-and-Mine": {
        "name":       "Coal and Mine",
        "ministries": ["Ministry of Coal", "Ministry of Mines"],
        "pib_key":    "coal",
        "apis": [
            {"name": "Coal India",     "url": "https://www.coalindia.in/"},
            {"name": "IBM",            "url": "https://ibm.gov.in/"},
        ],
        "indicators": ["coal_production", "coal_dispatch", "mineral_output"],
    },

    "Commerce-and-Industry": {
        "name":       "Commerce and Industry",
        "ministries": ["Ministry of Commerce and Industry"],
        "pib_key":    "commerce",
        "rss":        ["https://commerce.gov.in/rss"],
        "apis": [
            {"name": "DPIIT",   "url": "https://dpiit.gov.in/"},
            {"name": "Export",  "url": "https://www.dgft.gov.in/"},
            {"name": "FDI",     "url": "https://www.fdi.gov.in/"},
        ],
        "indicators": ["exports", "imports", "trade_balance", "fdi_inflows"],
    },

    "Communications-and-IT": {
        "name":       "Communications and Information Technology",
        "ministries": ["Ministry of Electronics and Information Technology",
                       "Department of Telecommunications"],
        "pib_key":    "electronics",
        "apis": [
            {"name": "TRAI",    "url": "https://www.trai.gov.in/"},
            {"name": "NASSCOM", "url": "https://nasscom.in/"},
        ],
        "indicators": ["internet_subscribers", "mobile_users", "it_exports"],
    },

    "Defence": {
        "name":       "Defence",
        "ministries": ["Ministry of Defence"],
        "pib_key":    "defence",
        "apis": [
            {"name": "DRDO",    "url": "https://drdo.gov.in/"},
            {"name": "Ordnance","url": "https://ofb.gov.in/"},
        ],
        "indicators": ["defence_budget", "defence_exports", "defence_production"],
    },

    "Education-and-Training": {
        "name":       "Education and Training",
        "ministries": ["Ministry of Education"],
        "pib_key":    "education",
        "apis": [
            {"name": "AISHE",   "url": "https://aishe.gov.in/"},
            {"name": "UDISE",   "url": "https://udiseplus.gov.in/"},
        ],
        "indicators": ["literacy_rate", "enrolment", "schools", "colleges"],
    },

    "Employment-and-Labour": {
        "name":       "Employment and Labour",
        "ministries": ["Ministry of Labour & Employment"],
        "pib_key":    "labour",
        "apis": [
            {"name": "PLFS",    "url": "https://mospi.gov.in/plfs"},
            {"name": "EPFO",    "url": "https://www.epfindia.gov.in/"},
            {"name": "ESIC",    "url": "https://www.esic.gov.in/"},
        ],
        "indicators": ["unemployment_rate", "epfo_payroll", "wage_rate", "labour_force"],
    },

    "Energy-and-Power": {
        "name":       "Energy and Power",
        "ministries": ["Ministry of Power", "Ministry of New and Renewable Energy"],
        "pib_key":    "power",
        "apis": [
            {"name": "CEA",     "url": "https://www.cea.nic.in/"},
            {"name": "MNRE",    "url": "https://mnre.gov.in/"},
            {"name": "POSOCO",  "url": "https://posoco.in/"},
        ],
        "indicators": ["power_generation", "renewable_capacity", "t&d_losses", "electrification"],
    },

    "Environment-and-Natural-Resources": {
        "name":       "Environment and Natural Resources",
        "ministries": ["Ministry of Environment, Forest and Climate Change"],
        "pib_key":    "environment",
        "apis": [
            {"name": "CPCB",    "url": "https://cpcb.nic.in/"},
            {"name": "ENVIS",   "url": "http://www.envis.nic.in/"},
        ],
        "indicators": ["air_quality", "forest_cover", "water_quality", "emissions"],
    },

    "Finance-Banking-Insurance": {
        "name":       "Finance, Banking and Insurance",
        "ministries": ["Ministry of Finance", "RBI", "SEBI", "IRDAI"],
        "pib_key":    "finance",
        "rss":        ["https://rbi.org.in/scripts/rss.aspx?Id=2",
                       "https://www.sebi.gov.in/sebirss.aspx?id=press_releases"],
        "apis": [
            {"name": "RBI",     "url": "https://rbi.org.in/"},
            {"name": "SEBI",    "url": "https://sebi.gov.in/"},
            {"name": "IRDAI",   "url": "https://www.irdai.gov.in/"},
            {"name": "PFRDA",   "url": "https://www.pfrda.org.in/"},
        ],
        "indicators": ["repo_rate", "bank_credit", "npa_ratio", "forex_reserves",
                       "nifty", "sensex", "fii_flows"],
    },

    "Food-and-Public-Distribution": {
        "name":       "Food and Public Distribution",
        "ministries": ["Ministry of Consumer Affairs, Food & Public Distribution"],
        "pib_key":    "food",
        "apis": [
            {"name": "FCI",     "url": "https://fci.gov.in/"},
            {"name": "DFPD",    "url": "https://dfpd.gov.in/"},
        ],
        "indicators": ["food_grain_production", "procurement", "pds_coverage"],
    },

    "Forestry-and-Wildlife": {
        "name":       "Forestry and Wildlife",
        "ministries": ["Ministry of Environment, Forest and Climate Change"],
        "pib_key":    "environment",
        "apis": [
            {"name": "FSI",     "url": "https://fsi.nic.in/"},
            {"name": "WII",     "url": "https://wii.gov.in/"},
        ],
        "indicators": ["forest_cover", "tiger_count", "protected_areas"],
    },

    "Governance-and-Administration": {
        "name":       "Governance and Administration",
        "ministries": ["NITI Aayog", "MoSPI"],
        "pib_key":    "pmu",
        "apis": [
            {"name": "NITI Aayog","url": "https://niti.gov.in/"},
            {"name": "NeGP",     "url": "https://negp.gov.in/"},
        ],
        "indicators": ["ease_of_doing_business", "governance_index", "digital_india"],
    },

    "Health-and-Family-Welfare": {
        "name":       "Health and Family Welfare",
        "ministries": ["Ministry of Health & Family Welfare"],
        "pib_key":    "health",
        "rss":        ["https://pib.gov.in/RssMain.aspx?ModId=6&LangId=1"],
        "apis": [
            {"name": "ICMR",    "url": "https://www.icmr.gov.in/"},
            {"name": "NFHS",    "url": "https://mohfw.gov.in/"},
            {"name": "Ayushman","url": "https://pmjay.gov.in/"},
        ],
        "indicators": ["infant_mortality", "maternal_mortality", "immunization",
                       "doctor_ratio", "hospital_beds"],
    },

    "Home-Affairs-National-Security": {
        "name":       "Home Affairs and National Security",
        "ministries": ["Ministry of Home Affairs"],
        "pib_key":    "home",
        "indicators": ["crime_rate", "border_incidents", "disasters"],
    },

    "Housing-and-Urban-Development": {
        "name":       "Housing and Urban Development",
        "ministries": ["Ministry of Housing and Urban Affairs"],
        "pib_key":    "housing",
        "apis": [
            {"name": "Smart Cities", "url": "https://smartcities.gov.in/"},
            {"name": "PMAY",         "url": "https://pmayg.nic.in/"},
        ],
        "indicators": ["housing_units", "urban_population", "smart_cities"],
    },

    "Information-and-Broadcasting": {
        "name":       "Information and Broadcasting",
        "ministries": ["Ministry of Information & Broadcasting"],
        "pib_key":    "information",
        "apis": [
            {"name": "PIB",     "url": "https://pib.gov.in/"},
            {"name": "AIR",     "url": "https://allindiaradio.gov.in/"},
        ],
        "indicators": ["media_outlets", "cable_tv_subscribers"],
    },

    "International-Affairs": {
        "name":       "International Affairs",
        "ministries": ["Ministry of External Affairs"],
        "pib_key":    "external",
        "apis": [
            {"name": "MEA",     "url": "https://mea.gov.in/"},
        ],
        "indicators": ["diplomatic_relations", "indian_diaspora", "bilateral_trade"],
    },

    "Law-and-Justice": {
        "name":       "Law and Justice",
        "ministries": ["Ministry of Law & Justice"],
        "pib_key":    "law",
        "apis": [
            {"name": "eCourts",    "url": "https://ecourts.gov.in/"},
            {"name": "NyayaBandhu","url": "https://doj.gov.in/"},
        ],
        "indicators": ["pending_cases", "case_disposal_rate"],
    },

    "Petroleum-Oil-Natural-Gas": {
        "name":       "Petroleum, Oil and Natural Gas",
        "ministries": ["Ministry of Petroleum and Natural Gas"],
        "pib_key":    "petroleum",
        "apis": [
            {"name": "PPAC",    "url": "https://ppac.gov.in/"},
            {"name": "ONGC",    "url": "https://ongcindia.com/"},
        ],
        "indicators": ["crude_oil_production", "natural_gas", "refinery_output",
                       "petrol_diesel_prices"],
    },

    "Rural-Development-Panchayati-Raj": {
        "name":       "Rural Development and Panchayati Raj",
        "ministries": ["Ministry of Rural Development"],
        "pib_key":    "rural",
        "apis": [
            {"name": "MGNREGA",   "url": "https://nrega.nic.in/"},
            {"name": "PMGSY",     "url": "https://pmgsy.nic.in/"},
            {"name": "PMGKY",     "url": "https://rural.gov.in/"},
        ],
        "indicators": ["mgnrega_employment", "rural_roads", "swachh_bharat", "jjm"],
    },

    "Science-Technology-Research": {
        "name":       "Science, Technology and Research",
        "ministries": ["Ministry of Science & Technology"],
        "pib_key":    "science",
        "apis": [
            {"name": "DST",     "url": "https://dst.gov.in/"},
            {"name": "ISRO",    "url": "https://www.isro.gov.in/"},
            {"name": "CSIR",    "url": "https://www.csir.res.in/"},
        ],
        "indicators": ["r&d_expenditure", "patents", "publications", "startups"],
    },

    "Social-Justice-Empowerment": {
        "name":       "Social Justice and Empowerment",
        "ministries": ["Ministry of Social Justice and Empowerment"],
        "pib_key":    "social_justice",
        "apis": [
            {"name": "NSFDC",   "url": "https://nsfdc.nic.in/"},
        ],
        "indicators": ["sc_st_welfare", "disability_schemes", "obc_welfare"],
    },

    "Socio-Economic-Development": {
        "name":       "Socio-Economic Development",
        "ministries": ["MoSPI", "NITI Aayog"],
        "pib_key":    "niti",
        "apis": [
            {"name": "MoSPI",   "url": "https://mospi.gov.in/"},
            {"name": "NITI",    "url": "https://niti.gov.in/"},
        ],
        "indicators": ["hdri", "gini", "poverty_rate", "per_capita_income"],
    },

    "Sustainable-Development-Goals": {
        "name":       "Sustainable Development Goals",
        "ministries": ["NITI Aayog", "MoEFCC"],
        "pib_key":    "niti",
        "apis": [
            {"name": "SDG India Index",   "url": "https://sdgindiaindex.niti.gov.in/"},
            {"name": "VNR",               "url": "https://sustainabledevelopment.un.org/"},
        ],
        "indicators": ["sdg_index_score", "sdg_goals_progress"],
    },

    "Tourism": {
        "name":       "Tourism",
        "ministries": ["Ministry of Tourism"],
        "pib_key":    "tourism",
        "apis": [
            {"name": "Incredible India", "url": "https://www.incredibleindia.org/"},
            {"name": "Tourism Stats",    "url": "https://tourism.gov.in/"},
        ],
        "indicators": ["foreign_tourist_arrivals", "domestic_tourism", "tourism_gdp"],
    },

    "Transport-and-Infrastructure": {
        "name":       "Transport and Infrastructure",
        "ministries": ["Ministry of Railways", "Ministry of Road Transport",
                       "Ministry of Civil Aviation", "Ministry of Ports"],
        "pib_key":    "railways",
        "apis": [
            {"name": "Indian Railways", "url": "https://indianrailways.gov.in/"},
            {"name": "NHAI",            "url": "https://nhai.gov.in/"},
            {"name": "DGCA",            "url": "https://dgca.gov.in/"},
            {"name": "NMP",             "url": "https://nationalmonetisationpipeline.gov.in/"},
        ],
        "indicators": ["freight_traffic", "passenger_traffic", "highway_km",
                       "airport_passengers", "port_cargo"],
    },

    "Youth-Affairs-Sports": {
        "name":       "Youth Affairs and Sports",
        "ministries": ["Ministry of Youth Affairs & Sports"],
        "pib_key":    "sports",
        "apis": [
            {"name": "SAI",     "url": "https://sportsauthorityofindia.nic.in/"},
            {"name": "Khelo India", "url": "https://kheloindia.gov.in/"},
        ],
        "indicators": ["medals", "athletes_trained", "sports_infra"],
    },
}


def sector_list() -> dict:
    """Return all 31 sectors with metadata."""
    return {
        "total": len(SECTORS),
        "sectors": {
            k: {
                "name":       v["name"],
                "ministries": v.get("ministries", []),
                "indicators": v.get("indicators", []),
                "has_apis":   bool(v.get("apis")),
                "has_rss":    bool(v.get("rss")),
            }
            for k, v in SECTORS.items()
        }
    }


async def get_sector_data(sector_key: str) -> dict:
    """Full sector data — PIB releases + NDAP datasets + APIs."""
    if sector_key not in SECTORS:
        return {"error": f"Unknown sector. Use /api/sectors/list to see valid keys."}

    meta = SECTORS[sector_key]
    ck   = {"sk": sector_key}
    if c := c_get("sector", ck): return c

    tasks = {}

    # PIB releases for this sector
    pib_key = meta.get("pib_key", "")
    if pib_key:
        from scrapers.pib_scraper import get_sector_releases
        tasks["pib"] = get_sector_releases(pib_key, count=10)

    # NDAP datasets
    ndap_cat = meta.get("ndap_cat", meta["name"])
    from scrapers.india_portals import ndap_search_datasets
    tasks["ndap"] = ndap_search_datasets(query=ndap_cat, sector=ndap_cat)

    # Run concurrently
    import asyncio as _aio
    keys  = list(tasks.keys())
    coros = [tasks[k] for k in keys]
    results = await _aio.gather(*[_aio.ensure_future(c) for c in coros], return_exceptions=True)

    data = {"sector": meta["name"], "sector_key": sector_key}
    for k, r in zip(keys, results):
        data[k] = r if not isinstance(r, Exception) else {"error": str(r)}

    # Add static metadata
    data["ministries"]  = meta.get("ministries", [])
    data["apis"]        = meta.get("apis", [])
    data["indicators"]  = meta.get("indicators", [])
    data["rss_feeds"]   = meta.get("rss", [])

    c_set("sector", ck, data, ttl=1800)
    return data


async def get_sector_news(sector_key: str, count: int = 20) -> dict:
    """News + circulars for a sector from PIB + RSS."""
    if sector_key not in SECTORS:
        return {"error": "Unknown sector"}
    meta  = SECTORS[sector_key]
    articles = []

    # PIB
    pib_key = meta.get("pib_key", "")
    if pib_key:
        from scrapers.pib_scraper import get_sector_releases
        pib_data = await get_sector_releases(pib_key, count=count)
        articles.extend(pib_data.get("articles", []))

    # RSS feeds for sector
    for rss_url in meta.get("rss", [])[:2]:
        try:
            from utils.session import fetch as _fetch
            import xml.etree.ElementTree as ET
            r    = await _fetch(rss_url, accept="application/rss+xml,*/*")
            root = ET.fromstring(r.text)
            ch   = root.find("channel")
            items = ch.findall("item") if ch else root.findall(".//item")
            for item in items[:5]:
                def _t(tag):
                    el = item.find(tag)
                    return (el.text or "").strip() if el is not None else ""
                articles.append({
                    "title":     _t("title"),
                    "url":       _t("link"),
                    "published": _t("pubDate"),
                    "source":    rss_url.split("/")[2],
                })
        except Exception:
            pass

    return {"sector": meta["name"], "count": len(articles[:count]),
            "articles": articles[:count]}
