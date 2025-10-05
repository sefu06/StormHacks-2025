import React from "react";
import { signInWithGoogle } from "./firebase";

export default function Login({ onLogin }) {
  const handleLogin = async () => {
    console.log("Login clicked");
    const user = await signInWithGoogle();
    console.log("User returned:", user);
    if (user) {
      const token = await user.getIdToken();
      onLogin({ user, token });
    }
  };

  return (
    <button onClick={handleLogin} style={{ padding: "10px", fontSize: "16px" }}>
      Sign in with Google
    </button>
  );
}
