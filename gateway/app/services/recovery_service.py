import os
import hashlib
import httpx

from app.database.session import SessionLocal
from app.models.document import Document
from app.models.recovery_log import RecoveryLog


# =========================================================
# CONFIGURATION
# =========================================================

CHECK_INTERVAL = 30

HTTP_TIMEOUT = 30.0


# =========================================================
# 1. CALCULATE SHA-256 CHECKSUM
# =========================================================

def calculate_checksum(
    file_content: bytes
) -> str:

    sha256 = hashlib.sha256()

    sha256.update(file_content)

    return sha256.hexdigest()


# =========================================================
# 2. CHECK WHETHER FILE EXISTS
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
# 3. GET CHECKSUM FROM STORAGE NODE
# =========================================================

async def get_node_checksum(
    storage_node: str,
    file_name: str
):

    try:

        async with httpx.AsyncClient(
            timeout=10
        ) as client:

            response = await client.get(
                f"{storage_node}/storage/checksum/{file_name}"
            )

        # File does not exist
        if response.status_code == 404:
            return None

        if response.status_code != 200:
            return None

        data = response.json()

        return data.get(
            "checksum"
        )

    except httpx.RequestError:

        return None


# =========================================================
# 4. DOWNLOAD FILE FROM STORAGE NODE
# =========================================================

async def download_from_node(
    storage_node: str,
    file_name: str
):

    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT
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
# 5. RESTORE FILE TO STORAGE NODE
# =========================================================

async def restore_to_node(
    storage_node: str,
    file_name: str,
    file_content: bytes,
    content_type: str = "application/pdf"
):

    files = {

        "file": (
            file_name,
            file_content,
            content_type
        )

    }

    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT
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

    return response.json()


# =========================================================
# 6. SAVE RECOVERY LOG
# =========================================================

def save_recovery_log(
    db,
    document_id: int,
    file_name: str,
    source_node: str | None,
    target_node: str | None,
    status: str,
    message: str
):

    log = RecoveryLog(

        document_id=document_id,

        file_name=file_name,

        source_node=source_node,

        target_node=target_node,

        status=status,

        message=message

    )

    db.add(log)

    db.commit()


# =========================================================
# 7. RECOVER DOCUMENT
# =========================================================

