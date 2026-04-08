"""
Neo4j Graph Database Service for AARAMBH
=========================================
Manages entity relationships, stock connections, and knowledge graph.
"""

from neo4j import GraphDatabase, Driver, Session
from typing import Optional, List, Dict, Any, Tuple
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
NEO4J_ENABLED = os.environ.get("NEO4J_ENABLED", "true").lower() == "true"


class Neo4jGraph:
    """Neo4j graph database manager"""
    
    _driver: Optional[Driver] = None
    _connected: bool = False
    
    @classmethod
    def get_driver(cls) -> Optional[Driver]:
        """Get Neo4j driver with connection check"""
        if not NEO4J_ENABLED:
            return None
            
        if cls._driver is None:
            try:
                cls._driver = GraphDatabase.driver(
                    NEO4J_URI,
                    auth=(NEO4J_USER, NEO4J_PASSWORD)
                )
                cls._driver.verify_connectivity()
                cls._connected = True
                logger.info("Neo4j connected successfully")
            except Exception as e:
                logger.error(f"Neo4j connection failed: {e}")
                cls._connected = False
                return None
        return cls._driver
    
    @classmethod
    def is_connected(cls) -> bool:
        """Check if Neo4j is connected"""
        return cls._connected and cls.get_driver() is not None
    
    @classmethod
    def close(cls):
        """Close Neo4j driver"""
        if cls._driver:
            cls._driver.close()
            cls._driver = None
            cls._connected = False
    
    @classmethod
    def run_query(cls, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Run a Cypher query"""
        driver = cls.get_driver()
        if not driver:
            return []
        
        try:
            with driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            return []
    
    @classmethod
    def create_entity(cls, entity_type: str, entity_id: str, properties: Dict[str, Any]) -> bool:
        """Create or update an entity node"""
        driver = cls.get_driver()
        if not driver:
            return False
        
        query = f"""
        MERGE (e:{entity_type} {{id: $entity_id}})
        SET e += $properties, e.updated_at = datetime()
        RETURN e
        """
        
        try:
            with driver.session() as session:
                session.run(query, {
                    'entity_id': entity_id,
                    'properties': properties
                })
            return True
        except Exception as e:
            logger.error(f"Failed to create entity: {e}")
            return False
    
    @classmethod
    def create_relationship(cls, 
                          from_type: str, from_id: str,
                          to_type: str, to_id: str,
                          rel_type: str, properties: Dict[str, Any] = None) -> bool:
        """Create a relationship between two entities"""
        driver = cls.get_driver()
        if not driver:
            return False
        
        query = f"""
        MATCH (a:{from_type} {{id: $from_id}})
        MATCH (b:{to_type} {{id: $to_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $properties, r.updated_at = datetime()
        RETURN r
        """
        
        try:
            with driver.session() as session:
                session.run(query, {
                    'from_id': from_id,
                    'to_id': to_id,
                    'properties': properties or {}
                })
            return True
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            return False
    
    @classmethod
    def get_entity_relationships(cls, entity_type: str, entity_id: str, 
                                  direction: str = 'both') -> List[Dict[str, Any]]:
        """Get all relationships for an entity"""
        driver = cls.get_driver()
        if not driver:
            return []
        
        if direction == 'outgoing':
            query = f"""
            MATCH (e:{entity_type} {{id: $entity_id}})-[r]->(related)
            RETURN type(r) as relationship, related.id as related_id, 
                   labels(related) as related_types, r as properties
            """
        elif direction == 'incoming':
            query = f"""
            MATCH (e:{entity_type} {{id: $entity_id}})<-[r]-(related)
            RETURN type(r) as relationship, related.id as related_id, 
                   labels(related) as related_types, r as properties
            """
        else:
            query = f"""
            MATCH (e:{entity_type} {{id: $entity_id}})-[r]-(related)
            RETURN type(r) as relationship, related.id as related_id, 
                   labels(related) as related_types, r as properties
            """
        
        try:
            with driver.session() as session:
                result = session.run(query, {'entity_id': entity_id})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Failed to get relationships: {e}")
            return []
    
    @classmethod
    def find_shortest_path(cls, 
                          from_type: str, from_id: str,
                          to_type: str, to_id: str,
                          max_depth: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Find shortest path between two entities"""
        driver = cls.get_driver()
        if not driver:
            return None
        
        query = f"""
        MATCH path = shortestPath(
            (a:{from_type} {{id: $from_id}})-[*1..{max_depth}]-(b:{to_type} {{id: $to_id}})
        )
        RETURN [node in nodes(path) | {{id: node.id, type: labels(node), properties: properties(node)}}] as nodes,
               [rel in relationships(path) | {{type: type(rel), properties: properties(rel)}}] as relationships
        """
        
        try:
            with driver.session() as session:
                result = session.run(query, {
                    'from_id': from_id,
                    'to_id': to_id
                })
                record = result.single()
                if record:
                    return {
                        'nodes': record['nodes'],
                        'relationships': record['relationships']
                    }
        except Exception as e:
            logger.error(f"Failed to find path: {e}")
        return None
    
    @classmethod
    def create_stock_entity(cls, ticker: str, name: str, sector: str = None, 
                            market_cap: float = None, **kwargs) -> bool:
        """Create a stock entity"""
        properties = {
            'name': name,
            'ticker': ticker.upper(),
            'sector': sector or 'Unknown',
            'market_cap': market_cap or 0,
            'created_at': datetime.utcnow().isoformat(),
            **kwargs
        }
        return cls.create_entity('Stock', ticker.upper(), properties)
    
    @classmethod
    def create_company_entity(cls, name: str, company_id: str, 
                             industry: str = None, country: str = None, **kwargs) -> bool:
        """Create a company entity"""
        properties = {
            'name': name,
            'industry': industry or 'Unknown',
            'country': country or 'Unknown',
            'created_at': datetime.utcnow().isoformat(),
            **kwargs
        }
        return cls.create_entity('Company', company_id, properties)
    
    @classmethod
    def create_person_entity(cls, name: str, person_id: str, 
                            role: str = None, **kwargs) -> bool:
        """Create a person entity"""
        properties = {
            'name': name,
            'role': role or 'Unknown',
            'created_at': datetime.utcnow().isoformat(),
            **kwargs
        }
        return cls.create_entity('Person', person_id, properties)
    
    @classmethod
    def create_news_entity(cls, title: str, news_id: str, 
                          source: str = None, published_at: str = None, **kwargs) -> bool:
        """Create a news article entity"""
        properties = {
            'title': title,
            'source': source or 'Unknown',
            'published_at': published_at or datetime.utcnow().isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            **kwargs
        }
        return cls.create_entity('News', news_id, properties)
    
    @classmethod
    def link_stock_to_sector(cls, ticker: str, sector: str) -> bool:
        """Link a stock to its sector"""
        # Create sector if not exists
        cls.create_entity('Sector', sector, {'name': sector})
        return cls.create_relationship('Stock', ticker.upper(), 'Sector', sector, 'BELONGS_TO')
    
    @classmethod
    def link_stock_to_company(cls, ticker: str, company_id: str) -> bool:
        """Link a stock to its company"""
        return cls.create_relationship('Stock', ticker.upper(), 'Company', company_id, 'ISSUED_BY')
    
    @classmethod
    def link_news_to_stock(cls, news_id: str, ticker: str, sentiment: str = None) -> bool:
        """Link news to a stock with sentiment"""
        props = {'sentiment': sentiment} if sentiment else {}
        return cls.create_relationship('News', news_id, 'Stock', ticker.upper(), 'MENTIONS', props)
    
    @classmethod
    def link_person_to_company(cls, person_id: str, company_id: str, role: str = None) -> bool:
        """Link person to company (e.g., CEO, Director)"""
        props = {'role': role} if role else {}
        return cls.create_relationship('Person', person_id, 'Company', company_id, 'WORKS_AT', props)
    
    @classmethod
    def link_stocks_correlated(cls, ticker1: str, ticker2: str, 
                               correlation: float = None) -> bool:
        """Link two correlated stocks"""
        props = {'correlation': correlation} if correlation else {}
        return cls.create_relationship('Stock', ticker1.upper(), 'Stock', ticker2.upper(), 'CORRELATED_WITH', props)
    
    @classmethod
    def get_stock_network(cls, ticker: str, depth: int = 2) -> Dict[str, Any]:
        """Get network around a stock"""
        driver = cls.get_driver()
        if not driver:
            return {'nodes': [], 'relationships': []}
        
        query = f"""
        MATCH path = (s:Stock {{id: $ticker}})-[*1..{depth}]-(related)
        RETURN DISTINCT [node in nodes(path) | {{
            id: node.id, 
            type: labels(node), 
            properties: properties(node)
        }}] as nodes,
        [rel in relationships(path) | {{
            type: type(rel), 
            start: startNode(rel).id,
            end: endNode(rel).id,
            properties: properties(rel)
        }}] as relationships
        LIMIT 100
        """
        
        try:
            with driver.session() as session:
                result = session.run(query, {'ticker': ticker.upper()})
                records = [record.data() for record in result]
                
                # Deduplicate nodes and relationships
                all_nodes = []
                all_rels = []
                node_ids = set()
                rel_ids = set()
                
                for record in records:
                    for node in record.get('nodes', []):
                        if node['id'] not in node_ids:
                            all_nodes.append(node)
                            node_ids.add(node['id'])
                    
                    for rel in record.get('relationships', []):
                        rel_key = f"{rel['start']}-{rel['type']}-{rel['end']}"
                        if rel_key not in rel_ids:
                            all_rels.append(rel)
                            rel_ids.add(rel_key)
                
                return {
                    'nodes': all_nodes,
                    'relationships': all_rels,
                    'center': ticker.upper()
                }
        except Exception as e:
            logger.error(f"Failed to get stock network: {e}")
            return {'nodes': [], 'relationships': []}
    
    @classmethod
    def get_graph_stats(cls) -> Dict[str, Any]:
        """Get graph database statistics"""
        driver = cls.get_driver()
        if not driver:
            return {
                'connected': False,
                'enabled': NEO4J_ENABLED,
                'node_count': 0,
                'relationship_count': 0
            }
        
        try:
            with driver.session() as session:
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()['count']
                
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_result.single()['count']
                
                label_result = session.run("""
                    CALL db.labels() YIELD label
                    RETURN collect(label) as labels
                """)
                labels = label_result.single()['labels']
                
                return {
                    'connected': True,
                    'enabled': NEO4J_ENABLED,
                    'node_count': node_count,
                    'relationship_count': rel_count,
                    'labels': labels
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                'connected': False,
                'error': str(e),
                'node_count': 0,
                'relationship_count': 0
            }
    
    @classmethod
    def search_entities(cls, query: str, entity_type: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search entities by name or ID"""
        driver = cls.get_driver()
        if not driver:
            return []
        
        if entity_type:
            cypher = f"""
            MATCH (n:{entity_type})
            WHERE n.name CONTAINS $query OR n.id CONTAINS $query
            RETURN n.id as id, n.name as name, labels(n) as types, properties(n) as properties
            LIMIT $limit
            """
        else:
            cypher = """
            MATCH (n)
            WHERE n.name CONTAINS $query OR n.id CONTAINS $query
            RETURN n.id as id, n.name as name, labels(n) as types, properties(n) as properties
            LIMIT $limit
            """
        
        try:
            with driver.session() as session:
                result = session.run(cypher, {
                    'query': query,
                    'limit': limit
                })
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


# Convenience functions
def create_stock(ticker: str, name: str, **kwargs) -> bool:
    """Create stock entity"""
    return Neo4jGraph.create_stock_entity(ticker, name, **kwargs)

def create_company(name: str, company_id: str, **kwargs) -> bool:
    """Create company entity"""
    return Neo4jGraph.create_company_entity(name, company_id, **kwargs)

def create_person(name: str, person_id: str, **kwargs) -> bool:
    """Create person entity"""
    return Neo4jGraph.create_person_entity(name, person_id, **kwargs)

def link_stock_sector(ticker: str, sector: str) -> bool:
    """Link stock to sector"""
    return Neo4jGraph.link_stock_to_sector(ticker, sector)

def link_stock_company(ticker: str, company_id: str) -> bool:
    """Link stock to company"""
    return Neo4jGraph.link_stock_to_company(ticker, company_id)

def link_news_stock(news_id: str, ticker: str, sentiment: str = None) -> bool:
    """Link news to stock"""
    return Neo4jGraph.link_news_to_stock(news_id, ticker, sentiment)

def get_stock_relationships(ticker: str) -> List[Dict[str, Any]]:
    """Get stock relationships"""
    return Neo4jGraph.get_entity_relationships('Stock', ticker.upper())

def get_stock_network(ticker: str, depth: int = 2) -> Dict[str, Any]:
    """Get stock network"""
    return Neo4jGraph.get_stock_network(ticker, depth)

def graph_stats() -> Dict[str, Any]:
    """Get graph stats"""
    return Neo4jGraph.get_graph_stats()


# Export
__all__ = [
    'Neo4jGraph', 'create_stock', 'create_company', 'create_person',
    'link_stock_sector', 'link_stock_company', 'link_news_stock',
    'get_stock_relationships', 'get_stock_network', 'graph_stats'
]
