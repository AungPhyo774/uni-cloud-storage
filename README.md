# Campus Hub: Distributed Storage System for University Documents

> **Campus Hub** is a web-based university document management system built around a distributed storage architecture. It separates application logic, document metadata, and physical file storage so that university documents can be managed through role-based access, multiple logical storage nodes, replication, integrity checking, and recovery.

## Overview

Campus Hub is designed for a university environment with three main user roles:

- **Administrator** — manages users, classes, imports, storage health, replication, and recovery.
- **Lecturer** — manages teaching classes, uploads lecture materials, and reviews student submissions.
- **Student** — selects lecturers from the same class, uploads documents, and manages or downloads permitted documents.

The current deployment uses **one physical server laptop (Laptop A)** running Docker containers. Three isolated logical storage nodes run as separate containers on that server. Other laptops connect through the local network using only a web browser.

---

## Main Goals

Campus Hub focuses on:

1. Centralized university document management.
2. Separation of metadata from physical file storage.
3. Multiple logical storage nodes instead of a single file-storage service.
4. Primary and replica copies for document availability.
5. SHA-256 checksum verification for file integrity.
6. Node health monitoring and replica fallback.
7. Automatic recovery of missing or corrupted primary copies.
8. Role-based and class-based access control.
9. Bulk user creation through Excel files.
10. Lecturer multi-class management.
11. LAN deployment where client laptops do not need the project source code or backend software.

---

## Core Features

### Authentication and Authorization

- JWT-based login.
- Three roles:
  - Admin
  - Lecturer
  - Student
- Backend role authorization.
- Role-specific dashboards.
- Protected API endpoints.
- Frontend role checks are used for UI navigation, while backend authorization is the actual security boundary.

### Admin User Management

Admins can:

- Create Student accounts.
- Create Lecturer accounts.
- Assign a Student to one class.
- Assign a Lecturer to multiple teaching classes.
- Activate or deactivate users.
- View user information.
- Import Students from Excel.
- Import Lecturers from Excel.
- View generated initial passwords after account creation/import.

### Automatic Password Generation

Student and Lecturer accounts can receive an automatically generated **6-character initial password**.

The workflow is:

```text
Admin creates/imports account
        ↓
System generates 6-character password
        ↓
Password is displayed to Admin in the creation/import result
        ↓
Password is hashed with bcrypt
        ↓
Only password_hash is stored in PostgreSQL
```

The plaintext generated password is not intended to be stored as a database password value.

### Lecturer Multi-Class Management

A Lecturer can teach more than one class.

Example:

```text
Daw Moe Moe
    ├── First Year
    ├── Second Year
    └── Fourth Year
```

The relationship is stored through a lecturer-to-class assignment table rather than forcing one class value into the Lecturer account.

Lecturers can view and update their assigned classes from the **My Teaching Classes** UI.

### Class-Based Access

Supported classes:

```text
first_year
second_year
third_year
fourth_year
fifth_year
```

The system uses class information when determining which lecturers and student submissions are related.

Example:

```text
First-year Student
        ↓
First-year Lecturer / First-year content
        ✅ Allowed

First-year Student
        ↓
Second-year-only content
        ❌ Denied
```

### Student Document Management

Students can:

- View their class.
- View/select lecturers related to their class.
- Upload documents to a selected lecturer.
- View their own uploaded documents.
- Download permitted documents.
- Delete their own documents where permitted.
- View/download lecturer documents available to their class.

### Lecturer Document Management

Lecturers can:

- View their teaching classes.
- Upload lecture documents.
- View their own uploaded documents.
- View assigned student submissions.
- Download permitted documents.
- Delete their own documents where permitted.

### Distributed Storage

The current system uses three logical storage nodes:

```text
Node 1 → storage-node-1
Node 2 → storage-node-2
Node 3 → storage-node-3
```

They run as separate Docker containers on the same physical server.

This is a **logical distributed storage deployment**, not three independent physical servers.

### Round-Robin Placement

Primary and replica placement follows a logical sequence such as:

```text
Node 1 → Node 2
Node 2 → Node 3
Node 3 → Node 1
```

For example:

```text
document.pdf

Primary  = Node 1
Replica  = Node 2
```

Another document can use:

