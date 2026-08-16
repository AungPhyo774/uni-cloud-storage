# Distributed Cloud Storage System for University Documents

A university document storage system built with **FastAPI, PostgreSQL, Docker, Nginx, and JavaScript**. It provides JWT authentication, class-based access control, primary/replica storage, SHA-256 integrity verification, automatic recovery, monitoring, and LAN client access.

> **Current deployment:** Laptop A is the physical server. Node 1/2/3 are separate logical storage nodes running in Docker containers on Laptop A. Other laptops use only a web browser as clients.

## 1. Main Features

- Admin, Student, and Lecturer login with JWT.
- Admin creates Student/Lecturer accounts and assigns class year.
- Class-based document isolation.
- Student uploads to a selected lecturer in the same class.
- Lecturer uploads lecture documents for the same class.
- Student and Lecturer document lists, downloads, and permitted deletion.
- Three logical storage nodes with Round-Robin placement.
- Primary + replica copies.
- Node health monitoring and replica fallback.
- SHA-256 checksum verification.
- Automatic missing-primary recovery.
- Recovery logs and Admin monitoring.
- LAN access without installing the backend project on client laptops.

## 2. Architecture

```text
                    Same Wi-Fi / LAN
                           |
          +----------------+----------------+
          |                                 |
     Laptop B/C                         Laptop A
      Client                              Server
     Browser                                 |
          |                               Docker
          +-------- HTTP -----------------+
                                           |
                                        Nginx :8080
                                           |
                                    Frontend + Gateway
                                           |
                           +---------------+--------------+
                           |               |              |
                           v               v              v
                      PostgreSQL       Node 1           Node 2
                                       :9001            :9002
                                                           |
                                                           v
                                                        Node 3
                                                        :9003
```

**Important:** Node 1/2/3 are not three physical servers in the current setup. They are isolated Docker-based logical storage nodes on one physical server.

## 3. Project Structure

```text
distributed-cloud-storage/
├── frontend/
├── gateway/app/
├── storage-node-1/
├── storage-node-2/
├── storage-node-3/
├── nginx/default.conf
├── database/
├── docker-compose.yml
└── README.md
```

## 4. Technology Stack

- Frontend: HTML, CSS, JavaScript
- Backend: FastAPI, Uvicorn, SQLAlchemy, HTTPX
- Database: PostgreSQL
- Auth: JWT, bcrypt, python-jose
- Web server: Nginx
- Deployment: Docker, Docker Compose
- Integrity: SHA-256

## 5. Database

### `users`

```text
id, full_name, email, password_hash, role, class_year, is_active, created_at
```

### `documents`

```text
id, owner_id, lecturer_id, file_name, file_path, file_size,
content_type, storage_node, replica_node, checksum, created_at
```

### `recovery_logs`

```text
id, document_id, file_name, source_node, target_node, status, message, created_at
```

The database stores **metadata**, not the actual uploaded file binary.

## 6. Roles and Permissions

### Admin

- Login with the configured administrator account.
- Create Student/Lecturer accounts.
- Assign or change class.
- Activate/deactivate users.
- View node health, replication, recovery statistics, and recovery logs.

### Student

- Login and view class.
- Select a same-class lecturer.
- Upload documents.
- View their own documents.
- View/download lecturer documents for their class.
- Delete their own documents.

### Lecturer

- Login and view class.
- Upload lecture documents.
- View own documents.
- View/download student submissions assigned to them.
- Delete own documents.

Backend authorization is the real security boundary; frontend checks only control the UI.

## 7. Class Isolation

Supported classes:

```text
first_year
second_year
third_year
fourth_year
fifth_year
```

Example:

```text
First-year Student -> First-year content ✅
First-year Student -> Second-year content ❌
```

## 8. Document Flow

### Student upload

```text
Browser -> Nginx -> Gateway
                  |
                  +-> Validate user/class/lecturer
                  +-> SHA-256
                  +-> Select primary + replica
                  +-> Store file
                  +-> Save metadata in PostgreSQL
```

### Download

```text
Browser -> Gateway -> Primary
                       |
                       +-> fail -> Replica -> Browser
```

## 9. Replication

Primary/replica pair selection follows the logical sequence:

```text
Node 1 -> Node 2
Node 2 -> Node 3
Node 3 -> Node 1
```

PostgreSQL records:

```text
storage_node
replica_node
```

Example:

```text
assignment.docx
Primary = Node 1
Replica = Node 2
```

## 10. Integrity and Recovery

SHA-256 is calculated during upload and stored in PostgreSQL. Verification compares:

```text
Database checksum
      +
Primary checksum
      +
Replica checksum
```

Example healthy state:

```text
DB       = ABC123
Primary  = ABC123
Replica  = ABC123
```

