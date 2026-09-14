"""UDT-X Copilot REST API Router.

Exposes endpoints for querying the AI Agent, retrieving the capability graph,
and getting personalized shift recommendations.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from services.api.app.routers.auth import UserRecord, get_current_user
from services.api.app.services.agent_engine import (
    CopilotQueryRequest,
    CopilotResponse,
    copilot_agent,
)
from services.api.app.services.capability_registry import (
    ACTION_REGISTRY,
    ROUTE_REGISTRY,
)
from services.api.app.services.personalization import personalization_engine

router = APIRouter(prefix="/copilot", tags=["AI Copilot & Capability Agent"])


@router.post("/query", response_model=CopilotResponse)
async def query_copilot(
    body: CopilotQueryRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> CopilotResponse:
    """Execute query against the AI Copilot with permission checks and tool validation."""
    session_id = body.session_id or current_user.email
    response = copilot_agent.process_query(
        query=body.query,
        user_role=current_user.role,
        user_display_name=current_user.display_name,
        current_route=body.current_route or "/",
        confirmed_action=body.action_request,
        session_id=session_id,
        conversation_history=body.conversation_history,
    )
    return response


@router.get("/capabilities")
async def get_capabilities(
    current_user: UserRecord = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve the full website capability graph and action registry."""
    # Filter actions based on role clearance
    available_actions = {
        k: (v.model_dump() if hasattr(v, "model_dump") else v.dict())
        for k, v in ACTION_REGISTRY.items()
        if v.required_role == "analyst" or current_user.role == "admin"
    }
    available_routes = {
        k: (v.model_dump() if hasattr(v, "model_dump") else v.dict())
        for k, v in ROUTE_REGISTRY.items()
    }

    return {
        "routes": available_routes,
        "actions": available_actions,
        "user_role": current_user.role,
        "offline_support_mode": "hybrid_local_rag",
    }


@router.get("/recommendations")
async def get_recommendations(
    current_user: UserRecord = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Retrieve personalized next-best recommendations tailored to user role and active alerts."""
    recs = personalization_engine.get_personalized_recommendations(
        user_role=current_user.role,
        user_display_name=current_user.display_name,
    )
    return [r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in recs]
