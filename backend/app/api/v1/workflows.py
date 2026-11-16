"""Workflows API: CRUD, AI Generator, Graph Validator, and Execution Dispatcher."""

from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_workspace
from app.database.models import (
    User,
    Workspace,
    Workflow,
    WorkflowVersion,
    WorkflowNode,
    Execution,
    ExecutionStatus,
    Integration,
    IntegrationCredential,
)
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowGraphSchema,
    WorkflowGenerateRequest,
    WorkflowGenerateResponse,
    WorkflowValidateResponse,
    WorkflowVersionResponse,
    WorkflowPublishRequest,
)
from app.schemas.execution import ExecutionResponse
from app.engine.dag import DAG, DAGValidationError
from app.engine.runner import WorkflowExecutionRunner
from app.ai.planner.planner import WorkflowPlanner
from app.workflows.templates import WORKFLOW_TEMPLATES

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Workflow).where(Workflow.workspace_id == workspace.id).order_by(desc(Workflow.updated_at))
    )
    workflows = res.scalars().all()
    results = []
    for wf in workflows:
        # Load current version graph if present
        graph = None
        if wf.current_version_id:
            v_res = await db.execute(select(WorkflowVersion).where(WorkflowVersion.id == wf.current_version_id))
            ver = v_res.scalars().first()
            if ver and ver.graph_data:
                graph = WorkflowGraphSchema(**ver.graph_data)
        results.append(
            WorkflowResponse(
                id=wf.id,
                workspace_id=wf.workspace_id,
                name=wf.name,
                description=wf.description,
                is_active=wf.is_active,
                current_version_id=wf.current_version_id,
                graph=graph,
                created_at=wf.created_at,
                updated_at=wf.updated_at,
            )
        )
    return results


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreate,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    if payload.graph is not None:
        try:
            graph_dict = payload.graph.model_dump()
            dag = DAG(graph_dict["nodes"], graph_dict["edges"])
            valid, errors, _ = dag.validate()
        except DAGValidationError as exc:
            valid, errors = False, [str(exc)]
        if not valid:
            raise HTTPException(status_code=422, detail={"message": "Workflow graph is invalid", "errors": errors})

    wf = Workflow(
        workspace_id=workspace.id,
        name=payload.name,
        description=payload.description,
        is_active=True,
    )
    db.add(wf)
    await db.flush()

    # Initial version snapshot
    graph_dict = payload.graph.model_dump() if payload.graph else {"nodes": [], "edges": []}
    ver = WorkflowVersion(
        workflow_id=wf.id,
        version_number=1,
        graph_data=graph_dict,
        is_published=True,
        changelog="Initial creation",
    )
    db.add(ver)
    await db.flush()

    wf.current_version_id = ver.id
    await db.commit()
    await db.refresh(wf)

    from app.core.audit import log_audit_event
    await log_audit_event(
        db=db,
        workspace_id=workspace.id,
        action="WORKFLOW_CREATED",
        resource_type="workflow",
        resource_id=wf.id,
        details={"name": wf.name},
    )

    return WorkflowResponse(
        id=wf.id,
        workspace_id=wf.workspace_id,
        name=wf.name,
        description=wf.description,
        is_active=wf.is_active,
        current_version_id=wf.current_version_id,
        graph=WorkflowGraphSchema(**graph_dict),
        created_at=wf.created_at,
        updated_at=wf.updated_at,
    )


@router.get("/templates")
async def list_workflow_templates():
    """List all pre-configured, production-ready workflow templates."""
    return WORKFLOW_TEMPLATES


