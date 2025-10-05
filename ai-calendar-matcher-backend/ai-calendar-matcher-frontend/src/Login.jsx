import React from "react";
import { signInWithGoogle, logout } from "./Firebase";

export default function Login({ onLogin }) {
  const handleLogin = async () => {
    const user = await signInWithGoogle();
    if (user) {
      onLogin({ user, token: user.accessToken });
    }
  };

  return (
    <div>
      <button onClick={handleLogin}>Sign in with Google</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
