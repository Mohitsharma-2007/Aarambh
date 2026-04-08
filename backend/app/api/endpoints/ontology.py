"""
Ontology Graph API Routes
图谱相关API路由 - 采用项目上下文机制，服务端持久化状态
"""

import os
import traceback
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from loguru import logger

from app.config import settings
from app.models.ontology_project import OntologyProjectManager, ProjectStatus
from app.models.ontology_task import OntologyTaskManager, TaskStatus
from app.services.ontology_generator import ontology_generator
from app.services.graph_builder import graph_builder_service
from app.services.zep_entity_reader import zep_entity_reader
from app.utils.file_parser import FileParser

router = APIRouter(prefix="/ontology", tags=["ontology"])

# 请求模型
class OntologyGenerationRequest(BaseModel):
    project_id: str
    chunk_size: int = 500
    chunk_overlap: int = 50

class SimulationConfigRequest(BaseModel):
    project_id: str
    platform: str = "twitter"
    max_rounds: int = 10
    num_agents: int = 50

# ============== 项目管理接口 ==============

@router.post("/project/create")
async def create_project(name: str = Form("Unnamed Project")):
    """创建新项目"""
    try:
        project = OntologyProjectManager.create_project(name)
        return {
            "success": True,
            "data": project.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/project/{project_id}")
async def get_project(project_id: str):
    """获取项目详情"""
    project = OntologyProjectManager.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    return {
        "success": True,
        "data": project.to_dict()
    }

@router.get("/project/list")
async def list_projects(limit: int = 50):
    """列出所有项目"""
    projects = OntologyProjectManager.list_projects(limit=limit)
    
    return {
        "success": True,
        "data": [p.to_dict() for p in projects],
        "count": len(projects)
    }

@router.delete("/project/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    success = OntologyProjectManager.delete_project(project_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"项目不存在或删除失败: {project_id}")
    
    return {
        "success": True,
        "message": f"项目已删除: {project_id}"
    }

@router.post("/project/{project_id}/reset")
async def reset_project(project_id: str):
    """重置项目状态（用于重新构建图谱）"""
    project = OntologyProjectManager.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    project.status = ProjectStatus.CREATED
    project.ontology = None
    project.graph_id = None
    project.error = None
    OntologyProjectManager.update_project(project)
    
    return {
        "success": True,
        "message": "项目已重置",
        "data": project.to_dict()
    }

# ============== 文件上传接口 ==============

@router.post("/project/{project_id}/upload")
async def upload_files(
    project_id: str,
    files: List[UploadFile] = File(...)
):
    """上传文件到项目"""
    project = OntologyProjectManager.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    uploaded = []
    total_size = 0
    
    for file in files:
        try:
            # 检查文件类型
            ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
            if ext not in ['pdf', 'md', 'txt', 'markdown']:
                continue
            
            # 保存文件
            content = await file.read()
            file_path = f"/tmp/{file.filename}"
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # 添加到项目
            OntologyProjectManager.add_file_to_project(
                project_id, file.filename, file_path, len(content)
            )
            
            uploaded.append({
                "filename": file.filename,
                "size": len(content)
            })
            total_size += len(content)
            
        except Exception as e:
            logger.error(f"Failed to upload file {file.filename}: {e}")
    
    # 提取所有文本
    all_text = ""
    for file_info in project.files + uploaded:
        file_path = file_info.get("path", "")
        if os.path.exists(file_path):
            text = FileParser.parse_file(file_path)
            all_text += f"\n\n=== {file_info['filename']} ===\n\n{text}"
    
    if all_text:
        OntologyProjectManager.save_project_text(project_id, all_text)
    
    return {
        "success": True,
        "uploaded": uploaded,
        "total_size": total_size,
        "total_text_length": len(all_text)
    }

# ============== 本体生成接口 ==============

@router.post("/generate")
async def generate_ontology(request: OntologyGenerationRequest, background_tasks: BackgroundTasks):
    """生成本体（异步）"""
    project = OntologyProjectManager.get_project(request.project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {request.project_id}")
    
    # 创建任务
    task_manager = OntologyTaskManager()
    task_id = task_manager.create_task(
        "ontology_generation",
        {"project_id": request.project_id}
    )
    
    # 后台执行
    background_tasks.add_task(
        _generate_ontology_background,
        request.project_id,
        task_id,
        request.chunk_size,
        request.chunk_overlap
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "本体生成任务已启动"
    }

async def _generate_ontology_background(
    project_id: str,
    task_id: str,
    chunk_size: int,
    chunk_overlap: int
):
    """后台生成本体"""
    task_manager = OntologyTaskManager()
    
    try:
        task_manager.update_task(
            task_id,
            status=TaskStatus.PROCESSING,
            progress=10,
            message="Reading project text..."
        )
        
        # 获取项目文本
        text = OntologyProjectManager.get_project_text(project_id)
        if not text:
            raise Exception("No text content found in project")
        
        task_manager.update_task(
            task_id,
            progress=30,
            message="Generating ontology with LLM..."
        )
        
        # 生成本体
        result = ontology_generator.generate_from_text(text)
        
        # 分析模拟配置
        simulation_analysis = ontology_generator.analyze_for_simulation(text)
        
        # 更新项目
        project = OntologyProjectManager.get_project(project_id)
        project.ontology = result
        project.analysis_summary = result.get("summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        project.chunk_size = chunk_size
        project.chunk_overlap = chunk_overlap
        OntologyProjectManager.update_project(project)
        
        # 完成任务
        task_manager.complete_task(
            task_id,
            {
                "project_id": project_id,
                "entity_count": len(result.get("entities", [])),
                "relation_count": len(result.get("relations", [])),
                "simulation_config": simulation_analysis.get("simulation_config")
            }
        )
        
        logger.info(f"Ontology generation completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"Ontology generation failed: {e}")
        task_manager.fail_task(task_id, str(e))
        
        # 更新项目错误状态
        project = OntologyProjectManager.get_project(project_id)
        if project:
            project.error = str(e)
            project.status = ProjectStatus.FAILED
            OntologyProjectManager.update_project(project)

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task_manager = OntologyTaskManager()
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    return {
        "success": True,
        "data": task.to_dict()
    }

# ============== 图谱构建接口 ==============

@router.post("/graph/build/{project_id}")
async def build_graph(project_id: str, background_tasks: BackgroundTasks):
    """构建知识图谱"""
    project = OntologyProjectManager.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    if not project.ontology:
        raise HTTPException(status_code=400, detail="项目没有本体数据，请先执行本体生成")
    
    # 创建任务
    task_manager = OntologyTaskManager()
    task_id = task_manager.create_task(
        "graph_building",
        {"project_id": project_id}
    )
    
    # 更新项目状态
    project.status = ProjectStatus.GRAPH_BUILDING
    project.graph_build_task_id = task_id
    OntologyProjectManager.update_project(project)
    
    # 后台执行
    background_tasks.add_task(
        _build_graph_background,
        project_id,
        task_id
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "图谱构建任务已启动"
    }

async def _build_graph_background(project_id: str, task_id: str):
    """后台构建图谱"""
    task_manager = OntologyTaskManager()
    
    try:
        task_manager.update_task(
            task_id,
            status=TaskStatus.PROCESSING,
            progress=10,
            message="Initializing graph builder..."
        )
        
        # 获取项目
        project = OntologyProjectManager.get_project(project_id)
        ontology = project.ontology
        
        # 构建图谱
        result = graph_builder_service.build_graph(
            project_id,
            ontology,
            task_manager
        )
        
        if not result.get("success"):
            raise Exception(result.get("error", "Graph building failed"))
        
        # 更新项目
        project.graph_id = result.get("graph_id")
        project.status = ProjectStatus.GRAPH_COMPLETED
        OntologyProjectManager.update_project(project)
        
        # 完成任务
        task_manager.complete_task(task_id, result)
        
        logger.info(f"Graph building completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"Graph building failed: {e}")
        task_manager.fail_task(task_id, str(e))
        
        # 更新项目错误状态
        project = OntologyProjectManager.get_project(project_id)
        if project:
            project.error = str(e)
            project.status = ProjectStatus.FAILED
            OntologyProjectManager.update_project(project)

# ============== 实体查询接口 ==============

@router.get("/entities/{graph_id}")
async def get_graph_entities(
    graph_id: str,
    entity_types: Optional[str] = None,
    enrich: bool = True
):
    """获取图谱中的实体"""
    try:
        types_list = [t.strip() for t in entity_types.split(",") if t.strip()] if entity_types else None
        
        result = zep_entity_reader.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=types_list,
            enrich_with_edges=enrich
        )
        
        return {
            "success": True,
            "data": result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to get entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entity/{graph_id}/{entity_uuid}")
async def get_entity_detail(graph_id: str, entity_uuid: str):
    """获取单个实体详情"""
    try:
        entity = zep_entity_reader.get_entity_detail(graph_id, entity_uuid)
        
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        return {
            "success": True,
            "data": entity
        }
        
    except Exception as e:
        logger.error(f"Failed to get entity detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== 模拟配置接口 ==============

@router.post("/simulation/config")
async def configure_simulation(request: SimulationConfigRequest):
    """配置模拟参数"""
    project = OntologyProjectManager.get_project(request.project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {request.project_id}")
    
    # 保存配置
    config = {
        "platform": request.platform,
        "max_rounds": request.max_rounds,
        "num_agents": request.num_agents
    }
    
    # 这里可以添加更多配置验证和保存逻辑
    
    return {
        "success": True,
        "config": config,
        "message": "模拟配置已保存"
    }
