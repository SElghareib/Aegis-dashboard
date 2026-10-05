from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..core.database import get_db
from ..models.models import Agent, Tool, AgentTool, Run, RunStep, Approval, AuditLog, Workspace
from ..schemas.schemas import (
    AgentCreate, AgentResponse, AgentToolResponse, ToolResponse,
    RunCreate, RunResponse, RunStepResponse, ApprovalResponse, ApprovalDecision
)
from ..routers.auth import get_current_user
from ..models.enums import RunStatus, ApprovalStatus, UserRole
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["Agents"])


def check_workspace_access(workspace_id: int, user, db: Session, required_role: UserRole = UserRole.VIEWER):
    """Check if user has access to workspace with required role"""
    from ..routers.workspaces import check_workspace_access as check_access
    return check_access(workspace_id, user, db, required_role)


@router.get("/{workspace_id}", response_model=List[AgentResponse])
def list_agents(
    workspace_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all agents in workspace"""
    check_workspace_access(workspace_id, current_user, db)
    agents = db.query(Agent).filter(Agent.workspace_id == workspace_id).all()
    return agents


@router.post("/{workspace_id}", response_model=AgentResponse)
def create_agent(
    workspace_id: int,
    agent_data: AgentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new agent"""
    check_workspace_access(workspace_id, current_user, db, UserRole.MEMBER)
    
    agent = Agent(
        workspace_id=workspace_id,
        name=agent_data.name,
        description=agent_data.description,
        system_prompt=agent_data.system_prompt
    )
    db.add(agent)
    
    # Log audit
    audit_log = AuditLog(
        workspace_id=workspace_id,
        actor_id=current_user.id,
        action="agent_created",
        resource_type="agent",
        resource_id=agent.id,
        details={"name": agent_data.name}
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/tools", response_model=List[ToolResponse])
def list_tools(db: Session = Depends(get_db)):
    """List available tools"""
    tools = db.query(Tool).all()
    return tools


@router.post("/{agent_id}/tools/{tool_id}")
def assign_tool_to_agent(
    agent_id: int,
    tool_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign a tool to an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    check_workspace_access(agent.workspace_id, current_user, db, UserRole.ADMIN)
    
    agent_tool = AgentTool(agent_id=agent_id, tool_id=tool_id)
    db.add(agent_tool)
    db.commit()
    
    return {"message": "Tool assigned"}


@router.post("/{workspace_id}/run", response_model=RunResponse)
def run_agent(
    workspace_id: int,
    run_data: RunCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run an agent with given input"""
    check_workspace_access(workspace_id, current_user, db, UserRole.MEMBER)
    
    # Create run record
    run = Run(
        workspace_id=workspace_id,
        agent_id=run_data.agent_id,
        automation_id=run_data.automation_id,
        input_data=run_data.input_data,
        status=RunStatus.RUNNING,
        started_at=datetime.utcnow()
    )
    db.add(run)
    db.flush()
    
    # Simulate agent execution steps
    steps = [
        ("task_classification", "classify", {"input": run_data.input_data}),
        ("knowledge_retrieval", "search_kb", {"query": str(run_data.input_data)}),
        ("reasoning", "reason", {}),
        ("action_proposal", "propose_action", {}),
    ]
    
    for i, (step_type, action, input_data) in enumerate(steps):
        run_step = RunStep(
            run_id=run.id,
            step_order=i,
            step_type=step_type,
            action=action,
            input_data=input_data,
            output_data={"status": "success"},
            duration_ms=100
        )
        db.add(run_step)
    
    # Check if approval needed (mock logic)
    needs_approval = True  # In real app, this would be based on action type
    
    if needs_approval:
        run.status = RunStatus.WAITING_APPROVAL
        
        approval = Approval(
            workspace_id=workspace_id,
            run_id=run.id,
            requested_action="refund_request",
            action_details={
                "order_id": "48291",
                "amount": 74.00,
                "reason": "Matches refund policy"
            },
            requested_by=current_user.id
        )
        db.add(approval)
        
        # Log audit
        audit_log = AuditLog(
            workspace_id=workspace_id,
            actor_id=current_user.id,
            action="approval_requested",
            resource_type="approval",
            resource_id=approval.id
        )
        db.add(audit_log)
    else:
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.utcnow()
        run.output_data = {"result": "completed"}
    
    db.commit()
    db.refresh(run)
    return run


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(
    run_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get run details with steps"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    check_workspace_access(run.workspace_id, current_user, db)
    return run


@router.get("/runs/{run_id}/steps", response_model=List[RunStepResponse])
def get_run_steps(
    run_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get run execution steps"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    check_workspace_access(run.workspace_id, current_user, db)
    steps = db.query(RunStep).filter(RunStep.run_id == run_id).order_by(RunStep.step_order).all()
    return steps
