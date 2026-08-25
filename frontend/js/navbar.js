function loadStudentNavbar() {

    const navbarContainer =
        document.getElementById("studentNavbar");

    if (!navbarContainer) {
        return;
    }


    navbarContainer.innerHTML = `

        <nav
            class="fixed inset-x-0 top-0 z-50
                   h-20
                   border-b border-[#bae6fd]
                   bg-white/95
                   backdrop-blur-xl"
        >

            <div
                class="mx-auto flex h-full max-w-7xl
                       items-center justify-between
                       px-4 sm:px-6 lg:px-8"
            >


                <!-- =========================================
                     LOGO
                ========================================== -->

                <a
                    href="student-dashboard.html"
                    class="flex shrink-0 items-center gap-3"
                >

                    <div
                        class="flex h-11 w-11 items-center
                               justify-center rounded-xl
                               bg-[#0284c7]
                               text-white
                               shadow-lg
                               shadow-[#0284c7]/20"
                    >
                        <i
                            class="fa-solid fa-graduation-cap text-lg"
                        ></i>
                    </div>


                    <div class="hidden sm:block">

                        <p
                            class="text-lg font-bold
                                   leading-tight
                                   tracking-tight
                                   text-[#0a3751]"
                        >
                           Campus Hub
                        </p>

                        <p
                            class="mt-0.5 text-xs font-medium
                                   leading-tight
                                   text-[#0369a1]"
                        >
                           Distributed Storage System
                        </p>

                    </div>

                </a>


                <!-- =========================================
                     NAVIGATION
                ========================================== -->

                <div
                    class="hidden items-center gap-1 md:flex"
                >

                    <!-- Dashboard -->

                    <a
                        href="student-dashboard.html"
                        data-page="student-dashboard.html"
                        class="nav-link inline-flex items-center
                               rounded-xl
                               px-4 py-2.5
                               text-sm font-medium
                               leading-none
                               text-[#075985]
                               transition
                               hover:bg-[#e0f2fe]
                               hover:text-[#0a3751]"
                    >

                        <i
                            class="fa-solid fa-house mr-2 text-sm"
                        ></i>

                        Dashboard

                    </a>


                    <!-- Upload -->

                    <a
                        href="student-upload.html"
                        data-page="student-upload.html"
                        class="nav-link inline-flex items-center
                               rounded-xl
                               px-4 py-2.5
                               text-sm font-medium
                               leading-none
                               text-[#075985]
                               transition
                               hover:bg-[#e0f2fe]
                               hover:text-[#0a3751]"
                    >

                        <i
                            class="fa-solid fa-cloud-arrow-up mr-2 text-sm"
                        ></i>

                        Upload

                    </a>


                    <!-- My Documents -->

                    <a
                        href="student-documents.html"
                        data-page="student-documents.html"
                        class="nav-link inline-flex items-center
                               rounded-xl
                               px-4 py-2.5
                               text-sm font-medium
                               leading-none
                               text-[#075985]
                               transition
                               hover:bg-[#e0f2fe]
                               hover:text-[#0a3751]"
                    >

                        <i
                            class="fa-solid fa-folder-open mr-2 text-sm"
                        ></i>

                        My Documents

                    </a>


                    <!-- Lecturer Materials -->

                    <a
                        href="lecturer-documents.html"
                        data-page="lecturer-documents.html"
                        class="nav-link inline-flex items-center
                               rounded-xl
                               px-4 py-2.5
                               text-sm font-medium
                               leading-none
                               text-[#075985]
                               transition
                               hover:bg-[#e0f2fe]
                               hover:text-[#0a3751]"
                    >

                        <i
                            class="fa-solid fa-book-open mr-2 text-sm"
                        ></i>

                        Lecturer Documents

                    </a>

                </div>


                <!-- =========================================
                     USER AREA
                ========================================== -->

                <div
                    class="flex shrink-0 items-center gap-2"
                >

                    <!-- User name -->

                    <div
                        class="hidden text-right sm:block"
                    >

                        <p
                            id="navUserName"
                            class="text-sm font-semibold
                                   leading-tight
                                   text-[#0a3751]"
                        >
                            Student
                        </p>

                        <p
                            class="mt-0.5 text-xs
                                   leading-tight
                                   text-[#0369a1]"
                        >
                            Student Account
                        </p>

                    </div>


                    <!-- Logout -->

                    <button
                        type="button"
                        onclick="logout()"
                        class="flex h-10 w-10
                               items-center justify-center
                               rounded-xl
                               border border-red-200
                               bg-red-50
                               text-red-600
                               transition
                               hover:bg-red-100"
                        title="Logout"
                    >

                        <i
                            class="fa-solid fa-right-from-bracket text-sm"
                        ></i>

                    </button>


                    <!-- Change Password -->

                    <a
                        href="change-password.html"
                        class="flex h-10 w-10
                               items-center justify-center
                               rounded-xl
                               border border-[#bae6fd]
                               text-[#075985]
                               transition
                               hover:border-[#7dd3fc]
                               hover:bg-[#e0f2fe]"
                        title="Change password"
                    >

                        <i
                            class="fa-solid fa-lock text-sm"
                        ></i>

                    </a>

                </div>

            </div>

        </nav>

    `;


    /* =========================================
       ACTIVE NAVIGATION
    ========================================== */

    const currentPage =
        window.location.pathname
            .split("/")
            .pop()
            .toLowerCase();


    document
        .querySelectorAll(".nav-link")
        .forEach(link => {

            const page =
                link
                    .getAttribute("data-page")
                    .toLowerCase();


            if (page === currentPage) {

                link.classList.remove(
                    "text-[#075985]"
                );

                link.classList.add(
                    "bg-[#e0f2fe]",
                    "font-semibold",
                    "text-[#0284c7]"
                );

            }

        });


    /* =========================================
       LOAD USER NAME
    ========================================== */

    if (
        typeof getCurrentUser === "function"
    ) {

        getCurrentUser()

            .then(user => {

                const navUserName =
                    document.getElementById(
                        "navUserName"
                    );


                if (
                    navUserName &&
                    user &&
                    user.full_name
                ) {

                    navUserName.textContent =
                        user.full_name;

                }

            })

            .catch(() => {

                // Ignore navbar user loading error

            });

    }

}