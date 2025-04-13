// app/frontend/src/services/api.js

// Adjust this if your API isn't proxied to '/api' by Vite's dev server
// Or use the full backend URL like 'http://localhost:8000' during development
// and handle production URLs appropriately (e.g., via environment variables)
const API_BASE_URL = '/api'; // Assuming Vite proxies /api to your backend

/**
 * Helper function to handle potential errors from fetch responses.
 * Tries to parse JSON error detail, otherwise uses status text.
 * @param {Response} response - The fetch response object.
 * @returns {Promise<Error>} - A promise that rejects with an Error object.
 */
const handleApiError = async (response) => {
    let errorDetails = `HTTP error! status: ${response.status} (${response.statusText})`;
    try {
        // Try to get more specific error message from backend response body
        const errorData = await response.json();
        errorDetails += `: ${JSON.stringify(errorData.detail || errorData)}`;
    } catch (e) {
        // Ignore if response body isn't JSON or parsing fails
        console.debug("Response body wasn't valid JSON or empty.");
    }
    return new Error(errorDetails);
};


/**
 * Fetches a single ruleset by its ID.
 * @param {string} id - The ID of the ruleset to fetch.
 * @returns {Promise<object>} - A promise resolving to the ruleset data object.
 */
export const getRuleSet = async (id) => {
  if (!id) {
    // Return a rejected promise for consistency in error handling
    return Promise.reject(new Error("RuleSet ID is required for fetching."));
  }
  const url = `${API_BASE_URL}/rulesets/${id}`;
  console.log(`API: Fetching ruleset ${id} from ${url}`);

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw await handleApiError(response); // Use helper to create error
    }
    const data = await response.json();
    console.log(`API: Successfully fetched ruleset ${id}`);
    return data;
  } catch (error) {
    console.error(`API: Failed to fetch rule set ${id}:`, error);
    throw error; // Re-throw the original or constructed error
  }
};

/**
 * Saves a ruleset (creates if no id, updates if id is provided).
 * @param {string | null | undefined} id - The ID of the ruleset to update, or null/undefined to create.
 * @param {object} ruleSetData - The ruleset data (name, rules array).
 * @returns {Promise<object>} - A promise resolving to the saved/created ruleset data from the backend.
 */
export const saveRuleSet = async (id, ruleSetData) => {
  const url = id ? `${API_BASE_URL}/rulesets/${id}` : `${API_BASE_URL}/rulesets`;
  const method = id ? 'PUT' : 'POST';
  console.log(`API: Saving ruleset ${id ? `(ID: ${id})` : '(new)'} using ${method} at ${url}`);

  try {
    const response = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        // Add authentication headers if needed, e.g., Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(ruleSetData),
    });

    if (!response.ok) {
       throw await handleApiError(response); // Use helper
    }

    const data = await response.json();
    console.log(`API: Successfully ${id ? 'updated' : 'created'} ruleset. Response:`, data);
    return data; // Return the saved/created ruleset (often includes the final ID)
  } catch (error) {
    console.error(`API: Failed to save rule set ${id ? `(ID: ${id})` : '(new)'}:`, error);
    throw error; // Re-throw
  }
};

/**
 * Fetches a list of all available rulesets.
 * Assumes the backend endpoint is GET /api/rulesets
 * @returns {Promise<Array<object>>} - A promise resolving to an array of ruleset objects
 *                                      (e.g., [{id: string, name: string}]).
 */
export const getRuleSetsList = async () => {
    const url = `${API_BASE_URL}/rulesets`;
    console.log(`API: Fetching ruleset list from ${url}`);
    try {
        const response = await fetch(url, {
             headers: {
                // Add authentication headers if needed
             }
        });
        if (!response.ok) {
             throw await handleApiError(response); // Use helper
        }
        const data = await response.json();
        console.log(`API: Successfully fetched ruleset list (${Array.isArray(data) ? data.length : 0} items).`);
        // Ensure we return an array, even if the API unexpectedly returns something else
        return Array.isArray(data) ? data : [];
    } catch (error) {
        console.error("API: Failed to fetch rule sets list:", error);
        throw error; // Re-throw
    }
};


// --- Add other API functions as needed ---

// Example: Delete a ruleset
// export const deleteRuleSet = async (id) => {
//   if (!id) return Promise.reject(new Error("RuleSet ID required for deletion."));
//   const url = `${API_BASE_URL}/rulesets/${id}`;
//   console.log(`API: Deleting ruleset ${id} at ${url}`);
//   try {
//       const response = await fetch(url, {
//           method: 'DELETE',
//           headers: { /* Auth headers */ }
//       });
//       if (!response.ok) {
//           throw await handleApiError(response);
//       }
//       console.log(`API: Successfully deleted ruleset ${id}`);
//       // DELETE often returns 204 No Content or the deleted object/ID
//       // Return a success indicator or specific data if needed
//       return { success: true, id: id };
//   } catch (error) {
//       console.error(`API: Failed to delete ruleset ${id}:`, error);
//       throw error;
//   }
// };

// Example: Placeholder for C-Store Config fetch (adjust endpoint as needed)
// export const getCStoreConfigs = async () => {
//   const url = `${API_BASE_URL}/cstore/configs`; // Example endpoint
//   console.log(`API: Fetching C-Store configs from ${url}`);
//   try {
//     const response = await fetch(url);
//     if (!response.ok) throw await handleApiError(response);
//     const data = await response.json();
//     return Array.isArray(data) ? data : [];
//   } catch (error) {
//     console.error("API: Failed to fetch C-Store configs:", error);
//     throw error;
//   }
// };
