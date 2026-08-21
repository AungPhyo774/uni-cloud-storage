// main API client
const API_BASE_URL = "";


async function apiRequest(
    endpoint,
    options = {}
) {
    const token = localStorage.getItem("access_token");

    const headers = {
        ...(options.headers || {})
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
            ...options,
            headers
        }
    );

    let data = null;

    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok) {

        const message =
            data?.detail ||
            `Request failed: ${response.status}`;

        throw new Error(message);
    }

    return data;
}


// #Login API
async function loginUser(
    email,
    password
) {

    const body = new URLSearchParams();

    body.append(
        "username",
        email
    );

    body.append(
        "password",
        password
    );

    const response = await fetch(
        `${API_BASE_URL}/auth/login`,
        {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/x-www-form-urlencoded"
            },
            body
        }
    );

    const data = await response.json();

    if (!response.ok) {

        throw new Error(
            data.detail ||
            "Login failed"
        );
    }

    localStorage.setItem(
        "access_token",
        data.access_token
    );

    return data;
}

// ADMIN - CREATE USER
async function createAdminUser(data) {

    return await apiRequest(
        "/users/admin/create-user",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(data)
        }
    );
}

async function updateAdminUser(
    userId,
    data
) {

    return await apiRequest(
        `/users/admin/users/${userId}`,
        {
            method: "PATCH",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(data)
        }
    );
}
async function getCurrentUser() {

    return await apiRequest(
        "/users/me"
    );
}

// Student API Functions
async function getLecturers() {

    return await apiRequest(
        "/documents/lecturers-list"
    );
}

//student upload
async function uploadStudentDocument(
    lecturerId,
    file
) {

    const formData = new FormData();

    formData.append(
        "file",
        file
    );

    return await apiRequest(
        `/documents/upload-to-lecturer/${lecturerId}`,
        {
            method: "POST",
            body: formData
        }
    );
}

//My documents—
async function getMyDocuments() {

    return await apiRequest(
        "/documents/my-all-documents"
    );
}

//Lecturer documents—
async function getLecturerDocuments() {

    return await apiRequest(
        "/documents/lecturer-documents"
    );
}

//Download Function
async function downloadDocument(
    documentId,
    fileName
) {

    const token =
        localStorage.getItem(
            "access_token"
        );

    const response = await fetch(
        `${API_BASE_URL}/documents/${documentId}/download`,
        {
            headers: {
                "Authorization":
                    `Bearer ${token}`
            }
        }
    );

    if (!response.ok) {

        let message =
            "Download failed";

        try {

            const data =
                await response.json();

            message =
                data.detail || message;

        } catch {}

        throw new Error(message);
    }

    const blob =
        await response.blob();

    const url =
        window.URL.createObjectURL(
            blob
        );

    const a =
        document.createElement("a");

    a.href = url;

    a.download = fileName;

    document.body.appendChild(a);

    a.click();

    a.remove();

    window.URL.revokeObjectURL(
        url
    );
}

//-----------------------------------------------
//Lecturer APIs
//Lecturer upload—
async function uploadLecturerDocument(
    file
) {

    const formData =new FormData();

    formData.append(
        "file",
        file
    );

    return await apiRequest(
        "/documents/lecturer/upload",
        {
            method: "POST",
            body: formData
        }
    );
}

//Student submissions—
async function getStudentSubmissions() {

    return await apiRequest(
        "/documents/student-documents"
    );
}


//Admin APIs
//Users
async function getAdminUsers() {

    return await apiRequest(
        "/users/admin/users"
    );
}

//Class summary
async function getClassSummary() {

    return await apiRequest(
        "/admin/classes/summary"
    );
}

//Node health
async function getNodeHealth() {

    return await apiRequest(
        "/admin/nodes/health"
    );
}

//Replication status
async function getReplicationStatus() {

    return await apiRequest(
        "/admin/replication/status"
    );
}

//Recovery stats
async function getRecoveryStats() {

    return await apiRequest(
        "/recovery/stats"
    );
}

//Recovery logs
async function getRecoveryLogs(
    status = null
) {

    let endpoint =
        "/recovery/logs";

    if (status) {

        endpoint =
            `/recovery/logs/filter?status=${encodeURIComponent(status)}`;
    }

    return await apiRequest(
        endpoint
    );
}


//logout
function logout() {

    localStorage.removeItem(
        "access_token"
    );

    window.location.href =
        "login.html";
}

// =========================================================
// DELETE DOCUMENT
// =========================================================

async function deleteDocument(
    documentId
) {

    return await apiRequest(
        `/documents/${documentId}`,
        {
            method: "DELETE"
        }
    );
}


// =========================================================
// ADMIN EXCEL IMPORT
// =========================================================

async function importStudentsExcel(
    file
) {

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );


    return await apiRequest(
        "/admin/import/students",
        {
            method: "POST",
            body: formData
        }
    );
}


async function importLecturersExcel(
    file
) {

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );


    return await apiRequest(
        "/admin/import/lecturers",
        {
            method: "POST",
            body: formData
        }
    );
}
