/* ======================================================
   Manage Experience JavaScript
====================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* ======================================================
       Elements
    ====================================================== */

    const modal = document.getElementById("experienceModal");

    const form = document.getElementById("experienceForm");

    const addBtn = document.getElementById("addExperienceBtn");

    const closeBtn = document.getElementById("closeExperienceModal");

    const modalTitle = document.getElementById("modalTitle");

    const currentJob = document.getElementById("currentJob");

    const endDate = document.getElementById("endDate");

    const errorBox = document.getElementById("experienceError");
    const errorText = document.getElementById("experienceErrorText");



    /* ======================================================
       Open Add Modal
    ====================================================== */

    if (addBtn) {

        addBtn.addEventListener("click", () => {

            form.reset();

            errorBox.style.display = "none";
            errorText.textContent = "";

            modalTitle.textContent = "Add Experience";

            form.action = "/add-experience";

            document.getElementById("experienceId").value = "";

            currentJob.checked = false;

            endDate.disabled = false;

            errorBox.style.display = "none";
            errorText.textContent = "";

            modal.style.display = "flex";

        });

    }


    /* ======================================================
       Close Modal
    ====================================================== */

    function closeModal() {

        modal.style.display = "none";

    }

    if (closeBtn) {

        closeBtn.addEventListener("click", closeModal);

    }

    window.addEventListener("click", function (e) {

        if (e.target === modal) {

            closeModal();

        }

    });


    /* ======================================================
       Current Working Checkbox
    ====================================================== */

    if (currentJob) {

        currentJob.addEventListener("change", function () {

            if (this.checked) {

                endDate.value = "";

                endDate.disabled = true;

            }

            else {

                endDate.disabled = false;

            }

        });

    }


    /* ======================================================
       Edit Experience
    ====================================================== */

    document.querySelectorAll(".editBtn").forEach(button => {

        button.addEventListener("click", function () {

            const id = this.dataset.id || "";

            document.getElementById("jobTitle").value =
                this.dataset.job || "";

            document.getElementById("companyName").value =
                this.dataset.company || "";

            document.getElementById("employmentType").value =
                this.dataset.type || "";

            document.getElementById("location").value =
                this.dataset.location || "";

            document.getElementById("startDate").value =
                this.dataset.start || "";

            document.getElementById("description").value =
                this.dataset.description || "";

            const isCurrent =
                this.dataset.current === "true" ||
                this.dataset.current === "True";

            currentJob.checked = isCurrent;

            if (isCurrent) {

                endDate.value = "";

                endDate.disabled = true;

            }

            else {

                endDate.disabled = false;

                endDate.value =
                    this.dataset.end || "";

            }

            document.getElementById("experienceId").value = id;

            form.action = "/edit-experience/" + id;

            modalTitle.textContent = "Edit Experience";

            errorBox.style.display = "none";
            errorText.textContent = "";

            modal.style.display = "flex";

        });

    });

    /* ======================================================
    Submit Experience Form
    ====================================================== */

    form.addEventListener("submit", async function (e) {

        e.preventDefault();

        errorBox.style.display = "none";
        errorText.textContent = "";

        const saveBtn = document.getElementById("saveExperienceBtn");
        const spinner = saveBtn.querySelector(".btn-spinner");
        const btnText = saveBtn.querySelector(".btn-text");

        saveBtn.disabled = true;
        spinner.style.display = "inline-flex";
        btnText.textContent = "Saving...";

        try {

            const response = await fetch(form.action, {

                method: "POST",
                body: new FormData(form)

            });

            const result = await response.json();

            if (result.success) {

                window.location.href = result.redirect;

            } else {

                // Restore button
                saveBtn.disabled = false;
                spinner.style.display = "none";
                btnText.textContent = "Save Experience";

                errorText.textContent = result.message;
                errorBox.style.display = "flex";

            }

        } catch (error) {

            // Restore button
            saveBtn.disabled = false;
            spinner.style.display = "none";
            btnText.textContent = "Save Experience";

            errorText.textContent =
                "Something went wrong. Please try again.";

            errorBox.style.display = "flex";

        }

    });

});

