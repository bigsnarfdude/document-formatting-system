import json
import re
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

try:
    from .models import (
        DocumentElement, 
        FormattingRule, 
        RuleGenerationResponse, 
        RuleCondition, 
        RuleAction,
        RuleOperator
    )
except ImportError:
    from models import (
        DocumentElement, 
        FormattingRule, 
        RuleGenerationResponse, 
        RuleCondition, 
        RuleAction,
        RuleOperator
    )

class RuleEngine:
    """Handles rule generation using templates and LLM fallback"""
    
    def __init__(self):
        self.rule_templates = self._load_rule_templates()
        self.llm_client = None  # Will be initialized if needed
    
    async def generate_rule(self, element: DocumentElement, intent: str) -> RuleGenerationResponse:
        """Generate a formatting rule from user intent"""
        
        # First, try template matching
        template_result = self._try_template_matching(element, intent)
        if template_result:
            return template_result
        
        # Fallback to LLM
        return await self._generate_with_llm(element, intent)
    
    def _try_template_matching(self, element: DocumentElement, intent: str) -> Optional[RuleGenerationResponse]:
        """Try to match intent against rule templates"""
        
        intent_lower = intent.lower()
        
        # Heading templates
        if any(word in intent_lower for word in ['heading', 'title', 'header']):
            return self._create_heading_rule(element, intent_lower)
        
        # List templates
        if any(word in intent_lower for word in ['list', 'bullet', 'numbered']):
            return self._create_list_rule(element, intent_lower)
        
        # Body text templates
        if any(word in intent_lower for word in ['body', 'paragraph', 'text', 'content']):
            return self._create_body_text_rule(element, intent_lower)
        
        # Filter templates
        if any(word in intent_lower for word in ['remove', 'filter', 'delete', 'hide']):
            return self._create_filter_rule(element, intent_lower)
        
        return None
    
    def _create_heading_rule(self, element: DocumentElement, intent: str) -> RuleGenerationResponse:
        """Create a heading rule from template"""
        
        # Determine heading level
        level = 1
        if 'level 2' in intent or 'heading 2' in intent:
            level = 2
        elif 'level 3' in intent or 'heading 3' in intent:
            level = 3
        elif 'level 4' in intent or 'heading 4' in intent:
            level = 4
        elif 'level 5' in intent or 'heading 5' in intent:
            level = 5
        
        # Build conditions based on element properties
        conditions = []
        
        # All caps text often indicates headings
        if element.properties.text_case == "UPPER":
            conditions.append(RuleCondition(
                property="text_case",
                operator=RuleOperator.EQUALS,
                value="UPPER"
            ))
        
        # Bold text
        if element.properties.is_bold:
            conditions.append(RuleCondition(
                property="is_bold",
                operator=RuleOperator.EQUALS,
                value=True
            ))
        
        # Font size
        if element.properties.font_size > 12:
            conditions.append(RuleCondition(
                property="font_size",
                operator=RuleOperator.GREATER_THAN,
                value=12
            ))
        
        # Standalone text (short)
        if element.properties.is_standalone:
            conditions.append(RuleCondition(
                property="is_standalone",
                operator=RuleOperator.EQUALS,
                value=True
            ))
        
        # Policy codes
        if element.properties.contains_code:
            conditions.append(RuleCondition(
                property="contains_code",
                operator=RuleOperator.EQUALS,
                value=True
            ))
        
        rule = FormattingRule(
            id=str(uuid.uuid4()),
            description=f"Classify text as Heading {level} based on formatting patterns",
            conditions=conditions,
            action=RuleAction(
                classify_as=f"Heading {level}",
                set_style={
                    "is_bold": True,
                    "font_size": 12 + (level * 2)
                }
            ),
            priority=200 - (level * 10),  # Higher level = higher priority
            created_at=datetime.now().isoformat()
        )
        
        return RuleGenerationResponse(
            rule=rule,
            type="success",
            message=f"Created Heading {level} rule based on text properties"
        )
    
    def _create_list_rule(self, element: DocumentElement, intent: str) -> RuleGenerationResponse:
        """Create a list rule from template"""
        
        conditions = []
        
        # Bullet point indicators
        if element.properties.starts_with_bullet:
            conditions.append(RuleCondition(
                property="starts_with_bullet",
                operator=RuleOperator.EQUALS,
                value=True
            ))
        
        # Numbered list indicators
        if element.properties.starts_with_number:
            conditions.append(RuleCondition(
                property="starts_with_number",
                operator=RuleOperator.EQUALS,
                value=True
            ))
        
        # If no obvious list markers, look for patterns
        if not conditions and any(marker in element.text[:10] for marker in ['•', '○', '●', '-']):
            conditions.append(RuleCondition(
                property="text",
                operator=RuleOperator.STARTS_WITH,
                value="•"
            ))
        
        rule = FormattingRule(
            id=str(uuid.uuid4()),
            description="Classify text as List Paragraph based on bullet/number patterns",
            conditions=conditions,
            action=RuleAction(
                classify_as="List Paragraph",
                set_style={
                    "margin_left": 20  # Indent list items
                }
            ),
            priority=150,
            created_at=datetime.now().isoformat()
        )
        
        return RuleGenerationResponse(
            rule=rule,
            type="success",
            message="Created List Paragraph rule based on bullet/number patterns"
        )
    
    def _create_body_text_rule(self, element: DocumentElement, intent: str) -> RuleGenerationResponse:
        """Create a body text rule from template"""
        
        conditions = []
        
        # Not bold, not all caps, reasonable length
        if not element.properties.is_bold:
            conditions.append(RuleCondition(
                property="is_bold",
                operator=RuleOperator.EQUALS,
                value=False
            ))
        
        if element.properties.text_case != "UPPER":
            conditions.append(RuleCondition(
                property="text_case",
                operator=RuleOperator.NOT_EQUALS,
                value="UPPER"
            ))
        
        if element.properties.word_count > 5:
            conditions.append(RuleCondition(
                property="word_count",
                operator=RuleOperator.GREATER_THAN,
                value=5
            ))
        
        rule = FormattingRule(
            id=str(uuid.uuid4()),
            description="Classify explanatory text as Body Text",
            conditions=conditions,
            action=RuleAction(
                classify_as="Body Text",
                set_style={
                    "font_size": 12,
                    "is_bold": False
                }
            ),
            priority=50,  # Lower priority than headings
            created_at=datetime.now().isoformat()
        )
        
        return RuleGenerationResponse(
            rule=rule,
            type="success",
            message="Created Body Text rule for explanatory content"
        )
    
    def _create_filter_rule(self, element: DocumentElement, intent: str) -> RuleGenerationResponse:
        """Create a filter rule from template"""
        
        conditions = []
        
        # Common filter patterns
        if "page" in element.text.lower():
            conditions.append(RuleCondition(
                property="text",
                operator=RuleOperator.CONTAINS,
                value="page"
            ))
        
        if "intentionally" in element.text.lower():
            conditions.append(RuleCondition(
                property="text",
                operator=RuleOperator.CONTAINS,
                value="intentionally left blank"
            ))
        
        rule = FormattingRule(
            id=str(uuid.uuid4()),
            description="Filter out unwanted content",
            conditions=conditions,
            action=RuleAction(
                classify_as="FILTER",
                set_style={}
            ),
            priority=300,  # Highest priority
            created_at=datetime.now().isoformat()
        )
        
        return RuleGenerationResponse(
            rule=rule,
            type="success",
            message="Created filter rule to remove unwanted content"
        )
    
    async def _generate_with_llm(self, element: DocumentElement, intent: str) -> RuleGenerationResponse:
        """Generate rule using LLM when templates don't match"""
        
        try:
            # Initialize LLM client if not already done
            if not self.llm_client:
                self.llm_client = self._initialize_llm_client()
            
            # Construct prompt
            prompt = self._build_llm_prompt(element, intent)
            
            # Call LLM
            response = await self._call_llm(prompt)
            
            # Parse and validate response
            rule_data = self._parse_llm_response(response)
            
            if rule_data:
                rule = FormattingRule(**rule_data)
                return RuleGenerationResponse(
                    rule=rule,
                    type="success",
                    message="Generated rule using AI analysis"
                )
            else:
                return RuleGenerationResponse(
                    type="clarification",
                    message="I need more information. Could you be more specific about how this should be formatted?"
                )
                
        except Exception as e:
            return RuleGenerationResponse(
                type="error",
                message=f"Unable to generate rule: {str(e)}"
            )
    
    def _initialize_llm_client(self):
        """Initialize Ollama client with Gemma 3 27B model"""
        try:
            import requests
            
            # Test if Ollama is running
            response = requests.get("http://localhost:11434/api/version", timeout=2)
            if response.status_code == 200:
                return {"type": "ollama", "host": "http://localhost:11434", "model": "gemma3:27b-it-qat"}
            else:
                return None
        except:
            return None
    
    def _build_llm_prompt(self, element: DocumentElement, intent: str) -> str:
        """Build prompt for LLM rule generation"""
        
        return f"""
You are a document formatting expert. Generate a JSON rule based on the user's intent.

ELEMENT TO FORMAT:
Text: "{element.text}"
Properties: {element.properties.dict()}

USER INTENT:
{intent}

RULE SCHEMA:
{{
  "id": "unique_id",
  "description": "human readable description",
  "conditions": [
    {{"property": "property_name", "operator": "equals|contains|greaterThan|etc", "value": "value"}}
  ],
  "action": {{
    "classify_as": "classification_label",
    "set_style": {{"property": "value"}}
  }},
  "priority": 100,
  "created_at": "timestamp"
}}

AVAILABLE PROPERTIES:
- font_name, font_size, is_bold, is_italic, is_underline
- text_case, alignment, rgb_color
- contains_code, is_date, is_email, is_phone, is_url
- starts_with_bullet, starts_with_number, is_standalone, word_count

AVAILABLE OPERATORS:
- equals, notEquals, contains, greaterThan, lessThan, startsWith, endsWith, matchesRegex

Generate ONLY the JSON rule, no additional text:
"""
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API"""
        if not self.llm_client:
            raise ValueError("LLM client not available. Please start Ollama with 'ollama serve'.")
        
        try:
            # Use Ollama API with Gemma 3 27B
            import requests
            import json
            
            payload = {
                "model": self.llm_client["model"],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            response = requests.post(
                f"{self.llm_client['host']}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise ValueError(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            raise ValueError(f"Ollama API call failed: {str(e)}")
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse and validate LLM response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return None
            
            json_str = json_match.group(0)
            rule_data = json.loads(json_str)
            
            # Add required fields if missing
            if "id" not in rule_data:
                rule_data["id"] = str(uuid.uuid4())
            if "created_at" not in rule_data:
                rule_data["created_at"] = datetime.now().isoformat()
            if "priority" not in rule_data:
                rule_data["priority"] = 100
            
            return rule_data
            
        except (json.JSONDecodeError, KeyError) as e:
            return None
    
    def _load_rule_templates(self) -> Dict[str, Any]:
        """Load rule templates from configuration"""
        # This would load from a config file in production
        return {
            "heading_patterns": [
                "heading", "title", "header", "section"
            ],
            "list_patterns": [
                "list", "bullet", "numbered", "item"
            ],
            "body_patterns": [
                "body", "paragraph", "text", "content"
            ],
            "filter_patterns": [
                "remove", "filter", "delete", "hide"
            ]
        }