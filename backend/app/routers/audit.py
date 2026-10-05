from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..models.models import AuditLog, Workspace
from ..schemas.schemas import AuditLogResponse
from ..routers.auth import get_current_user
from ..models.enums import UserRole
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit Logs"])


def check_workspace_access(workspace_id: int, user, db: Session, required_role: UserRole = UserRole.VIEWER):
    """Check if user has access to workspace with required role"""
    from ..routers.workspaces import check_workspace_access as check_access
    return check_access(workspace_id, user, db, required_role)


@router.get("/{workspace_id}", response_model=List[AuditLogResponse])
def list_audit_logs(
    workspace_id: int,
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List audit logs for workspace"""
    check_workspace_access(workspace_id, current_user, db, UserRole.MEMBER)
    logs = db.query(AuditLog).filter(
        AuditLog.workspace_id == workspace_id
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return logs
