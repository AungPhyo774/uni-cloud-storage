// =========================================================
// ADMIN USERS PAGE
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        setupRoleSelector();

        setupCreateUser();

        setupStudentImport();

        setupLecturerImport();

        loadUsers();

    }
);


// =========================================================
// ROLE SELECTOR
// =========================================================

function setupRoleSelector() {

    const roleSelect =
        document.getElementById(
            "role"
        );

    const studentClassField =
        document.getElementById(
            "studentClassField"
        );

    const lecturerClassesField =
        document.getElementById(
            "lecturerClassesField"
        );


    roleSelect.addEventListener(
        "change",
        function () {

            if (
                this.value === "lecturer"
            ) {

                studentClassField
                    .classList
                    .add("hidden");

                lecturerClassesField
                    .classList
                    .remove("hidden");

            } else {

                studentClassField
                    .classList
                    .remove("hidden");

                lecturerClassesField
                    .classList
                    .add("hidden");

            }

        }
    );
}


// =========================================================
// LOAD USERS
// =========================================================

async function loadUsers() {

    try {

        const currentUser =
            await getCurrentUser();


        if (
            currentUser.role !== "admin"
        ) {

            window.location.href =
                "login.html";

            return;
        }


        document.getElementById(
            "topUser"
        ).textContent =
            currentUser.full_name
            || "Administrator";


        document.getElementById(
            "topEmail"
        ).textContent =
            currentUser.email
            || "";


        const users =
            await getAdminUsers();


        const tbody =
            document.getElementById(
                "usersBody"
            );


        tbody.innerHTML = "";


        if (
            users.length === 0
        ) {

            tbody.innerHTML = `
                <tr>
                    <td
                        colspan="6"
                        class="px-5 py-10 text-center text-slate-500"
                    >
                        No users found.
                    </td>
                </tr>
            `;

            return;
        }


        users.forEach(
            user => {

                const row =
                    document.createElement(
                        "tr"
                    );


                let classText = "-";


                if (
                    user.role === "student"
                ) {

                    classText =
                        user.class_year
                        || "-";

                } else if (
                    user.role === "lecturer"
                ) {

                    if (
                        Array.isArray(
                            user.classes
                        )
                    ) {

                        classText =
                            user.classes.join(
                                ", "
                            );

                    }

                }


                row.innerHTML = `

                    <td class="px-5 py-4 font-semibold">
                        ${escapeHtml(
                            user.full_name
                        )}
                    </td>

                    <td class="px-5 py-4">
                        ${escapeHtml(
                            user.email
                        )}
                    </td>

                    <td class="px-5 py-4">
                        ${escapeHtml(
                            user.role
                        )}
                    </td>

                    <td class="px-5 py-4">
                        ${escapeHtml(
                            classText
                        )}
                    </td>

                    <td class="px-5 py-4">

                        <span
                            class="${
                                user.is_active
                                    ? "text-emerald-700"
                                    : "text-red-700"
                            }"
                        >
                            ${
                                user.is_active
                                    ? "Active"
                                    : "Inactive"
                            }
                        </span>

                    </td>

                    <td class="px-5 py-4">

                        <button
                            type="button"
                            onclick="changeStatus(
                                ${user.id},
                                ${user.is_active}
                            )"
                            class="px-3 py-1.5 rounded-lg border"
                        >
                            ${
                                user.is_active
                                    ? "Deactivate"
                                    : "Activate"
                            }
                        </button>

                    </td>

                `;


                tbody.appendChild(
                    row
                );

            }
        );

    } catch (error) {

        showError(
            "usersError",
            error.message
        );

    }
}


// =========================================================
// CREATE USER
// =========================================================

