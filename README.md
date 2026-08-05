# Distributed Cloud Storage System for University Documents

A distributed document storage system developed using **FastAPI**, **PostgreSQL**, and multiple **Storage Nodes**.

This project demonstrates the concepts of:

- Distributed Systems
- Gateway Architecture
- Round Robin Load Balancing
- Authentication using JWT
- Role-Based Access Control
- Distributed File Storage
- Metadata Management

---

# Project Architecture

```
                        +------------------+
                        |     Client       |
                        | Student/Lecturer |
                        +--------+---------+
                                 |
                                 |
                          HTTP REST API
                                 |
                                 ▼
                    +------------------------+
                    |       Gateway API      |
                    |        FastAPI         |
                    +-----------+------------+
                                |
             ------------------------------------------
             |                  |                    |
             ▼                  ▼                    ▼
      Storage Node 1     Storage Node 2      Storage Node 3
        Port 9001          Port 9002           Port 9003
             |                  |                    |
             ------------------------------
                          |
                          ▼
                  Local File Storage

Gateway stores only metadata in PostgreSQL.
Actual PDF files are stored inside Storage Nodes.
```

---

# Current Features

## Authentication

- User Registration
- Login
- JWT Authentication
- Password Hashing (bcrypt)
- JWT Token Verification

---

## User Roles

### Student

- Register
- Login
- Upload PDF to selected lecturer
- Download own documents
- Download lecturer documents
- View own uploaded documents
- Delete own documents

---

### Lecturer

- Login
- Upload documents for students
- Download own documents
- Download documents shared by students

---

## Distributed Storage

Gateway never stores actual files.

Instead,

```
Client
    ↓
Gateway
    ↓
Round Robin
    ↓
Node1
Node2
Node3
```

Example

```
File 1
↓

Node1

File2
↓

Node2

File3
↓

Node3

File4
↓

Node1
```

---

## Storage Node

Each storage node contains

```
app/
storage/
requirements.txt
Dockerfile
```

Each node provides

```
POST   /storage/upload

GET    /storage/download/{file_name}

DELETE /storage/delete/{file_name}
```

---

# Current Folder Structure

```
distributed-cloud-storage/

│
├── frontend/
│   ├── css/
│   ├── js/
│   ├── images/
│   ├── login.html
│   ├── dashboard.html
│   └── upload.html
│
├── gateway/
│   │
│   ├── app/
│   │   │
│   │   ├── database/
│   │   │     base.py
│   │   │     session.py
│   │   │
│   │   ├── dependencies/
│   │   │     auth.py
│   │   │
│   │   ├── models/
│   │   │     user.py
│   │   │     document.py
│   │   │
│   │   ├── routers/
│   │   │     auth.py
│   │   │     users.py
│   │   │     documents.py
│   │   │
│   │   ├── schemas/
│   │   │
│   │   ├── services/
│   │   │     storage_service.py
│   │   │     user_service.py
│   │   │
│   │   ├── utils/
│   │   │     jwt.py
│   │   │     security.py
│   │   │
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── storage-node-1/
│   ├── app/
│   ├── storage/
│   ├── requirements.txt
│   └── Dockerfile
│
├── storage-node-2/
│   ├── app/
│   ├── storage/
│   ├── requirements.txt
│   └── Dockerfile
│
├── storage-node-3/
│   ├── app/
│   ├── storage/
│   ├── requirements.txt
│   └── Dockerfile
│
├── database/
│
│   ├── init.sql
│   └── postgres-data/
│
└── docker-compose.yml
```

---

# Technologies

Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT
- bcrypt
- HTTPX

Database

- PostgreSQL

Distributed Storage

- FastAPI Storage Nodes

Frontend

- HTML
- CSS
- JavaScript

---

# Requirements

Python

```
3.12+
```

PostgreSQL

```
16+
```

---

# Install Gateway

```
cd gateway
```

Create virtual environment

```
python -m venv venv
```

Windows

```
venv\Scripts\activate
```

Linux

```
source venv/bin/activate
```

Install libraries

```
python -m pip install fastapi,uvicorn,etc (install only libraries using in project)
```

---

# Environment Variables

Create

```
.env
```

inside gateway

Example

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/distributed_storage

SECRET_KEY=YOUR_SECRET_KEY

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

# PostgreSQL

Create database

```
distributed_storage
```

Tables will be created automatically

```
users

documents
```

---

# Run Gateway

```
cd gateway

py -m uvicorn app.main:app --reload
```

Swagger

```
http://127.0.0.1:8000/docs
```

---

# Run Storage Node 1

```
cd storage-node-1

py -m uvicorn app.main:app --reload --port 9001
```

---

# Run Storage Node 2

```
cd storage-node-2

py -m uvicorn app.main:app --reload --port 9002
```

---

# Run Storage Node 3

```
cd storage-node-3

py -m uvicorn app.main:app --reload --port 9003
```

---

# Verify

Open

```
http://127.0.0.1:9001/docs
```

```
http://127.0.0.1:9002/docs
```

```
http://127.0.0.1:9003/docs
```

All three Storage Nodes should be running.

---

# Upload Flow

```
Student

↓

Gateway

↓

Round Robin

↓

Node1

↓

Save Metadata

↓

PostgreSQL
```

Second upload

```
Node2
```

Third upload

```
Node3
```

Fourth upload

```
Node1
```

---

# Download Flow

```
Client

↓

Gateway

↓

PostgreSQL

↓

Read storage_node

↓

Correct Storage Node

↓

Return PDF
```

---

# Delete Flow

```
Gateway

↓

Delete PDF from Storage Node

↓

Delete Metadata from PostgreSQL

↓

Done
```

---

# Current APIs

Authentication

```
POST /auth/register

POST /auth/login
```

Users

```
GET /users/me

GET /users/student-area

GET /users/lecturer-area
```

Documents

```
POST /documents/upload-to-lecturer/{lecturer_id}

POST /documents/lecturer/upload

GET /documents/

GET /documents/{document_id}

GET /documents/{document_id}/download

DELETE /documents/{document_id}

GET /documents/lecturers

GET /documents/lecturer-documents
```

---

# Current Progress

Completed

- User Registration
- Login
- JWT Authentication
- Password Hashing
- Role Authorization
- Document Upload
- Document Download
- Document Delete
- Distributed Storage
- Three Storage Nodes
- Round Robin Load Balancing
- PostgreSQL Metadata
- Student → Lecturer Upload
- Lecturer → Student Document Sharing

---

# Known Limitations

Current implementation stores each file on only one storage node.

If a storage node becomes unavailable, files stored on that node cannot be downloaded.

Replication and chunk-based storage have not yet been implemented.

---

# Future Improvements

- File Replication
- Chunk-Based Storage
- Automatic Failover
- Health Check
- Storage Node Recovery
- File Integrity Verification
- Admin Dashboard
- User Management
- Search Documents
- Docker Deployment
- Kubernetes Deployment

---

# Notes for New Developers

Before writing any new feature:

- Start PostgreSQL.
- Run Gateway.
- Run all three Storage Nodes.
- Verify `/docs` on Gateway and each Storage Node.
- Test login to obtain a JWT.
- Use the JWT in Swagger's **Authorize** button.
- Verify uploads rotate across Node 1, Node 2, and Node 3 (Round Robin).
- Confirm downloads use the `storage_node` value stored in PostgreSQL.
- Confirm deletes remove both the physical PDF from the Storage Node and the metadata from PostgreSQL.

---


Distributed Systems Practice Project
