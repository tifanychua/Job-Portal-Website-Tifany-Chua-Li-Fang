// ======================================================
// ELEMENTS
// ======================================================

const addSkillBtn = document.getElementById("addSkillBtn");
const emptyAddSkillBtn = document.getElementById("emptyAddSkillBtn");

const skillModal = document.getElementById("skillModal");
const editSkillModal = document.getElementById("editSkillModal");

const closeSkillModal = document.getElementById("closeSkillModal");
const closeEditSkillModal = document.getElementById("closeEditSkillModal");

const industrySelect = document.getElementById("industry");
const categorySelect = document.getElementById("category");
const skillSelect = document.getElementById("skill");

const editIndustry = document.getElementById("editIndustry");
const editCategory = document.getElementById("editCategory");
const editSkill = document.getElementById("editSkill");

// ======================================================
// OPEN ADD MODAL
// ======================================================

function openAddModal() {

    skillModal.classList.add("show");

    loadIndustries();

}

if (addSkillBtn) {

    addSkillBtn.addEventListener("click", openAddModal);

}

if (emptyAddSkillBtn) {

    emptyAddSkillBtn.addEventListener("click", openAddModal);

}

// ======================================================
// CLOSE ADD MODAL
// ======================================================

closeSkillModal.addEventListener("click", () => {

    skillModal.classList.remove("show");

    document.getElementById("skillForm").reset();

    categorySelect.innerHTML =
        '<option value="">Select Skill Category</option>';

    categorySelect.disabled = true;

    skillSelect.innerHTML =
        '<option value="">Select Skill</option>';

    skillSelect.disabled = true;

});

// ======================================================
// CLOSE EDIT MODAL
// ======================================================

closeEditSkillModal.addEventListener("click", () => {

    editSkillModal.classList.remove("show");

});

// ======================================================
// CLICK OUTSIDE TO CLOSE
// ======================================================

window.addEventListener("click", (e) => {

    if (e.target === skillModal) {

        skillModal.classList.remove("show");

    }

    if (e.target === editSkillModal) {

        editSkillModal.classList.remove("show");

    }

});

// ======================================================
// LOAD INDUSTRIES
// ======================================================

async function loadIndustries() {

    try {

        const response = await fetch("/api/industries");

        const industries = await response.json();

        industrySelect.innerHTML =
            '<option value="">Select Industry</option>';

        editIndustry.innerHTML =
            '<option value="">Select Industry</option>';

        industries.forEach(industry => {

            const option1 = document.createElement("option");

            option1.value = industry.industry_id;

            option1.textContent = industry.industry_name;

            industrySelect.appendChild(option1);

            const option2 = document.createElement("option");

            option2.value = industry.industry_id;

            option2.textContent = industry.industry_name;

            editIndustry.appendChild(option2);

        });

    } catch (error) {

        console.error("Failed to load industries:", error);

    }

}

// ======================================================
// INITIAL LOAD
// ======================================================

loadIndustries();

// ======================================================
// LOAD CATEGORIES
// ======================================================

async function loadCategories(industryId, isEdit = false) {

    if (!industryId) return;

    try {

        const response = await fetch(`/api/skill-categories/${industryId}`);

        const categories = await response.json();

        const select = isEdit ? editCategory : categorySelect;

        select.innerHTML =
            '<option value="">Select Skill Category</option>';

        categories.forEach(category => {

            const option = document.createElement("option");

            option.value = category.category_id;
            option.textContent = category.category_name;

            select.appendChild(option);

        });

        select.disabled = false;

    } catch (error) {

        console.error(error);

    }

}

// ======================================================
// LOAD SKILLS
// ======================================================

async function loadSkills(categoryId, isEdit = false) {

    if (!categoryId) return;

    try {

        const response = await fetch(`/api/skills/${categoryId}`);

        const skills = await response.json();

        const select = isEdit ? editSkill : skillSelect;

        select.innerHTML =
            '<option value="">Select Skill</option>';

        skills.forEach(skill => {

            const option = document.createElement("option");

            option.value = skill.skill_id;
            option.textContent = skill.skill_name;

            select.appendChild(option);

        });

        select.disabled = false;

    } catch (error) {

        console.error(error);

    }

}