```text
Primary  = Node 2
Replica  = Node 3
```

### Replication

Each uploaded document can have:

```text
Primary copy
      +
Replica copy
```

PostgreSQL records the storage locations.

Example metadata:

```text
storage_node = storage-node-1
replica_node = storage-node-2
```

### SHA-256 Integrity Verification

A SHA-256 checksum is generated for uploaded files.

The database stores the expected checksum so the system can compare file integrity.

Conceptually:

```text
Database checksum
       +
Primary file checksum
       +
Replica file checksum
```

A mismatch can indicate that a file is missing or corrupted.

### Automatic Recovery

The recovery process follows:

```text
Periodic check
      ↓
Check node
      ↓
Check file
      ↓
Verify checksum
      ↓
Primary missing/corrupt?
      ↓
Check replica
      ↓
Copy valid replica → primary
      ↓
Write recovery log
```

A recovery log can contain information such as:

```text
Document
Source Node
Target Node
Status
Message
Timestamp
```

### Node Monitoring

Admins can view storage-node health through the Admin UI.

Example:

```text
Node 1   ONLINE
Node 2   ONLINE
Node 3   ONLINE
```

The system can also detect a node becoming unavailable and use replica fallback where appropriate.

### Excel Bulk Import

Admins can import users from Excel instead of creating every account manually.

#### Student Excel format

```text
full_name | email | class_year
```

Example:

```text
Win Win    | win@gmail.com  | first_year
Aung Aung  | aung@gmail.com | first_year
Hla Hla    | hla@gmail.com  | second_year
Mg Mg      | mg@gmail.com   | third_year
```

A Student belongs to one current class.

#### Lecturer Excel format

```text
full_name | email | classes
```

Example:

```text
U Hla | uhla@gmail.com | first_year,second_year,fourth_year
U Min | umin@gmail.com | second_year,third_year
```

A Lecturer can have multiple teaching classes.

Import results can report:

```text
Total Rows
Created
Skipped
Generated Passwords
Reasons for skipped rows
```

---

# Architecture

## Current Deployment: Option A

The current architecture uses one physical server and multiple browser clients.

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
                         +----------------------+------------------+
                         |                      |                  |
                         v                      v                  v
                    PostgreSQL              Node 1              Node 2
                                          :9001                :9002
                                                                    |
                                                                    v
                                                                  Node 3
                                                                  :9003
```

### Important

Node 1, Node 2, and Node 3 are currently:

```text
3 logical storage nodes
        ↓
3 Docker containers
        ↓
1 physical server laptop
```

They are **not three separate physical servers** in the current deployment.

---

## Internal Service Communication

Inside the Docker Compose network, services communicate by service name.

```text
storage-node-1:9001
storage-node-2:9002
storage-node-3:9003
```

The Gateway should use these Docker service names for container-to-container communication instead of `127.0.0.1`.

---

# Project Structure

```text
distributed-cloud-storage/
│
├── frontend/
│   ├── login.html
│   ├── admin-dashboard.html
│   ├── admin-users.html
│   ├── lecturer-dashboard.html
│   ├── lecturer-classes.html
│   ├── student-dashboard.html
│   ├── student-upload.html
│   ├── student-documents.html
│   ├── lecturer-upload.html
│   ├── lecturer-my-documents.html
│   ├── lecturer-documents.html
│   ├── student-submissions.html
│   └── js/
│       ├── api.js
│       ├── admin-users.js
│       ├── lecturer-dashboard.js
│       └── lecturer-classes.js
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
│   ├── app/
│   ├── storage/
│   └── Dockerfile
│
├── storage-node-2/
│   ├── app/
│   ├── storage/
│   └── Dockerfile
│
├── storage-node-3/
│   ├── app/
│   ├── storage/
│   └── Dockerfile
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

# Technology Stack

## Frontend

- HTML5
- CSS3
- JavaScript
- Tailwind CSS

## Backend

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- HTTPX
- Pydantic

## Database

- PostgreSQL 16

## Authentication and Security

- JWT
- `python-jose`
- bcrypt
- Role-based authorization

## Web / Reverse Proxy

- Nginx

## Deployment

- Docker
- Docker Compose

## File Integrity

- SHA-256

---

# Database Design

