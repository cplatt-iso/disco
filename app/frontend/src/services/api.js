// app/frontend/src/services/api.js

// Adjust this if your API isn't proxied to '/api' by Vite's dev server
// Or use the full backend URL like 'http://localhost:8000' during development
// and handle production URLs appropriately (e.g., via environment variables)
const API_BASE_URL = '/api';

/**
 * Fetches a single ruleset by its ID.
 * @param {string} id - The ID of the ruleset to fetch.
 * @returns {Promise<object>} - A promise resolving to the ruleset data.
 */
export const getRuleSet = async (id) => {
  if (!id) {
    return Promise.reject(new Error("RuleSet ID is required for fetching."));
  }
  console.log(`API: Fetching ruleset ${id}`);
  try {
    const response = await fetch(`${API_BASE_URL}/rulesets/${id}`);
    if (!response.ok) {
      // Try to get error details from backend if available
      let errorDetails = `HTTP error! status: ${response.status}`;
      try {
          const errorData = await response.json();
          errorDetails += `, ${JSON.stringify(errorData.detail || errorData)}`;
      } catch (e) { /* Ignore if response body isn't JSON */ }
      throw new Error(errorDetails);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Failed to fetch rule set:", error);
    throw error; // Re-throw to be caught by the calling component
  }
};

/**
 * Saves a ruleset (creates if no id, updates if id is provided).
 * @param {string | null | undefined} id - The ID of the ruleset to update, or null/undefined to create.
 * @param {object} ruleSetData - The ruleset data (name, rules array).
 * @returns {Promise<object>} - A promise resolving to the saved/created ruleset data.
 */
export const saveRuleSet = async (id, ruleSetData) => {
  const url = id ? `${API_BASE_URL}/rulesets/${id}` : `${API_BASE_URL}/rulesets`;
  const method = id ? 'PUT' : 'POST';
  console.log(`API: Saving ruleset ${id ? id : '(new)'} using ${method} at ${url}`);

  try {
    const response = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(ruleSetData),
    });
    if (!response.ok) {
      let errorDetails = `HTTP error! status: ${response.status}`;
       try {
          const errorData = await response.json();
          errorDetails += `, ${JSON.stringify(errorData.detail || errorData)}`;
      } catch (e) { /* Ignore if response body isn't JSON */ }
      throw new Error(errorDetails);
    }
    const data = await response.json();
    return data; // Return the saved/created ruleset (often includes the ID)
  } catch (error) {
    console.error("Failed to save rule set:", error);
    throw error; // Re-throw
  }
};

/**
* Fetches a list of all rulesets.
* @returns {Promise<Array<object>>} - A promise resolving to an array of ruleset objects (e.g., [{id: string, name: string}]).
*/
export const getRuleSetsList = async () => {
    console.log(`API: Fetching ruleset list`);
    try {
        const response = await fetch(`${API_BASE_URL}/rulesets`);
        if (!response.ok) {
             let errorDetails = `HTTP error! status: ${response.status}`;
             try {
                 const errorData = await response.json();
                 errorDetails += `, ${JSON.stringify(errorData.detail || errorData)}`;
             } catch (e) { /* Ignore if response body isn't JSON */ }
             throw new Error(errorDetails);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Failed to fetch rule sets list:", error);
        throw error; // Re-throw
    }
};


// --- Add other API functions as needed ---
// export const deleteRuleSet = async (id) => { ... };
// export const getCStoreConfigs = async () => { ... };
// export const saveCStoreConfig = async (config) => { ... };
// etc.
