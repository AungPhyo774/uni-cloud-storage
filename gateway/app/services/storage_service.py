import httpx


STORAGE_NODES = [
    "http://127.0.0.1:9001",
    "http://127.0.0.1:9002",
    "http://127.0.0.1:9003"
]

current_node = 0


async def upload_to_storage(
    file_content: bytes,
    file_name: str,
    content_type: str
):

    global current_node

    storage_node = STORAGE_NODES[current_node]

    print(storage_node)
    
    current_node = (
        current_node + 1
    ) % len(STORAGE_NODES)

    files = {
        "file": (
            file_name,
            file_content,
            content_type
        )
    }

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{storage_node}/storage/upload",
            files=files
        )

    if response.status_code != 200:
        raise Exception(
            "Storage node failed"
        )

    return {
        "storage_node": storage_node,
        "response": response.json()
    }