function setupCreateUser() {

    const form =
        document.getElementById(
            "createUserForm"
        );


    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const role =
                document.getElementById(
                    "role"
                ).value;


            const fullName =
                document.getElementById(
                    "fullName"
                ).value.trim();


            const email =
                document.getElementById(
                    "email"
                ).value.trim();


            const classYear =
                document.getElementById(
                    "classYear"
                ).value;


            const classes =
                [
                    ...document.querySelectorAll(
                        ".lecturer-class:checked"
                    )
                ].map(
                    checkbox =>
                        checkbox.value
                );


            if (!role) {

                showCreateMessage(
                    "Please select a role.",
                    false
                );

                return;
            }


            if (
                role === "student"
                &&
                !classYear
            ) {

                showCreateMessage(
                    "Please select a class.",
                    false
                );

                return;
            }


            if (
                role === "lecturer"
                &&
                classes.length === 0
            ) {

                showCreateMessage(
                    "Please select at least one teaching class.",
                    false
                );

                return;
            }


            const data = {

                full_name:
                    fullName,

                email:
                    email,

                role:
                    role,

                class_year:
                    role === "student"
                        ? classYear
                        : null,

                classes:
                    role === "lecturer"
                        ? classes
                        : []

            };


            try {

                const result =
                    await createAdminUser(
                        data
                    );


                const classText =
                    role === "student"
                        ? classYear
                        : classes.join(
                            ", "
                        );


                const message =
                    document.getElementById(
                        "createMessage"
                    );


                message.innerHTML = `

                    <strong>
                        User created successfully.
                    </strong>

                    <br><br>

                    Name:
                    ${escapeHtml(
                        result.user.full_name
                    )}

                    <br>

                    Email:
                    ${escapeHtml(
                        result.user.email
                    )}

                    <br>

                    Class:
                    ${escapeHtml(
                        classText
                    )}

                    <br><br>

                    <strong>
                        Generated Password:
                    </strong>

                    <code>
                        ${escapeHtml(
                            result.generated_password
                        )}
                    </code>

                `;


                message.className =
                    "mt-4 p-4 rounded-xl text-sm bg-emerald-50 text-emerald-700";


                form.reset();


                document
                    .getElementById(
                        "studentClassField"
                    )
                    .classList
                    .remove("hidden");


                document
                    .getElementById(
                        "lecturerClassesField"
                    )
                    .classList
                    .add("hidden");


                await loadUsers();

            } catch (error) {

                showCreateMessage(
                    error.message,
                    false
                );

            }

        }
    );
}


// =========================================================
// IMPORT STUDENTS
// =========================================================

function setupStudentImport() {

    const button =
        document.getElementById(
            "importStudentsButton"
        );


    button.addEventListener(
        "click",
        async function () {

            const input =
                document.getElementById(
                    "studentExcel"
                );


            const file =
                input.files[0];


            if (!file) {

                showImportMessage(
                    "Please select students.xlsx.",
                    false
                );

                return;
            }


            try {

                showImportMessage(
                    "Importing students...",
                    true
                );


                const result =
                    await importStudentsExcel(
                        file
                    );


                showImportResult(
                    result
                );


                input.value = "";


                showImportMessage(
                    "Student import completed.",
                    true
                );


                await loadUsers();

            } catch (error) {

                showImportMessage(
                    error.message,
                    false
                );

            }

        }
    );
}


// =========================================================
// IMPORT LECTURERS
// =========================================================

function setupLecturerImport() {

    const button =
        document.getElementById(
            "importLecturersButton"
        );


    button.addEventListener(
        "click",
        async function () {

            const input =
                document.getElementById(
                    "lecturerExcel"
                );


            const file =
                input.files[0];


            if (!file) {

                showImportMessage(
                    "Please select lecturers.xlsx.",
                    false
                );

                return;
            }


            try {

                showImportMessage(
                    "Importing lecturers...",
                    true
                );


                const result =
                    await importLecturersExcel(
                        file
                    );


                showImportResult(
                    result
                );


                input.value = "";


                showImportMessage(
                    "Lecturer import completed.",
                    true
                );


                await loadUsers();

            } catch (error) {

                showImportMessage(
                    error.message,
                    false
                );

            }

        }
    );
}


// =========================================================
// IMPORT RESULT
// =========================================================

