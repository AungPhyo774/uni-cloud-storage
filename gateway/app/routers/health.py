from fastapi import APIRouter

from app.services.node_health_service import (
    check_node_health
)


router = APIRouter(
    prefix="/storage",
    tags=["Storage Health"]
)


@router.get("/nodes/health")
async def storage_nodes_health():

    nodes = await check_node_health()

    return {
        "nodes": nodes
    }