@router.post("/templates/{template_id}/instantiate", response_model=WorkflowResponse)
async def instantiate_template(
    template_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Instantiate a workflow template into the active workspace."""
    template = next((t for t in WORKFLOW_TEMPLATES if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Workflow template not found")

    graph_dict = {
        "nodes": template["nodes"],
        "edges": template["edges"],
    }

    wf = Workflow(
        workspace_id=workspace.id,
        name=template["name"],
        description=template["description"],
        is_active=True,
    )
    db.add(wf)
    await db.flush()

    ver = WorkflowVersion(
        workflow_id=wf.id,
        version_number=1,
        graph_data=graph_dict,
        is_published=True,
        changelog=f"Instantiated from template: {template['name']}",
    )
    db.add(ver)
    await db.flush()

    wf.current_version_id = ver.id
    await db.commit()
    await db.refresh(wf)

    from app.core.audit import log_audit_event
    await log_audit_event(
        db=db,
        workspace_id=workspace.id,
        action="WORKFLOW_CREATED",
        resource_type="workflow",
        resource_id=wf.id,
        details={"name": wf.name},
    )

    await log_audit_event(
        db=db,
        workspace_id=workspace.id,
        action="WORKFLOW_INSTANTIATED_FROM_TEMPLATE",
        resource_type="workflow",
        resource_id=wf.id,
        details={"template_id": template_id, "template_name": template["name"]},
    )

    return WorkflowResponse(
        id=wf.id,
        workspace_id=wf.workspace_id,
        name=wf.name,
        description=wf.description,
        is_active=wf.is_active,
        current_version_id=wf.current_version_id,
        graph=WorkflowGraphSchema(**graph_dict),
        created_at=wf.created_at,
        updated_at=wf.updated_at,
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.workspace_id == workspace.id)
    )
    wf = res.scalars().first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    graph = None
    if wf.current_version_id:
        v_res = await db.execute(select(WorkflowVersion).where(WorkflowVersion.id == wf.current_version_id))
        ver = v_res.scalars().first()
        if ver and ver.graph_data:
            graph = WorkflowGraphSchema(**ver.graph_data)

    return WorkflowResponse(
        id=wf.id,
        workspace_id=wf.workspace_id,
        name=wf.name,
        description=wf.description,
        is_active=wf.is_active,
        current_version_id=wf.current_version_id,
        graph=graph,
        created_at=wf.created_at,
        updated_at=wf.updated_at,
    )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    payload: WorkflowUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.workspace_id == workspace.id)
    )
    wf = res.scalars().first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if payload.name is not None:
        wf.name = payload.name
    if payload.description is not None:
        wf.description = payload.description

    # Create immutable version snapshot if graph updated
    if payload.graph is not None:
        # Determine latest version number
        num_res = await db.execute(
            select(WorkflowVersion.version_number)
            .where(WorkflowVersion.workflow_id == wf.id)
            .order_by(desc(WorkflowVersion.version_number))
            .limit(1)
        )
        latest_num = num_res.scalar_one_or_none() or 0

        new_ver = WorkflowVersion(
            workflow_id=wf.id,
            version_number=latest_num + 1,
            graph_data=payload.graph.model_dump(),
            # Graph edits are drafts unless explicitly published.  Existing
            # published snapshots remain immutable.
            is_published=payload.is_published is True,
            changelog=payload.changelog or f"Version {latest_num + 1}",
        )
        db.add(new_ver)
        await db.flush()
        wf.current_version_id = new_ver.id

        if payload.is_published is True:
            dag = DAG(payload.graph.model_dump()["nodes"], payload.graph.model_dump()["edges"])
            try:
                valid, errors, _ = dag.validate()
            except DAGValidationError as exc:
                valid, errors = False, [str(exc)]
            if not valid:
                raise HTTPException(status_code=422, detail={"message": "Workflow graph is invalid", "errors": errors})
            await db.execute(
                WorkflowVersion.__table__.update()
                .where(WorkflowVersion.workflow_id == wf.id, WorkflowVersion.id != new_ver.id)
                .values(is_published=False)
            )

    await db.commit()
    await db.refresh(wf)

    # Return updated graph
    v_res = await db.execute(select(WorkflowVersion).where(WorkflowVersion.id == wf.current_version_id))
    ver = v_res.scalars().first()
    graph = WorkflowGraphSchema(**ver.graph_data) if ver and ver.graph_data else None

    return WorkflowResponse(
        id=wf.id,
        workspace_id=wf.workspace_id,
        name=wf.name,
        description=wf.description,
        is_active=wf.is_active,
        current_version_id=wf.current_version_id,
        graph=graph,
        created_at=wf.created_at,
        updated_at=wf.updated_at,
    )


@router.post("/{workflow_id}/validate", response_model=WorkflowValidateResponse)
async def validate_workflow(
    workflow_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.workspace_id == workspace.id)
    )
    wf = res.scalars().first()
    if not wf or not wf.current_version_id:
        raise HTTPException(status_code=404, detail="Workflow or version not found")

    v_res = await db.execute(select(WorkflowVersion).where(WorkflowVersion.id == wf.current_version_id))
    ver = v_res.scalars().first()
    graph = ver.graph_data or {}
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    try:
        dag = DAG(nodes, edges)
        is_valid, errors, warnings = dag.validate()
    except DAGValidationError as exc:
        is_valid, errors, warnings = False, [str(exc)], []
    order = []
    if is_valid:
        order = dag.detect_cycles_and_sort()

    return WorkflowValidateResponse(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        execution_order=order,
    )


@router.post("/{workflow_id}/publish", response_model=WorkflowResponse)
async def publish_workflow(
    workflow_id: str,
    payload: WorkflowPublishRequest = WorkflowPublishRequest(),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Validate and publish the workflow's current draft version."""
    res = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.workspace_id == workspace.id)
    )
    wf = res.scalars().first()
    if not wf or not wf.current_version_id:
        raise HTTPException(status_code=404, detail="Workflow or draft version not found")
    ver_res = await db.execute(select(WorkflowVersion).where(WorkflowVersion.id == wf.current_version_id))
    ver = ver_res.scalars().first()
    if not ver:
        raise HTTPException(status_code=404, detail="Workflow version not found")
    graph = ver.graph_data or {}
    try:
        dag = DAG(graph.get("nodes", []), graph.get("edges", []))
        valid, errors, _ = dag.validate()
    except DAGValidationError as exc:
        valid, errors = False, [str(exc)]
    if not valid:
        raise HTTPException(status_code=422, detail={"message": "Workflow graph is invalid", "errors": errors})

    await db.execute(
        WorkflowVersion.__table__.update()
        .where(WorkflowVersion.workflow_id == wf.id)
        .values(is_published=False)
    )
    ver.is_published = True
    if payload.changelog is not None:
        ver.changelog = payload.changelog
    await db.commit()
    await db.refresh(wf)
    return await get_workflow(workflow_id, workspace, db)


