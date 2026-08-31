# Campus Hub: Distributed Storage System for University Documents

**Campus Hub** is a web-based university document management system built around a distributed storage architecture. It separates application logic, document metadata, and physical file storage so that university documents can be managed through role-based access, multiple logical storage nodes, replication, integrity checking, and recovery.

## Overview

Campus Hub is designed for a university environment with three main user roles:

- **Administrator** — manages users, classes, imports, storage health, replication, and recovery.
- **Lecturer** — manages teaching classes, uploads lecture materials, and reviews student submissions.
- **Student** — selects lecturers from the same class, uploads documents, and manages or downloads permitted documents.

> **Current deployment:** Laptop A acts as the physical server. Storage Node 1, Node 2, and Node 3 run as separate Docker containers on Laptop A. Other laptops connect as browser-based clients through the LAN.

---

## 1. Core Features

### Authentication & Authorization
- JWT-based login.
- Three roles: **Admin, Lecturer, Student**.
- Backend role-based authorization.
- Role-specific dashboards and protected APIs.

### Admin Management
- Create Student and Lecturer accounts.
- Import Students from Excel.
- Import Lecturers from Excel.
- Activate/deactivate accounts.
- Assign a Student to a class.
- View system, storage, replication, and recovery status.

### Automatic Passwords
- System generates a **6-character initial password** for created/imported Student and Lecturer accounts.
- The generated password is shown to the Admin in the creation/import result.
- Only the password hash is stored in PostgreSQL.

```text
Generate Password
       ↓
Show to Admin
       ↓
bcrypt hash
       ↓
Store password_hash only
```

### Lecturer Multi-Class
A Lecturer can teach multiple classes.

Example:

```text
Daw Moe Moe
 ├── First Year
 ├── Second Year
 └── Fourth Year
```

Teaching assignments are stored through the lecturer-to-class relationship.

### Student Documents
- Select a lecturer from the student's class.
- Upload documents.
- View personal documents.
- Download permitted documents.
- Delete permitted documents.
- View/download lecturer documents for the class.

### Lecturer Documents
- Upload lecture materials.
- View personal documents.
- View assigned student submissions.
- Download permitted submissions.
- Delete permitted own documents.

### Distributed Storage
- Three logical storage nodes.
- Each node runs as a separate Docker container.
- Primary and replica copies are maintained.
- Storage placement uses a logical Round-Robin sequence.

### Replication
```text
Node 1 → Node 2
Node 2 → Node 3
Node 3 → Node 1
```

Example:

```text
assignment.docx
Primary  = Node 1
Replica  = Node 2
```

### Integrity & Recovery
- SHA-256 checksum is calculated during upload.
- Checksum is stored in PostgreSQL.
- Storage-node health is monitored.
- Replica fallback is available when a primary node cannot be reached.
- Missing/corrupted primary files can be recovered from a valid replica.
- Recovery operations are recorded in recovery logs.

### Excel Bulk Import
Admins can create multiple accounts from Excel.

#### Students
```text
full_name | email | class_year
```

#### Lecturers
```text
full_name | email | classes
```

Example Lecturer row:

```text
U Hla | uhla@gmail.com | first_year,second_year,fourth_year
```

Import results can report:

```text
Total Rows
Created
Skipped
Reason
Generated Password
```

---

## 2. Architecture

### Option A — One Server + Multiple Clients

```text
                         Same Wi-Fi / LAN
                                |
                +---------------+---------------+
                |                               |
           Laptop B/C                       Laptop A
            CLIENT                            SERVER
            Browser                              |
                |                              Docker
                +--------- HTTP ----------------+
                                                |
                                             Nginx :8080
                                                |
                                          FastAPI Gateway
                                                |
                            +-------------------+------------------+
                            |                   |                  |
                            v                   v                  v
                       PostgreSQL          Storage Node 1     Storage Node 2
                                             :9001              :9002
                                                                     |
                                                                     v
                                                                Storage Node 3
                                                                     :9003
```

