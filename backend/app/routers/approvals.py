from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..models.models import Approval, AuditLog, Run
from ..schemas.schemas import ApprovalResponse, ApprovalDecision
from ..routers.auth import get_current_user
from ..models.enums import ApprovalStatus, RunStatus, UserRole
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/approvals", tags=["Approvals"])


def check_workspace_access(workspace_id: int, user, db: Session, required_role: UserRole = UserRole.VIEWER):
    """Check if user has access to workspace with required role"""
    from ..routers.workspaces import check_workspace_access as check_access
    return check_access(workspace_id, user, db, required_role)


@router.get("/{workspace_id}", response_model=List[ApprovalResponse])
def list_approvals(
    workspace_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all pending approvals in workspace"""
    check_workspace_access(workspace_id, current_user, db)
    approvals = db.query(Approval).filter(
        Approval.workspace_id == workspace_id,
        Approval.status == ApprovalStatus.PENDING
    ).all()
    return approvals


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve_action(
    approval_id: int,
    decision: ApprovalDecision,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve or reject a pending action"""
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    check_workspace_access(approval.workspace_id, current_user, db, UserRole.ADMIN)
    
    # Update approval status
    approval.status = ApprovalStatus.APPROVED if decision.approved else ApprovalStatus.REJECTED
    approval.reviewed_by = current_user.id
    approval.review_comment = decision.comment
    approval.reviewed_at = datetime.utcnow()
    
    # If approved and associated with a run, update run status
    if decision.approved and approval.run_id:
        run = db.query(Run).filter(Run.id == approval.run_id).first()
        if run:
            run.status = RunStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            run.output_data = {"approved": True, "action": approval.requested_action}
    
    # Log audit
    audit_log = AuditLog(
        workspace_id=approval.workspace_id,
        actor_id=current_user.id,
        action="approval_reviewed",
        resource_type="approval",
        resource_id=approval_id,
        details={"approved": decision.approved, "comment": decision.comment}
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(approval)
    return approval


@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(
    approval_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get approval details"""
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    check_workspace_access(approval.workspace_id, current_user, db)
    return approval
