// src/components/ProtectedRoute.jsx

import React from 'react'; // Removed unused useContext import
import { Navigate, useLocation } from 'react-router-dom';
import { useUserContext } from '../context/UserContext'; // Import the custom hook

const ProtectedRoute = ({ children }) => {
  // Use the custom hook to get the authentication status from the context
  const { isAuthenticated } = useUserContext();
  let location = useLocation(); // Get current location for redirect state

  console.log("ProtectedRoute: isAuthenticated =", isAuthenticated, " | Path:", location.pathname); // Add log for debugging

  if (!isAuthenticated) {
    // User not authenticated, redirect them to the /login page.
    // state={{ from: location }} allows the Login page to redirect back
    // to the originally intended page after successful login.
    console.log("ProtectedRoute: Redirecting to /login from", location.pathname);
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // User is authenticated, render the child components (the actual page)
  return children;
};

export default ProtectedRoute;