The database stores document metadata and application information. The actual uploaded file binary is stored in the storage-node volumes.

## `users`

Typical fields:

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

`class_year` represents the current class for a Student where applicable.

## `class_years`

Stores supported academic class definitions.

Typical values:

```text
first_year
second_year
third_year
fourth_year
fifth_year
```

## `lecturer_teaching_classes`

Maps a Lecturer to one or more classes.

Conceptually:

```text
lecturer_id
class_id
```

Example:

```text
Lecturer 24 → First Year
Lecturer 24 → Second Year
Lecturer 24 → Fourth Year
```

## `documents`

Typical fields:

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

The table stores metadata such as ownership, lecturer relationship, file information, storage locations, and checksum.

## `recovery_logs`

Typical fields:

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

The recovery table provides an audit trail for recovery operations.

---

# Document Lifecycle

## Student Upload

```text
Student
   ↓
Browser
   ↓
Nginx
   ↓
FastAPI Gateway
   ↓
Authenticate user
   ↓
Check role/class/lecturer relationship
   ↓
Calculate SHA-256
   ↓
Select primary + replica nodes
   ↓
Store physical file
   ↓
Save metadata in PostgreSQL
   ↓
Return success
```

## Lecturer Upload

```text
Lecturer
   ↓
Browser
   ↓
Nginx
   ↓
Gateway
   ↓
Check lecturer permissions
   ↓
Select storage nodes
   ↓
Store primary + replica
   ↓
Save metadata
```

## Download

```text
Client
  ↓
Gateway
  ↓
Check authorization
  ↓
Primary storage node
  |
  +---- available → return file
  |
  +---- unavailable → try replica
                          ↓
                       return file
```

## Delete

```text
Authorized user
      ↓
Gateway
      ↓
Check ownership / permission
      ↓
Delete physical file
      ↓
Delete PostgreSQL metadata
      ↓
Commit transaction
```

---

# Lecturer Multi-Class Flow

```text
Admin
  ↓
Create/import Lecturer
  ↓
Assign multiple classes
  ↓
lecturer_teaching_classes
  ↓
Lecturer Login
  ↓
Teaching Classes UI
  ↓
View / update assigned classes
```

Example:

```text
Daw Moe Moe

☑ First Year
☑ Second Year
☐ Third Year
☑ Fourth Year
☐ Fifth Year
```

The lecturer can update this assignment from the UI.

---

# Admin Excel Import Flow

## Students

```text
Admin
  ↓
Choose students.xlsx
  ↓
POST /admin/import/students
  ↓
Validate spreadsheet rows
  ↓
Validate full name / email / class
  ↓
Generate password
  ↓
Hash password
  ↓
Create user
  ↓
Return created/skipped results
  ↓
Show generated passwords to Admin
```

## Lecturers

```text
Admin
  ↓
Choose lecturers.xlsx
  ↓
POST /admin/import/lecturers
  ↓
Validate full name / email / classes
  ↓
Generate password
  ↓
Hash password
  ↓
Create lecturer
  ↓
Create multi-class assignments
  ↓
Return results
```

---

# Roles and Permissions

## Admin

Admin can:

- Login.
- View the Admin dashboard.
- Create Students.
- Create Lecturers.
- Import Students from Excel.
- Import Lecturers from Excel.
- Assign Student classes.
- Assign Lecturer teaching classes.
- Activate/deactivate users.
- View system-level storage information.
- View storage-node health.
- View replication information.
- View recovery statistics.
- View recovery logs.

## Student

Student can:

- Login.
- View profile/class.
- Select an available same-class lecturer.
- Upload documents.
- View own documents.
- Download permitted documents.
- Delete own documents where permitted.
- View/download lecturer documents for the relevant class.

## Lecturer

Lecturer can:

- Login.
- View profile.
- View assigned teaching classes.
- Update teaching classes.
- Upload lecture documents.
- View own documents.
- View student submissions assigned to them.
- Download permitted student submissions.
- Delete own documents where permitted.

---

# Main API Endpoints

The deployed Swagger/OpenAPI specification is the authoritative source for the exact current API.

## Authentication

```text
POST /auth/login
GET  /users/me
```

## Student / Lecturer Documents

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

## Admin