**Important:** Node 1/2/3 are three **logical storage nodes**, not three physical servers. They currently run as separate Docker containers on one physical server.

---

## 3. Request / Document Flow

### Student Upload

```text
Student Browser
      ↓
Nginx
      ↓
FastAPI Gateway
      ↓
Authenticate + authorize
      ↓
Validate class / lecturer
      ↓
Calculate SHA-256
      ↓
Select primary + replica
      ↓
Store file on storage nodes
      ↓
Save metadata in PostgreSQL
```

### Download

```text
Browser
  ↓
Gateway
  ↓
Authorization
  ↓
Primary Node
  |
  +---- available → return file
  |
  +---- unavailable → Replica → return file
```

---

## 4. Project Structure

```text
distributed-cloud-storage/
│
├── frontend/
│   ├── login.html
│   ├── admin-dashboard.html
│   ├── admin-users.html
│   ├── lecturer-dashboard.html
│   ├── lecturer-classes.html
│   ├── lecturer-upload.html
│   ├── lecturer-my-documents.html
│   ├── student-dashboard.html
│   ├── student-upload.html
│   ├── student-documents.html
│   ├── lecturer-documents.html
│   ├── student-submissions.html
│   └── js/
│       └── api.js
│
├── gateway/
│   ├── app/
│   │   ├── dependencies/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── Dockerfile
│   └── requirements.txt
│
├── storage-node-1/
├── storage-node-2/
├── storage-node-3/
│
├── nginx/
│   └── default.conf
│
├── database/
│
├── docker-compose.yml
└── README.md
```

---

## 5. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript, Tailwind CSS |
| Backend | Python, FastAPI, Uvicorn |
| ORM | SQLAlchemy |
| Database | PostgreSQL 16 |
| Authentication | JWT, python-jose |
| Password Security | bcrypt |
| HTTP Communication | HTTPX |
| Web Server | Nginx |
| Deployment | Docker, Docker Compose |
| Integrity | SHA-256 |

---

## 6. Database

### `users`

```text
id
full_name
email
password_hash
role
class_year
is_active
created_at
```

### `class_years`

```text
id
class_year
display_name
```

Supported classes:

```text
first_year
second_year
third_year
fourth_year
fifth_year
```

### `lecturer_teaching_classes`

```text
id
lecturer_id
class_id
```

This supports multiple teaching classes per Lecturer.

### `documents`

```text
id
owner_id
lecturer_id
file_name
file_path
file_size
content_type
storage_node
replica_node
checksum
created_at
```

### `recovery_logs`

```text
id
document_id
file_name
source_node
target_node
status
message
created_at
```

> PostgreSQL stores application and document **metadata**. Actual uploaded files are stored in the storage-node directories/volumes.

---

## 7. Roles & Permissions

### Admin

```text
Login
Create users
Import Students/​Lecturers
Manage users
Assign classes
Monitor nodes
View replication
View recovery
```

### Student

```text
Login
View class
Select same-class lecturer
Upload documents
View own documents
Download permitted documents
Delete permitted own documents
View/download class lecturer documents
```

### Lecturer

```text
Login
View teaching classes
Manage multiple teaching classes
Upload lecture documents
View own documents
View student submissions assigned to them
Download permitted submissions
Delete permitted own documents
```

> Backend authorization is the real security boundary. Frontend role checks are for UI navigation only.

---

## 8. Class-Based Access

The system separates content by academic class.

```text
First-year Student
        ↓
First-year lecturer/content
        ✅

First-year Student
        ↓
Second-year-only content
        ❌
```

A Lecturer can be assigned to more than one class.

---

## 9. Main API Endpoints

### Authentication

```text
POST /auth/login
GET  /users/me
```

### Documents

```text
GET    /documents/lecturers-list
POST   /documents/upload-to-lecturer/{lecturer_id}
POST   /documents/lecturer/upload
GET    /documents/my-all-documents
GET    /documents/lecturer-documents
GET    /documents/student-documents
GET    /documents/{document_id}/download
DELETE /documents/{document_id}
```