function showImportResult(
    result
) {

    const section =
        document.getElementById(
            "importResultSection"
        );


    const summary =
        document.getElementById(
            "importSummary"
        );


    const tbody =
        document.getElementById(
            "importResultBody"
        );


    section.classList.remove(
        "hidden"
    );


    summary.innerHTML = `

        <div class="p-4 rounded-xl bg-slate-50">

            Total Rows

            <strong>
                ${result.total_rows}
            </strong>

        </div>


        <div class="p-4 rounded-xl bg-emerald-50">

            Created

            <strong>
                ${result.created_count}
            </strong>

        </div>


        <div class="p-4 rounded-xl bg-red-50">

            Skipped

            <strong>
                ${result.skipped_count}
            </strong>

        </div>

    `;


    tbody.innerHTML = "";


    const users =
        result.created_users
        ||
        result.created_lecturers
        ||
        [];


    users.forEach(
        user => {

            const classText =
                user.role === "student"
                    ? (
                        user.class_year
                        || "-"
                    )
                    : (
                        Array.isArray(
                            user.classes
                        )
                            ? user.classes.join(
                                ", "
                            )
                            : "-"
                    );


            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML = `

                <td class="px-4 py-3">
                    ${escapeHtml(
                        user.full_name
                    )}
                </td>

                <td class="px-4 py-3">
                    ${escapeHtml(
                        user.email
                    )}
                </td>

                <td class="px-4 py-3">
                    ${escapeHtml(
                        user.role
                    )}
                </td>

                <td class="px-4 py-3">
                    ${escapeHtml(
                        classText
                    )}
                </td>

                <td class="px-4 py-3">

                    <code>
                        ${escapeHtml(
                            user.password
                        )}
                    </code>

                    <button
                        type="button"
                        onclick="copyPassword(
                            '${escapeJs(
                                user.password
                            )}'
                        )"
                    >
                        Copy
                    </button>

                </td>

            `;


            tbody.appendChild(
                row
            );

        }
    );
}


// =========================================================
// CHANGE STATUS
// =========================================================

async function changeStatus(
    userId,
    currentStatus
) {

    const isActive =
        currentStatus === true
        || currentStatus === "true"
        || currentStatus === 1;

    const action = isActive
        ? "deactivate"
        : "activate";

    if (!window.confirm(`Are you sure you want to ${action} this account?`)) {
        return;
    }

    try {

        await updateAdminUser(
            userId,
            {
                is_active:
                    !isActive
            }
        );


        await loadUsers();

        showError(
            "usersError",
            `Account ${action}d successfully.`
        );

    } catch (error) {

        alert(
            error.message
        );

    }
}


// =========================================================
// COPY PASSWORD
// =========================================================

async function copyPassword(
    password
) {

    try {

        await navigator
            .clipboard
            .writeText(
                password
            );

        alert(
            "Password copied."
        );

    } catch {

        alert(
            "Unable to copy password."
        );

    }
}


// =========================================================
// MESSAGES
// =========================================================

function showCreateMessage(
    message,
    success
) {

    const element =
        document.getElementById(
            "createMessage"
        );


    element.textContent =
        message;


    element.className =
        success
            ? "mt-4 p-4 rounded-xl text-sm bg-emerald-50 text-emerald-700"
            : "mt-4 p-4 rounded-xl text-sm bg-red-50 text-red-700";


    element.classList.remove(
        "hidden"
    );
}


function showImportMessage(
    message,
    success
) {

    const element =
        document.getElementById(
            "importMessage"
        );


    element.textContent =
        message;


    element.className =
        success
            ? "p-4 rounded-xl text-sm bg-emerald-50 text-emerald-700"
            : "p-4 rounded-xl text-sm bg-red-50 text-red-700";


    element.classList.remove(
        "hidden"
    );
}


function showError(
    id,
    message
) {

    const element =
        document.getElementById(
            id
        );


    element.textContent =
        message;


    element.classList.remove(
        "hidden"
    );
}

async function updateAdminUser(
    userId,
    data
) {

    return await apiRequest(
        `/admin/users/${userId}`,
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


function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


function escapeJs(
    value
) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "\\",
            "\\\\"
        )
        .replaceAll(
            "'",
            "\\'"
        )
        .replaceAll(
            "\n",
            "\\n"
        )
        .replaceAll(
            "\r",
            "\\r"
        );
}