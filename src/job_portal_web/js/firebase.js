import { initializeApp } from
"https://www.gstatic.com/firebasejs/11.10.0/firebase-app.js";

import { getAuth } from
"https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyDU2b62zMofwamN0sI55hCphEleaZ7-Wb8",
    authDomain: "job-portal-website-fc6fd.firebaseapp.com",
    databaseURL: "https://job-portal-website-fc6fd-default-rtdb.firebaseio.com",
    projectId: "job-portal-website-fc6fd",
    storageBucket: "job-portal-website-fc6fd.firebasestorage.app",
    messagingSenderId: "644094639765",
    appId: "1:644094639765:web:390c343f50bec5c1e1259c",
    measurementId: "G-2KC5FXTBKV"
  };

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);