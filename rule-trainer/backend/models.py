from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum

class TextCase(str, Enum):
    UPPER = "UPPER"
    LOWER = "lower"
    TITLE = "Title"
    SENTENCE = "Sentence"
    MIXED = "Mixed"

class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"

class ElementProperties(BaseModel):
    """Style properties extracted from document elements"""
    font_name: str = Field(default="Arial")
    font_size: float = Field(default=12.0)
    is_bold: bool = Field(default=False)
    is_italic: bool = Field(default=False)
    is_underline: bool = Field(default=False)
    text_case: TextCase = Field(default=TextCase.MIXED)
    alignment: Alignment = Field(default=Alignment.LEFT)
    rgb_color: List[int] = Field(default=[0, 0, 0])  # [R, G, B]
    
    # Semantic properties (added by property enricher)
    contains_code: bool = Field(default=False)
    is_date: bool = Field(default=False)
    is_email: bool = Field(default=False)
    is_phone: bool = Field(default=False)
    is_url: bool = Field(default=False)
    starts_with_bullet: bool = Field(default=False)
    starts_with_number: bool = Field(default=False)
    is_standalone: bool = Field(default=False)
    word_count: int = Field(default=0)

class DocumentElement(BaseModel):
    """A single element (paragraph/block) in a document"""
    id: str = Field(description="Unique identifier for this element")
    text: str = Field(description="The text content of this element")
    properties: ElementProperties = Field(description="Style and semantic properties")
    page_number: int = Field(default=1)
    position: Dict[str, float] = Field(default_factory=dict)  # x, y, width, height

class DocumentContent(BaseModel):
    """Complete document structure"""
    title: str = Field(default="Untitled Document")
    elements: List[DocumentElement] = Field(description="All document elements")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RuleOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "notEquals"
    CONTAINS = "contains"
    GREATER_THAN = "greaterThan"
    LESS_THAN = "lessThan"
    STARTS_WITH = "startsWith"
    ENDS_WITH = "endsWith"
    MATCHES_REGEX = "matchesRegex"

class RuleCondition(BaseModel):
    """A single condition in a formatting rule"""
    property: str = Field(description="Property name to check")
    operator: RuleOperator = Field(description="Comparison operator")
    value: Union[str, int, float, bool] = Field(description="Value to compare against")

class RuleAction(BaseModel):
    """Action to take when rule conditions are met"""
    classify_as: Optional[str] = Field(default=None, description="Classification label")
    set_style: Optional[Dict[str, Any]] = Field(default=None, description="Style properties to set")

class FormattingRule(BaseModel):
    """A complete formatting rule"""
    id: str = Field(description="Unique rule identifier")
    description: str = Field(description="Human-readable rule description")
    conditions: List[RuleCondition] = Field(description="Conditions that must be met")
    action: RuleAction = Field(description="Action to take when conditions match")
    priority: int = Field(default=100, description="Rule priority (higher = more specific)")
    created_at: Optional[str] = Field(default=None)

class RuleGenerationRequest(BaseModel):
    """Request to generate a new rule"""
    element: DocumentElement = Field(description="Element to create rule for")
    intent: str = Field(description="User's natural language intent")

class RuleGenerationResponse(BaseModel):
    """Response from rule generation"""
    rule: Optional[FormattingRule] = Field(default=None)
    type: str = Field(default="success")  # "success", "clarification", "error"
    message: Optional[str] = Field(default=None)

class RuleExportRequest(BaseModel):
    """Request to export rules"""
    rules: List[FormattingRule] = Field(description="Rules to export")
    format: str = Field(default="json", description="Export format")

class FileUploadResponse(BaseModel):
    """Response from file upload"""
    document: DocumentContent = Field(description="Processed document content")
    success: bool = Field(default=True)
    message: Optional[str] = Field(default=None)

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None)
    code: Optional[int] = Field(default=None)