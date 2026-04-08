"""MiroFish-style Swarm Intelligence Engine"""
import asyncio
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from app.config import settings
from app.services.graph_service import graph_service
from app.services.ai_service import ai_service


class SwarmAgent:
    """Individual AI agent in the swarm"""
    
    def __init__(self, agent_id: str, role: str, expertise: str):
        self.id = agent_id
        self.role = role  # diplomat, economist, analyst, strategist
        self.expertise = expertise  # geopolitics, economics, defense, technology
        self.memory = []
        self.behavior = {
            'risk_tolerance': 0.5,
            'information_weight': 0.8,
            'collaboration_factor': 0.7,
            'prediction_confidence': 0.6
        }
        
    def update_memory(self, information: Dict[str, Any]):
        """Update agent memory with new information"""
        self.memory.append({
            'timestamp': datetime.now().isoformat(),
            'information': information,
            'processed': False
        })
        
        # Keep only last 50 memories
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]
    
    def get_context(self) -> str:
        """Get agent context for decision making"""
        recent_memories = self.memory[-10:]  # Last 10 memories
        context = f"Agent {self.id} ({self.role}, {self.expertise})\n"
        context += f"Behavior: {self.behavior}\n"
        context += "Recent memories:\n"
        
        for memory in recent_memories:
            context += f"- {memory['timestamp']}: {memory['information']}\n"
            
        return context


class SwarmIntelligenceEngine:
    """MiroFish-style swarm intelligence engine"""
    
    def __init__(self):
        self.agents: List[SwarmAgent] = []
        self.simulation_running = False
        self.prediction_history = []
        
        if settings.SWARM_ENGINE_ENABLED:
            self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize the swarm with different agent types"""
        agent_configs = [
            # Diplomatic agents
            ("diplomat_001", "diplomat", "geopolitics"),
            ("diplomat_002", "diplomat", "international_relations"),
            ("diplomat_003", "diplomat", "conflict_resolution"),
            
            # Economic agents
            ("economist_001", "economist", "macroeconomics"),
            ("economist_002", "economist", "financial_markets"),
            ("economist_003", "economist", "trade_policy"),
            
            # Defense analysts
            ("defense_analyst_001", "defense_analyst", "military_strategy"),
            ("defense_analyst_002", "defense_analyst", "security_threats"),
            ("defense_analyst_003", "defense_analyst", "regional_conflicts"),
            
            # Technology analysts
            ("tech_analyst_001", "tech_analyst", "emerging_tech"),
            ("tech_analyst_002", "tech_analyst", "cybersecurity"),
            ("tech_analyst_003", "tech_analyst", "innovation_trends"),
            
            # Strategic analysts
            ("strategist_001", "strategist", "geopolitical_strategy"),
            ("strategist_002", "strategist", "economic_strategy"),
            ("strategist_003", "strategist", "long_term_trends"),
        ]
        
        for agent_id, role, expertise in agent_configs:
            agent = SwarmAgent(agent_id, role, expertise)
            self.agents.append(agent)
        
        logger.info(f"Initialized {len(self.agents)} swarm agents")
    
    async def run_simulation(self, seed_data: Dict[str, Any], simulation_steps: int = 10) -> Dict[str, Any]:
        """Run swarm simulation with seed data"""
        if not settings.SWARM_ENGINE_ENABLED:
            return {"error": "Swarm engine disabled"}
            
        logger.info(f"Starting swarm simulation with {len(self.agents)} agents")
        self.simulation_running = True
        
        try:
            # Step 1: Seed agents with initial information
            await self._seed_agents(seed_data)
            
            # Step 2: Run simulation steps
            simulation_results = []
            for step in range(simulation_steps):
                logger.info(f"Simulation step {step + 1}/{simulation_steps}")
                
                # Agent interactions and decision making
                step_results = await self._run_simulation_step(step)
                simulation_results.append(step_results)
                
                # Small delay between steps
                await asyncio.sleep(0.1)
            
            # Step 3: Synthesize predictions
            predictions = await self._synthesize_predictions(simulation_results)
            
            # Step 4: Generate report
            report = await self._generate_simulation_report(seed_data, simulation_results, predictions)
            
            self.simulation_running = False
            
            return {
                'simulation_id': str(uuid.uuid4()),
                'seed_data': seed_data,
                'agents_count': len(self.agents),
                'simulation_steps': simulation_results,
                'predictions': predictions,
                'report': report,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Swarm simulation error: {e}")
            self.simulation_running = False
            return {"error": str(e)}
    
    async def _seed_agents(self, seed_data: Dict[str, Any]):
        """Seed all agents with initial information"""
        for agent in self.agents:
            relevant_data = self._filter_relevant_data(seed_data, agent.expertise)
            agent.update_memory(relevant_data)
    
    async def _run_simulation_step(self, step: int) -> Dict[str, Any]:
        """Run a single simulation step"""
        step_results = {
            'step': step,
            'agent_decisions': [],
            'interactions': [],
            'emergent_behaviors': []
        }
        
        # Agent decision making
        for agent in self.agents:
            decision = await self._agent_decision(agent, step)
            step_results['agent_decisions'].append({
                'agent_id': agent.id,
                'role': agent.role,
                'decision': decision
            })
        
        # Agent interactions (simplified)
        interactions = self._generate_agent_interactions(step)
        step_results['interactions'] = interactions
        
        return step_results
    
    async def _agent_decision(self, agent: SwarmAgent, step: int) -> Dict[str, Any]:
        """Generate agent decision based on memory and role"""
        context = agent.get_context()
        
        prompt = f"""You are {agent.id}, a {agent.role} specializing in {agent.expertise}.
        
