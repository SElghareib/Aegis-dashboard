from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..models.models import Document, DocumentChunk, Workspace, AuditLog
from ..schemas.schemas import DocumentResponse, KnowledgeSearchRequest, KnowledgeSearchResult
from ..routers.auth import get_current_user
from ..models.enums import DocumentStatus, UserRole
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


def check_workspace_access(workspace_id: int, user, db: Session, required_role: UserRole = UserRole.VIEWER):
    """Check if user has access to workspace with required role"""
    from ..routers.workspaces import check_workspace_access as check_access
    return check_access(workspace_id, user, db, required_role)


@router.get("/{workspace_id}/documents", response_model=List[DocumentResponse])
def list_documents(
    workspace_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all documents in workspace"""
    check_workspace_access(workspace_id, current_user, db)
    documents = db.query(Document).filter(Document.workspace_id == workspace_id).all()
    return documents


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document details"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    check_workspace_access(document.workspace_id, current_user, db)
    return document


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    check_workspace_access(document.workspace_id, current_user, db, UserRole.MEMBER)
    
    # Delete chunks first
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
    db.delete(document)
    
    # Log audit
    audit_log = AuditLog(
        workspace_id=document.workspace_id,
        actor_id=current_user.id,
        action="document_deleted",
        resource_type="document",
        resource_id=document_id
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Document deleted"}


@router.post("/search", response_model=List[KnowledgeSearchResult])
def search_knowledge(
    search_request: KnowledgeSearchRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search knowledge base using vector similarity"""
    check_workspace_access(search_request.workspace_id, current_user, db)
    
    # TODO: Implement actual vector search with pgvector
    # For now, return mock results
    
    # Get indexed documents in workspace
    documents = db.query(Document).filter(
        Document.workspace_id == search_request.workspace_id,
        Document.status == DocumentStatus.INDEXED
    ).all()
    
    doc_map = {d.id: d.filename for d in documents}
    
    # Mock search - in production this would use pgvector
    results = []
    for doc in documents[:search_request.limit]:
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).limit(2).all()
        
        for chunk in chunks:
            results.append(KnowledgeSearchResult(
                content=chunk.content[:500],  # Truncate for response
                document_id=doc.id,
                document_name=doc.filename,
                chunk_index=chunk.chunk_index,
                score=0.85,  # Mock score
                metadata=chunk.metadata_json
            ))
    
    return results


@router.post("/{workspace_id}/index/{document_id}")
def index_document(
    workspace_id: int,
    document_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger document indexing (background job)"""
    check_workspace_access(workspace_id, current_user, db, UserRole.MEMBER)
    
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.workspace_id == workspace_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update status to processing
    document.status = DocumentStatus.PROCESSING
    db.commit()
    
    # TODO: Trigger background job for actual indexing
    # For now, simulate immediate indexing with mock data
    
    # Create mock chunks
    for i in range(3):
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=i,
            content=f"Mock content chunk {i} from {document.filename}",
            embedding=json.dumps([0.1] * 1536),  # Mock embedding
            metadata_json={"source": document.filename}
        )
        db.add(chunk)
    
    document.status = DocumentStatus.INDEXED
    db.commit()
    
    # Log audit
    audit_log = AuditLog(
        workspace_id=workspace_id,
        actor_id=current_user.id,
        action="document_indexed",
        resource_type="document",
        resource_id=document_id
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Document indexed", "document_id": document_id}
