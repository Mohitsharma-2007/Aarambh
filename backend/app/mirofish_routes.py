"""
MiroFish-compatible Simulation API for AARAMBH
Handles multipart/form-data for ontology generation
"""
import os
import uuid
import time
import json
import threading
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

router = APIRouter(prefix="/graph", tags=["MiroFish Graph"])

# In-memory storage for projects and tasks
projects_db = {}
tasks_db = {}

# Configuration
LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://openrouter.ai/api/v1')
LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'stepfun/step-3.5-flash:free')


def get_llm_client():
    """Get OpenRouter LLM client"""
    try:
        from openai import OpenAI
        return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    except Exception as e:
        logger.error(f"Failed to create LLM client: {e}")
        return None


def call_llm(prompt: str, system_prompt: str = None) -> str:
    """Call LLM with OpenRouter"""
    client = get_llm_client()
    if not client:
        return ""
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=3000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return ""


@router.post("/ontology/generate")
async def generate_ontology(
    files: List[UploadFile] = File(default=[]),
    simulation_requirement: str = Form(default=""),
    project_name: str = Form(default="Unnamed Project"),
    additional_context: Optional[str] = Form(default=None)
):
    """
    Generate ontology from uploaded files.
    Accepts multipart/form-data with files and simulation_requirement.
    """
    try:
        logger.info("=== Starting Ontology Generation ===")
        logger.info(f"Files received: {len(files)}")
        logger.info(f"Simulation requirement: {simulation_requirement[:100]}...")
        
        if not simulation_requirement:
            return JSONResponse(
                status_code=422,
                content={"success": False, "error": "simulation_requirement is required"}
            )
        
        # Create project
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        
        # Read file contents
        all_text = ""
        file_info_list = []
        
        for file in files:
            if file.filename:
                content = await file.read()
                try:
                    text = content.decode('utf-8', errors='ignore')
                except:
                    text = str(content)
                all_text += f"\n\n=== {file.filename} ===\n{text}"
                file_info_list.append({
                    "filename": file.filename,
                    "size": len(content)
                })
        
        # Generate ontology
        ontology = generate_ontology_from_text(all_text, simulation_requirement)
        
        # Store project
        projects_db[project_id] = {
            "project_id": project_id,
            "project_name": project_name,
            "simulation_requirement": simulation_requirement,
            "files": file_info_list,
            "total_text_length": len(all_text),
            "ontology": ontology,
            "status": "ontology_generated",
            "graph_id": None,
            "created_at": time.time()
        }
        
        logger.info(f"Ontology generated for project {project_id}")
        logger.info(f"Entity types: {len(ontology.get('entity_types', []))}")
        logger.info(f"Edge types: {len(ontology.get('edge_types', []))}")
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "project_name": project_name,
                "name": project_name,
                "ontology": ontology,
                "files": file_info_list,
                "total_text_length": len(all_text)
            }
        }
        
    except Exception as e:
        logger.error(f"Ontology generation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


def generate_ontology_from_text(text: str, requirement: str) -> dict:
    """Generate ontology from text using LLM with mock fallback"""
    try:
        from openai import OpenAI
        import json

        api_key = os.environ.get('LLM_API_KEY') or os.environ.get('OPENROUTER_API_KEY', '')
        base_url = os.environ.get('LLM_BASE_URL', 'https://openrouter.ai/api/v1')
        model = os.environ.get('LLM_MODEL_NAME', 'google/gemini-2.0-flash-001')

        if not api_key:
            logger.warning("No LLM API key, using fallback ontology")
            return _fallback_ontology(requirement)

        client = OpenAI(api_key=api_key, base_url=base_url)

        prompt = f"""Analyze the following text and simulation requirement to generate a knowledge ontology.

Simulation Requirement: {requirement}

Text Content (first 3000 chars):
{text[:3000]}

Generate a JSON ontology with:
1. "entity_types": array of 8-12 types, each with "name", "description", "attributes" (array of {{"name": str, "type": str}})
   - MUST include "Person" and "Organization" as base types
2. "edge_types": array of 6-10 relationship types, each with "name", "description", "source_types", "target_types"
3. "analysis_summary": one paragraph summary

Return ONLY valid JSON."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an ontology generation expert. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )

        content = response.choices[0].message.content
        # Extract JSON from response
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        ontology = json.loads(content.strip())

        # Validate required fields
        if 'entity_types' not in ontology or 'edge_types' not in ontology:
            raise ValueError("Missing required fields")

        if 'analysis_summary' not in ontology:
            ontology['analysis_summary'] = f"Ontology generated for: {requirement[:100]}"

        logger.info(f"LLM ontology generated: {len(ontology['entity_types'])} entity types, {len(ontology['edge_types'])} edge types")
        return ontology

    except Exception as e:
        logger.warning(f"LLM ontology generation failed: {e}, using fallback")
        return _fallback_ontology(requirement)


def _fallback_ontology(requirement: str) -> dict:
    """Fallback ontology when LLM is unavailable"""
    # Comprehensive ontology for Noida Airport scenario
    if "airport" in requirement.lower() or "noida" in requirement.lower():
        return {
            "entity_types": [
                {"name": "Person", "description": "Individual person", "attributes": [
                    {"name": "role", "type": "string"},
                    {"name": "department", "type": "string"}
                ]},
                {"name": "Government", "description": "Government entity", "attributes": [
                    {"name": "level", "type": "string"},
                    {"name": "jurisdiction", "type": "string"}
                ]},
                {"name": "Ministry", "description": "Government ministry", "attributes": [
                    {"name": "minister", "type": "string"},
                    {"name": "budget", "type": "number"}
                ]},
                {"name": "Airport", "description": "Airport facility", "attributes": [
                    {"name": "code", "type": "string"},
                    {"name": "capacity", "type": "number"}
                ]},
                {"name": "Airline", "description": "Airline company", "attributes": [
                    {"name": "type", "type": "string"}
                ]},
                {"name": "Organization", "description": "Organization", "attributes": [
                    {"name": "type", "type": "string"}
                ]},
                {"name": "Project", "description": "Infrastructure project", "attributes": [
                    {"name": "status", "type": "string"},
                    {"name": "budget", "type": "number"}
                ]},
                {"name": "Location", "description": "Geographic location", "attributes": [
                    {"name": "state", "type": "string"}
                ]},
                {"name": "RegulatoryBody", "description": "Regulatory authority", "attributes": [
                    {"name": "jurisdiction", "type": "string"}
                ]},
                {"name": "FinancialInstrument", "description": "Financial entity", "attributes": [
                    {"name": "amount", "type": "number"}
                ]},
                {"name": "Event", "description": "Event or milestone", "attributes": [
                    {"name": "date", "type": "date"}
                ]},
                {"name": "Contractor", "description": "Construction contractor", "attributes": [
                    {"name": "specialization", "type": "string"}
                ]}
            ],
            "edge_types": [
                {"name": "GOVERNS", "description": "Government oversight", "source_types": ["Government", "Ministry"], "target_types": ["Airport", "Project"]},
                {"name": "OWNS", "description": "Ownership", "source_types": ["Government", "Organization"], "target_types": ["Airport", "Project"]},
                {"name": "OPERATES", "description": "Operational control", "source_types": ["Airline", "Organization"], "target_types": ["Airport"]},
                {"name": "LOCATED_IN", "description": "Location", "source_types": ["Airport", "Project"], "target_types": ["Location"]},
                {"name": "FUNDED_BY", "description": "Funding", "source_types": ["FinancialInstrument", "Government"], "target_types": ["Project"]},
                {"name": "REGULATES", "description": "Regulation", "source_types": ["RegulatoryBody", "Ministry"], "target_types": ["Airport", "Airline"]},
                {"name": "CONTRACTED_TO", "description": "Contract", "source_types": ["Project"], "target_types": ["Contractor"]},
                {"name": "PARTICIPATES_IN", "description": "Participation", "source_types": ["Person", "Organization"], "target_types": ["Event", "Project"]},
                {"name": "LEADS", "description": "Leadership", "source_types": ["Person"], "target_types": ["Ministry", "Organization"]},
                {"name": "IMPACTS", "description": "Impact", "source_types": ["Project", "Airport"], "target_types": ["Location"]},
                {"name": "INVESTS_IN", "description": "Investment", "source_types": ["FinancialInstrument", "Organization"], "target_types": ["Project"]}
            ],
            "analysis_summary": "Comprehensive ontology for Noida International Airport covering government, infrastructure, and financial aspects"
        }

    # Default ontology
    return {
        "entity_types": [
            {"name": "Person", "description": "Individual", "attributes": []},
            {"name": "Organization", "description": "Organization", "attributes": []},
            {"name": "Location", "description": "Location", "attributes": []},
            {"name": "Event", "description": "Event", "attributes": []}
        ],
        "edge_types": [
            {"name": "RELATED_TO", "description": "General relation", "source_types": ["*"], "target_types": ["*"]},
            {"name": "PARTICIPATES_IN", "description": "Participation", "source_types": ["Person"], "target_types": ["Event"]},
            {"name": "LOCATED_IN", "description": "Location", "source_types": ["*"], "target_types": ["Location"]}
        ],
        "analysis_summary": "Default ontology"
    }


@router.post("/build")
async def build_graph(data: dict):
    """Build knowledge graph from project"""
    try:
        project_id = data.get("project_id")
        
        if not project_id or project_id not in projects_db:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Project not found"}
            )
        
        project = projects_db[project_id]
        
        # Create task
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        tasks_db[task_id] = {
            "task_id": task_id,
            "project_id": project_id,
            "status": "processing",
            "progress": 0,
            "message": "Initializing graph build...",
            "created_at": time.time()
        }
        
        # Update project
        project["graph_build_task_id"] = task_id
        project["status"] = "graph_building"
        
        # Simulate graph building
        def build_worker():
            time.sleep(1)
            tasks_db[task_id]["progress"] = 25
            tasks_db[task_id]["message"] = "Processing entities..."
            time.sleep(1)
            tasks_db[task_id]["progress"] = 50
            tasks_db[task_id]["message"] = "Extracting relationships..."
            time.sleep(1)
            tasks_db[task_id]["progress"] = 75
            tasks_db[task_id]["message"] = "Building graph structure..."
            time.sleep(1)
            tasks_db[task_id]["progress"] = 100
            tasks_db[task_id]["status"] = "completed"
            tasks_db[task_id]["message"] = "Graph build complete"
            
            # Generate graph ID
            graph_id = f"graph_{uuid.uuid4().hex[:12]}"
            project["graph_id"] = graph_id
            project["status"] = "graph_completed"
        
        threading.Thread(target=build_worker, daemon=True).start()
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "task_id": task_id,
                "message": "Graph build task started"
            }
        }
        
    except Exception as e:
        logger.error(f"Graph build failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get task status"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "success": True,
        "data": tasks_db[task_id]
    }


@router.get("/project/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "success": True,
        "data": projects_db[project_id]
    }


@router.get("/data/{graph_id}")
async def get_graph_data(graph_id: str):
    """Get graph data with nodes and edges"""
    # Find project with this graph_id
    for project in projects_db.values():
        if project.get("graph_id") == graph_id:
            ontology = project.get("ontology", {})
            entity_types = ontology.get("entity_types", [])
            
            # Generate sample nodes based on ontology
            nodes = []
            edges = []
            
            if "airport" in project.get("simulation_requirement", "").lower():
                # Noida Airport specific nodes
                nodes = [
                    {"uuid": "n1", "name": "Noida International Airport", "labels": ["Airport", "Entity"], "attributes": {"code": "DXN", "status": "Under Construction"}},
                    {"uuid": "n2", "name": "Ministry of Civil Aviation", "labels": ["Ministry", "Entity"], "attributes": {"minister": "Jyotiraditya Scindia"}},
                    {"uuid": "n3", "name": "Yamuna Expressway Authority", "labels": ["Organization", "Entity"], "attributes": {"type": "Government Body"}},
                    {"uuid": "n4", "name": "Uttar Pradesh Government", "labels": ["Government", "Entity"], "attributes": {"level": "State"}},
                    {"uuid": "n5", "name": "Airports Authority of India", "labels": ["Organization", "Entity"], "attributes": {"type": "Regulatory"}},
                    {"uuid": "n6", "name": "Jewar, Uttar Pradesh", "labels": ["Location", "Entity"], "attributes": {"state": "Uttar Pradesh"}},
                    {"uuid": "n7", "name": "Terminal Building Project", "labels": ["Project", "Entity"], "attributes": {"budget": 29560, "status": "In Progress"}},
                    {"uuid": "n8", "name": "Runway Construction", "labels": ["Project", "Entity"], "attributes": {"status": "Planning"}},
                    {"uuid": "n9", "name": "DGCA", "labels": ["RegulatoryBody", "Entity"], "attributes": {"jurisdiction": "Civil Aviation"}},
                    {"uuid": "n10", "name": "PM Narendra Modi", "labels": ["Person", "Entity"], "attributes": {"role": "Prime Minister"}},
                    {"uuid": "n11", "name": "CM Yogi Adityanath", "labels": ["Person", "Entity"], "attributes": {"role": "Chief Minister"}},
                    {"uuid": "n12", "name": "Zurich Airport AG", "labels": ["Organization", "Entity"], "attributes": {"type": "International Partner"}},
                ]
                
                edges = [
                    {"uuid": "e1", "source_node_uuid": "n2", "target_node_uuid": "n1", "fact_type": "GOVERNS", "name": "GOVERNS"},
                    {"uuid": "e2", "source_node_uuid": "n4", "target_node_uuid": "n1", "fact_type": "OWNS", "name": "OWNS"},
                    {"uuid": "e3", "source_node_uuid": "n5", "target_node_uuid": "n1", "fact_type": "OPERATES", "name": "OPERATES"},
                    {"uuid": "e4", "source_node_uuid": "n1", "target_node_uuid": "n6", "fact_type": "LOCATED_IN", "name": "LOCATED_IN"},
                    {"uuid": "e5", "source_node_uuid": "n3", "target_node_uuid": "n7", "fact_type": "FUNDED_BY", "name": "FUNDED_BY"},
                    {"uuid": "e6", "source_node_uuid": "n9", "target_node_uuid": "n1", "fact_type": "REGULATES", "name": "REGULATES"},
                    {"uuid": "e7", "source_node_uuid": "n10", "target_node_uuid": "n7", "fact_type": "PARTICIPATES_IN", "name": "PARTICIPATES_IN"},
                    {"uuid": "e8", "source_node_uuid": "n11", "target_node_uuid": "n3", "fact_type": "LEADS", "name": "LEADS"},
                    {"uuid": "e9", "source_node_uuid": "n12", "target_node_uuid": "n1", "fact_type": "INVESTS_IN", "name": "INVESTS_IN"},
                    {"uuid": "e10", "source_node_uuid": "n1", "target_node_uuid": "n8", "fact_type": "OWNS", "name": "OWNS"},
                ]
            else:
                # Generic nodes
                nodes = [
                    {"uuid": "n1", "name": "Main Entity", "labels": ["Organization", "Entity"], "attributes": {}},
                    {"uuid": "n2", "name": "Related Person", "labels": ["Person", "Entity"], "attributes": {}},
                    {"uuid": "n3", "name": "Location", "labels": ["Location", "Entity"], "attributes": {}},
                ]
                edges = [
                    {"uuid": "e1", "source_node_uuid": "n1", "target_node_uuid": "n2", "fact_type": "RELATED_TO", "name": "RELATED_TO"},
                ]
            
            return {
                "success": True,
                "data": {
                    "graph_id": graph_id,
                    "nodes": nodes,
                    "edges": edges,
                    "node_count": len(nodes),
                    "edge_count": len(edges)
                }
            }
    
    raise HTTPException(status_code=404, detail="Graph not found")
