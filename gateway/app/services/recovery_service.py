import os
import hashlib
import httpx

from app.database.session import SessionLocal
from app.models.document import Document


# =========================================================
# CONFIGURATION
# =========================================================

CHECK_INTERVAL = 30


# =========================================================
# CHECK FILE EXISTS
# =========================================================

async def check_file_exists(
    storage_node: str,
    file_name: str
):

    try:

        async with httpx.AsyncClient(
            timeout=10
        ) as client:

            response = await client.get(
                f"{storage_node}/storage/check/{file_name}"
            )

        if response.status_code != 200:
            return False

        data = response.json()

        return data.get(
            "exists",
            False
        )

    except httpx.RequestError:

        return False


# =========================================================
# DOWNLOAD FILE FROM NODE
# =========================================================

async def download_from_node(
    storage_node: str,
    file_name: str
):

    async with httpx.AsyncClient(
        timeout=30
    ) as client:

        response = await client.get(
            f"{storage_node}/storage/download/{file_name}"
        )

    if response.status_code != 200:

        raise Exception(
            f"Failed to download "
            f"{file_name} "
            f"from {storage_node}"
        )

    return response.content


# =========================================================
# RESTORE FILE TO NODE
# =========================================================

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

    async with httpx.AsyncClient(
        timeout=30
    ) as client:

        response = await client.post(
            f"{storage_node}/storage/restore/{file_name}",
            files=files
        )

    if response.status_code != 200:

        raise Exception(
            f"Failed to restore "
            f"{file_name} "
            f"to {storage_node}"
        )


# =========================================================
# GET SHA-256 CHECKSUM FROM STORAGE NODE
# =========================================================

async def get_node_checksum(
    storage_node: str,
    file_name: str
):

    try:

        async with httpx.AsyncClient(
            timeout=30
        ) as client:

            response = await client.get(
                f"{storage_node}/storage/checksum/{file_name}"
            )

        if response.status_code == 404:

            return None

        if response.status_code != 200:

            return None

        data = response.json()

        return data.get("checksum")

    except httpx.RequestError:

        return None


# =========================================================
# CALCULATE SHA-256 LOCALLY
#
# Used after downloading replica.
# =========================================================

def calculate_checksum(
    file_content: bytes
):

    return hashlib.sha256(
        file_content
    ).hexdigest()


# =========================================================
# RECOVER DOCUMENT
# =========================================================

async def recover_document(
    document: Document
):

    file_name = os.path.basename(
        document.file_path
    )

    primary = document.storage_node
    replica = document.replica_node

    print(
        f"[RECOVERY] Checking {file_name}"
    )

    # =====================================================
    # 1. CHECK PRIMARY CHECKSUM
    # =====================================================

    primary_checksum = await get_node_checksum(
        primary,
        file_name
    )

    # =====================================================
    # 2. CHECK REPLICA CHECKSUM
    # =====================================================

    replica_checksum = await get_node_checksum(
        replica,
        file_name
    )

    # =====================================================
    # 3. BOTH FILES MISSING
    # =====================================================

    if (
        primary_checksum is None
        and replica_checksum is None
    ):

        print(
            f"[ERROR] Both primary and replica "
            f"missing: {file_name}"
        )

        return

    # =====================================================
    # 4. PRIMARY MISSING
    # =====================================================

    if primary_checksum is None:

        print(
            f"[WARNING] Primary missing: "
            f"{file_name}"
        )

        if replica_checksum is None:

            print(
                f"[ERROR] Replica also missing: "
                f"{file_name}"
            )

            return

        # -----------------------------------------------
        # Download from replica
        # -----------------------------------------------

        file_content = await download_from_node(
            replica,
            file_name
        )

        # -----------------------------------------------
        # Restore primary
        # -----------------------------------------------

        await restore_to_node(
            primary,
            file_name,
            file_content
        )

        print(
            f"[RECOVERY SUCCESS] "
            f"{file_name} restored to primary"
        )

        return

    # =====================================================
    # 5. REPLICA MISSING
    # =====================================================

    if replica_checksum is None:

        print(
            f"[WARNING] Replica missing: "
            f"{file_name}"
        )

        # -----------------------------------------------
        # Download from primary
        # -----------------------------------------------

        file_content = await download_from_node(
            primary,
            file_name
        )

        # -----------------------------------------------
        # Restore replica
        # -----------------------------------------------

        await restore_to_node(
            replica,
            file_name,
            file_content
        )

        print(
            f"[RECOVERY SUCCESS] "
            f"{file_name} restored to replica"
        )

        return

    # =====================================================
    # 6. BOTH EXIST
    # =====================================================

    if primary_checksum == replica_checksum:

        print(
            f"[INTEGRITY OK] "
            f"{file_name}"
        )

        return

    # =====================================================
    # 7. CHECKSUM MISMATCH
    # =====================================================

    print(
        f"[CORRUPTION DETECTED] "
        f"{file_name}"
    )

    print(
        f"[PRIMARY CHECKSUM] "
        f"{primary_checksum}"
    )

    print(
        f"[REPLICA CHECKSUM] "
        f"{replica_checksum}"
    )

    file_content = await download_from_node(
        replica,
        file_name
    )

    downloaded_checksum = calculate_checksum(
        file_content
    )
    if downloaded_checksum != replica_checksum:

        print(
            f"[ERROR] Replica data is also corrupted: "
            f"{file_name}"
        )

        return

    # =====================================================
    # 10. RESTORE PRIMARY
    # =====================================================

    await restore_to_node(
        primary,
        file_name,
        file_content
    )

    print(
        f"[RECOVERY SUCCESS] "
        f"Corrupted primary restored: "
        f"{file_name}"
    )


