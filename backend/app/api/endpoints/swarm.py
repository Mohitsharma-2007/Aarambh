"""Swarm Intelligence API endpoints"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio

from app.services.swarm_intelligence import swarm_intelligence
from app.config import settings

router = APIRouter(prefix="/swarm", tags=["swarm"])


class SwarmSimulationRequest(BaseModel):
    """Request model for swarm simulation"""
    seed_data: Dict[str, Any]
    simulation_steps: int = 10
    agent_types: Optional[list] = None


class SwarmSimulationResponse(BaseModel):
    """Response model for swarm simulation"""
    simulation_id: str
    status: str
    agents_count: int
    predictions: Dict[str, Any]
    report: str
    timestamp: str


@router.post("/simulate", response_model=SwarmSimulationResponse)
async def run_swarm_simulation(
    request: SwarmSimulationRequest,
    background_tasks: BackgroundTasks
) -> SwarmSimulationResponse:
    """
    Run MiroFish-style swarm intelligence simulation
    
    Takes seed data (news, economic indicators, policy drafts) and runs
    multi-agent simulation to generate predictions and intelligence reports.
    """
    try:
        if not settings.SWARM_ENGINE_ENABLED:
            raise HTTPException(status_code=503, detail="Swarm engine disabled")
        
        # Run simulation
        results = await swarm_intelligence.run_simulation(
            seed_data=request.seed_data,
            simulation_steps=request.simulation_steps
        )
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return SwarmSimulationResponse(
            simulation_id=results["simulation_id"],
            status="completed",
            agents_count=results["agents_count"],
            predictions=results["predictions"],
            report=results["report"],
            timestamp=results["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Swarm simulation error: {str(e)}")


@router.get("/status")
async def get_swarm_status() -> Dict[str, Any]:
    """Get current swarm engine status"""
    return {
        "enabled": settings.SWARM_ENGINE_ENABLED,
        "agents_count": len(swarm_intelligence.agents) if settings.SWARM_ENGINE_ENABLED else 0,
        "simulation_running": swarm_intelligence.simulation_running,
        "agent_types": [
            {
                "role": agent.role,
                "expertise": agent.expertise,
                "memory_count": len(agent.memory)
            }
            for agent in swarm_intelligence.agents
        ] if settings.SWARM_ENGINE_ENABLED else [],
        "configuration": {
            "agent_count": settings.AGENT_SIMULATION_COUNT,
            "mirofish_api_url": settings.MIROFISH_API_URL
        }
    }


@router.get("/agents")
async def get_agent_list() -> Dict[str, Any]:
    """Get list of all swarm agents"""
    if not settings.SWARM_ENGINE_ENABLED:
        return {"agents": [], "enabled": False}
    
    return {
        "enabled": True,
        "agents": [
            {
                "id": agent.id,
                "role": agent.role,
                "expertise": agent.expertise,
                "memory_count": len(agent.memory),
                "behavior": agent.behavior
            }
            for agent in swarm_intelligence.agents
        ]
    }


@router.get("/predictions/{simulation_id}")
async def get_simulation_predictions(simulation_id: str) -> Dict[str, Any]:
    """Get predictions for a specific simulation (placeholder)"""
    # In production, this would fetch from database
    return {
        "simulation_id": simulation_id,
        "message": "Historical predictions not implemented yet",
        "note": "This endpoint would return stored simulation results"
    }