Automatic recovery follows this idea:

```text
Periodic check
     |
     v
Primary missing/corrupt?
     |
     v
Check replica
     |
     v
Copy replica -> primary
     |
     v
Write recovery log
```

A recovery record can look like:

```text
Document: assignment.pdf
Source: Node 2
Target: Node 1
Status: SUCCESS
```

## 11. Main API Endpoints

```text
POST /auth/login                    GET /users/me
GET  /documents/lecturers-list     POST /documents/upload-to-lecturer/{lecturer_id}
POST /documents/lecturer/upload    GET  /documents/my-all-documents
GET  /documents/lecturer-documents  GET  /documents/student-documents
GET  /documents/{document_id}/download
DELETE /documents/{document_id}
GET  /admin/nodes/health            GET /admin/replication/status
GET  /recovery/stats                GET /recovery/logs
```

## 12. Docker Setup

From the project root on **Laptop A**:

```powershell
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Stop:

```powershell
docker compose down
```

Logs:

```powershell
docker compose logs -f gateway
docker compose logs -f nginx
```

## 13. Docker Node URLs

Inside Compose, use service names:

```text
storage-node-1:9001
storage-node-2:9002
storage-node-3:9003
```


## 14. Persistent Storage

Keep each node separate:

```yaml
storage-node-1: { volumes: [./storage-node-1/storage:/app/storage] }
storage-node-2: { volumes: [./storage-node-2/storage:/app/storage] }
storage-node-3: { volumes: [./storage-node-3/storage:/app/storage] }
```


## 15. Nginx and Frontend

When Windows port 80 is unavailable, use for example:

```yaml
ports:
  - "8080:80"
```

Then open:

```text
http://localhost:8080/
http://localhost:8080/docs
```

For Option A, the frontend can use:

```javascript
const API_BASE_URL = "";
```

This keeps client requests on the same server origin.

## 16. LAN Client Access

Laptop A is the server. Laptop B/C are clients. Client laptops only need a browser and the same LAN/Wi-Fi.

Find Laptop A's address:

```powershell
ipconfig
```

Example:

```text
192.168.1.10
```

A client then opens:

```text
http://192.168.1.10:8080/
```

The client laptops do **not** need:

```text
Python
FastAPI
PostgreSQL
Docker
Storage Node code
Backend source code
```

## 17. Test Plan

```text
[✓] Admin/Student/Lecturer login
[✓] Admin creates users and assigns classes
[✓] Same-class access; cross-class denied
[✓] Student/Lecturer upload, list, download, delete
[✓] Round-Robin primary/replica placement
[✓] Node health and replica fallback
[✓] SHA-256 integrity verification
[✓] Automatic recovery and recovery logs
[✓] LAN access from client laptop(s)
```

## 18. Failure Test

Stop a storage node:

```powershell
docker compose stop storage-node-1
```

Verify Admin shows Node 1 offline. A document whose primary is Node 1 should still be downloadable from its replica when fallback is available.

Restart:

```powershell
docker compose start storage-node-1
```

If the primary copy is missing, the recovery service should restore it from the replica and create a recovery log.

## 19. Useful PostgreSQL Checks

Open PostgreSQL:

```powershell
docker compose exec postgres psql -U postgres -d distributed_storage
```

Users:

```sql
SELECT id, full_name, email, role, class_year, is_active
FROM users ORDER BY id DESC;
```

Documents:

```sql
SELECT id, file_name, owner_id, lecturer_id, storage_node, replica_node, checksum
FROM documents ORDER BY id DESC;
```

Recovery:

```sql
SELECT id, document_id, file_name, source_node, target_node, status, created_at
FROM recovery_logs ORDER BY id DESC;
```


## 20. Data Location

```text
User accounts        -> PostgreSQL users
Document metadata    -> PostgreSQL documents
Recovery history     -> PostgreSQL recovery_logs
Actual files         -> Node 1/2/3 storage directories/volumes
```


## 21. What This Project Demonstrates

```text
Authentication
Role-based authorization
Class-based isolation
Multiple logical storage nodes
Round-Robin placement
Primary/replica replication
Fault tolerance
Replica fallback
SHA-256 integrity verification
Automatic recovery
Node monitoring
Recovery logging
Multi-client LAN access
```

## 22. Final Architecture Summary

```text
Client Browser -> Nginx -> FastAPI Gateway
                         -> PostgreSQL
                         -> Node 1/2/3
                         -> Primary + Replica
                         -> Checksum + Recovery
```

The current Option A deployment demonstrates logical distributed storage. Node 1/2/3 can later be moved to separate physical/virtual servers for stronger host-level fault tolerance.


## Project Title

**Distributed Cloud Storage System for University Documents**