```text
GET /admin/users
GET /admin/nodes/health
GET /admin/replication/status
GET /admin/classes/summary
```

## Excel Import

```text
POST /admin/import/students
POST /admin/import/lecturers
```

## Lecturer Class Management

```text
GET /lecturers/classes
GET /lecturers/me/classes
PUT /lecturers/me/classes
```

## Recovery

```text
GET /recovery/stats
GET /recovery/logs
GET /recovery/logs/filter?status=...
```

---

# Running the Project

## Requirements

The server laptop needs:

- Docker Desktop
- Docker Compose
- A modern web browser
- Enough disk space for PostgreSQL and node storage

Client laptops only need:

- A modern web browser
- Connection to the same LAN/Wi-Fi as the server laptop

Client laptops do **not** need:

```text
Python
FastAPI
PostgreSQL
Docker
Storage Node source code
Backend source code
```

---

## Start on Laptop A

From the project root:

```powershell
docker compose up -d
```

Check services:

```powershell
docker compose ps
```

Typical services:

```text
distributed-postgres
distributed-gateway
distributed-nginx
storage-node-1
storage-node-2
storage-node-3
```

If build files or Python dependencies changed:

```powershell
docker compose up -d --build
```

For a clean rebuild:

```powershell
docker compose down
docker compose build --no-cache
docker compose up -d
```

Stop the system:

```powershell
docker compose down
```

---

# Access the System

## Server Laptop

```text
http://localhost:8080/
```

Swagger:

```text
http://localhost:8080/docs
```

OpenAPI:

```text
http://localhost:8080/openapi.json
```

## LAN Clients

Find Laptop A's local IP:

```powershell
ipconfig
```

Example:

```text
192.168.1.10
```

Other laptops can open:

```text
http://192.168.1.10:8080/
```

They only need a browser.

---

# Docker Services

A typical Compose deployment contains:

```text
Nginx
  ↓
FastAPI Gateway
  ↓
PostgreSQL
  ↓
Storage Node 1
Storage Node 2
Storage Node 3
```

## Storage Node Ports

Inside the Docker network:

```text
storage-node-1:9001
storage-node-2:9002
storage-node-3:9003
```

The actual host exposure depends on the current `docker-compose.yml`.

---

# Persistent Storage

Each node keeps its own storage directory:

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

PostgreSQL uses a persistent Docker volume for database data.

Conceptually:

```text
PostgreSQL
    ↓
metadata / users / documents / recovery logs

Node 1 volume
    ↓
actual files

Node 2 volume
    ↓
actual files

Node 3 volume
    ↓
actual files
```

---

# Data Location

```text
User accounts
    → PostgreSQL.users

Class definitions
    → PostgreSQL.class_years

Lecturer class assignments
    → PostgreSQL.lecturer_teaching_classes

Document metadata
    → PostgreSQL.documents

Recovery history
    → PostgreSQL.recovery_logs

Actual uploaded files
    → Storage Node 1/2/3 volumes
```

The database does not need to store the whole uploaded file binary.

---

# Testing

## Authentication Test

Test:

```text
Admin login
Student login
Lecturer login
```

Expected:

```text
Admin    → Admin Dashboard
Student  → Student Dashboard
Lecturer → Lecturer Dashboard
```

## Role Authorization Test

Try accessing another role's protected API.

Expected:

```text
Authorized role → success
Wrong role      → 403 Forbidden
Unauthenticated → 401 Unauthorized
```

## Student Upload Test

```text
Login as Student
       ↓
Select lecturer
       ↓
Choose file
       ↓
Upload
       ↓
Check document list
       ↓
Check database metadata
       ↓
Check storage node
```

## Lecturer Multi-Class Test

```text
Login as Lecturer
       ↓
Open Teaching Classes
       ↓
Check existing assignments
       ↓
Select multiple classes
       ↓
Save
       ↓
Refresh
       ↓
Verify assignments remain
```

Example:

```text
First Year
Second Year
Fourth Year
```

## Excel Import Test

Student file:

```text
students.xlsx
```

Expected:

```text
Total Rows
Created
Skipped
Generated Passwords
```

Lecturer file:

```text
lecturers.xlsx
```

Expected:

```text
Lecturer
Email
Teaching Classes
Generated Password
```

