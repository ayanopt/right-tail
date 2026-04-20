import React, { useState } from "react";
import { useAppDispatch, useAppSelector } from "../hooks";
import { selectIsAuthenticated } from "../store/authSlice";

export function LoginForm() {
  const dispatch = useAppDispatch();
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  if (isAuthenticated) {
    return <p>You are logged in.</p>;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: dispatch login thunk
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit">Log in</button>
    </form>
  );
}
