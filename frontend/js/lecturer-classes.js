document.addEventListener("DOMContentLoaded", loadClasses);

async function loadClasses() {
    const container = document.getElementById("classesContainer");
    const button = document.getElementById("saveClassesButton");

    try {
        const user = await getCurrentUser();

        if (!user || user.role !== "lecturer") {
            window.location.href = "login.html";
            return;
        }

        const [availableClasses, currentResult] = await Promise.all([
            getAvailableClasses(),
            getMyTeachingClasses()
        ]);
        const currentClasses = new Set(
            (Array.isArray(currentResult?.classes) ? currentResult.classes : [])
                .map(item => item.class_year)
        );

        container.innerHTML = "";
        (Array.isArray(availableClasses) ? availableClasses : [])
            .forEach(item => {
            const label = document.createElement("label");
            label.className = "flex cursor-pointer items-start gap-4 rounded-2xl border border-slate-200 p-5 transition hover:border-blue-300 hover:bg-blue-50";
            label.innerHTML = `
                <input type="checkbox" class="teaching-class mt-1 h-5 w-5 accent-blue-600" value="${escapeHtml(item.class_year)}" ${currentClasses.has(item.class_year) ? "checked" : ""}>
                <span>
                    <span class="block font-semibold text-slate-900">${escapeHtml(item.display_name)}</span>
                    <span class="mt-1 block text-xs text-slate-500">${escapeHtml(item.class_year)}</span>
                </span>
            `;
            container.appendChild(label);
        });

        if (!Array.isArray(availableClasses) || !availableClasses.length) {
            container.innerHTML = '<p class="text-sm text-slate-500">No classes are available yet.</p>';
        }
    } catch (error) {
        container.innerHTML = `<p class="text-sm text-red-600">${escapeHtml(error.message)}</p>`;
        button.disabled = true;
    }
}

document.getElementById("saveClassesButton").addEventListener("click", async event => {
    const button = event.currentTarget;
    const selectedClasses = [...document.querySelectorAll(".teaching-class:checked")]
        .map(checkbox => checkbox.value);

    if (!selectedClasses.length) {
        showMessage("Please select at least one class.", false);
        return;
    }

    try {
        button.disabled = true;
        button.textContent = "Saving...";
        const result = await updateMyTeachingClasses(selectedClasses);
        showMessage(result.message, true);
    } catch (error) {
        showMessage(error.message, false);
    } finally {
        button.disabled = false;
        button.textContent = "Save Classes";
    }
});

function showMessage(message, success) {
    const element = document.getElementById("classMessage");
    element.textContent = message;
    element.className = success
        ? "mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700"
        : "mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700";
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