## Distributed Storage Test

Upload several files and verify that:

- Files are placed across the logical nodes.
- PostgreSQL records the primary node.
- PostgreSQL records the replica node.
- The replica exists where expected.

---

# Failure and Recovery Test

Stop a storage node:

```powershell
docker compose stop storage-node-1
```

Check status:

```powershell
docker compose ps
```

Check Admin Node Status.

Then test a document whose primary node is Node 1.

Expected behavior, when a valid replica exists:

```text
Primary Node 1
     ↓
Unavailable
     ↓
Replica Node 2
     ↓
Document still available
```

Restart:

```powershell
docker compose start storage-node-1
```

If the primary copy is missing or corrupted, verify that the recovery mechanism can restore it from a valid replica and write a recovery record.

---

# Useful Docker Commands

## View all containers

```powershell
docker compose ps
```

## Gateway logs

```powershell
docker compose logs -f gateway
```

## Nginx logs

```powershell
docker compose logs -f nginx
```

## Storage node logs

```powershell
docker compose logs -f storage-node-1
docker compose logs -f storage-node-2
docker compose logs -f storage-node-3
```

## Restart Gateway

```powershell
docker compose restart gateway
```

## Restart Nginx

```powershell
docker compose restart nginx
```

## Stop a storage node

```powershell
docker compose stop storage-node-1
```

## Start it again

```powershell
docker compose start storage-node-1
```

---

# Useful PostgreSQL Commands

Open PostgreSQL:

```powershell
docker compose exec postgres psql -U postgres -d distributed_storage
```

## View users

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

## View documents

```sql
SELECT
    id,
    file_name,
    owner_id,
    lecturer_id,
    storage_node,
    replica_node,
    checksum,
    created_at
FROM documents
ORDER BY id DESC;
```

## View Lecturer class assignments

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

## View recovery logs

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

# Troubleshooting

## 401 Unauthorized

The access token may be missing or expired.

Clear the browser token:

```javascript
localStorage.removeItem("access_token");
```

Then log in again.

## 403 Forbidden

The current account may not have the required role or permission.

Check:

```text
users.role
users.class_year
lecturer_teaching_classes
```

## 502 Bad Gateway

Check:

```powershell
docker compose ps
docker compose logs gateway
docker compose logs nginx
```

Make sure the Gateway container is running and Nginx is proxying to:

```text
http://gateway:8000
```

## API Returns HTML Instead of JSON

If an API such as:

```text
/lecturers/me/classes
```

returns `login.html`, check the Nginx routing rules.

API paths must be proxied to the Gateway before the frontend fallback route.

Example:

```nginx
location ^~ /lecturers/ {
    proxy_pass http://gateway:8000;
}
```

## Browser Shows Old JavaScript

Use:

```text
Ctrl + Shift + R
```

to perform a hard refresh.

## Port 80 Is Already in Use

Expose Nginx on another host port:

```yaml
ports:
  - "8080:80"
```

Then use:

```text
http://localhost:8080/
```

## Existing Database Columns Do Not Change Automatically

Changing a SQLAlchemy model does not automatically migrate an already-existing database schema.

For structural changes, use an explicit database migration or `ALTER TABLE`.

---

# Security Notes

- Never commit real JWT secrets or database credentials.
- Keep `.env` files containing secrets out of source control.
- Store passwords as hashes, not plaintext database values.
- Enforce authorization in the backend.
- Treat frontend role checks as UI behavior, not as the security boundary.
- Keep PostgreSQL and storage-node ports internal where practical.
- Validate uploaded files and enforce suitable size/type limits.
- Use HTTPS when deploying outside a trusted local network.
- Do not expose administrative endpoints publicly without appropriate protection.

---

# Docker Image Export

The application images can be exported with Docker:

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

Important:

```text
Docker images
    ≠
PostgreSQL data
    ≠
Uploaded files
```

Database data and storage-node files require their own backup/transfer process.

---

# LAN Deployment Model

The current deployment is:

```text
                UNIVERSITY LAN
                     |
          +----------+----------+
          |                     |
      Laptop B                Laptop C
       Client                  Client
      Browser                 Browser
          \                     /
           \                   /
            +------ Laptop A -+
                   Server
                    |
                  Docker
                    |
        +-----------+-----------+
        |           |           |
      Nginx      Gateway     PostgreSQL
                    |
          +---------+---------+
          |         |         |
        Node 1    Node 2    Node 3
```

