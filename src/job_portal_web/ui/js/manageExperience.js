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


    /* ======================================================
       Open Add Modal
    ====================================================== */

    if (addBtn) {

        addBtn.addEventListener("click", () => {

            form.reset();

            modalTitle.textContent = "Add Experience";

            form.action = "/add-experience";

            document.getElementById("experienceId").value = "";

            currentJob.checked = false;

            endDate.disabled = false;

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

            modal.style.display = "flex";

        });

    });

});