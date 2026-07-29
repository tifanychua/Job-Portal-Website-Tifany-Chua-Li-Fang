
import { auth } from "./firebase.js";

import {
    createUserWithEmailAndPassword,
    updateProfile
} from "https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js";

const form = document.getElementById("employerForm");
const passwordInput = document.getElementById("wizardPassword");

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

function validateStep1() {

    const companyName = document.getElementById("companyName").value.trim();
    const businessEmail = document.getElementById("businessEmail").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const registrationNumber = document.getElementById("registrationNumber").value.trim();
    const postalCode = document.getElementById("postalCode").value.trim();
    const companyWebsite = document.getElementById("companyWebsite").value.trim();

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const phoneRegex = /^\d{9,10}$/;
    const postalRegex = /^\d{5}$/;

    if (companyName.length < 2 || companyName.length > 100) {
        alert("Company name must be between 2 and 100 characters.");
        return false;
    }

    if (!emailRegex.test(businessEmail)) {
        alert("Please enter a valid business email.");
        return false;
    }

    if (!phoneRegex.test(phone)) {
        alert("Company phone number must contain 9 or 10 digits.");
        return false;
    }

    if (!postalRegex.test(postalCode)) {
        alert("Postal code must contain 5 digits.");
        return false;
    }

    if (registrationNumber.length !== 12) {
        alert("Please enter a valid company registration number.");
        return false;
    }

    if (companyWebsite !== "") {
        try {
            new URL(companyWebsite);
        } catch {
            alert("Please enter a valid website URL.");
            return false;
        }
    }

    return true;
}

function validateStep2() {

    const contactFullName =
        document.getElementById("contactFullName").value.trim();

    const contactEmail =
        document.getElementById("contactEmail").value.trim();

    const contactPhone =
        document.getElementById("contactPhone").value.trim();

    const altPhone =
        document.getElementById("altPhone").value.trim();

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const phoneRegex = /^\d{9,10}$/;

    if (contactFullName.length < 2 || contactFullName.length > 100) {
        alert("Contact person's name must be between 2 and 100 characters.");
        return false;
    }

    if (!emailRegex.test(contactEmail)) {
        alert("Please enter a valid contact email.");
        return false;
    }

    if (!phoneRegex.test(contactPhone)) {
        alert("Contact phone number must contain 9 or 10 digits.");
        return false;
    }

    if (altPhone !== "" && !phoneRegex.test(altPhone)) {
        alert("Alternative phone number must contain 9 or 10 digits.");
        return false;
    }

    return true;
}

function validateStep3() {

    const accountEmail =
        document.getElementById("accountEmail").value.trim();

    const password =
        document.getElementById("wizardPassword").value;

    const confirmPassword =
        document.getElementById("wizardConfirmPassword").value;

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    const passwordRegex =
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;

    if (!emailRegex.test(accountEmail)) {
        alert("Please enter a valid account email.");
        return false;
    }

    if (!passwordRegex.test(password)) {
        alert("Password does not meet the security requirements.");
        return false;
    }

    if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return false;
    }

    return true;
}

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    const accountEmail =
        document.getElementById("accountEmail").value.trim();

    const password =
        document.getElementById("wizardPassword").value;

    try {

        // Create Firebase Authentication account
        const credential =
            await createUserWithEmailAndPassword(
                auth,
                accountEmail,
                password
            );

        await updateProfile(credential.user, {
            displayName: document.getElementById("companyName").value
        });

        const token = await credential.user.getIdToken();

        const employerData = {

            token,

            companyName:
                document.getElementById("companyName").value,

            registrationNumber:
                document.getElementById("registrationNumber").value,

            businessEmail:
                document.getElementById("businessEmail").value,

            phone:
                document.getElementById("phoneCode").value +
                " " +
                document.getElementById("phone").value,

            industry:
                document.getElementById("industry").value,

            companySize:
                document.getElementById("companySize").value,

            companyWebsite:
                document.getElementById("companyWebsite").value,

            companyDescription:
                document.getElementById("companyDescription").value,

            address:
                document.getElementById("companyAddress").value,

            city:
                document.getElementById("city").value,

            state:
                document.getElementById("state").value,

            postalCode:
                document.getElementById("postalCode").value,

            country:
                document.getElementById("country").value,

            contactFullName:
                document.getElementById("contactFullName").value,

            contactJobTitle:
                document.getElementById("contactJobTitle").value,

            contactDepartment:
                document.getElementById("contactDepartment").value,

            contactEmail:
                document.getElementById("contactEmail").value,

            contactPhone:
                document.getElementById("contactPhoneCode").value +
                " " +
                document.getElementById("contactPhone").value,

            altPhone:
                document.getElementById("altPhone").value
                    ? document.getElementById("altPhoneCode").value +
                      " " +
                      document.getElementById("altPhone").value
                    : "",

            preferredContactMethod:
                document.querySelector(
                    'input[name="preferredContactMethod"]:checked'
                ).value,

            bestTimeToContact:
                document.getElementById("bestTimeToContact").value,

            correspondenceAddress:
                document.getElementById("correspondenceAddress").value,

        };

        const response = await fetch("/firebase-register/employer", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(employerData)

        });

        const result = await response.json();

        if (response.ok) {

            window.location.href =
                "/login?registered=success&role=employer";

        } else {

            alert(result.error || "Registration failed.");

        }

    } catch (error) {

        alert(error.message);

    }

});

window.validateStep1 = validateStep1;
window.validateStep2 = validateStep2;
window.validateStep3 = validateStep3;