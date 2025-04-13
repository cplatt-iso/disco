// src/context/UserContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// Define the context - keep it local to this module
const UserContext = createContext(null);

// Export the Provider component
export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null); // State to hold user info if needed
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();

  // Effect to check for existing token on initial load
  useEffect(() => {
    const token = localStorage.getItem('disco_token');
    if (token) {
      // In a real app, you'd ideally validate the token with the backend here.
      // For simplicity now, we assume a token means the user *was* authenticated.
      console.log("UserContext: Found token, setting authenticated state.");
      setIsAuthenticated(true);
      // You could decode the token (if JWT) to get basic user info without an API call,
      // but be careful about relying on potentially stale/insecure frontend data.
      // Example: setUser({ username: decodedToken.sub });
    } else {
      console.log("UserContext: No token found.");
      setIsAuthenticated(false); // Explicitly set to false if no token
    }
  }, []); // Empty dependency array ensures this runs only once on mount

  const login = async (username, password) => {
    console.log("UserContext: Attempting login...");
    setIsAuthenticated(false); // Reset auth state during attempt
    try {
      // Ensure this matches your FastAPI token endpoint path
      const response = await fetch('/api/auth/token', {
        method: 'POST',
        // FastAPI's OAuth2PasswordBearer expects form data
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: username, password: password })
      });

      if (!response.ok) {
        // Try to parse error detail from backend response
        const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
        console.error("UserContext: Login failed", response.status, errorData);
        // Throw an error with details from backend if possible
        throw new Error(errorData.detail || `Invalid credentials or server error (${response.status})`);
      }

      const data = await response.json(); // Should contain { access_token: "...", token_type: "bearer" }
      if (data.access_token) {
        localStorage.setItem('disco_token', data.access_token);
        setIsAuthenticated(true);
        // Optionally fetch user details using the new token or set from token if available
        // setUser({ username: username }); // Placeholder
        console.log("UserContext: Login successful.");
        navigate('/dashboard'); // Navigate to dashboard after successful login
        return true; // Indicate success to the caller (Login page)
      } else {
           throw new Error("Login response did not include access token.");
      }

    } catch (error) {
      console.error("UserContext: Login error", error);
      localStorage.removeItem('disco_token'); // Ensure token is removed on failed login
      setIsAuthenticated(false);
      setUser(null);
      // Re-throw the error so the Login component can display it
      throw error;
    }
  };

  const logout = () => {
    console.log("UserContext: Logging out.");
    localStorage.removeItem('disco_token');
    setIsAuthenticated(false);
    setUser(null);
    navigate('/login'); // Redirect to login page is appropriate here
  };

  // Provide state and functions to children
  return (
    <UserContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </UserContext.Provider>
  );
};

// Export the custom hook for consuming the context
//    vvvvvvv ENSURE 'export' IS PRESENT vvvvvvv
export const useUserContext = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    // This error check is very helpful during development
    throw new Error('useUserContext must be used within a UserProvider');
  }
  return context;
};
