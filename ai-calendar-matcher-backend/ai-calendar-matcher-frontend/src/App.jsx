import React, { useState } from "react";
import Login from "./components/Login.jsx";

function App() {
  const [user, setUser] = useState(null);

  const handleLogin = ({ user, token }) => {
    console.log("Logged in user:", user);
    console.log("Token:", token);
    setUser(user);
  };

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h1>AI Calendar Matcher</h1>
      {!user ? (
        <Login onLogin={handleLogin} />
      ) : (
        <div>
          <h2>Welcome, {user.displayName}!</h2>
          <p>Email: {user.email}</p>
        </div>
      )}
    </div>
  );
}

export default App;
