// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from "firebase/auth";

const firebaseConfig = {
    apiKey: "AIzaSyAKEyek1xpqGeteLElxiGbQogg7xAjz3tc",
    authDomain: "stormhacks-2025-e48d7.firebaseapp.com",
    projectId: "stormhacks-2025-e48d7",
    storageBucket: "stormhacks-2025-e48d7.appspot.com",
    messagingSenderId: "253375249549",
    appId: "1:253375249549:web:1c008f76042dcafcc976c4"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const provider = new GoogleAuthProvider();

export const signInWithGoogle = async () => {
    try {
        const result = await signInWithPopup(auth, provider);
        return result.user;
    } catch (error) {
        console.error("Login failed:", error);
        alert(error.message); // <- will show errors in the browser
    }
};

export const logout = async () => {
    await signOut(auth);
};
