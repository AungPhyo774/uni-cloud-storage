import httpx


STORAGE_NODES = [
    "http://127.0.0.1:9001",
    "http://127.0.0.1:9002",
    "http://127.0.0.1:9003"
]


async def check_node_health():

    results = []

    async with httpx.AsyncClient(timeout=3.0) as client:

        for node in STORAGE_NODES:

            try:

                response = await client.get(
                    f"{node}/health"
                )

                if response.status_code == 200:

                    results.append({
                        "node": node,
                        "status": "online"
                    })

                else:

                    results.append({
                        "node": node,
                        "status": "offline"
                    })

            except httpx.RequestError:

                results.append({
                    "node": node,
                    "status": "offline"
                })

    return results