// ======================================================
// ADD MODAL
// Industry Changed
// ======================================================

industrySelect.addEventListener("change", async function () {

    categorySelect.disabled = true;
    skillSelect.disabled = true;

    categorySelect.innerHTML =
        '<option value="">Select Skill Category</option>';

    skillSelect.innerHTML =
        '<option value="">Select Skill</option>';

    if (this.value) {

        await loadCategories(this.value);

    }

});

// ======================================================
// ADD MODAL
// Category Changed
// ======================================================

categorySelect.addEventListener("change", async function () {

    skillSelect.disabled = true;

    skillSelect.innerHTML =
        '<option value="">Select Skill</option>';

    if (this.value) {

        await loadSkills(this.value);

    }

});

// ======================================================
// EDIT MODAL
// Industry Changed
// ======================================================

editIndustry.addEventListener("change", async function () {

    editCategory.disabled = true;
    editSkill.disabled = true;

    editCategory.innerHTML =
        '<option value="">Select Skill Category</option>';

    editSkill.innerHTML =
        '<option value="">Select Skill</option>';

    if (this.value) {

        await loadCategories(this.value, true);

    }

});

// ======================================================
// EDIT MODAL
// Category Changed
// ======================================================

editCategory.addEventListener("change", async function () {

    editSkill.disabled = true;

    editSkill.innerHTML =
        '<option value="">Select Skill</option>';

    if (this.value) {

        await loadSkills(this.value, true);

    }

});

// ======================================================
// EDIT BUTTON
// ======================================================

const editButtons = document.querySelectorAll(".editSkillBtn");

editButtons.forEach(button => {

    button.addEventListener("click", async function () {

        const documentId = this.dataset.id;

        const industryId = this.dataset.industry;

        const categoryId = this.dataset.category;

        const skillId = this.dataset.skill;

        const level = this.dataset.level;

        editSkillModal.classList.add("show");

        document.getElementById("editSkillForm").action =
            `/edit-skill/${documentId}`;

        // Load industries
        await loadIndustries();

        editIndustry.value = industryId;

        // Load categories
        await loadCategories(industryId, true);

        editCategory.value = categoryId;

        // Load skills
        await loadSkills(categoryId, true);

        editSkill.value = skillId;

        document.getElementById("editLevel").value = level;

    });

});

// ======================================================
// SEARCH
// ======================================================

const searchInput = document.getElementById("skillSearch");

if (searchInput) {

    searchInput.addEventListener("input", function () {

        const keyword = this.value.trim().toLowerCase();

        const cards = document.querySelectorAll(".education-card");

        cards.forEach(card => {

            const text = card.innerText.toLowerCase();

            if (text.includes(keyword)) {
                card.style.display = "flex";
            } else {
                card.style.display = "none";
            }

        });

    });

}

// ======================================================
// RESET ADD FORM
// ======================================================

const skillForm = document.getElementById("skillForm");

if (skillForm) {

    skillForm.addEventListener("reset", () => {

        categorySelect.innerHTML =
            '<option value="">Select Skill Category</option>';

        categorySelect.disabled = true;

        skillSelect.innerHTML =
            '<option value="">Select Skill</option>';

        skillSelect.disabled = true;

    });

}

// ======================================================
// RESET EDIT FORM
// ======================================================

const editForm = document.getElementById("editSkillForm");

if (editForm) {

    editForm.addEventListener("reset", () => {

        editCategory.innerHTML =
            '<option value="">Select Skill Category</option>';

        editCategory.disabled = true;

        editSkill.innerHTML =
            '<option value="">Select Skill</option>';

        editSkill.disabled = true;

    });

}

// ======================================================
// ESC KEY CLOSE MODALS
// ======================================================

document.addEventListener("keydown", function (event) {

    if (event.key === "Escape") {

        skillModal.classList.remove("show");

        editSkillModal.classList.remove("show");

    }

});

// ======================================================
// OPTIONAL: PREVENT DOUBLE SUBMIT
// ======================================================

document.querySelectorAll("form").forEach(form => {

    form.addEventListener("submit", function () {

        const submitButton = this.querySelector(
            "button[type='submit']"
        );

        if (submitButton) {

            submitButton.disabled = true;

            submitButton.innerHTML =
                '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

        }

    });

});