Context:
{context}

Step {step} of simulation. Make a decision based on your role and expertise.
Consider:
1. Your role's priorities
2. Recent information in memory
3. Potential risks and opportunities
4. Collaboration with other agents

Return JSON format:
{{
    "decision": "brief decision description",
    "confidence": 0.0-1.0,
    "rationale": "reasoning for decision",
    "recommended_actions": ["action1", "action2"],
    "risk_assessment": "low/medium/high"
}}"""
        
        try:
            response = await ai_service.query(prompt, context=context, model="meta-llama/llama-3.2-3b-instruct:free")
            
            # Try to parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "decision": response[:200],
                    "confidence": 0.5,
                    "rationale": "AI response",
                    "recommended_actions": [],
                    "risk_assessment": "medium"
                }
        except Exception as e:
            logger.error(f"Agent {agent.id} decision error: {e}")
            return {
                "decision": "Error in decision making",
                "confidence": 0.0,
                "rationale": str(e),
                "recommended_actions": [],
                "risk_assessment": "high"
            }
    
    def _generate_agent_interactions(self, step: int) -> List[Dict[str, Any]]:
        """Generate interactions between agents"""
        interactions = []
        
        # Simple interaction rules
        for i, agent1 in enumerate(self.agents):
            for agent2 in self.agents[i+1:]:
                # Agents with complementary expertise interact
                if self._should_interact(agent1, agent2):
                    interaction = {
                        'agent1': agent1.id,
                        'agent2': agent2.id,
                        'type': 'information_exchange',
                        'topic': f"{agent1.expertise}_x_{agent2.expertise}",
                        'strength': 0.7
                    }
                    interactions.append(interaction)
        
        return interactions
    
    def _should_interact(self, agent1: SwarmAgent, agent2: SwarmAgent) -> bool:
        """Determine if two agents should interact"""
        # Complementary expertise interactions
        complementary_pairs = [
            ('geopolitics', 'economics'),
            ('defense_analyst', 'geopolitics'),
            ('tech_analyst', 'defense_analyst'),
            ('strategist', 'economist'),
        ]
        
        pair1 = (agent1.expertise, agent2.expertise)
        pair2 = (agent2.expertise, agent1.expertise)
        
        return pair1 in complementary_pairs or pair2 in complementary_pairs
    
    async def _synthesize_predictions(self, simulation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize predictions from all simulation steps"""
        prompt = f"""You are analyzing results from a swarm intelligence simulation with {len(self.agents)} AI agents.

Simulation Results:
{json.dumps(simulation_results, indent=2)}

Synthesize predictions about:
1. Geopolitical developments (next 1-3 months)
2. Economic trends (next 3-6 months)
3. Risk factors and opportunities
4. Agent consensus and disagreements

Return JSON format:
{{
    "geopolitical_predictions": [
        {{"event": "description", "probability": 0.0-1.0, "timeline": "months"}}
    ],
    "economic_predictions": [
        {{"indicator": "description", "trend": "up/down/stable", "confidence": 0.0-1.0}}
    ],
    "risk_factors": ["risk1", "risk2"],
    "opportunities": ["opportunity1", "opportunity2"],
    "agent_consensus": {{"topic": "description", "agreement_level": 0.0-1.0}},
    "overall_assessment": "brief summary"
}}"""
        
        try:
            response = await ai_service.query(prompt, model="meta-llama/llama-3.2-3b-instruct:free")
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "geopolitical_predictions": [],
                    "economic_predictions": [],
                    "risk_factors": [],
                    "opportunities": [],
                    "agent_consensus": {},
                    "overall_assessment": response[:500]
                }
        except Exception as e:
            logger.error(f"Prediction synthesis error: {e}")
            return {"error": str(e)}
    
    async def _generate_simulation_report(self, seed_data: Dict[str, Any], 
                                     simulation_results: List[Dict[str, Any]], 
                                     predictions: Dict[str, Any]) -> str:
        """Generate final simulation report"""
        report_prompt = f"""Generate a comprehensive intelligence report based on swarm simulation.

SEED DATA:
{json.dumps(seed_data, indent=2)}

SIMULATION RESULTS:
{json.dumps(simulation_results[-3:], indent=2)}  # Last 3 steps

PREDICTIONS:
{json.dumps(predictions, indent=2)}

Format as structured intelligence report:
# Swarm Intelligence Analysis

## Executive Summary
[Brief 2-3 sentence summary]

## Key Findings
- Finding 1 with evidence
- Finding 2 with evidence
- Finding 3 with evidence

## Agent Insights
### Diplomatic Agents
[Key insights from diplomatic agents]

### Economic Agents  
[Key insights from economic agents]

### Defense & Security Agents
[Key insights from defense agents]

### Technology Agents
[Key insights from technology agents]

### Strategic Analysts
[Key insights from strategic agents]

## Predictions
### Geopolitical (1-3 months)
[Predictions with probabilities]

### Economic (3-6 months)
[Economic trends and indicators]

## Risk Assessment
[High, medium, low risk factors]

## Recommendations
[Actionable recommendations based on analysis]

## Confidence Levels
[Overall confidence in predictions and recommendations]

---
*Report generated by AARAMBH Swarm Intelligence Engine*
*Simulation time: {datetime.now().isoformat()}*
*Agents: {len(self.agents)} AI agents*
"""
        
        try:
            report = await ai_service.query(report_prompt, model="meta-llama/llama-3.2-3b-instruct:free")
            return report
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return f"Error generating report: {str(e)}"
    
    def _filter_relevant_data(self, seed_data: Dict[str, Any], expertise: str) -> Dict[str, Any]:
        """Filter data relevant to agent's expertise"""
        relevance_map = {
            'geopolitics': ['geopolitics', 'diplomacy', 'conflict', 'international_relations'],
            'economics': ['economics', 'finance', 'trade', 'gdp', 'inflation'],
            'defense_analyst': ['defense', 'military', 'security', 'terrorism'],
            'tech_analyst': ['technology', 'innovation', 'cybersecurity', 'research'],
            'strategist': ['strategy', 'policy', 'long_term', 'planning']
        }
        
        relevant_keywords = relevance_map.get(expertise, [])
        filtered_data = {}
        
        for key, value in seed_data.items():
            if any(keyword in str(value).lower() for keyword in relevant_keywords):
                filtered_data[key] = value
        
        return filtered_data


# Singleton instance
swarm_intelligence = SwarmIntelligenceEngine()
