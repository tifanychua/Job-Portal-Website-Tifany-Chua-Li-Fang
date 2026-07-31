import { auth } from "./firebase.js";

import {
    createUserWithEmailAndPassword,
    updateProfile
} from "https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js";

const form = document.getElementById("registerForm");
const passwordInput = document.getElementById("password");

passwordInput.addEventListener("input", function () {

    const password = this.value;

    toggleRule("rule-length", password.length >= 8);
    toggleRule("rule-uppercase", /[A-Z]/.test(password));
    toggleRule("rule-lowercase", /[a-z]/.test(password));
    toggleRule("rule-number", /\d/.test(password));
    toggleRule("rule-special", /[^A-Za-z0-9]/.test(password));

});

function toggleRule(id, valid) {

    const rule = document.getElementById(id);

    if (!rule) return;

    if (valid) {
        rule.classList.add("valid");
    } else {
        rule.classList.remove("valid");
    }

}

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (name.length < 2) {
        alert("Name must contain at least 2 characters.");
        return;
    }

    if (name.length > 100) {
        alert("Name is too long.");
        return;
    }

    // Required
    if (email === "") {
        alert("Email address is required.");
        return;
    }

    // Maximum length (RFC standard)
    if (email.length > 254) {
        alert("Email address is too long.");
        return;
    }

    // Email format
    if (!emailRegex.test(email)) {
        alert("Please enter a valid email address.");
        return;
    }

    const passwordRegex =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&^#()_\-+=\[\]{}|\\:;"'<>,./~`])[A-Za-z\d@$!%*?&^#()_\-+=\[\]{}|\\:;"'<>,./~`]{8,}$/;

    if (!passwordRegex.test(password)) {
        alert(
            "Password must be at least 8 characters long and include:\n" +
            "• At least one uppercase letter\n" +
            "• At least one lowercase letter\n" +
            "• At least one number\n" +
            "• At least one special character"
        );
        return;
    }

    if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return;
    }

    const phoneRegex = /^\d{9,10}$/;

    if (phone !== "" && !phoneRegex.test(phone)) {
        alert("Phone number must contain 9 or 10 digits.");
        return;
    }

    try {

        // Create Firebase Authentication user
        const credential = await createUserWithEmailAndPassword(
            auth,
            email,
            password
        );

        // Update Firebase display name
        await updateProfile(credential.user, {
            displayName: name
        });

        // Get Firebase ID Token
        const token = await credential.user.getIdToken();

        // Save profile to Firestore through FastAPI
        const response = await fetch("/firebase-register/job-seeker", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                token,
                name,
                phone
            })
        });

        console.log(response.status);

        const result = await response.json();

        console.log(result);

        if (response.ok) {

            window.location.href = "/login?registered=success&role=job_seeker";

        } else {

            alert(JSON.stringify(result));

        }

    } catch (error) {

        alert(error.message);

    }

});