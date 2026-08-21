document.addEventListener(
    "DOMContentLoaded",
    loadClasses
);


async function loadClasses() {

    const container =
        document.getElementById(
            "classesContainer"
        );

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


        const availableClasses =
            await getAvailableClasses();


        const currentResult =
            await getMyTeachingClasses();


        if (
            !Array.isArray(
                availableClasses
            )
        ) {

            throw new Error(
                "Invalid response from /lecturers/classes"
            );
        }


        if (
            !currentResult ||
            !Array.isArray(
                currentResult.classes
            )
        ) {

            throw new Error(
                "Invalid response from /lecturers/me/classes"
            );
        }


        const currentClasses =
            currentResult.classes.map(
                item =>
                    item.class_year
            );


        container.innerHTML = "";


        availableClasses.forEach(
            item => {

                const checked =
                    currentClasses.includes(
                        item.class_year
                    );


                const wrapper =
                    document.createElement(
                        "label"
                    );


                wrapper.className = `
                    flex
                    items-center
                    gap-3
                    p-5
                    rounded-xl
                    border
                    border-slate-200
                    cursor-pointer
                    hover:bg-slate-50
                `;


                wrapper.innerHTML = `

                    <input
                        type="checkbox"
                        class="teaching-class"
                        value="${escapeHtml(
                            item.class_year
                        )}"
                        ${checked ? "checked" : ""}
                    >

                    <div>

                        <p class="font-semibold">
                            ${escapeHtml(
                                item.display_name
                            )}
                        </p>

                        <p class="text-xs text-slate-500">
                            ${escapeHtml(
                                item.class_year
                            )}
                        </p>

                    </div>

                `;


                container.appendChild(
                    wrapper
                );

            }
        );

    } catch (error) {

        container.innerHTML = `
            <p class="text-sm text-red-600">
                ${escapeHtml(
                    error.message
                )}
            </p>
        `;
    }
}


document
    .getElementById(
        "saveClassesButton"
    )
    .addEventListener(
        "click",
        async function () {

            const selectedClasses =
                [
                    ...document.querySelectorAll(
                        ".teaching-class:checked"
                    )
                ].map(
                    checkbox =>
                        checkbox.value
                );


            if (
                selectedClasses.length === 0
            ) {

                showMessage(
                    "Please select at least one class.",
                    false
                );

                return;
            }


            try {

                this.disabled =
                    true;

                this.textContent =
                    "Saving...";


                const result =
                    await updateMyTeachingClasses(
                        selectedClasses
                    );


                showMessage(
                    result.message,
                    true
                );


                await loadClasses();

            } catch (error) {

                showMessage(
                    error.message,
                    false
                );

            } finally {

                this.disabled =
                    false;

                this.textContent =
                    "Save Classes";
            }
        }
    );


function showMessage(
    message,
    success
) {

    const element =
        document.getElementById(
            "classMessage"
        );


    element.textContent =
        message;


    element.className =
        success
            ? "mt-5 p-4 rounded-xl text-sm bg-emerald-50 text-emerald-700"
            : "mt-5 p-4 rounded-xl text-sm bg-red-50 text-red-700";


    element.classList.remove(
        "hidden"
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