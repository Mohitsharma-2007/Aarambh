"""
Ontology Project Management Models
Used for persisting project state on the server side, avoiding passing large amounts of data between frontend and APIs
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from app.database import Base


class ProjectStatus(str, Enum):
    """Project Status"""
    CREATED = "created"              # Just created, files uploaded
    ONTOLOGY_GENERATED = "ontology_generated"  # Ontology generated
    GRAPH_BUILDING = "graph_building"    # Graph building in progress
    GRAPH_COMPLETED = "graph_completed"  # Graph build completed
    SIMULATION_CREATED = "simulation_created"  # Simulation created
    SIMULATION_READY = "simulation_ready"  # Environment setup complete
    SIMULATION_RUNNING = "simulation_running"  # Simulation running
    SIMULATION_COMPLETED = "simulation_completed"  # Simulation finished
    REPORT_GENERATING = "report_generating"  # Report being generated
    REPORT_COMPLETED = "report_completed"  # Report generation complete
    FAILED = "failed"                # Failed


@dataclass
class OntologyProject:
    """Project Data Model"""
    project_id: str
    name: str
    status: ProjectStatus
    created_at: str
    updated_at: str
    
    # File information
    files: List[Dict[str, str]] = field(default_factory=list)  # [{filename, path, size}]
    total_text_length: int = 0
    
    # Ontology information (filled after API 1 generation)
    ontology: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[str] = None
    
    # Graph information (filled after API 2 completion)
    graph_id: Optional[str] = None
    graph_build_task_id: Optional[str] = None
    
    # Simulation information
    simulation_id: Optional[str] = None
    simulation_status: Optional[str] = None
    
    # Report information
    report_id: Optional[str] = None
    report_status: Optional[str] = None
    
    # Configuration
    simulation_requirement: Optional[str] = None
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Error information
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "status": self.status.value if isinstance(self.status, ProjectStatus) else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "files": self.files,
            "total_text_length": self.total_text_length,
            "ontology": self.ontology,
            "analysis_summary": self.analysis_summary,
            "graph_id": self.graph_id,
            "graph_build_task_id": self.graph_build_task_id,
            "simulation_id": self.simulation_id,
            "simulation_status": self.simulation_status,
            "report_id": self.report_id,
            "report_status": self.report_status,
            "simulation_requirement": self.simulation_requirement,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OntologyProject':
        """Create from dictionary"""
        status = data.get('status', 'created')
        if isinstance(status, str):
            status = ProjectStatus(status)
        
        return cls(
            project_id=data['project_id'],
            name=data.get('name', 'Unnamed Project'),
            status=status,
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            files=data.get('files', []),
            total_text_length=data.get('total_text_length', 0),
            ontology=data.get('ontology'),
            analysis_summary=data.get('analysis_summary'),
            graph_id=data.get('graph_id'),
            graph_build_task_id=data.get('graph_build_task_id'),
            simulation_id=data.get('simulation_id'),
            simulation_status=data.get('simulation_status'),
            report_id=data.get('report_id'),
            report_status=data.get('report_status'),
            simulation_requirement=data.get('simulation_requirement'),
            chunk_size=data.get('chunk_size', 500),
            chunk_overlap=data.get('chunk_overlap', 50),
            error=data.get('error')
        )


class OntologyProjectManager:
    """Project Manager - Responsible for project persistence and retrieval"""
    
    # Project storage root directory - use absolute path
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    PROJECTS_DIR = os.path.join(BASE_DIR, 'uploads', 'projects')
    
    @classmethod
    def _ensure_projects_dir(cls):
        """Ensure project directory exists"""
        os.makedirs(cls.PROJECTS_DIR, exist_ok=True)
    
    @classmethod
    def _get_project_dir(cls, project_id: str) -> str:
        """Get project directory path"""
        return os.path.join(cls.PROJECTS_DIR, project_id)
    
    @classmethod
    def _get_project_meta_path(cls, project_id: str) -> str:
        """Get project metadata file path"""
        return os.path.join(cls._get_project_dir(project_id), 'project.json')
    
    @classmethod
    def _get_project_files_dir(cls, project_id: str) -> str:
        """Get project file storage directory"""
        return os.path.join(cls._get_project_dir(project_id), 'files')
    
    @classmethod
    def _get_project_text_path(cls, project_id: str) -> str:
        """Get project extracted text storage path"""
        return os.path.join(cls._get_project_dir(project_id), 'extracted_text.txt')
    
    @classmethod
    def create_project(cls, name: str = "Unnamed Project") -> OntologyProject:
        """Create new project"""
        cls._ensure_projects_dir()
        
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        project = OntologyProject(
            project_id=project_id,
            name=name,
            status=ProjectStatus.CREATED,
            created_at=now,
            updated_at=now
        )
        
        # Create project directory
        project_dir = cls._get_project_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(cls._get_project_files_dir(project_id), exist_ok=True)
        
        # Save project metadata
        cls._save_project(project)
        
        return project
    
    @classmethod
    def _save_project(cls, project: OntologyProject):
        """Save project to file"""
        meta_path = cls._get_project_meta_path(project.project_id)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def get_project(cls, project_id: str) -> Optional[OntologyProject]:
        """Get project"""
        meta_path = cls._get_project_meta_path(project_id)
        if not os.path.exists(meta_path):
            return None
        
        try:
            with open(meta_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            return OntologyProject.from_dict(data)
        except Exception:
            return None
    
    @classmethod
    def update_project(cls, project: OntologyProject):
        """Update project"""
        project.updated_at = datetime.now().isoformat()
        cls._save_project(project)
    
    @classmethod
    def delete_project(cls, project_id: str) -> bool:
        """Delete project"""
        project_dir = cls._get_project_dir(project_id)
        if not os.path.exists(project_dir):
            return False
        
        try:
            shutil.rmtree(project_dir)
            return True
        except Exception:
            return False
    
    @classmethod
    def list_projects(cls, limit: int = 50) -> List[OntologyProject]:
        """List all projects"""
        cls._ensure_projects_dir()
        projects = []
        
        for project_id in os.listdir(cls.PROJECTS_DIR):
            project = cls.get_project(project_id)
            if project:
                projects.append(project)
        
        # Sort by update time
        projects.sort(key=lambda p: p.updated_at, reverse=True)
        return projects[:limit]
    
    @classmethod
    def add_file_to_project(cls, project_id: str, filename: str, file_path: str, size: int) -> bool:
        """Add file to project"""
        project = cls.get_project(project_id)
        if not project:
            return False
        
        # Move file to project directory
        target_dir = cls._get_project_files_dir(project_id)
        target_path = os.path.join(target_dir, filename)
        
        if os.path.exists(file_path):
            shutil.move(file_path, target_path)
        
        # Update project file list
        project.files.append({
            "filename": filename,
            "path": target_path,
            "size": size
        })
        cls.update_project(project)
        
        return True
    
    @classmethod
    def get_project_text(cls, project_id: str) -> str:
        """Get project extracted text content"""
        text_path = cls._get_project_text_path(project_id)
        if os.path.exists(text_path):
            with open(text_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    @classmethod
    def save_project_text(cls, project_id: str, text: str):
        """Save project extracted text content"""
        text_path = cls._get_project_text_path(project_id)
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Update project text length
        project = cls.get_project(project_id)
        if project:
            project.total_text_length = len(text)
            cls.update_project(project)
