"""
æ–‡ä»¶è§£æžå·¥å…·
æ”¯æŒPDFã€Markdownã€TXTæ–‡ä»¶çš„æ–‡æœ¬æå–
"""

import os
from pathlib import Path
from typing import List, Optional


def _read_text_with_fallback(file_path: str) -> str:
    """
    è¯»å–æ–‡æœ¬æ–‡ä»¶ï¼ŒUTF-8å¤±è´¥æ—¶è‡ªåŠ¨æŽ¢æµ‹ç¼–ç ã€‚
    
    é‡‡ç”¨å¤šçº§å›žé€€ç­–ç•¥ï¼š
    1. é¦–å…ˆå°è¯• UTF-8 è§£ç 
    2. ä½¿ç”¨ charset_normalizer æ£€æµ‹ç¼–ç 
    3. å›žé€€åˆ° chardet æ£€æµ‹ç¼–ç 
    4. æœ€ç»ˆä½¿ç”¨ UTF-8 + errors='replace' å…œåº•
    
    Args:
        file_path: æ–‡ä»¶è·¯å¾„
        
    Returns:
        è§£ç åŽçš„æ–‡æœ¬å†…å®¹
    """
    data = Path(file_path).read_bytes()
    
    # é¦–å…ˆå°è¯• UTF-8
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        pass
    
    # å°è¯•ä½¿ç”¨ charset_normalizer æ£€æµ‹ç¼–ç 
    encoding = None
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best and best.encoding:
            encoding = best.encoding
    except Exception:
        pass
    
    # å›žé€€åˆ° chardet
    if not encoding:
        try:
            import chardet
            result = chardet.detect(data)
            encoding = result.get('encoding') if result else None
        except Exception:
            pass
    
    # æœ€ç»ˆå…œåº•ï¼šä½¿ç”¨ UTF-8 + replace
    if not encoding:
        encoding = 'utf-8'
    
    return data.decode(encoding, errors='replace')


class FileParser:
    """æ–‡ä»¶è§£æžå™¨"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.markdown', '.txt'}
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        ä»Žæ–‡ä»¶ä¸­æå–æ–‡æœ¬
        
        Args:
            file_path: æ–‡ä»¶è·¯å¾„
            
        Returns:
            æå–çš„æ–‡æœ¬å†…å®¹
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"æ–‡ä»¶ä¸å­˜åœ¨: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"ä¸æ”¯æŒçš„æ–‡ä»¶æ ¼å¼: {suffix}")
        
        if suffix == '.pdf':
            return cls._extract_from_pdf(file_path)
        elif suffix in {'.md', '.markdown'}:
            return cls._extract_from_md(file_path)
        elif suffix == '.txt':
            return cls._extract_from_txt(file_path)
        
        raise ValueError(f"æ— æ³•å¤„ç†çš„æ–‡ä»¶æ ¼å¼: {suffix}")
    
    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """ä»ŽPDFæå–æ–‡æœ¬"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("éœ€è¦å®‰è£…PyMuPDF: pip install PyMuPDF")
        
        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def _extract_from_md(file_path: str) -> str:
        """ä»ŽMarkdownæå–æ–‡æœ¬ï¼Œæ”¯æŒè‡ªåŠ¨ç¼–ç æ£€æµ‹"""
        return _read_text_with_fallback(file_path)
    
    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """ä»ŽTXTæå–æ–‡æœ¬ï¼Œæ”¯æŒè‡ªåŠ¨ç¼–ç æ£€æµ‹"""
        return _read_text_with_fallback(file_path)
    
    @classmethod
    def extract_from_multiple(cls, file_paths: List[str]) -> str:
        """
        ä»Žå¤šä¸ªæ–‡ä»¶æå–æ–‡æœ¬å¹¶åˆå¹¶
        
        Args:
            file_paths: æ–‡ä»¶è·¯å¾„åˆ—è¡¨
            
        Returns:
            åˆå¹¶åŽçš„æ–‡æœ¬
        """
        all_texts = []
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                text = cls.extract_text(file_path)
                filename = Path(file_path).name
                all_texts.append(f"=== æ–‡æ¡£ {i}: {filename} ===\n{text}")
            except Exception as e:
                all_texts.append(f"=== æ–‡æ¡£ {i}: {file_path} (æå–å¤±è´¥: {str(e)}) ===")
        
        return "\n\n".join(all_texts)


def split_text_into_chunks(
    text: str, 
    chunk_size: int = 500, 
    overlap: int = 50
) -> List[str]:
    """
    å°†æ–‡æœ¬åˆ†å‰²æˆå°å—
    
    Args:
        text: åŽŸå§‹æ–‡æœ¬
        chunk_size: æ¯å—çš„å­—ç¬¦æ•°
        overlap: é‡å å­—ç¬¦æ•°
        
    Returns:
        æ–‡æœ¬å—åˆ—è¡¨
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # å°è¯•åœ¨å¥å­è¾¹ç•Œå¤„åˆ†å‰²
        if end < len(text):
            # æŸ¥æ‰¾æœ€è¿‘çš„å¥å­ç»“æŸç¬¦
            for sep in ['ã€‚', 'ï¼', 'ï¼Ÿ', '.\n', '!\n', '?\n', '\n\n', '. ', '! ', '? ']:
                last_sep = text[start:end].rfind(sep)
                if last_sep != -1 and last_sep > chunk_size * 0.3:
                    end = start + last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # ä¸‹ä¸€ä¸ªå—ä»Žé‡å ä½ç½®å¼€å§‹
        start = end - overlap if end < len(text) else len(text)
    
    return chunks