### Admin

```text
GET /admin/users
GET /admin/classes/summary
GET /admin/nodes/health
GET /admin/replication/status
```

### Excel Import

```text
POST /admin/import/students
POST /admin/import/lecturers
```

### Lecturer Classes

```text
GET /lecturers/classes
GET /lecturers/me/classes
PUT /lecturers/me/classes
```

### Recovery

```text
GET /recovery/stats
GET /recovery/logs
GET /recovery/logs/filter?status=...
```

Use:

```text
http://localhost:8080/docs
```

as the authoritative Swagger/OpenAPI reference for the deployed build.

---

## 10. Docker Deployment

From the project root on Laptop A:

```powershell
docker compose up -d
```

Check:

```powershell
docker compose ps
```

Typical services:

```text
distributed-nginx
distributed-gateway
distributed-postgres
storage-node-1
storage-node-2
storage-node-3
```

### Rebuild after code/dependency changes

```powershell
docker compose up -d --build
```

### Clean rebuild

```powershell
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Stop

```powershell
docker compose down
```

### Logs

```powershell
docker compose logs -f gateway
docker compose logs -f nginx
docker compose logs -f storage-node-1
docker compose logs -f storage-node-2
docker compose logs -f storage-node-3
```

---

## 11. Docker Storage Nodes

Inside Docker Compose, the Gateway communicates with the storage services using:

```text
storage-node-1:9001
storage-node-2:9002
storage-node-3:9003
```

Do not use `127.0.0.1:9001`, `127.0.0.1:9002`, or `127.0.0.1:9003` for Gateway-to-node communication inside the Compose network.

---

## 12. Persistent Storage

Each storage node has its own mounted directory:

```yaml
storage-node-1:
  volumes:
    - ./storage-node-1/storage:/app/storage

storage-node-2:
  volumes:
    - ./storage-node-2/storage:/app/storage

storage-node-3:
  volumes:
    - ./storage-node-3/storage:/app/storage
```

PostgreSQL also uses a persistent Docker volume.

---

## 13. Nginx / Frontend

The current host port is:

```yaml
ports:
  - "8080:80"
```

Open on Laptop A:

```text
http://localhost:8080/
http://localhost:8080/docs
```

For same-origin API calls:

```javascript
const API_BASE_URL = "";
```

---

## 14. LAN Deployment

Laptop A:

```text
SERVER
Docker
Nginx
Gateway
PostgreSQL
Node 1
Node 2
Node 3
```

Laptop B/C:

```text
CLIENT
Browser only
```

Find Laptop A's IP:

```powershell
ipconfig
```

Example:

```text
192.168.1.10
```

Clients open:

```text
http://192.168.1.10:8080/
```

Client laptops do **not** need:

```text
Python
FastAPI
PostgreSQL
Docker
Backend source code
Storage-node source code
```

They only need a browser and access to the same LAN/Wi-Fi.

---

## 15. Data Location

```text
Users              → PostgreSQL.users
Classes             → PostgreSQL.class_years
Lecturer classes    → PostgreSQL.lecturer_teaching_classes
Document metadata   → PostgreSQL.documents
Recovery history    → PostgreSQL.recovery_logs
Actual files        → Storage Node 1/2/3 volumes
```

---

## 16. Integrity & Recovery

### Checksum

```text
Upload file
    ↓
SHA-256
    ↓
Store checksum in PostgreSQL
```

A healthy document conceptually has:

```text
Database checksum = Primary checksum = Replica checksum
```

### Recovery

```text
Health check
    ↓
Primary missing/corrupt?
    ↓
Check replica
    ↓
Copy valid replica → primary
    ↓
