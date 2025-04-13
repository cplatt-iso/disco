// src/pages/RuleSetList.jsx

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; // Import Link for navigation
import { getRuleSetsList } from '../services/api'; // Assuming you create/have this function in api.js

function RuleSetList() {
  const [ruleSets, setRuleSets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    console.log("RuleSetList: Fetching rulesets...");
    getRuleSetsList()
      .then(data => {
        console.log("RuleSetList: Fetched data:", data);
        // Ensure data is an array before setting state
        setRuleSets(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(err => {
        console.error("RuleSetList: Error fetching rulesets:", err);
        setError(`Failed to load rulesets: ${err.message || 'Unknown error'}`);
        setRuleSets([]); // Clear rulesets on error
        setLoading(false);
      });
  }, []); // Empty dependency array means this runs once on mount

  // --- Render Logic ---

  if (loading) {
      return <div className="text-center p-4">Loading rulesets...</div>;
  }

  if (error) {
      return <div className="text-red-600 bg-red-100 p-4 rounded border border-red-300">{error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-700">Rule Sets</h1>
        {/* Button/Link to create a new ruleset */}
        <Link
          to="/rulesets/new"
          className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
        >
          + Create New Rule Set
        </Link>
      </div>

      {/* List of Rulesets */}
      {ruleSets.length === 0 ? (
        <p className="text-gray-600 italic">No rule sets found. Create one!</p>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {ruleSets.map((ruleSet, index) => (
              <li
                key={ruleSet.id || index} // Use ID as key, fallback to index if ID missing
                className={`flex justify-between items-center p-4 ${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'} border-b border-gray-200 last:border-b-0 hover:bg-gray-100`}
              >
                <span className="text-gray-800 font-medium">
                  {ruleSet.name || `Unnamed Rule Set (ID: ${ruleSet.id})`}
                </span>
                {/* Link to edit the specific ruleset */}
                <Link
                  to={`/rulesets/edit/${ruleSet.id}`}
                  className="text-blue-600 hover:text-blue-800 font-semibold text-sm py-1 px-3 rounded border border-blue-300 hover:border-blue-500 transition duration-150 ease-in-out"
                >
                  Edit
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default RuleSetList;
