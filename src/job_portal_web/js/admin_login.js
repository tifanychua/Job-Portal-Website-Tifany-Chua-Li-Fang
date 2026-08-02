import { auth } from "./firebase.js";

import {
    signInWithEmailAndPassword
} from "https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js";

const form = document.getElementById("adminLoginForm");

form.addEventListener("submit", async function (e) {

    e.preventDefault();

    const email = document.getElementById("email").value;

    const password = document.getElementById("password").value;

    try {

        // Firebase Authentication
        const credential = await signInWithEmailAndPassword(
            auth,
            email,
            password
        );

        const token = await credential.user.getIdToken();

        // Send token to Admin Login API
        const response = await fetch("/admin/firebase-login", {

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

            window.location.href = result.redirect;

        } else {

            alert(result.error);

            await auth.signOut();   // Logout if not an admin
        }

    }
    catch (error) {

        alert(error.message);

    }

});