"""
åŠ¨ä½œæ—¥å¿—è®°å½•å™¨
ç”¨äºŽè®°å½•OASISæ¨¡æ‹Ÿä¸­æ¯ä¸ªAgentçš„åŠ¨ä½œï¼Œä¾›åŽç«¯ç›‘æŽ§ä½¿ç”¨

æ—¥å¿—ç»“æž„:
    sim_xxx/
    â”œâ”€â”€ twitter/
    â”‚   â””â”€â”€ actions.jsonl    # Twitter å¹³å°åŠ¨ä½œæ—¥å¿—
    â”œâ”€â”€ reddit/
    â”‚   â””â”€â”€ actions.jsonl    # Reddit å¹³å°åŠ¨ä½œæ—¥å¿—
    â”œâ”€â”€ simulation.log       # ä¸»æ¨¡æ‹Ÿè¿›ç¨‹æ—¥å¿—
    â””â”€â”€ run_state.json       # è¿è¡ŒçŠ¶æ€ï¼ˆAPI æŸ¥è¯¢ç”¨ï¼‰
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional


class PlatformActionLogger:
    """å•å¹³å°åŠ¨ä½œæ—¥å¿—è®°å½•å™¨"""
    
    def __init__(self, platform: str, base_dir: str):
        """
        åˆå§‹åŒ–æ—¥å¿—è®°å½•å™¨
        
        Args:
            platform: å¹³å°åç§° (twitter/reddit)
            base_dir: æ¨¡æ‹Ÿç›®å½•çš„åŸºç¡€è·¯å¾„
        """
        self.platform = platform
        self.base_dir = base_dir
        self.log_dir = os.path.join(base_dir, platform)
        self.log_path = os.path.join(self.log_dir, "actions.jsonl")
        self._ensure_dir()
    
    def _ensure_dir(self):
        """ç¡®ä¿ç›®å½•å­˜åœ¨"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    def log_action(
        self,
        round_num: int,
        agent_id: int,
        agent_name: str,
        action_type: str,
        action_args: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        success: bool = True
    ):
        """è®°å½•ä¸€ä¸ªåŠ¨ä½œ"""
        entry = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "action_type": action_type,
            "action_args": action_args or {},
            "result": result,
            "success": success,
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def log_round_start(self, round_num: int, simulated_hour: int):
        """è®°å½•è½®æ¬¡å¼€å§‹"""
        entry = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "event_type": "round_start",
            "simulated_hour": simulated_hour,
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def log_round_end(self, round_num: int, actions_count: int):
        """è®°å½•è½®æ¬¡ç»“æŸ"""
        entry = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "event_type": "round_end",
            "actions_count": actions_count,
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def log_simulation_start(self, config: Dict[str, Any]):
        """è®°å½•æ¨¡æ‹Ÿå¼€å§‹"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "simulation_start",
            "platform": self.platform,
            "total_rounds": config.get("time_config", {}).get("total_simulation_hours", 72) * 2,
            "agents_count": len(config.get("agent_configs", [])),
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def log_simulation_end(self, total_rounds: int, total_actions: int):
        """è®°å½•æ¨¡æ‹Ÿç»“æŸ"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "simulation_end",
            "platform": self.platform,
            "total_rounds": total_rounds,
            "total_actions": total_actions,
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