async def recover_document(
    document: Document,
    db
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
    # GET CHECKSUMS
    # =====================================================

    primary_checksum = await get_node_checksum(
        primary,
        file_name
    )

    replica_checksum = await get_node_checksum(
        replica,
        file_name
    )

    db_checksum = document.checksum


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


    # =====================================================
    # CASE 1
    #
    # PRIMARY + REPLICA BOTH EXIST
    #
    # DB == PRIMARY == REPLICA
    #
    # Everything is healthy
    # =====================================================

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


    # =====================================================
    # CASE 2
    #
    # PRIMARY MISSING
    #
    # Replica is available and trusted
    #
    # Replica → Primary
    # =====================================================

    if primary_checksum is None:

        print(
            f"[WARNING] Primary missing: "
            f"{file_name}"
        )


        # ---------------------------------------------
        # Replica also missing
        # ---------------------------------------------

        if replica_checksum is None:

            print(
                f"[CRITICAL] Both primary "
                f"and replica missing: "
                f"{file_name}"
            )

            save_recovery_log(

                db=db,

                document_id=document.id,

                file_name=file_name,

                source_node=None,

                target_node=primary,

                status="FAILED",

                message=(
                    "Both primary and "
                    "replica files are missing"
                )

            )

            return "both_missing"


        # ---------------------------------------------
        # Check whether replica is trusted
        # ---------------------------------------------

        if (
            db_checksum
            and replica_checksum != db_checksum
        ):

            print(
                f"[CRITICAL] "
                f"Replica checksum does "
                f"not match database: "
                f"{file_name}"
            )

            save_recovery_log(

                db=db,

                document_id=document.id,

                file_name=file_name,

                source_node=replica,

                target_node=primary,

                status="FAILED",

                message=(
                    "Replica exists but "
                    "checksum does not "
                    "match database"
                )

            )

            return "unrecoverable"


        # ---------------------------------------------
        # Download from replica
        # ---------------------------------------------

        print(
            f"[RECOVERY] "
            f"Downloading {file_name} "
            f"from replica"
        )

        file_content = await download_from_node(

            replica,

            file_name

        )


        # ---------------------------------------------
        # Verify downloaded data
        # ---------------------------------------------

        downloaded_checksum = calculate_checksum(
            file_content
        )

        if (
            db_checksum
            and downloaded_checksum != db_checksum
        ):

            print(
                f"[CRITICAL] "
                f"Replica data corrupted: "
                f"{file_name}"
            )

            save_recovery_log(

                db=db,

                document_id=document.id,

                file_name=file_name,

                source_node=replica,

                target_node=primary,

                status="FAILED",

                message=(
                    "Replica checksum "
                    "verification failed"
                )

            )

            return "unrecoverable"


        # ---------------------------------------------
        # Restore Primary
        # ---------------------------------------------

        print(
            f"[RECOVERY] "
            f"Restoring {file_name} "
            f"to primary"
        )

        await restore_to_node(

            primary,

            file_name,

            file_content,

            document.content_type

        )


        # ---------------------------------------------
        # Recovery log
        # ---------------------------------------------

        save_recovery_log(

            db=db,

            document_id=document.id,

            file_name=file_name,

            source_node=replica,

            target_node=primary,

            status="SUCCESS",

            message=(
                "Primary restored "
                "from replica"
            )

        )

        print(
            f"[RECOVERY SUCCESS] "
            f"{file_name} restored "
            f"to primary"
        )

        return "primary_recovered"


    # =====================================================
    # CASE 3
    #
    # REPLICA MISSING
    #
    # Primary is trusted
    #
    # Primary → Replica
    # =====================================================

    if replica_checksum is None:

        print(
            f"[WARNING] Replica missing: "
            f"{file_name}"
        )


        # ---------------------------------------------
        # Primary must match DB
        # ---------------------------------------------

        if (
            db_checksum
            and primary_checksum != db_checksum
        ):

            print(
                f"[CRITICAL] "
                f"Primary checksum does "
                f"not match database: "
                f"{file_name}"
            )

            save_recovery_log(

                db=db,

                document_id=document.id,

                file_name=file_name,

                source_node=primary,

                target_node=replica,

                status="FAILED",

                message=(
                    "Primary exists but "
                    "checksum does not "
                    "match database"
                )

            )

            return "unrecoverable"


        # ---------------------------------------------
        # Download from Primary
        # ---------------------------------------------

        print(
            f"[RECOVERY] "
            f"Downloading {file_name} "
            f"from primary"
        )

        file_content = await download_from_node(

            primary,

            file_name

        )


        # ---------------------------------------------
        # Verify downloaded data
        # ---------------------------------------------

        downloaded_checksum = calculate_checksum(
            file_content
        )

        if (
            db_checksum
            and downloaded_checksum != db_checksum
        ):

            print(
                f"[CRITICAL] "
                f"Primary data corrupted: "
                f"{file_name}"
            )

            save_recovery_log(

                db=db,

                document_id=document.id,

                file_name=file_name,

                source_node=primary,

                target_node=replica,

                status="FAILED",

                message=(
                    "Primary checksum "
                    "verification failed"
                )

            )

            return "unrecoverable"


        # ---------------------------------------------
        # Restore Replica
        # ---------------------------------------------

        print(
            f"[RECOVERY] "
            f"Restoring {file_name} "
            f"to replica"
        )

        await restore_to_node(

            replica,

            file_name,

            file_content,

            document.content_type

        )


        # ---------------------------------------------
        # Recovery log
        # ---------------------------------------------

        save_recovery_log(

            db=db,

            document_id=document.id,

            file_name=file_name,

            source_node=primary,

            target_node=replica,

            status="SUCCESS",

            message=(
                "Replica restored "
                "from primary"
            )

        )

        print(
            f"[RECOVERY SUCCESS] "
            f"{file_name} restored "
            f"to replica"
        )

        return "replica_recovered"


    # =====================================================
    # CASE 4
    #
    # PRIMARY CORRUPTED
    #
    # Replica == DB
    #
    # Replica → Primary
    # =====================================================

    if (
        db_checksum
        and replica_checksum == db_checksum
        and primary_checksum != db_checksum
    ):

        print(
            f"[CORRUPTION DETECTED] "
            f"Primary corrupted: "
            f"{file_name}"
        )


        # ---------------------------------------------
        # Download trusted Replica
        # ---------------------------------------------

        file_content = await download_from_node(

            replica,

            file_name

        )


        # ---------------------------------------------
        # Verify Replica
        # ---------------------------------------------

        downloaded_checksum = calculate_checksum(
            file_content
        )

        if downloaded_checksum != db_checksum:

            print(
                f"[CRITICAL] "
                f"Replica verification failed: "
                f"{file_name}"
            )

            save_recovery_log(

                db=db,

                document_id=document.id,

                file_name=file_name,

                source_node=replica,

                target_node=primary,

                status="FAILED",

                message=(
                    "Trusted replica "
                    "verification failed"
                )

            )

            return "unrecoverable"


        # ---------------------------------------------
        # Restore Primary
        # ---------------------------------------------

        await restore_to_node(

            primary,

            file_name,

            file_content,

            document.content_type

        )


        save_recovery_log(

            db=db,

            document_id=document.id,

            file_name=file_name,

            source_node=replica,

            target_node=primary,

            status="SUCCESS",

            message=(
                "Corrupted primary "
                "restored from replica"
            )

        )

        print(
            f"[RECOVERY SUCCESS] "
            f"Primary restored: "
            f"{file_name}"
        )

        return "primary_recovered"


    # =====================================================
    # CASE 5
    #
    # REPLICA CORRUPTED
    #
    # Primary == DB
    #
    # Primary → Replica
    # =====================================================

    if (
        db_checksum
        and primary_checksum == db_checksum
        and replica_checksum != db_checksum
    ):

        print(
            f"[CORRUPTION DETECTED] "
            f"Replica corrupted: "
            f"{file_name}"
        )


        # ---------------------------------------------
        # Download trusted Primary
        # ---------------------------------------------

        file_content = await download_from_node(

            primary,

            file_name

        )


        # ---------------------------------------------
        # Verify Primary
        # ---------------------------------------------

        downloaded_checksum = calculate_checksum(
            file_content
        )

        if downloaded_checksum != db_checksum:

            print(
                f"[CRITICAL] "
                f"Primary verification failed: "
                f"{file_name}"
            )

            save_recovery_log(

                db=db,

                document_id=document.id,

                file_name=file_name,

                source_node=primary,

                target_node=replica,

                status="FAILED",

                message=(
                    "Trusted primary "
                    "verification failed"
                )

            )

            return "unrecoverable"


        # ---------------------------------------------
        # Restore Replica
        # ---------------------------------------------

        await restore_to_node(

            replica,

            file_name,

            file_content,

            document.content_type

        )


        save_recovery_log(

            db=db,

            document_id=document.id,

            file_name=file_name,

            source_node=primary,

            target_node=replica,

            status="SUCCESS",

            message=(
                "Corrupted replica "
                "restored from primary"
            )

        )

        print(
            f"[RECOVERY SUCCESS] "
            f"Replica restored: "
            f"{file_name}"
        )

        return "replica_recovered"


    # =====================================================
    # CASE 6
    #
    # NO TRUSTED COPY
    # =====================================================

    print(
        f"[CRITICAL] "
        f"No trusted copy available: "
        f"{file_name}"
    )

    save_recovery_log(

        db=db,

        document_id=document.id,

        file_name=file_name,

        source_node=None,

        target_node=None,

        status="FAILED",

        message=(
            "No trusted copy available"
        )

    )

    return "unrecoverable"


# =========================================================
# 8. VERIFY DOCUMENT INTEGRITY
# =========================================================

async def verify_document_integrity(
    document: Document
):

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
        f"[INTEGRITY CHECK] "
        f"{file_name}"
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


    # =====================================================
    # ALL THREE MATCH
    # =====================================================

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


    # =====================================================
    # PRIMARY == DB
    #
    # REPLICA CORRUPTED
    # =====================================================

    if (
        db_checksum
        and primary_checksum == db_checksum
        and replica_checksum != db_checksum
    ):

        print(
            f"[CORRUPTION DETECTED] "
            f"Replica corrupted: "
            f"{file_name}"
        )

        file_content = await download_from_node(

            document.storage_node,

            file_name

        )

        downloaded_checksum = calculate_checksum(
            file_content
        )

        if downloaded_checksum != db_checksum:

            return "unrecoverable"


        await restore_to_node(

            document.replica_node,

            file_name,

            file_content,

            document.content_type

        )

        print(
            f"[RECOVERY SUCCESS] "
            f"Replica restored: "
            f"{file_name}"
        )

        return "replica_recovered"


    # =====================================================
    # REPLICA == DB
    #
    # PRIMARY CORRUPTED
    # =====================================================

    if (
        db_checksum
        and replica_checksum == db_checksum
        and primary_checksum != db_checksum
    ):

        print(
            f"[CORRUPTION DETECTED] "
            f"Primary corrupted: "
            f"{file_name}"
        )

        file_content = await download_from_node(

            document.replica_node,

            file_name

        )

        downloaded_checksum = calculate_checksum(
            file_content
        )

        if downloaded_checksum != db_checksum:

            return "unrecoverable"


        await restore_to_node(

            document.storage_node,

            file_name,

            file_content,

            document.content_type

        )

        print(
            f"[RECOVERY SUCCESS] "
            f"Primary restored: "
            f"{file_name}"
        )

        return "primary_recovered"


    # =====================================================
    # BOTH MISSING
    # =====================================================

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


    # =====================================================
    # NO TRUSTED COPY
    # =====================================================

    print(
        f"[CRITICAL] "
        f"No trusted copy available: "
        f"{file_name}"
    )

    return "unrecoverable"


# =========================================================
# 9. RUN PERIODIC RECOVERY CHECK
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

                # -----------------------------------------
                # Recovery
                # -----------------------------------------

                await recover_document(

                    document,

                    db

                )


                # -----------------------------------------
                # Integrity verification
                # -----------------------------------------

                result = (
                    await verify_document_integrity(
                        document
                    )
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