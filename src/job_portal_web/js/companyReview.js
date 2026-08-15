// ======================================================
// Company Review Wizard
// ======================================================

document.addEventListener("DOMContentLoaded", () => {

    const steps = document.querySelectorAll(".review-step");

    const progressSteps = document.querySelectorAll(".step");

    let currentStep = 0;

    // ==================================================
    // Employment Fields
    // ==================================================

    const startDate = document.getElementById("startDate");
    const endDate = document.getElementById("endDate");
    const stillWorking = document.getElementById("stillWorking");

    const jobTitle = document.getElementById("jobTitle");
    const department = document.getElementById("department");
    const location = document.getElementById("location");

    if (stillWorking && endDate) {

        stillWorking.addEventListener("change", () => {

            if (stillWorking.checked) {

                endDate.value = "";

                endDate.disabled = true;

                endDate.removeAttribute("required");

            } else {

                endDate.disabled = false;

                endDate.setAttribute("required", "required");

            }

        });

    }

    // ==================================================
    // Show Step
    // ==================================================

    function showStep(index){

        steps.forEach(step=>{

            step.classList.add("hidden");

        });

        steps[index].classList.remove("hidden");

        progressSteps.forEach((step,i)=>{

            if(i<=index){

                step.classList.add("active");

            }else{

                step.classList.remove("active");

            }

        });

        window.scrollTo({

            top:0,

            behavior:"smooth"

        });

    }

    showStep(0);

    // ==================================================
    // Next Button
    // ==================================================

    document.querySelectorAll(".btn-next").forEach(button=>{

        button.addEventListener("click",()=>{

            if (currentStep === 0) {

                if (currentStep === 0 && ratingInput.value === "") {

                    ratingError.textContent = "Please select an overall rating.";

                    ratingError.style.display = "block";

                    return;

                }

            }

            if(!validateStep(currentStep)){

                return;

            }

            if(currentStep === 1 && !validateDate()){

                return;

            }

            if(currentStep < steps.length-1){

                currentStep++;

                showStep(currentStep);

            }

        });

    });

    // ==================================================
    // Back Button
    // ==================================================

    document.querySelectorAll(".btn-back").forEach(button=>{

        button.addEventListener("click",()=>{

            if(currentStep>0){

                currentStep--;

                showStep(currentStep);

            }

        });

    });

        // ==================================================
    // Validate Current Step
    // ==================================================

    function validateStep(index){

        const current = steps[index];

        const requiredFields = current.querySelectorAll(
            "input[required], textarea[required], select[required]"
        );

        for(const field of requiredFields){

            field.classList.remove("input-error");

            // Radio Button
            if(field.type==="radio"){

                const checked=current.querySelector(
                    `input[name="${field.name}"]:checked`
                );

                if(!checked){

                    alert("Please answer all required questions.");

                    return false;

                }

            }

            // Checkbox
            else if(field.type==="checkbox"){

                continue;

            }

            // Normal Input
            else{

                if(field.value.trim()===""){

                    field.classList.add("input-error");

                    field.focus();

                    alert("Please complete all required fields.");

                    return false;

                }

            }

        }

        return true;

    }

    // ==================================================
    // Star Ratings (All Rating Groups)
    // ==================================================

    const ratingInput = document.getElementById("overallRating");
    const ratingError = document.getElementById("ratingError");

    document.querySelectorAll(".star-rating").forEach(group => {

        const stars = group.querySelectorAll("i");

        const hiddenInput =
            group.parentElement.querySelector("input[type='hidden']");

        stars.forEach((star, index) => {

            star.addEventListener("click", () => {

                stars.forEach((item, i) => {

                    if (i <= index) {

                        item.classList.remove("fa-regular");
                        item.classList.add("fa-solid");
                        item.classList.add("active");

                    } else {

                        item.classList.remove("fa-solid");
                        item.classList.remove("active");
                        item.classList.add("fa-regular");

                    }

                });

                if (hiddenInput) {

                    hiddenInput.value = index + 1;

                }

                if (hiddenInput &&
                    hiddenInput.id === "overallRating") {

                    ratingError.textContent = "";

                }

            });

        });

    });

    // ==================================================
    // Character Counter
    // ==================================================

    document.querySelectorAll("textarea[maxlength]").forEach(textarea=>{

        const counter=document.createElement("small");

        counter.className="helper-text";

        textarea.after(counter);

        function update(){

            counter.textContent=
                `${textarea.value.length}/${textarea.maxLength} characters`;

        }

        textarea.addEventListener("input",update);

        update();

    });

        // ==================================================
    // Prevent Double Submit
    // ==================================================

    const form=document.querySelector("form");

    if(form){

        form.addEventListener("submit",(e)=>{

            if(!validateStep(currentStep)){

                e.preventDefault();

                return;

            }

            const ratings = form.querySelectorAll(
                ".rating-item input[type='hidden']"
            );

            for (const rating of ratings) {

                if (rating.value === "") {

                    alert("Please rate every category before submitting.");

                    e.preventDefault();

                    return;

                }

            }

            const submitButton=form.querySelector(
                "button[type='submit']"
            );

            if(submitButton){

                submitButton.disabled=true;

                submitButton.innerHTML=
                    '<i class="fa-solid fa-spinner fa-spin"></i> Submitting...';

            }

        });

    }

    // ==================================================
    // Radio Button Active Style
    // ==================================================

    document.querySelectorAll(".option-btn input").forEach(input=>{

        input.addEventListener("change",()=>{

            const group=input.closest(".option-group");

            group.querySelectorAll(".option-btn").forEach(label=>{

                label.classList.remove("active");

            });

            input.parentElement.classList.add("active");

        });

    });

    // ==================================================
    // Progress Click
    // ==================================================

    progressSteps.forEach((step,index)=>{

        step.addEventListener("click",()=>{

            if(index<=currentStep){

                currentStep=index;

                showStep(currentStep);

            }

        });

    });

    // ==================================================
    // Smooth Scroll
    // ==================================================

    function scrollTopPage(){

        window.scrollTo({

            top:0,

            behavior:"smooth"

        });

    }

    document.querySelectorAll(".btn-next,.btn-back").forEach(btn=>{

        btn.addEventListener("click",()=>{

            setTimeout(scrollTopPage,150);

        });

    });

    // ==================================================
    // Keyboard Support (Left / Right)
    // ==================================================

    document.addEventListener("keydown",(event)=>{

        if(event.key==="ArrowRight"){

            const next=document.querySelector(".review-step:not(.hidden) .btn-next");

            if(next){

                next.click();

            }

        }

        if(event.key==="ArrowLeft"){

            const back=document.querySelector(".review-step:not(.hidden) .btn-back");

            if(back){

                back.click();

            }

        }

    });

    function validateDate() {

        if (!startDate) {

            return true;

        }

        if (stillWorking.checked) {

            return true;

        }

        if (!startDate.value || !endDate.value) {

            return true;

        }

        const start = new Date(startDate.value);

        const end = new Date(endDate.value);

        if (end <= start) {

            alert("Ended Working must be later than Started Working.");

            endDate.focus();

            return false;

        }

        return true;

    }

    if (startDate && endDate) {

        const today = new Date();

        const currentMonth =
            today.getFullYear() +
            "-" +
            String(today.getMonth() + 1).padStart(2, "0");

        startDate.max = currentMonth;

        endDate.max = currentMonth;

    }

    if (jobTitle) {

        jobTitle.addEventListener("input", () => {

            jobTitle.value = jobTitle.value.replace(/[0-9]/g, "");

        });

    }

    if (department) {

        department.addEventListener("input", () => {

            department.value =
                department.value.replace(/[0-9]/g, "");

        });

    }

    if (location) {

        location.addEventListener("input", () => {

            location.value =
                location.value.replace(/[0-9]/g, "");

        });

    }


    // ==================================================
    // Auto Focus
    // ==================================================

    function focusFirstField(){

        const field=steps[currentStep].querySelector(

            "input,textarea,select"

        );

        if(field){

            field.focus();

        }

    }

    focusFirstField();

});