class SimulationLogManager:
    """
    æ¨¡æ‹Ÿæ—¥å¿—ç®¡ç†å™¨
    ç»Ÿä¸€ç®¡ç†æ‰€æœ‰æ—¥å¿—æ–‡ä»¶ï¼ŒæŒ‰å¹³å°åˆ†ç¦»
    """
    
    def __init__(self, simulation_dir: str):
        """
        åˆå§‹åŒ–æ—¥å¿—ç®¡ç†å™¨
        
        Args:
            simulation_dir: æ¨¡æ‹Ÿç›®å½•è·¯å¾„
        """
        self.simulation_dir = simulation_dir
        self.twitter_logger: Optional[PlatformActionLogger] = None
        self.reddit_logger: Optional[PlatformActionLogger] = None
        self._main_logger: Optional[logging.Logger] = None
        
        # è®¾ç½®ä¸»æ—¥å¿—
        self._setup_main_logger()
    
    def _setup_main_logger(self):
        """è®¾ç½®ä¸»æ¨¡æ‹Ÿæ—¥å¿—"""
        log_path = os.path.join(self.simulation_dir, "simulation.log")
        
        # åˆ›å»º logger
        self._main_logger = logging.getLogger(f"simulation.{os.path.basename(self.simulation_dir)}")
        self._main_logger.setLevel(logging.INFO)
        self._main_logger.handlers.clear()
        
        # æ–‡ä»¶å¤„ç†å™¨
        file_handler = logging.FileHandler(log_path, encoding='utf-8', mode='w')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self._main_logger.addHandler(file_handler)
        
        # æŽ§åˆ¶å°å¤„ç†å™¨
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(message)s',
            datefmt='%H:%M:%S'
        ))
        self._main_logger.addHandler(console_handler)
        
        self._main_logger.propagate = False
    
    def get_twitter_logger(self) -> PlatformActionLogger:
        """èŽ·å– Twitter å¹³å°æ—¥å¿—è®°å½•å™¨"""
        if self.twitter_logger is None:
            self.twitter_logger = PlatformActionLogger("twitter", self.simulation_dir)
        return self.twitter_logger
    
    def get_reddit_logger(self) -> PlatformActionLogger:
        """èŽ·å– Reddit å¹³å°æ—¥å¿—è®°å½•å™¨"""
        if self.reddit_logger is None:
            self.reddit_logger = PlatformActionLogger("reddit", self.simulation_dir)
        return self.reddit_logger
    
    def log(self, message: str, level: str = "info"):
        """è®°å½•ä¸»æ—¥å¿—"""
        if self._main_logger:
            getattr(self._main_logger, level.lower(), self._main_logger.info)(message)
    
    def info(self, message: str):
        self.log(message, "info")
    
    def warning(self, message: str):
        self.log(message, "warning")
    
    def error(self, message: str):
        self.log(message, "error")
    
    def debug(self, message: str):
        self.log(message, "debug")


# ============ å…¼å®¹æ—§æŽ¥å£ ============

class ActionLogger:
    """
    åŠ¨ä½œæ—¥å¿—è®°å½•å™¨ï¼ˆå…¼å®¹æ—§æŽ¥å£ï¼‰
    å»ºè®®ä½¿ç”¨ SimulationLogManager ä»£æ›¿
    """
    
    def __init__(self, log_path: str):
        self.log_path = log_path
        self._ensure_dir()
    
    def _ensure_dir(self):
        log_dir = os.path.dirname(self.log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    def log_action(
        self,
        round_num: int,
        platform: str,
        agent_id: int,
        agent_name: str,
        action_type: str,
        action_args: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        success: bool = True
    ):
        entry = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "action_type": action_type,
            "action_args": action_args or {},
            "result": result,
            "success": success,
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def log_round_start(self, round_num: int, simulated_hour: int, platform: str):
        entry = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "event_type": "round_start",
            "simulated_hour": simulated_hour,
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def log_round_end(self, round_num: int, actions_count: int, platform: str):
        entry = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "event_type": "round_end",
            "actions_count": actions_count,
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def log_simulation_start(self, platform: str, config: Dict[str, Any]):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "event_type": "simulation_start",
            "total_rounds": config.get("time_config", {}).get("total_simulation_hours", 72) * 2,
            "agents_count": len(config.get("agent_configs", [])),
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def log_simulation_end(self, platform: str, total_rounds: int, total_actions: int):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "event_type": "simulation_end",
            "total_rounds": total_rounds,
            "total_actions": total_actions,
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


# å…¨å±€æ—¥å¿—å®žä¾‹ï¼ˆå…¼å®¹æ—§æŽ¥å£ï¼‰
_global_logger: Optional[ActionLogger] = None


def get_logger(log_path: Optional[str] = None) -> ActionLogger:
    """èŽ·å–å…¨å±€æ—¥å¿—å®žä¾‹ï¼ˆå…¼å®¹æ—§æŽ¥å£ï¼‰"""
    global _global_logger
    
    if log_path:
        _global_logger = ActionLogger(log_path)
    
    if _global_logger is None:
        _global_logger = ActionLogger("actions.jsonl")
    
    return _global_logger