@router.get("/{workflow_id}/versions", response_model=List[WorkflowVersionResponse])
async def list_workflow_versions(
    workflow_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.workspace_id == workspace.id)
    )
    if not res.scalars().first():
        raise HTTPException(status_code=404, detail="Workflow not found")
    versions = await db.execute(
        select(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == workflow_id)
        .order_by(desc(WorkflowVersion.version_number))
    )
    return versions.scalars().all()


@router.post("/generate", response_model=WorkflowGenerateResponse)
async def generate_workflow_ai(
    payload: WorkflowGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """Natural-language workflow generation using AI Planner."""
    planner = WorkflowPlanner()
    result = await planner.generate_workflow(payload.prompt)
    return result


@router.post("/{workflow_id}/execute", response_model=ExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Trigger asynchronous workflow execution."""
    res = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.workspace_id == workspace.id)
    )
    wf = res.scalars().first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow has no executable version published")

    published_res = await db.execute(
        select(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == wf.id, WorkflowVersion.is_published.is_(True))
        .order_by(desc(WorkflowVersion.version_number))
        .limit(1)
    )
    published = published_res.scalars().first()
    if not published:
        raise HTTPException(status_code=404, detail="Workflow has no executable version published")

    # Check if Gmail integration is connected to pass credential context
    integ_res = await db.execute(
        select(Integration)
        .options(selectinload(Integration.credentials))
        .where(Integration.workspace_id == workspace.id, Integration.provider == "GMAIL")
    )
    gmail_integ = integ_res.scalars().first()
    credential = None
    if gmail_integ and gmail_integ.is_connected:
        credential_res = await db.execute(
            select(IntegrationCredential).where(IntegrationCredential.integration_id == gmail_integ.id)
        )
        credential = credential_res.scalars().first()
    context_data = {
        "workspace_id": workspace.id,
        "gmail_connected": bool(gmail_integ and gmail_integ.is_connected and credential),
    }

    execution = Execution(
        workspace_id=workspace.id,
        workflow_id=wf.id,
        workflow_version_id=published.id,
        status=ExecutionStatus.QUEUED.value,
        trigger_type="MANUAL",
        context_data=context_data,
        token_usage={},
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    from app.core.audit import log_audit_event
    await log_audit_event(
        db=db,
        workspace_id=workspace.id,
        action="WORKFLOW_EXECUTED",
        resource_type="execution",
        resource_id=execution.id,
        details={"workflow_id": wf.id, "workflow_name": wf.name},
    )

    # Prefer Celery so provider calls never block the request process. Local
    # fallback remains available when Redis is intentionally not running.
    dispatched_celery = False
    from app.workers.celery_app import is_redis_available
    if is_redis_available():
        try:
            from app.workers.tasks import execute_workflow_task
            execute_workflow_task.apply_async(args=[execution.id, {}], connect_timeout=1, retry=False)
            dispatched_celery = True
        except Exception:
            pass

    if not dispatched_celery:
        background_tasks.add_task(WorkflowExecutionRunner.start_execution, execution.id, {})

    return ExecutionResponse(
        id=execution.id,
        workspace_id=execution.workspace_id,
        workflow_id=execution.workflow_id,
        workflow_version_id=execution.workflow_version_id,
        status=execution.status,
        trigger_type=execution.trigger_type,
        context_data=execution.context_data,
        started_at=execution.started_at,
        token_usage=execution.token_usage,
        nodes=[],
    )



