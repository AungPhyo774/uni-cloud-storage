import os
import httpx

from app.database.session import SessionLocal
from app.models.document import Document


CHECK_INTERVAL = 30


async def check_file_exists(
    storage_node: str,
    file_name: str
):

    try:

        async with httpx.AsyncClient(timeout=10) as client:

            response = await client.get(
                f"{storage_node}/storage/check/{file_name}"
            )

        if response.status_code != 200:
            return False

        data = response.json()

        return data.get("exists", False)

    except httpx.RequestError:

        return False


async def download_from_node(
    storage_node: str,
    file_name: str
):

    async with httpx.AsyncClient(timeout=30) as client:

        response = await client.get(
            f"{storage_node}/storage/download/{file_name}"
        )

    if response.status_code != 200:

        raise Exception(
            f"Failed to download {file_name} "
            f"from {storage_node}"
        )

    return response.content


async def restore_to_node(
    storage_node: str,
    file_name: str,
    file_content: bytes
):

    files = {
        "file": (
            file_name,
            file_content,
            "application/pdf"
        )
    }

    async with httpx.AsyncClient(timeout=30) as client:

        response = await client.post(
            f"{storage_node}/storage/restore/{file_name}",
            files=files
        )

    if response.status_code != 200:

        raise Exception(
            f"Failed to restore {file_name} "
            f"to {storage_node}"
        )


async def recover_document(
    document
):

    file_name = os.path.basename(
        document.file_path
    )

    primary = document.storage_node
    replica = document.replica_node

    print(
        f"[RECOVERY] Checking {file_name}"
    )

    # ---------------------------------------------
    # Check primary
    # ---------------------------------------------

    primary_exists = await check_file_exists(
        primary,
        file_name
    )

    # ---------------------------------------------
    # Primary is healthy
    # ---------------------------------------------

    if primary_exists:

        print(
            f"[OK] Primary has {file_name}"
        )

        return

    # ---------------------------------------------
    # Primary missing
    # ---------------------------------------------

    print(
        f"[WARNING] Primary missing: "
        f"{file_name}"
    )

    # ---------------------------------------------
    # Check replica
    # ---------------------------------------------

    replica_exists = await check_file_exists(
        replica,
        file_name
    )

    if not replica_exists:

        print(
            f"[ERROR] Both primary and replica "
            f"missing: {file_name}"
        )

        return

    # ---------------------------------------------
    # Download from replica
    # ---------------------------------------------

    print(
        f"[RECOVERY] Downloading "
        f"{file_name} from replica"
    )

    file_content = await download_from_node(
        replica,
        file_name
    )

    # ---------------------------------------------
    # Restore primary
    # ---------------------------------------------

    print(
        f"[RECOVERY] Restoring "
        f"{file_name} to primary"
    )

    await restore_to_node(
        primary,
        file_name,
        file_content
    )

    print(
        f"[RECOVERY SUCCESS] "
        f"{file_name} restored"
    )


async def run_recovery_check():

    db = SessionLocal()

    try:

        documents = (
            db.query(Document)
            .all()
        )

        for document in documents:

            try:

                await recover_document(
                    document
                )

            except Exception as error:

                print(
                    f"[RECOVERY ERROR] "
                    f"Document {document.id}: "
                    f"{error}"
                )

    finally:

        db.close()