// src/App.jsx

import React from 'react'; // useContext might not be needed directly here anymore
// Import BrowserRouter as Router at the top level
import { BrowserRouter as Router, Route, Routes, Navigate, NavLink } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import RulesEditor from './pages/RulesEditor';
import RuleSetList from './pages/RuleSetList';
import ProtectedRoute from './components/ProtectedRoute';
// Correctly import only the exported members needed from UserContext
import { UserProvider, useUserContext } from './context/UserContext';

// Helper component to render the main layout and routes.
// It can now reliably use hooks that depend on Router and UserContext
// because it will always be rendered inside both providers.
function AppContent() {
  // Use the exported custom hook to get context values
  const { isAuthenticated, logout } = useUserContext();

  // Define NavLink active/inactive styling using a function
  const getNavLinkClass = ({ isActive }) =>
    `block px-4 py-2 mt-2 text-sm font-semibold rounded-lg transition duration-150 ease-in-out ${
      isActive
        ? 'bg-blue-500 text-white shadow-inner' // Example active styles
        : 'text-gray-600 hover:bg-gray-200 hover:text-gray-700' // Example inactive styles
    }`;

  return (
    // The main layout structure (Sidebar + Main Content)
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar: Render only if authenticated */}
      {isAuthenticated && (
        <aside className="w-64 bg-white shadow-md p-4 flex flex-col">
          <div className="text-xl font-bold text-gray-700 mb-6">DISCO</div>
          <nav className="flex-grow">
            {/* Use NavLink directly for navigation and active styling */}
            <NavLink to="/dashboard" className={getNavLinkClass}>
              Dashboard
            </NavLink>
            <NavLink to="/rulesets" className={getNavLinkClass}>
              Rule Sets
            </NavLink>
            <NavLink to="/settings" className={getNavLinkClass}>
              Settings
            </NavLink>
          </nav>
          {/* Logout Button at the bottom */}
           <button
              onClick={logout} // Assumes logout function is provided by useUserContext
              className="w-full px-4 py-2 mt-4 text-sm font-semibold text-white bg-red-500 rounded-lg hover:bg-red-600 transition duration-150 ease-in-out"
           >
              Logout
          </button>
        </aside>
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* This div now simply holds the Routes component */}
        <div className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-200">
          {/* The Routes component defines the different pages */}
          <Routes>
            {/* Public Route */}
            <Route path="/login" element={<Login />} />

            {/* Protected Routes */}
            {/* Redirect root path based on authentication */}
             <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />} />

            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/settings/*" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

            {/* --- Rule Set Routes --- */}
            <Route path="/rulesets" element={<ProtectedRoute><RuleSetList /></ProtectedRoute>} />
            <Route path="/rulesets/edit/:id" element={<ProtectedRoute><RulesEditor /></ProtectedRoute>} />
            <Route path="/rulesets/new" element={<ProtectedRoute><RulesEditor /></ProtectedRoute>} />

            {/* Catch-all: Redirect unknown paths */}
            <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

// Main App component sets up the Providers in the correct order
function App() {
  return (
    <Router> {/* <--- Router is now the outermost component */}
      <UserProvider> {/* <--- UserProvider is inside Router */}
        <AppContent /> {/* <--- Renders the layout and Routes, consuming context */}
      </UserProvider>
    </Router>
  );
}

export default App;