# =========================================================
# RUN RECOVERY CHECK
# =========================================================

async def run_recovery_check():

    db = SessionLocal()

    try:

        documents = (
            db.query(Document)
            .all()
        )

        for document in documents:

            try:

                result = await verify_document_integrity(
                    document
                )

                print(
                    f"[INTEGRITY RESULT] "
                    f"Document {document.id}: "
                    f"{result}"
                )

            except Exception as error:

                print(
                    f"[RECOVERY ERROR] "
                    f"Document {document.id}: "
                    f"{error}"
                )

    finally:

        db.close()
                

async def verify_document_integrity(document):

    file_name = os.path.basename(
        document.file_path
    )

    db_checksum = document.checksum

    primary_checksum = await get_node_checksum(
        document.storage_node,
        file_name
    )

    replica_checksum = await get_node_checksum(
        document.replica_node,
        file_name
    )

    print(
        f"[CHECKSUM] {file_name}"
    )

    print(
        f"  DB      : {db_checksum}"
    )

    print(
        f"  Primary : {primary_checksum}"
    )

    print(
        f"  Replica : {replica_checksum}"
    )

    # ------------------------------------------
    # Case 1
    # ------------------------------------------

    if (
        db_checksum
        and primary_checksum == db_checksum
        and replica_checksum == db_checksum
    ):

        print(
            f"[INTEGRITY OK] "
            f"{file_name}"
        )

        return "healthy"

    # ------------------------------------------
    # Case 2
    # Primary missing/corrupted
    # Replica matches DB
    # ------------------------------------------

    if (
        db_checksum
        and replica_checksum == db_checksum
        and primary_checksum != db_checksum
    ):

        print(
            f"[RECOVERY] "
            f"Primary corrupted/missing: "
            f"{file_name}"
        )

        file_content = await download_from_node(
            document.replica_node,
            file_name
        )

        await restore_to_node(
            document.storage_node,
            file_name,
            file_content
        )

        print(
            f"[RECOVERY SUCCESS] "
            f"Primary restored: "
            f"{file_name}"
        )

        return "primary_recovered"

    # ------------------------------------------
    # Case 3
    # Replica missing/corrupted
    # Primary matches DB
    # ------------------------------------------

    if (
        db_checksum
        and primary_checksum == db_checksum
        and replica_checksum != db_checksum
    ):

        print(
            f"[RECOVERY] "
            f"Replica corrupted/missing: "
            f"{file_name}"
        )

        file_content = await download_from_node(
            document.storage_node,
            file_name
        )

        await restore_to_node(
            document.replica_node,
            file_name,
            file_content
        )

        print(
            f"[RECOVERY SUCCESS] "
            f"Replica restored: "
            f"{file_name}"
        )

        return "replica_recovered"

    # ------------------------------------------
    # Case 4
    # ------------------------------------------

    if (
        primary_checksum is None
        and replica_checksum is None
    ):

        print(
            f"[CRITICAL] "
            f"Both copies missing: "
            f"{file_name}"
        )

        return "both_missing"

    # ------------------------------------------
    # Case 5
    # ------------------------------------------

    print(
        f"[CRITICAL] "
        f"No trusted copy available: "
        f"{file_name}"
    )

    return "unrecoverable"