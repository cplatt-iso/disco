// src/pages/Login.jsx

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
// Import the CORRECTLY named custom hook from your UserContext file
import { useUserContext } from '../context/UserContext';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Use the CORRECT hook to get the login function
  const { login } = useUserContext();
  const navigate = useNavigate();
  const location = useLocation();

  // Determine where to redirect after login
  // Defaults to /dashboard if no previous location was stored
  const from = location.state?.from?.pathname || "/dashboard";

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(''); // Clear previous errors
    setLoading(true);

    if (!username || !password) {
        setError('Please enter both username and password.');
        setLoading(false);
        return;
    }

    try {
      // Call the login function from the context
      await login(username, password);
      console.log("Login page: Login successful, navigating to:", from);
      // Navigation is now handled inside the login function in UserContext on success
      // navigate(from, { replace: true }); // Keep this commented unless context doesn't navigate

    } catch (err) {
      console.error("Login page: Login failed:", err);
      // Use the error message provided by the context's login function
      setError(err.message || 'Login failed. Please check your credentials.');
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="px-8 py-6 mt-4 text-left bg-white shadow-lg rounded-lg w-full max-w-md">
        <h3 className="text-2xl font-bold text-center text-gray-700">Login to DISCO</h3>
        <form onSubmit={handleSubmit}>
          <div className="mt-4">
            <div>
              <label className="block text-gray-700" htmlFor="username">Username</label>
              <input
                type="text"
                placeholder="Username"
                id="username"
                className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <div className="mt-4">
              <label className="block text-gray-700" htmlFor="password">Password</label>
              <input
                type="password"
                placeholder="Password"
                id="password"
                className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            {error && <p className="mt-3 text-xs text-red-600">{error}</p>}
            <div className="flex items-baseline justify-center"> {/* Changed to center */}
              <button
                type="submit"
                className="px-6 py-2 mt-4 text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-opacity-50 disabled:opacity-50"
                disabled={loading}
              >
                {loading ? 'Logging in...' : 'Login'}
              </button>
            </div>
             {/* Optional: Add link for password reset or registration if needed */}
          </div>
        </form>
      </div>
    </div>
  );
}

export default Login;
