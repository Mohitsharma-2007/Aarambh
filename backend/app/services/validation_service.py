"""Validation Service - ensures LLM outputs match expected schemas"""
import json
import re
from typing import Type, TypeVar, Optional, List, Dict, Any, Union
from pydantic import BaseModel, ValidationError
from loguru import logger

T = TypeVar("T", bound=BaseModel)

class ValidationService:
    """Validator for LLM outputs"""

    def parse_and_validate(self, text: str, model: Any) -> Optional[Any]:
        """Parse JSON from text and validate against a Pydantic model or type"""
        # 1. Extract JSON
        json_data = self._extract_json(text)
        if not json_data:
            return None

        # 2. Validate
        try:
            from pydantic import TypeAdapter
            adapter = TypeAdapter(model)
            return adapter.validate_python(json_data)
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[Union[dict, list]]:
        """Robust JSON extraction from LLM response"""
        if not text:
            return None
            
        # Try direct load
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try markdown code blocks
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            try:
                content = match.group(1).strip()
                return json.loads(content)
            except json.JSONDecodeError:
                pass

        # Try searching for first { or [ and last } or ]
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1:
            try:
                return json.loads(text[first_brace:last_brace+1])
            except json.JSONDecodeError:
                pass

        first_bracket = text.find('[')
        last_bracket = text.rfind(']')
        if first_bracket != -1 and last_bracket != -1:
            try:
                return json.loads(text[first_bracket:last_bracket+1])
            except json.JSONDecodeError:
                pass

        return None

# Singleton
validation_service = ValidationService()
