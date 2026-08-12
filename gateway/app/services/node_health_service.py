import httpx


# =========================================================
# STORAGE NODES
# =========================================================

STORAGE_NODES = [
    {
        "name": "Node 1",
        "url": "http://127.0.0.1:9001"
    },
    {
        "name": "Node 2",
        "url": "http://127.0.0.1:9002"
    },
    {
        "name": "Node 3",
        "url": "http://127.0.0.1:9003"
    }
]


# =========================================================
# CHECK ONE NODE
# =========================================================

async def check_node_health(
    node_url: str
) -> bool:

    try:

        async with httpx.AsyncClient(
            timeout=3.0
        ) as client:

            response = await client.get(
                f"{node_url}/health"
            )

        return response.status_code == 200

    except httpx.RequestError:

        return False


# =========================================================
# GET ALL NODE HEALTH
# =========================================================

async def get_node_health():

    results = []

    for node in STORAGE_NODES:

        is_online = await check_node_health(
            node["url"]
        )

        results.append(
            {
                "name": node["name"],
                "url": node["url"],
                "status": (
                    "online"
                    if is_online
                    else "offline"
                )
            }
        )

    return results


# =========================================================
# GET HEALTHY NODES ONLY
# =========================================================

async def get_healthy_nodes():

    healthy_nodes = []

    for node in STORAGE_NODES:

        is_online = await check_node_health(
            node["url"]
        )

        if is_online:

            healthy_nodes.append(
                node["url"]
            )

    return healthy_nodes