"""
MiroFish Simulation API Endpoints for AARAMBH
Handles simulation creation, preparation, and execution
"""
import os
import uuid
import time
import threading
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter(prefix="/simulation", tags=["MiroFish Simulation"])

# In-memory storage
simulations_db = {}
simulation_tasks_db = {}


@router.post("/create")
async def create_simulation(data: dict):
    """Create a new simulation"""
    try:
        project_id = data.get("project_id")
        graph_id = data.get("graph_id")
        
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        
        simulations_db[simulation_id] = {
            "simulation_id": simulation_id,
            "project_id": project_id,
            "graph_id": graph_id,
            "status": "created",
            "created_at": time.time(),
            "config": {
                "enable_twitter": data.get("enable_twitter", True),
                "enable_reddit": data.get("enable_reddit", True),
                "max_rounds": data.get("max_rounds", 10)
            },
            "profiles": {},
            "actions": []
        }
        
        return {
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "status": "created"
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/prepare")
async def prepare_simulation(data: dict):
    """Prepare simulation environment (async)"""
    try:
        simulation_id = data.get("simulation_id")
        
        if not simulation_id or simulation_id not in simulations_db:
            return {"success": False, "error": "Simulation not found"}
        
        # Create preparation task
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        simulation_tasks_db[task_id] = {
            "task_id": task_id,
            "simulation_id": simulation_id,
            "status": "processing",
            "progress": 0,
            "message": "Preparing simulation environment...",
            "created_at": time.time()
        }
        
        # Simulate preparation
        def prepare_worker():
            sim = simulations_db[simulation_id]
            
            simulation_tasks_db[task_id]["progress"] = 25
            simulation_tasks_db[task_id]["message"] = "Generating agent profiles..."
            time.sleep(2)
            
            # Generate sample profiles
            sim["profiles"] = {
                "twitter": [
                    {"agent_id": "agent_1", "username": "NoidaAirportWatch", "bio": "Tracking Noida International Airport development"},
                    {"agent_id": "agent_2", "username": "UPDevelopment", "bio": "Uttar Pradesh infrastructure updates"},
                    {"agent_id": "agent_3", "username": "AviationIndia", "bio": "Indian aviation industry analyst"}
                ],
                "reddit": [
                    {"agent_id": "agent_4", "username": "AirportFan2024", "bio": "Aviation enthusiast"},
                    {"agent_id": "agent_5", "username": "NoidaResident", "bio": "Local resident tracking developments"},
                    {"agent_id": "agent_6", "username": "InvestmentAnalyst", "bio": "Infrastructure investment specialist"}
                ]
            }
            
            simulation_tasks_db[task_id]["progress"] = 50
            simulation_tasks_db[task_id]["message"] = "Configuring simulation parameters..."
            time.sleep(2)
            
            simulation_tasks_db[task_id]["progress"] = 75
            simulation_tasks_db[task_id]["message"] = "Initializing platforms..."
            time.sleep(1)
            
            simulation_tasks_db[task_id]["progress"] = 100
            simulation_tasks_db[task_id]["status"] = "completed"
            simulation_tasks_db[task_id]["message"] = "Environment ready"
            
            sim["status"] = "prepared"
        
        threading.Thread(target=prepare_worker, daemon=True).start()
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "simulation_id": simulation_id
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/prepare/status")
async def get_prepare_status(data: dict):
    """Get preparation task status"""
    task_id = data.get("task_id")
    
    if task_id and task_id in simulation_tasks_db:
        return {"success": True, "data": simulation_tasks_db[task_id]}
    
    return {"success": False, "error": "Task not found"}


@router.get("/{simulation_id}")
async def get_simulation(simulation_id: str):
    """Get simulation details"""
    if simulation_id not in simulations_db:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return {
        "success": True,
        "data": simulations_db[simulation_id]
    }


@router.get("/{simulation_id}/profiles")
async def get_simulation_profiles(simulation_id: str, platform: str = "reddit"):
    """Get simulation agent profiles"""
    if simulation_id not in simulations_db:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations_db[simulation_id]
    profiles = sim.get("profiles", {}).get(platform, [])
    
    return {
        "success": True,
        "data": profiles
    }


@router.get("/{simulation_id}/config")
async def get_simulation_config(simulation_id: str):
    """Get simulation configuration"""
    if simulation_id not in simulations_db:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations_db[simulation_id]
    
    return {
        "success": True,
        "data": {
            "simulation_id": simulation_id,
            "config": sim.get("config", {}),
            "time_config": {
                "total_simulation_hours": 72,
                "minutes_per_round": 60
            },
            "platform_config": {
                "twitter": {"enabled": sim["config"].get("enable_twitter", True)},
                "reddit": {"enabled": sim["config"].get("enable_reddit", True)}
            }
        }
    }


@router.post("/start")
async def start_simulation(data: dict):
    """Start simulation"""
    try:
        simulation_id = data.get("simulation_id")
        
        if not simulation_id or simulation_id not in simulations_db:
            return {"success": False, "error": "Simulation not found"}
        
        sim = simulations_db[simulation_id]
        sim["status"] = "running"
        sim["started_at"] = time.time()
        sim["current_round"] = 0
        sim["max_rounds"] = data.get("max_rounds", sim["config"].get("max_rounds", 10))
        
        # Generate some initial actions
        sim["actions"] = [
            {
                "timestamp": time.time(),
                "agent_id": "agent_1",
                "agent_name": "NoidaAirportWatch",
                "action_type": "CREATE_POST",
                "platform": "twitter",
                "round_num": 1,
                "action_args": {
                    "content": "Breaking: Noida International Airport runway construction entering final phase. Expected completion by Q2 2025. #NoidaAirport #Infrastructure"
                }
            },
            {
                "timestamp": time.time(),
                "agent_id": "agent_4",
                "agent_name": "AirportFan2024",
                "action_type": "CREATE_POST",
                "platform": "reddit",
                "round_num": 1,
                "action_args": {
                    "content": "Just visited the Noida Airport site. The terminal building is massive! Can't wait for operations to begin."
                }
            }
        ]
        
        return {
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "status": "running",
                "max_rounds": sim["max_rounds"]
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/stop")
async def stop_simulation(data: dict):
    """Stop simulation"""
    simulation_id = data.get("simulation_id")
    
    if simulation_id and simulation_id in simulations_db:
        simulations_db[simulation_id]["status"] = "stopped"
        return {"success": True, "data": {"status": "stopped"}}
    
    return {"success": False, "error": "Simulation not found"}


@router.get("/{simulation_id}/run-status")
async def get_run_status(simulation_id: str):
    """Get simulation run status"""
    if simulation_id not in simulations_db:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations_db[simulation_id]
    
    return {
        "success": True,
        "data": {
            "simulation_id": simulation_id,
            "status": sim.get("status", "unknown"),
            "current_round": sim.get("current_round", 0),
            "max_rounds": sim.get("max_rounds", 10),
            "total_actions": len(sim.get("actions", [])),
            "twitter_actions": len([a for a in sim.get("actions", []) if a.get("platform") == "twitter"]),
            "reddit_actions": len([a for a in sim.get("actions", []) if a.get("platform") == "reddit"])
        }
    }


@router.get("/{simulation_id}/actions")
async def get_simulation_actions(simulation_id: str, limit: int = 50):
    """Get simulation actions"""
    if simulation_id not in simulations_db:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = simulations_db[simulation_id]
    actions = sim.get("actions", [])[:limit]
    
    return {
        "success": True,
        "data": {
            "actions": actions,
            "total": len(sim.get("actions", []))
        }
    }


@router.get("/list")
async def list_simulations(project_id: Optional[str] = None):
    """List all simulations"""
    sims = list(simulations_db.values())
    
    if project_id:
        sims = [s for s in sims if s.get("project_id") == project_id]
    
    return {
        "success": True,
        "data": sims
    }