The client laptops do not need to install the project.

This architecture is suitable for demonstration and LAN deployment. Stronger host-level fault tolerance would require moving storage nodes to separate physical or virtual machines.

---

# Academic Data and Future Enhancement

The current system uses a Student's current `class_year` for class-based access.

For a longer-term academic lifecycle, the recommended extension is a separate historical table such as:

```text
student_class_history
```

Conceptually:

```text
student_id
class_id
academic_year
start_date
end_date
status
```

This would allow:

```text
2026-2027 → First Year  → completed
2027-2028 → Second Year → completed
2028-2029 → Third Year  → active
```

A future Admin promotion workflow can then:

```text
Admin
  ↓
Promote Student
  ↓
Close current history
  ↓
Create new history row
  ↓
Update users.class_year
```

Graduation can similarly use a student status such as:

```text
active
graduated
suspended
withdrawn
```

This preserves historical academic information without creating separate tables such as:

```text
students_first_year
students_second_year
students_third_year
```

or:

```text
documents_first_year
documents_second_year
documents_third_year
```

The preferred design is one normalized set of tables with relationships and historical records.

---

# Why Docker Is Used

Docker provides isolated runtime environments for the services.

In the current deployment:

```text
Physical Server: Laptop A

Docker
├── distributed-nginx
├── distributed-gateway
├── distributed-postgres
├── storage-node-1
├── storage-node-2
└── storage-node-3
```

This provides:

- Service isolation.
- Reproducible environments.
- Consistent dependency installation.
- Simple multi-service deployment.
- Separate logical storage-node processes.
- Easier movement of the system to another Docker host.

The three storage nodes are logically separate even though they currently share one physical host.

---

# What the Project Demonstrates

Campus Hub demonstrates practical experience with:

```text
Authentication
Role-based authorization
Class-based access control
REST API design
Database design
File upload/download
Distributed storage
Multiple logical storage nodes
Round-Robin placement
Primary/replica storage
Checksum verification
Fault tolerance
Replica fallback
Automatic recovery
Recovery logging
Node monitoring
Docker
Docker Compose
Nginx reverse proxy
LAN deployment
Excel bulk import
Automatic password generation
Lecturer multi-class management
Frontend/backend integration
```

---

# Current Status

Core system areas completed:

```text
Authentication & Roles          ✅
Admin UI                        ✅
Student UI                      ✅
Lecturer UI                     ✅
Admin Excel Import              ✅
Automatic password generation   ✅
Lecturer multi-class UI         ✅
Class-based access              ✅
Document upload/download        ✅
Three logical storage nodes     ✅
Round-Robin placement           ✅
Primary + Replica               ✅
SHA-256 integrity               ✅
Node monitoring                 ✅
Replica fallback                ✅
Automatic recovery              ✅
Recovery logs                   ✅
Docker deployment               ✅
LAN client access                ✅
```

---

# Project Demo Flow

A complete demonstration can follow this sequence:

```text
1. Admin Login
        ↓
2. Create / Import Users
        ↓
3. Show Generated Password
        ↓
4. Lecturer Login
        ↓
5. Show Multi-Class Assignment
        ↓
6. Student Login
        ↓
7. Upload Document
        ↓
8. Lecturer Views Submission
        ↓
9. Admin Checks Storage Nodes
        ↓
10. View Replication Status
        ↓
11. Simulate Node Failure
        ↓
12. Verify Replica Fallback
        ↓
13. Verify Recovery Log
```

---

# Future Enhancements

Possible future improvements include:

- Student academic promotion workflow.
- Student class history.
- Graduation management.
- Bulk student promotion.
- More advanced audit logging.
- File versioning.
- Search and filtering.
- Pagination for large document collections.
- Background health monitoring.
- Stronger multi-host fault tolerance.
- HTTPS and production-grade deployment.
- Container orchestration for larger deployments.
- Separate physical or virtual machines for storage nodes.

---

# Project Title

## **Campus Hub: Distributed Storage System for University Documents**

---

# Author

**Aung Phyo Hein**
