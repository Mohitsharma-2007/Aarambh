"""
é¡¹ç›®ä¸Šä¸‹æ–‡ç®¡ç†
ç”¨äºŽåœ¨æœåŠ¡ç«¯æŒä¹…åŒ–é¡¹ç›®çŠ¶æ€ï¼Œé¿å…å‰ç«¯åœ¨æŽ¥å£é—´ä¼ é€’å¤§é‡æ•°æ®
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
from ..config import Config


class ProjectStatus(str, Enum):
    """é¡¹ç›®çŠ¶æ€"""
    CREATED = "created"              # åˆšåˆ›å»ºï¼Œæ–‡ä»¶å·²ä¸Šä¼ 
    ONTOLOGY_GENERATED = "ontology_generated"  # æœ¬ä½“å·²ç”Ÿæˆ
    GRAPH_BUILDING = "graph_building"    # å›¾è°±æž„å»ºä¸­
    GRAPH_COMPLETED = "graph_completed"  # å›¾è°±æž„å»ºå®Œæˆ
    FAILED = "failed"                # å¤±è´¥


@dataclass
class Project:
    """é¡¹ç›®æ•°æ®æ¨¡åž‹"""
    project_id: str
    name: str
    status: ProjectStatus
    created_at: str
    updated_at: str
    
    # æ–‡ä»¶ä¿¡æ¯
    files: List[Dict[str, str]] = field(default_factory=list)  # [{filename, path, size}]
    total_text_length: int = 0
    
    # æœ¬ä½“ä¿¡æ¯ï¼ˆæŽ¥å£1ç”ŸæˆåŽå¡«å……ï¼‰
    ontology: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[str] = None
    
    # å›¾è°±ä¿¡æ¯ï¼ˆæŽ¥å£2å®ŒæˆåŽå¡«å……ï¼‰
    graph_id: Optional[str] = None
    graph_build_task_id: Optional[str] = None
    
    # é…ç½®
    simulation_requirement: Optional[str] = None
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # é”™è¯¯ä¿¡æ¯
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """è½¬æ¢ä¸ºå­—å…¸"""
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
            "simulation_requirement": self.simulation_requirement,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """ä»Žå­—å…¸åˆ›å»º"""
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
            simulation_requirement=data.get('simulation_requirement'),
            chunk_size=data.get('chunk_size', 500),
            chunk_overlap=data.get('chunk_overlap', 50),
            error=data.get('error')
        )


class ProjectManager:
    """é¡¹ç›®ç®¡ç†å™¨ - è´Ÿè´£é¡¹ç›®çš„æŒä¹…åŒ–å­˜å‚¨å’Œæ£€ç´¢"""
    
    # é¡¹ç›®å­˜å‚¨æ ¹ç›®å½•
    PROJECTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'projects')
    
    @classmethod
    def _ensure_projects_dir(cls):
        """ç¡®ä¿é¡¹ç›®ç›®å½•å­˜åœ¨"""
        os.makedirs(cls.PROJECTS_DIR, exist_ok=True)
    
    @classmethod
    def _get_project_dir(cls, project_id: str) -> str:
        """èŽ·å–é¡¹ç›®ç›®å½•è·¯å¾„"""
        return os.path.join(cls.PROJECTS_DIR, project_id)
    
    @classmethod
    def _get_project_meta_path(cls, project_id: str) -> str:
        """èŽ·å–é¡¹ç›®å…ƒæ•°æ®æ–‡ä»¶è·¯å¾„"""
        return os.path.join(cls._get_project_dir(project_id), 'project.json')
    
    @classmethod
    def _get_project_files_dir(cls, project_id: str) -> str:
        """èŽ·å–é¡¹ç›®æ–‡ä»¶å­˜å‚¨ç›®å½•"""
        return os.path.join(cls._get_project_dir(project_id), 'files')
    
    @classmethod
    def _get_project_text_path(cls, project_id: str) -> str:
        """èŽ·å–é¡¹ç›®æå–æ–‡æœ¬å­˜å‚¨è·¯å¾„"""
        return os.path.join(cls._get_project_dir(project_id), 'extracted_text.txt')
    
    @classmethod
    def create_project(cls, name: str = "Unnamed Project") -> Project:
        """
        åˆ›å»ºæ–°é¡¹ç›®
        
        Args:
            name: é¡¹ç›®åç§°
            
        Returns:
            æ–°åˆ›å»ºçš„Projectå¯¹è±¡
        """
        cls._ensure_projects_dir()
        
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        project = Project(
            project_id=project_id,
            name=name,
            status=ProjectStatus.CREATED,
            created_at=now,
            updated_at=now
        )
        
        # åˆ›å»ºé¡¹ç›®ç›®å½•ç»“æž„
        project_dir = cls._get_project_dir(project_id)
        files_dir = cls._get_project_files_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(files_dir, exist_ok=True)
        
        # ä¿å­˜é¡¹ç›®å…ƒæ•°æ®
        cls.save_project(project)
        
        return project
    
    @classmethod
    def save_project(cls, project: Project) -> None:
        """ä¿å­˜é¡¹ç›®å…ƒæ•°æ®"""
        project.updated_at = datetime.now().isoformat()
        meta_path = cls._get_project_meta_path(project.project_id)
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def get_project(cls, project_id: str) -> Optional[Project]:
        """
        èŽ·å–é¡¹ç›®
        
        Args:
            project_id: é¡¹ç›®ID
            
        Returns:
            Projectå¯¹è±¡ï¼Œå¦‚æžœä¸å­˜åœ¨è¿”å›žNone
        """
        meta_path = cls._get_project_meta_path(project_id)
        
        if not os.path.exists(meta_path):
            return None
        
        with open(meta_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        return Project.from_dict(data)
    
    @classmethod
    def list_projects(cls, limit: int = 50) -> List[Project]:
        """
        åˆ—å‡ºæ‰€æœ‰é¡¹ç›®
        
        Args:
            limit: è¿”å›žæ•°é‡é™åˆ¶
            
        Returns:
            é¡¹ç›®åˆ—è¡¨ï¼ŒæŒ‰åˆ›å»ºæ—¶é—´å€’åº
        """
        cls._ensure_projects_dir()
        
        projects = []
        for project_id in os.listdir(cls.PROJECTS_DIR):
            project = cls.get_project(project_id)
            if project:
                projects.append(project)
        
        # æŒ‰åˆ›å»ºæ—¶é—´å€’åºæŽ’åº
        projects.sort(key=lambda p: p.created_at, reverse=True)
        
        return projects[:limit]
    
    @classmethod
    def delete_project(cls, project_id: str) -> bool:
        """
        åˆ é™¤é¡¹ç›®åŠå…¶æ‰€æœ‰æ–‡ä»¶
        
        Args:
            project_id: é¡¹ç›®ID
            
        Returns:
            æ˜¯å¦åˆ é™¤æˆåŠŸ
        """
        project_dir = cls._get_project_dir(project_id)
        
        if not os.path.exists(project_dir):
            return False
        
        shutil.rmtree(project_dir)
        return True
    
    @classmethod
    def save_file_to_project(cls, project_id: str, file_storage, original_filename: str) -> Dict[str, str]:
        """
        ä¿å­˜ä¸Šä¼ çš„æ–‡ä»¶åˆ°é¡¹ç›®ç›®å½•
        
        Args:
            project_id: é¡¹ç›®ID
            file_storage: Flaskçš„FileStorageå¯¹è±¡
            original_filename: åŽŸå§‹æ–‡ä»¶å
            
        Returns:
            æ–‡ä»¶ä¿¡æ¯å­—å…¸ {filename, path, size}
        """
        files_dir = cls._get_project_files_dir(project_id)
        os.makedirs(files_dir, exist_ok=True)
        
        # ç”Ÿæˆå®‰å…¨çš„æ–‡ä»¶å
        ext = os.path.splitext(original_filename)[1].lower()
        safe_filename = f"{uuid.uuid4().hex[:8]}{ext}"
        file_path = os.path.join(files_dir, safe_filename)
        
        # ä¿å­˜æ–‡ä»¶
        file_storage.save(file_path)
        
        # èŽ·å–æ–‡ä»¶å¤§å°
        file_size = os.path.getsize(file_path)
        
        return {
            "original_filename": original_filename,
            "saved_filename": safe_filename,
            "path": file_path,
            "size": file_size
        }
    
    @classmethod
    def save_extracted_text(cls, project_id: str, text: str) -> None:
        """ä¿å­˜æå–çš„æ–‡æœ¬"""
        text_path = cls._get_project_text_path(project_id)
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
    
    @classmethod
    def get_extracted_text(cls, project_id: str) -> Optional[str]:
        """èŽ·å–æå–çš„æ–‡æœ¬"""
        text_path = cls._get_project_text_path(project_id)
        
        if not os.path.exists(text_path):
            return None
        
        with open(text_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @classmethod
    def get_project_files(cls, project_id: str) -> List[str]:
        """èŽ·å–é¡¹ç›®çš„æ‰€æœ‰æ–‡ä»¶è·¯å¾„"""
        files_dir = cls._get_project_files_dir(project_id)
        
        if not os.path.exists(files_dir):
            return []
        
        return [
            os.path.join(files_dir, f) 
            for f in os.listdir(files_dir) 
            if os.path.isfile(os.path.join(files_dir, f))
        ]

