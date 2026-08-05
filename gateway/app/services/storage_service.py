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

    # -----------------------------------------
    # 1. Select Primary Node
    # -----------------------------------------

    primary_index = current_node

    primary_node = STORAGE_NODES[primary_index]

    # -----------------------------------------
    # 2. Select Replica Node
    # -----------------------------------------

    replica_index = (
        primary_index + 1
    ) % len(STORAGE_NODES)

    replica_node = STORAGE_NODES[replica_index]

    # -----------------------------------------
    # 3. Move Round Robin pointer
    # -----------------------------------------

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

        # -----------------------------------------
        # 4. Upload to Primary
        # -----------------------------------------

        primary_response = await client.post(
            f"{primary_node}/storage/upload",
            files=files
        )

        if primary_response.status_code != 200:
            raise Exception(
                "Primary storage node failed"
            )

        # -----------------------------------------
        # 5. Upload to Replica
        # -----------------------------------------

        replica_response = await client.post(
            f"{replica_node}/storage/upload",
            files=files
        )

        if replica_response.status_code != 200:
            raise Exception(
                "Replica storage node failed"
            )

    return {
        "storage_node": primary_node,
        "replica_node": replica_node,
        "response": primary_response.json()
    }