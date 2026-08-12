from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from app.dependencies.auth import get_current_user
from app.models.user import User

from app.services.node_health_service import (
    get_node_health
)


router = APIRouter(
    prefix="/health",
    tags=["Health"]
)


# =========================================================
# PUBLIC GATEWAY HEALTH
# =========================================================

@router.get("/")
def gateway_health():

    return {
        "status": "healthy"
    }


# =========================================================
# ADMIN NODE HEALTH
# =========================================================

@router.get("/nodes")
async def nodes_health(
    current_user: User = Depends(
        get_current_user
    )
):

    if current_user.role != "admin":

        raise HTTPException(
            status_code=403,
            detail="Only admin can access node health"
        )

    nodes = await get_node_health()

    return {
        "nodes": nodes
    }