"""
æ–‡æœ¬å¤„ç†æœåŠ¡
"""

from typing import List, Optional
from ..utils.file_parser import FileParser, split_text_into_chunks


class TextProcessor:
    """æ–‡æœ¬å¤„ç†å™¨"""
    
    @staticmethod
    def extract_from_files(file_paths: List[str]) -> str:
        """ä»Žå¤šä¸ªæ–‡ä»¶æå–æ–‡æœ¬"""
        return FileParser.extract_from_multiple(file_paths)
    
    @staticmethod
    def split_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        åˆ†å‰²æ–‡æœ¬
        
        Args:
            text: åŽŸå§‹æ–‡æœ¬
            chunk_size: å—å¤§å°
            overlap: é‡å å¤§å°
            
        Returns:
            æ–‡æœ¬å—åˆ—è¡¨
        """
        return split_text_into_chunks(text, chunk_size, overlap)
    
    @staticmethod
    def preprocess_text(text: str) -> str:
        """
        é¢„å¤„ç†æ–‡æœ¬
        - ç§»é™¤å¤šä½™ç©ºç™½
        - æ ‡å‡†åŒ–æ¢è¡Œ
        
        Args:
            text: åŽŸå§‹æ–‡æœ¬
            
        Returns:
            å¤„ç†åŽçš„æ–‡æœ¬
        """
        import re
        
        # æ ‡å‡†åŒ–æ¢è¡Œ
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # ç§»é™¤è¿žç»­ç©ºè¡Œï¼ˆä¿ç•™æœ€å¤šä¸¤ä¸ªæ¢è¡Œï¼‰
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # ç§»é™¤è¡Œé¦–è¡Œå°¾ç©ºç™½
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    @staticmethod
    def get_text_stats(text: str) -> dict:
        """èŽ·å–æ–‡æœ¬ç»Ÿè®¡ä¿¡æ¯"""
        return {
            "total_chars": len(text),
            "total_lines": text.count('\n') + 1,
            "total_words": len(text.split()),
        }

