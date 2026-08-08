import httpx


STORAGE_NODES = [
    "http://127.0.0.1:9001",
    "http://127.0.0.1:9002",
    "http://127.0.0.1:9003"
]


current_node = 0


# =========================================================
# CHECK HEALTHY NODES
# =========================================================

async def get_healthy_nodes():

    healthy_nodes = []

    async with httpx.AsyncClient(timeout=3.0) as client:

        for node in STORAGE_NODES:

            try:

                response = await client.get(
                    f"{node}/health"
                )

                if response.status_code == 200:

                    healthy_nodes.append(node)

            except httpx.RequestError:

                pass

    return healthy_nodes


# =========================================================
# UPLOAD WITH PRIMARY + REPLICA
# =========================================================

async def upload_to_storage(
    file_content: bytes,
    file_name: str,
    content_type: str
):

    global current_node

    # -----------------------------------------------------
    # 1. Get healthy nodes
    # -----------------------------------------------------

    healthy_nodes = await get_healthy_nodes()

    if not healthy_nodes:

        raise Exception(
            "No storage nodes are available"
        )

    # -----------------------------------------------------
    # 2. Select Primary Node using Round Robin
    # -----------------------------------------------------

    primary_index = (
        current_node % len(healthy_nodes)
    )

    storage_node = healthy_nodes[
        primary_index
    ]

    # -----------------------------------------------------
    # 3. Move Round Robin pointer
    # -----------------------------------------------------

    current_node = (
        current_node + 1
    ) % len(healthy_nodes)

    # -----------------------------------------------------
    # 4. Select Replica Node
    #
    # Replica must be different from Primary
    # -----------------------------------------------------

    replica_node = None

    if len(healthy_nodes) >= 2:

        replica_index = (
            primary_index + 1
        ) % len(healthy_nodes)

        replica_node = healthy_nodes[
            replica_index
        ]

    # -----------------------------------------------------
    # 5. Prepare file
    # -----------------------------------------------------

    files = {
        "file": (
            file_name,
            file_content,
            content_type
        )
    }

    # -----------------------------------------------------
    # 6. Upload to Primary Node
    # -----------------------------------------------------

    async with httpx.AsyncClient(timeout=30.0) as client:

        primary_response = await client.post(
            f"{storage_node}/storage/upload",
            files=files
        )

        if primary_response.status_code != 200:

            raise Exception(
                "Primary storage node failed"
            )

        # -------------------------------------------------
        # 7. Upload same file to Replica Node
        # -------------------------------------------------

        if replica_node is not None:

            replica_files = {
                "file": (
                    file_name,
                    file_content,
                    content_type
                )
            }

            replica_response = await client.post(
                f"{replica_node}/storage/upload",
                files=replica_files
            )

            if replica_response.status_code != 200:

                # Important:
                # Primary succeeded but replica failed.
                raise Exception(
                    "Replica storage node failed"
                )

    # -----------------------------------------------------
    # 8. Return both nodes
    # -----------------------------------------------------

    return {
        "storage_node": storage_node,
        "replica_node": replica_node,
        "response": primary_response.json()
    }

# Download from all nodes
async def download_from_storage(
    file_name: str,
    primary_node: str,
    replica_node: str
):
    nodes = [
        primary_node,
        replica_node
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:

        for node in nodes:

            if not node:
                continue

            try:

                response = await client.get(
                    f"{node}/storage/download/{file_name}"
                )

                if response.status_code == 200:

                    return {
                        "response": response,
                        "storage_node": node
                    }

            except httpx.RequestError:
                continue

    return None


# add the node health function for data existing
async def check_node_health(node: str):

    try:

        async with httpx.AsyncClient(
            timeout=3.0
        ) as client:

            response = await client.get(
                f"{node}/"
            )

        return response.status_code == 200

    except httpx.RequestError:

        return False


# check the pdf file exist or not
async def check_file_on_node(
    node: str,
    file_name: str
):

    try:

        async with httpx.AsyncClient(
            timeout=5.0
        ) as client:

            response = await client.get(
                f"{node}/storage/exists/{file_name}"
            )

        if response.status_code != 200:
            return False

        result = response.json()

        return result.get("exists", False)

    except httpx.RequestError:

        return False


# Recovery function 
async def recover_file_to_node(
    source_node: str,
    target_node: str,
    file_name: str,
    content_type: str
):

    try:

        # -----------------------------------------
        # 1. Download file from source node
        # -----------------------------------------

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.get(
                f"{source_node}/storage/download/{file_name}"
            )

        if response.status_code != 200:

            return False

        file_content = response.content

        # -----------------------------------------
        # 2. Upload file to target node
        # -----------------------------------------

        files = {
            "file": (
                file_name,
                file_content,
                content_type
            )
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            upload_response = await client.post(
                f"{target_node}/storage/upload",
                files=files
            )

        if upload_response.status_code != 200:

            return False

        return True

    except httpx.RequestError:

        return False