Write recovery log
```

Example:

```text
Document: assignment.pdf
Source: Node 2
Target: Node 1
Status: SUCCESS
```

---

## 17. Failure Testing

Stop a node:

```powershell
docker compose stop storage-node-1
```

Check:

```powershell
docker compose ps
```

Verify the Admin UI reports Node 1 as unavailable.

For a document whose primary is Node 1, test download and verify that a valid replica can be used.

Restart:

```powershell
docker compose start storage-node-1
```

Then verify recovery and recovery logs where applicable.

---

## 18. Useful PostgreSQL Checks

Open PostgreSQL:

```powershell
docker compose exec postgres psql -U postgres -d distributed_storage
```

### Users

```sql
SELECT
    id,
    full_name,
    email,
    role,
    class_year,
    is_active
FROM users
ORDER BY id DESC;
```

### Documents

```sql
SELECT
    id,
    file_name,
    owner_id,
    lecturer_id,
    storage_node,
    replica_node,
    checksum
FROM documents
ORDER BY id DESC;
```

### Lecturer Teaching Classes

```sql
SELECT
    ltc.id,
    u.full_name AS lecturer,
    cy.class_year
FROM lecturer_teaching_classes ltc
JOIN users u
    ON u.id = ltc.lecturer_id
JOIN class_years cy
    ON cy.id = ltc.class_id
ORDER BY u.full_name, cy.id;
```

### Recovery

```sql
SELECT
    id,
    document_id,
    file_name,
    source_node,
    target_node,
    status,
    created_at
FROM recovery_logs
ORDER BY id DESC;
```

---

## 19. Troubleshooting

### 401 Unauthorized

Clear the browser token:

```javascript
localStorage.removeItem("access_token");
```

Then log in again.

### 403 Forbidden

Check the user's role and class relationship.

### 502 Bad Gateway

Check:

```powershell
docker compose ps
docker compose logs gateway
docker compose logs nginx
```

### API returns HTML instead of JSON

Check Nginx API routing. For example:

```nginx
location ^~ /lecturers/ {
    proxy_pass http://gateway:8000;
}
```

API routes must be proxied to the Gateway before the frontend fallback route.

### Frontend shows old JavaScript

Use:

```text
Ctrl + Shift + R
```

for a hard refresh.

---

## 20. Docker Image Export

Export application images:

```powershell
docker save -o campus-hub-images.tar `
  distributed-cloud-storage-gateway:latest `
  distributed-cloud-storage-storage-node-1:latest `
  distributed-cloud-storage-storage-node-2:latest `
  distributed-cloud-storage-storage-node-3:latest `
  nginx:alpine `
  postgres:16
```

Load them on another Docker host:

```powershell
docker load -i campus-hub-images.tar
```

> Docker images do not contain PostgreSQL's current volume data or uploaded files. Those require separate backup/transfer procedures.

---

## 21. Current Deployment Limitation

The current architecture provides **logical distributed storage**, because Node 1, Node 2, and Node 3 are separate containers on the same physical server.

```text
One physical laptop
       ↓
Docker
       ↓
Node 1
Node 2
Node 3
```

If the physical server itself fails, all three logical nodes are unavailable.

For stronger host-level fault tolerance, the storage nodes can later be distributed across separate physical or virtual servers.

---

## 22. Future Enhancements

Possible future improvements include:

- Student academic class history.
- Admin promotion workflow:
  `First Year → Second Year → Third Year → ...`
- Graduation management.
- Document history linked to academic year/class.

---

## 23. Final Architecture Summary

```text
Client Browser
      ↓
Nginx
      ↓
FastAPI Gateway
      ├── PostgreSQL
      │     ├── Users
      │     ├── Classes
      │     ├── Document Metadata
      │     └── Recovery Logs
      │
      └── Distributed Storage
            ├── Node 1
            ├── Node 2
            └── Node 3
                 ↓
          Primary + Replica
                 ↓
        SHA-256 + Recovery
```

---

## Project Title

**Campus Hub: Distributed Storage System for University Documents**

## Author

**Aung Phyo Hein**
