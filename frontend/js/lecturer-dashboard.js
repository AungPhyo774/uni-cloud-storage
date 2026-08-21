async function loadTeachingClasses() {

    const container =
        document.getElementById(
            "teachingClasses"
        );

    if (!container) {
        return;
    }

    try {

        const user =
            await getCurrentUser();

        if (
            !user ||
            user.role !== "lecturer"
        ) {

            window.location.href =
                "login.html";

            return;
        }

        const result =
            await getMyTeachingClasses();

        if (
            !result ||
            !Array.isArray(
                result.classes
            )
        ) {

            throw new Error(
                "Invalid response from /lecturers/me/classes"
            );
        }

        container.innerHTML = "";

        if (
            result.classes.length === 0
        ) {

            container.innerHTML = `
                <p class="text-sm text-slate-500">
                    No teaching classes assigned.
                </p>
            `;

            return;
        }

        result.classes.forEach(
            item => {

                const card =
                    document.createElement(
                        "div"
                    );

                card.className = `
                    p-5
                    rounded-xl
                    bg-blue-50
                    border
                    border-blue-100
                `;

                card.innerHTML = `
                    <p class="font-bold text-blue-900">
                        ${escapeHtml(
                            item.display_name
                        )}
                    </p>

                    <p class="text-xs text-blue-600 mt-1">
                        ${escapeHtml(
                            item.class_year
                        )}
                    </p>
                `;

                container.appendChild(
                    card
                );

            }
        );

    } catch (error) {

        console.error(
            "Teaching class error:",
            error
        );

        container.innerHTML = `
            <p class="text-sm text-red-600">
                ${escapeHtml(
                    error.message
                )}
            </p>
        `;
    }
}


function escapeHtml(value) {

    return String(
        value ?? ""
    )
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


loadTeachingClasses();