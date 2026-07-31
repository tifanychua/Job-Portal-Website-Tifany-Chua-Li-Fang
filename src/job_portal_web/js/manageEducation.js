// ======================================================
// ELEMENTS
// ======================================================

const modal = document.getElementById("educationModal");

const addEducationBtn = document.getElementById("addEducationBtn");
const closeEducationModal = document.getElementById("closeEducationModal");
const saveEducation = document.getElementById("saveEducation");

const educationContainer = document.getElementById("educationContainer");

const institution = document.getElementById("institution");
const suggestionBox = document.getElementById("institutionSuggestions");

const currentStudy = document.getElementById("currentStudy");
const endDate = document.getElementById("endDate");

// Currently editing card
let editingCard = null;

// ======================================================
// OPEN MODAL
// ======================================================

addEducationBtn.addEventListener("click", () => {

    editingCard = null;

    document.getElementById("modalTitle").textContent =
        "Add Education";

    clearForm();

    modal.classList.add("active");

});

// ======================================================
// CLOSE MODAL
// ======================================================

function closeModal() {

    modal.classList.remove("active");

}

closeEducationModal.onclick = closeModal;

window.onclick = function (e) {

    if (e.target === modal) {

        closeModal();

    }

};

// ======================================================
// CURRENTLY STUDYING
// ======================================================

currentStudy.addEventListener("change", function () {

    if (this.checked) {

        endDate.value = "";

        endDate.disabled = true;

    } else {

        endDate.disabled = false;

    }

});

// ======================================================
// UNIVERSITY AUTOCOMPLETE
// ======================================================

let searchTimer;

institution.addEventListener("input", function () {

    clearTimeout(searchTimer);

    searchTimer = setTimeout(async () => {

        const keyword = institution.value.trim();

        if (keyword.length < 3) {

            suggestionBox.innerHTML = "";
            suggestionBox.style.display = "none";

            return;

        }

        try {

            const response = await fetch(

                `/api/universities?name=${encodeURIComponent(keyword)}`

            );

            const universities = await response.json();

            suggestionBox.innerHTML = "";

            universities.slice(0, 8).forEach(uni => {

                const item = document.createElement("div");

                item.className = "autocomplete-item";

                item.innerHTML = `

                    <i class="fa-solid fa-graduation-cap"></i>

                    <span class="uni-name">

                        ${uni.name}

                    </span>

                    <span class="country">

                        ${uni.country}

                    </span>

                `;

                item.onclick = function () {

                    institution.value = uni.name;

                    suggestionBox.style.display = "none";

                };

                suggestionBox.appendChild(item);

            });

            suggestionBox.style.display =

                universities.length
                    ? "block"
                    : "none";

        }

        catch (err) {

            console.error(err);

        }

    }, 300);

});

// ======================================================
// CLOSE AUTOCOMPLETE
// ======================================================

document.addEventListener("click", function (e) {

    if (!e.target.closest(".autocomplete-container")) {

        suggestionBox.style.display = "none";

    }

});

// ======================================================
// SAVE EDUCATION
// ======================================================

const educationForm = document.getElementById("educationForm");

educationForm.addEventListener("submit", async function (e) {

    e.preventDefault();

    hideError();

    const qualification = document.getElementById("degree").value;

    const institution = document
        .getElementById("institution")
        .value.trim();

    const startDate = document
        .getElementById("startDate")
        .value;

    const endDate = document
        .getElementById("endDate")
        .value;

    const currentStudy =
        document.getElementById("currentStudy").checked;

    // ===========================================
    // Client Validation
    // ===========================================

    if (qualification === "") {

        showError("Please select your qualification.");

        return;

    }

    if (institution === "") {

        showError("Please enter your institution.");

        return;

    }

    if (startDate === "") {

        showError("Please select your start date.");

        return;

    }

    if (!currentStudy && endDate === "") {

        showError("Please select your end date.");

        return;

    }

    if (!currentStudy && endDate < startDate) {

        showError("Invalid study period.");

        return;

    }

    // ===========================================
    // Submit
    // ===========================================

    const formData = new FormData(educationForm);

    const response = await fetch(

        educationForm.action,

        {
            method: "POST",
            body: formData
        }

    );

    const result = await response.json();

    if (result.success) {

        window.location.href = result.redirect;

    }

    else {

        showError(result.message);

    }

});

// ======================================================
// CREATE EDUCATION CARD
// ======================================================

function createEducationCard(education) {

    const card = document.createElement("div");

    card.className = "education-card";

    updateEducationCard(card, education);

    educationContainer.prepend(card);

}

// ======================================================
// UPDATE EDUCATION CARD
// ======================================================

