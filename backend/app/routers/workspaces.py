from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..models.models import Workspace, WorkspaceMember, Document, AuditLog
from ..schemas.schemas import WorkspaceCreate, WorkspaceResponse, WorkspaceMemberResponse, DocumentResponse
from ..routers.auth import get_current_user
from ..models.enums import UserRole, DocumentStatus
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


def check_workspace_access(workspace_id: int, user, db: Session, required_role: UserRole = UserRole.VIEWER):
    """Check if user has access to workspace with required role"""
    membership = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this workspace"
        )
    
    # Role hierarchy: OWNER > ADMIN > MEMBER > VIEWER
    role_hierarchy = {UserRole.OWNER: 4, UserRole.ADMIN: 3, UserRole.MEMBER: 2, UserRole.VIEWER: 1}
    if role_hierarchy.get(membership.role, 0) < role_hierarchy.get(required_role, 0):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return membership


@router.get("/", response_model=List[WorkspaceResponse])
def list_workspaces(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """List all workspaces user has access to"""
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).all()
    workspace_ids = [m.workspace_id for m in memberships]
    workspaces = db.query(Workspace).filter(Workspace.id.in_(workspace_ids)).all()
    return workspaces


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workspace"""
    workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description
    )
    db.add(workspace)
    db.flush()
    
    # Add creator as owner
    membership = WorkspaceMember(
        user_id=current_user.id,
        workspace_id=workspace.id,
        role=UserRole.OWNER
    )
    db.add(membership)
    
    # Log audit
    audit_log = AuditLog(
        workspace_id=workspace.id,
        actor_id=current_user.id,
        action="workspace_created",
        resource_type="workspace",
        resource_id=workspace.id,
        details={"name": workspace_data.name}
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(workspace)
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workspace details"""
    check_workspace_access(workspace_id, current_user, db)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
def list_workspace_members(
    workspace_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List workspace members"""
    check_workspace_access(workspace_id, current_user, db, UserRole.MEMBER)
    members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).all()
    return members


@router.post("/{workspace_id}/documents/upload")
async def upload_document(
    workspace_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document to workspace"""
    check_workspace_access(workspace_id, current_user, db, UserRole.MEMBER)
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Create document record
    document = Document(
        workspace_id=workspace_id,
        filename=file.filename,
        file_path=f"/uploads/{workspace_id}/{file.filename}",
        file_size=file_size,
        content_type=file.content_type,
        status=DocumentStatus.PENDING
    )
    db.add(document)
    
    # Log audit
    audit_log = AuditLog(
        workspace_id=workspace_id,
        actor_id=current_user.id,
        action="document_uploaded",
        resource_type="document",
        resource_id=document.id,
        details={"filename": file.filename}
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(document)
    
    # TODO: Trigger background job for indexing
    
    return {"id": document.id, "filename": document.filename, "status": document.status}
