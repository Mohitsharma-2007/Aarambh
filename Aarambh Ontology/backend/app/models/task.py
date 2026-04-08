"""
ä»»åŠ¡çŠ¶æ€ç®¡ç†
ç”¨äºŽè·Ÿè¸ªé•¿æ—¶é—´è¿è¡Œçš„ä»»åŠ¡ï¼ˆå¦‚å›¾è°±æž„å»ºï¼‰
"""

import uuid
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class TaskStatus(str, Enum):
    """ä»»åŠ¡çŠ¶æ€æžšä¸¾"""
    PENDING = "pending"          # ç­‰å¾…ä¸­
    PROCESSING = "processing"    # å¤„ç†ä¸­
    COMPLETED = "completed"      # å·²å®Œæˆ
    FAILED = "failed"            # å¤±è´¥


@dataclass
class Task:
    """ä»»åŠ¡æ•°æ®ç±»"""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    progress: int = 0              # æ€»è¿›åº¦ç™¾åˆ†æ¯” 0-100
    message: str = ""              # çŠ¶æ€æ¶ˆæ¯
    result: Optional[Dict] = None  # ä»»åŠ¡ç»“æžœ
    error: Optional[str] = None    # é”™è¯¯ä¿¡æ¯
    metadata: Dict = field(default_factory=dict)  # é¢å¤–å…ƒæ•°æ®
    progress_detail: Dict = field(default_factory=dict)  # è¯¦ç»†è¿›åº¦ä¿¡æ¯
    
    def to_dict(self) -> Dict[str, Any]:
        """è½¬æ¢ä¸ºå­—å…¸"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "progress": self.progress,
            "message": self.message,
            "progress_detail": self.progress_detail,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class TaskManager:
    """
    ä»»åŠ¡ç®¡ç†å™¨
    çº¿ç¨‹å®‰å…¨çš„ä»»åŠ¡çŠ¶æ€ç®¡ç†
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """å•ä¾‹æ¨¡å¼"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, Task] = {}
                    cls._instance._task_lock = threading.Lock()
        return cls._instance
    
    def create_task(self, task_type: str, metadata: Optional[Dict] = None) -> str:
        """
        åˆ›å»ºæ–°ä»»åŠ¡
        
        Args:
            task_type: ä»»åŠ¡ç±»åž‹
            metadata: é¢å¤–å…ƒæ•°æ®
            
        Returns:
            ä»»åŠ¡ID
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
        
        with self._task_lock:
            self._tasks[task_id] = task
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """èŽ·å–ä»»åŠ¡"""
        with self._task_lock:
            return self._tasks.get(task_id)
    
    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        progress_detail: Optional[Dict] = None
    ):
        """
        æ›´æ–°ä»»åŠ¡çŠ¶æ€
        
        Args:
            task_id: ä»»åŠ¡ID
            status: æ–°çŠ¶æ€
            progress: è¿›åº¦
            message: æ¶ˆæ¯
            result: ç»“æžœ
            error: é”™è¯¯ä¿¡æ¯
            progress_detail: è¯¦ç»†è¿›åº¦ä¿¡æ¯
        """
        with self._task_lock:
            task = self._tasks.get(task_id)
            if task:
                task.updated_at = datetime.now()
                if status is not None:
                    task.status = status
                if progress is not None:
                    task.progress = progress
                if message is not None:
                    task.message = message
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
                if progress_detail is not None:
                    task.progress_detail = progress_detail
    
    def complete_task(self, task_id: str, result: Dict):
        """æ ‡è®°ä»»åŠ¡å®Œæˆ"""
        self.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            message="ä»»åŠ¡å®Œæˆ",
            result=result
        )
    
    def fail_task(self, task_id: str, error: str):
        """æ ‡è®°ä»»åŠ¡å¤±è´¥"""
        self.update_task(
            task_id,
            status=TaskStatus.FAILED,
            message="ä»»åŠ¡å¤±è´¥",
            error=error
        )
    
    def list_tasks(self, task_type: Optional[str] = None) -> list:
        """åˆ—å‡ºä»»åŠ¡"""
        with self._task_lock:
            tasks = list(self._tasks.values())
            if task_type:
                tasks = [t for t in tasks if t.task_type == task_type]
            return [t.to_dict() for t in sorted(tasks, key=lambda x: x.created_at, reverse=True)]
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """æ¸…ç†æ—§ä»»åŠ¡"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        with self._task_lock:
            old_ids = [
                tid for tid, task in self._tasks.items()
                if task.created_at < cutoff and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            ]
            for tid in old_ids:
                del self._tasks[tid]