function updateEducationCard(card, education) {

    // Store original values for editing later

    card.dataset.qualification = education.qualification;
    card.dataset.institution = education.institution;
    card.dataset.field = education.field;
    card.dataset.startDate = education.startDate;
    card.dataset.endDate = education.endDate;
    card.dataset.currentStudy = education.currentStudy;
    card.dataset.grade = education.grade;
    card.dataset.description = education.description;

    card.innerHTML = `

        <div class="education-icon">

            <i class="fa-solid fa-graduation-cap"></i>

        </div>

        <div class="education-body">

            <h3>

                ${education.qualification}

            </h3>

            <p class="institution">

                ${education.institution}

            </p>

            ${
                education.field
                ? `
                <p class="field-of-study">

                    ${education.field}

                </p>
                `
                : ""
            }

            <div class="education-meta">

                <span>

                    <i class="fa-regular fa-calendar"></i>

                    ${formatDate(education.startDate)}
                    -
                    ${
                        education.currentStudy
                        ? "Present"
                        : formatDate(education.endDate)
                    }

                </span>

            </div>

            ${
                education.grade
                ? `
                <p class="grade">

                    Result

                    <strong>

                        ${education.grade}

                    </strong>

                </p>
                `
                : ""
            }

            ${
                education.description
                ? `
                <p class="education-description">

                    ${education.description}

                </p>
                `
                : ""
            }

        </div>

        <div class="education-actions">

            <button
                class="icon-btn editBtn">

                <i class="fa-solid fa-pen"></i>

            </button>

            <button
                class="icon-btn deleteBtn">

                <i class="fa-solid fa-trash"></i>

            </button>

        </div>

    `;

    attachCardEvents(card);

}

// ======================================================
// EDIT & DELETE EVENTS
// ======================================================

function attachCardEvents(card) {

    const editBtn = card.querySelector(".editBtn");

    const deleteBtn = card.querySelector(".deleteBtn");

    editBtn.onclick = function () {

        editingCard = card;

        document.getElementById("modalTitle").textContent =
            "Edit Education";

        document.getElementById("degree").value =
            card.dataset.qualification;

        institution.value =
            card.dataset.institution;

        document.getElementById("fieldOfStudy").value =
            card.dataset.field;

        document.getElementById("startDate").value =
            card.dataset.startDate;

        if (card.dataset.currentStudy === "true") {

            currentStudy.checked = true;

            endDate.value = "";

            endDate.disabled = true;

        }

        else {

            currentStudy.checked = false;

            endDate.disabled = false;

            endDate.value =
                card.dataset.endDate;

        }

        document.getElementById("grade").value =
            card.dataset.grade;

        document.getElementById("description").value =
            card.dataset.description;

        modal.classList.add("active");

    };

    deleteBtn.onclick = function () {

        if (confirm("Delete this education record?")) {

            card.remove();

        }

    };

}

// ======================================================
// FORMAT MONTH
// ======================================================

function formatDate(value) {

    if (!value || value === "Present") {

        return value;

    }

    const months = [

        "Jan", "Feb", "Mar", "Apr",

        "May", "Jun", "Jul", "Aug",

        "Sep", "Oct", "Nov", "Dec"

    ];

    const parts = value.split("-");

    return months[parseInt(parts[1]) - 1] + " " + parts[0];

}

// ======================================================
// CLEAR FORM
// ======================================================

function clearForm() {

    document.getElementById("degree").value = "";

    institution.value = "";

    document.getElementById("fieldOfStudy").value = "";

    document.getElementById("startDate").value = "";

    endDate.value = "";

    currentStudy.checked = false;

    endDate.disabled = false;

    document.getElementById("grade").value = "";

    document.getElementById("description").value = "";

}

// ======================================================
// EDIT EDUCATION
// ======================================================

document.querySelectorAll(".editBtn").forEach(button => {

    button.addEventListener("click", async function () {

        try {

            const educationId = this.dataset.id;

            const response = await fetch(`/education/${educationId}`);

            if (!response.ok) {

                alert("Unable to load education.");

                return;

            }

            const education = await response.json();

            document.getElementById("modalTitle").textContent = "Edit Education";

            educationForm.action = "/update-education";

            document.getElementById("educationId").value = education.id;

            document.getElementById("degree").value =
                education.qualification;

            document.getElementById("institution").value =
                education.institution;

            document.getElementById("fieldOfStudy").value =
                education.field_of_study || "";

            document.getElementById("startDate").value =
                education.start_date || "";

            document.getElementById("endDate").value =
                education.end_date || "";

            document.getElementById("grade").value =
                education.grade || "";

            document.getElementById("description").value =
                education.description || "";

            currentStudy.checked = education.current_study;

            if (education.current_study) {

                endDate.disabled = true;

            } else {

                endDate.disabled = false;

            }

            modal.classList.add("active");

        }

        catch (err) {

            console.error(err);

            alert("Unable to load education.");

        }

    });

});

// ======================================================
// ADD EDUCATION
// ======================================================

addEducationBtn.addEventListener("click", () => {

    clearForm();

    document.getElementById("modalTitle").textContent =
        "Add Education";

    educationForm.action = "/add-education";

    document.getElementById("educationId").value = "";

    modal.classList.add("active");

});

// ======================================================
// ERROR MESSAGE
// ======================================================

function showError(message){

    document.getElementById("educationErrorText").textContent = message;

    document.getElementById("educationError").style.display = "flex";

}

function hideError(){

    document.getElementById("educationError").style.display = "none";

}