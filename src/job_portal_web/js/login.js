import { auth } from "./firebase.js";

import {
    signInWithEmailAndPassword
} from "https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js";

const form = document.getElementById("loginForm");
const loginBtn = document.getElementById("loginBtn");

function setLoading(isLoading) {

    if (isLoading) {

        loginBtn.disabled = true;

        loginBtn.innerHTML = `
            <i class="fa-solid fa-spinner fa-spin"></i>
            Logging in...
        `;

    } else {

        loginBtn.disabled = false;

        loginBtn.innerHTML = "Log In";

    }
}



form.addEventListener("submit", async function (e) {

    e.preventDefault();

    const email = document.getElementById("email").value;

    const password = document.getElementById("password").value;

    try {

        // Firebase Login
        const credential =
            await signInWithEmailAndPassword(
                auth,
                email,
                password
            );

        // Get Firebase Token
        const token = await credential.user.getIdToken();

        // Send Token to FastAPI
        const response = await fetch("/firebase-login", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                token: token
            })

        });

        const result = await response.json();

        if (response.ok) {

            window.location = result.redirect;

        } else {

            alert(result.error);

        }

    }
    catch (error) {
         setLoading(false);

    switch (error.code) {

        case "auth/invalid-credential":
        case "auth/wrong-password":
        case "auth/user-not-found":
            alert("Invalid email or password.");
            break;

        case "auth/invalid-email":
            alert("Please enter a valid email address.");
            break;

        case "auth/too-many-requests":
            alert("Too many failed login attempts. Please try again later.");
            break;

        case "auth/network-request-failed":
            alert("Network error. Please check your internet connection.");
            break;

        default:
            alert("Login failed. Please try again.");
    }

    }

});