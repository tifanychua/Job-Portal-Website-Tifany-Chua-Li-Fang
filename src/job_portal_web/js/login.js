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

    setLoading(true);

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {

        const credential =
            await signInWithEmailAndPassword(
                auth,
                email,
                password
            );

        const token = await credential.user.getIdToken();

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

            return;

        }

        setLoading(false);
        alert(result.error);

    }
    catch (error) {

        setLoading(false);
        alert(error.message);

    }

});


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

        alert(error.message);

    }

});