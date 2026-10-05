from pydantic import BaseModel, EmailStr, Optional
from typing import List, Dict, Any, Optional
from ..models.enums import UserRole, DocumentStatus, RunStatus, ApprovalStatus


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Workspace schemas
class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class WorkspaceMemberCreate(BaseModel):
    user_id: int
    role: UserRole = UserRole.MEMBER


class WorkspaceMemberResponse(BaseModel):
    id: int
    user_id: int
    workspace_id: int
    role: UserRole

    class Config:
        from_attributes = True


# Document schemas
class DocumentCreate(BaseModel):
    filename: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None


class DocumentResponse(BaseModel):
    id: int
    workspace_id: int
    filename: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    status: DocumentStatus
    created_at: str

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    metadata_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Knowledge search schemas
class KnowledgeSearchRequest(BaseModel):
    query: str
    workspace_id: int
    limit: int = 5


class KnowledgeSearchResult(BaseModel):
    content: str
    document_id: int
    document_name: str
    chunk_index: int
    score: float
    metadata: Optional[Dict[str, Any]] = None


# Agent schemas
class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None


class AgentResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class AgentToolResponse(BaseModel):
    id: int
    agent_id: int
    tool_id: int
    is_enabled: bool

    class Config:
        from_attributes = True


# Tool schemas
class ToolResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    schema_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Automation schemas
class AutomationStepCreate(BaseModel):
    step_order: int
    step_type: str
    config: Optional[Dict[str, Any]] = None


class AutomationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    steps: List[AutomationStepCreate] = []


class AutomationResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class AutomationStepResponse(BaseModel):
    id: int
    automation_id: int
    step_order: int
    step_type: str
    config: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Run schemas
class RunCreate(BaseModel):
    automation_id: Optional[int] = None
    agent_id: Optional[int] = None
    input_data: Optional[Dict[str, Any]] = None


class RunResponse(BaseModel):
    id: int
    workspace_id: int
    automation_id: Optional[int] = None
    agent_id: Optional[int] = None
    status: RunStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class RunStepResponse(BaseModel):
    id: int
    run_id: int
    step_order: int
    step_type: str
    action: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True


# Approval schemas
class ApprovalCreate(BaseModel):
    run_id: Optional[int] = None
    requested_action: str
    action_details: Optional[Dict[str, Any]] = None


class ApprovalResponse(BaseModel):
    id: int
    workspace_id: int
    run_id: Optional[int] = None
    requested_action: str
    action_details: Optional[Dict[str, Any]] = None
    status: ApprovalStatus
    requested_by: Optional[int] = None
    reviewed_by: Optional[int] = None
    review_comment: Optional[str] = None
    created_at: str
    reviewed_at: Optional[str] = None

    class Config:
        from_attributes = True


class ApprovalDecision(BaseModel):
    approved: bool
    comment: Optional[str] = None


# Audit log schemas
class AuditLogResponse(BaseModel):
    id: int
    workspace_id: int
    actor_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    created_at: str

    class Config:
        from_attributes = True


# Assistant/chat schemas
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    workspace_id: int
    messages: List[ChatMessage]
    mode: str = "ask"  # ask, investigate, act


class ChatResponse(BaseModel):
    response: str
    sources: List[KnowledgeSearchResult] = []
    tool_calls: List[Dict[str, Any]] = []
    run_id: Optional[int] = None
