// src/pages/RulesEditor.jsx

import React, { useState, useMemo, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Select from 'react-select'; // Import react-select
import ConditionEditor from '../components/ConditionEditor'; // Import the ConditionEditor component
import dicomDictionaryData from '../data/dicom_dictionary.json'; // Import the dictionary data
import { getRuleSet, saveRuleSet } from '../services/api'; // Import API functions

// Helper function to format DICOM dictionary entries for react-select
const formatDicomOption = (entry) => ({
    value: entry.tag, // The actual DICOM tag string like "(0010,0020)"
    label: `${entry.name} (${entry.tag})`, // What the user sees in the dropdown
    // Include original data in 'data' property for custom filtering
    data: {
        keyword: entry.keyword,
        name: entry.name,
    }
});

// Custom filter function for react-select (used in Actions)
const filterDicomOption = (option, inputValue) => {
  const lowerInput = inputValue.toLowerCase();
  // option.data contains the original data we passed in (name, keyword)
  // option.value is the tag string "(gggg, eeee)"
  // option.label is the display string "Name (gggg, eeee)"
  if (!inputValue) return true; // Show all if input is empty
  return (
    option.label.toLowerCase().includes(lowerInput) ||
    option.data.keyword.toLowerCase().includes(lowerInput) ||
    option.data.name.toLowerCase().includes(lowerInput) ||
    option.value.replace(/[(),\s]/g, '').toLowerCase().includes(lowerInput.replace(/[(),\s]/g, '')) // Compare tag format loosely
  );
};


// --- Define Action Options ---
const actionOptions = [
    { value: 'set_value', label: 'Set Value' },
    { value: 'remove_tag', label: 'Remove Tag' },
    { value: 'copy_from', label: 'Copy From Other Tag'},
    // Add other actions your backend supports
];

function RulesEditor() {
    const { id } = useParams(); // Get ruleset ID from URL, or undefined for new
    const navigate = useNavigate();
    const [ruleSetName, setRuleSetName] = useState('');
    const [rules, setRules] = useState([]); // Initialize as empty array
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const isNewRuleSet = !id;

    // Memoize the formatted DICOM options list to avoid re-calculating on every render
    const dicomOptions = useMemo(() => dicomDictionaryData.map(formatDicomOption), []);

    // --- Fetch existing ruleset data ---
    useEffect(() => {
        console.log("RulesEditor useEffect running. ID from URL:", id); // Log the ID
        if (id) {
            setIsLoading(true);
            setError(null);
            console.log("Attempting to fetch RuleSet with ID:", id); // Log before fetch
            getRuleSet(id)
                .then(data => {
                    console.log("Fetched RuleSet data:", data); // Log fetched data
                    setRuleSetName(data.name || ''); // Handle cases where name might be null/undefined

                    // Ensure rules and conditions are properly initialized and are arrays
                    const initializedRules = Array.isArray(data.rules) ? data.rules.map((rule, index) => ({
                        id: rule.id || `rule-${Date.now()}-${index}`, // Ensure key for React
                        description: rule.description || '',
                        action: rule.action || { type: '', params: {} },
                        conditions: Array.isArray(rule.conditions) ? rule.conditions.map(cond => ({
                            attribute: cond.attribute || '',
                            operator: cond.operator || '',
                            value: cond.value || ''
                        })) : [] // Default to empty array if conditions are missing/not an array
                    })) : []; // Default to empty array if rules are missing/not an array

                    console.log("Initialized rules for state:", initializedRules); // Log processed rules
                    setRules(initializedRules);
                })
                .catch(err => {
                    console.error("Error fetching rule set:", err); // Log the specific error
                    // Display a user-friendly message, include backend message if possible
                    const errorMsg = err.message || "An unknown error occurred.";
                    setError(`Failed to load rule set. ${errorMsg}`);
                    setRules([]); // Reset rules on error
                })
                .finally(() => setIsLoading(false));
        } else {
             console.log("No ID found, setting up for new RuleSet."); // Log new ruleset path
            // Sensible default for a new rule set
            setRuleSetName('New Rule Set');
            setRules([{
                id: `rule-${Date.now()}-0`, // Temporary ID for React key
                description: 'New Rule 1',
                action: { type: '', params: {} },
                conditions: []
            }]);
            setIsLoading(false); // Ensure loading is false for new ruleset
            setError(null); // Ensure no error is shown for new ruleset
        }
    }, [id]); // Re-run only if the ID from the URL changes


    // --- Handler Functions ---

    const handleRuleChange = (ruleIndex, field, value) => {
        const updatedRules = [...rules];
        // Ensure the rule exists at the index
        if (updatedRules[ruleIndex]) {
            updatedRules[ruleIndex] = { ...updatedRules[ruleIndex], [field]: value };
            setRules(updatedRules);
        }
    };

    const handleActionChange = (ruleIndex, actionType, actionParams = {}) => { // Default params to {}
        const updatedRules = [...rules];
        if (updatedRules[ruleIndex]) {
            updatedRules[ruleIndex].action = { type: actionType, params: actionParams };
            setRules(updatedRules);
        }
    };

    const handleActionParamChange = (ruleIndex, paramName, paramValue) => {
        const updatedRules = [...rules];
        // Ensure the rule and action structure exists
        if (updatedRules[ruleIndex] && updatedRules[ruleIndex].action) {
             // Ensure params object exists before spreading
            const currentParams = updatedRules[ruleIndex].action.params || {};
            updatedRules[ruleIndex].action.params = {
                ...currentParams,
                [paramName]: paramValue
            };
            setRules(updatedRules);
        }
    };

    const handleConditionChange = (ruleIndex, conditionIndex, field, value) => {
        const updatedRules = [...rules];
         // Ensure rule and conditions array exist
        if (updatedRules[ruleIndex] && Array.isArray(updatedRules[ruleIndex].conditions)) {
            const updatedConditions = [...updatedRules[ruleIndex].conditions];
            // Ensure condition exists at the index
            if (updatedConditions[conditionIndex]) {
                updatedConditions[conditionIndex] = {
                    ...updatedConditions[conditionIndex],
                    [field]: value,
                };

                // If operator changes to 'exists' or 'not_exists', clear the value
                if (field === 'operator' && (value === 'exists' || value === 'not_exists')) {
                    updatedConditions[conditionIndex].value = '';
                }

                updatedRules[ruleIndex].conditions = updatedConditions;
                setRules(updatedRules);
            }
        }
    };

    const addCondition = (ruleIndex) => {
        const updatedRules = [...rules];
        if (updatedRules[ruleIndex]) {
             // Ensure conditions array exists before pushing
            const currentConditions = Array.isArray(updatedRules[ruleIndex].conditions) ? updatedRules[ruleIndex].conditions : [];
            updatedRules[ruleIndex].conditions = [
                ...currentConditions,
                { attribute: '', operator: '', value: '' } // Add new blank condition
            ];
            setRules(updatedRules);
        }
    };

    const removeCondition = (ruleIndex, conditionIndex) => {
        const updatedRules = [...rules];
         // Ensure rule and conditions array exist
        if (updatedRules[ruleIndex] && Array.isArray(updatedRules[ruleIndex].conditions)) {
            // Filter out the condition at the specified index
            updatedRules[ruleIndex].conditions = updatedRules[ruleIndex].conditions.filter(
                (_, index) => index !== conditionIndex
            );
            setRules(updatedRules);
        }
    };

    const addRule = () => {
         // Ensure rules is an array before adding
        const currentRules = Array.isArray(rules) ? rules : [];
        setRules([
            ...currentRules,
            {
                id: `rule-${Date.now()}-${currentRules.length}`, // Temporary ID for key
                description: `New Rule ${currentRules.length + 1}`,
                action: { type: '', params: {} },
                conditions: []
            }
        ]);
    };

    const removeRule = (ruleIndexToRemove) => {
        // Ensure rules is an array before filtering
         const currentRules = Array.isArray(rules) ? rules : [];
        const updatedRules = currentRules.filter((_, index) => index !== ruleIndexToRemove);
        setRules(updatedRules);
    };

    const handleSave = () => {
        setIsLoading(true);
        setError(null);
        // Ensure rules is an array before mapping
         const currentRules = Array.isArray(rules) ? rules : [];
        const ruleSetData = {
            name: ruleSetName,
            // Clean up temporary IDs if needed before saving, or ensure backend handles it
             rules: currentRules.map(({ id: tempId, ...rest }) => {
                // Optionally only include 'id' if it's not one of our temp ones
                // This depends on whether your backend PUT expects/handles the ID in the body
                if (typeof tempId === 'string' && tempId.startsWith('rule-')) {
                    return rest; // Don't send temp ID for updates? Or maybe backend needs it? Adjust as needed.
                }
                return { id: tempId, ...rest }; // Send original ID if it exists
             }),
        };

        console.log("Saving RuleSet Data:", JSON.stringify(ruleSetData, null, 2)); // Log data being sent

        saveRuleSet(id, ruleSetData) // Pass id (can be undefined for new)
            .then(savedRuleSet => {
                console.log('Saved RuleSet:', savedRuleSet);
                setIsLoading(false);
                // If it was a new ruleset, navigate to the edit page with the new ID returned from backend
                if (!id && savedRuleSet.id) {
                    navigate(`/rulesets/edit/${savedRuleSet.id}`, { replace: true });
                     // Optionally refetch or update state based on savedRuleSet?
                     // For now, navigation handles showing the saved state.
                } else if (id && savedRuleSet) {
                     // Existing ruleset saved, maybe show a success message
                     // Or update state if backend returns slightly different data
                     console.log("Existing ruleset updated successfully.");
                     // Optionally re-initialize state from savedRuleSet if needed
                      // setRuleSetName(savedRuleSet.name);
                      // setRules(initializedRulesFromData(savedRuleSet.rules));
                }
            })
            .catch(err => {
                console.error("Error saving rule set:", err);
                 const errorMsg = err.message || "An unknown error occurred during save.";
                setError(`Failed to save rule set. ${errorMsg}`);
                setIsLoading(false);
            });
    };

    // --- Render Logic ---

    // Display error prominently if it occurs
     if (error) {
        return <div style={{ color: 'red', padding: '20px', border: '1px solid red', margin: '20px' }}>Error: {error}</div>;
     }

    // Show loading indicator
    if (isLoading) {
        return <div style={{ padding: '20px' }}>Loading rule set...</div>;
    }

    // Ensure rules is renderable (should be an array after useEffect/error handling)
     if (!Array.isArray(rules)) {
        console.error("State Error: rules is not an array before final render:", rules);
        return <div style={{ color: 'red', padding: '20px' }}>Internal Error: Rule data is invalid. Please try refreshing.</div>;
     }


    return (
        // Use classNames for styling based on your project's CSS setup (e.g., Tailwind, App.css)
        <div className="rules-editor-container" style={{ padding: '20px' }}>
            <h1 className="rules-editor-title">{isNewRuleSet ? 'Create New Rule Set' : `Edit Rule Set: ${ruleSetName || ''}`}</h1>

            {/* Ruleset Name Input */}
            <div className="ruleset-name-section" style={{ marginBottom: '20px' }}>
                <label htmlFor="ruleset-name" style={{ marginRight: '10px', fontWeight: 'bold' }}>Rule Set Name:</label>
                <input
                   type="text"
                   id="ruleset-name"
                   value={ruleSetName}
                   onChange={(e) => setRuleSetName(e.target.value)}
                   className="ruleset-name-input" // Add class for styling
                   style={{ width: '300px', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }} // Basic style
                />
            </div>

            {/* Rules List */}
            {rules.map((rule, ruleIndex) => (
                // Use a consistent and unique key
                <div key={rule.id || `rule-${ruleIndex}`} className="rule-card" style={{ border: '1px solid #ccc', padding: '15px', marginBottom: '20px', borderRadius: '5px', background: '#fff' }}>
                    {/* Rule Header: Description and Remove Button */}
                     <div className="rule-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                        <input
                            type="text"
                            value={rule.description}
                            onChange={(e) => handleRuleChange(ruleIndex, 'description', e.target.value)}
                            placeholder="Rule Description"
                            className="rule-description-input" // Add class
                            style={{ flexGrow: 1, marginRight: '10px', padding: '8px', border: 'none', fontSize: '1.1em', fontWeight: 'bold' }} // Basic style
                        />
                        <button type="button" onClick={() => removeRule(ruleIndex)} title="Remove Rule" className="remove-rule-button" style={{ color: '#dc3545', background: 'none', border: '1px solid #dc3545', borderRadius: '4px', cursor: 'pointer', fontSize: '0.9em', padding: '5px 10px' }}>
                          Remove Rule
                        </button>
                    </div>

                    {/* Action Editor Section */}
                     <div className="action-editor-section" style={{ marginBottom: '20px', padding: '15px', background: '#f9f9f9', borderRadius: '4px' }}>
                        <h4 style={{ marginTop: '0', marginBottom: '10px' }}>Action</h4>
                         <div className="action-controls" style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                             <select
                                value={rule.action?.type || ''} // Safer access
                                onChange={(e) => handleActionChange(ruleIndex, e.target.value, {})} // Reset params on type change
                                className="action-type-select" // Add class
                                style={{ padding: '8px', height: '38px', border: '1px solid #ccc', borderRadius: '4px', minWidth: '150px' }} // Basic style
                             >
                                <option value="">Select Action...</option>
                                {actionOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                             </select>

                             {/* --- Conditional Action Params --- */}
                             {/* Set Value Action */}
                             {rule.action?.type === 'set_value' && (
                                <>
                                <Select
                                    options={dicomOptions}
                                    value={dicomOptions.find(opt => opt.value === rule.action.params?.tagToSet) || null}
                                    onChange={(opt) => handleActionParamChange(ruleIndex, 'tagToSet', opt ? opt.value : '')}
                                    placeholder="Target Tag..."
                                    filterOption={filterDicomOption}
                                    classNamePrefix="action-select" // Use class prefix
                                    styles={{ container: base => ({ ...base, flexGrow: 1, minWidth: '200px' }), menu: base => ({ ...base, zIndex: 4 }) }} // Basic layout styles + zIndex
                                    isClearable
                                />
                                <input
                                    type="text"
                                    value={rule.action.params?.valueToSet || ''}
                                    onChange={(e) => handleActionParamChange(ruleIndex, 'valueToSet', e.target.value)}
                                    placeholder="Value to set"
                                    className="action-value-input" // Add class
                                    style={{ padding: '8px', height: '38px', flexGrow: 1, border: '1px solid #ccc', borderRadius: '4px' }} // Basic style
                                />
                                </>
                             )}
                              {/* Remove Tag Action */}
                              {rule.action?.type === 'remove_tag' && (
                                <Select
                                    options={dicomOptions}
                                    value={dicomOptions.find(opt => opt.value === rule.action.params?.tagToRemove) || null}
                                    onChange={(opt) => handleActionParamChange(ruleIndex, 'tagToRemove', opt ? opt.value : '')}
                                    placeholder="Tag to remove..."
                                    filterOption={filterDicomOption} // Use filter
                                    classNamePrefix="action-select"   // Use same class prefix
                                    styles={{ container: base => ({ ...base, flexGrow: 1, minWidth: '200px' }), menu: base => ({ ...base, zIndex: 4 }) }} // Basic layout styles + zIndex
                                    isClearable
                                />
                             )}
                            {/* Copy From Action */}
                            {rule.action?.type === 'copy_from' && (
                                <>
                                <Select
                                    options={dicomOptions}
                                    value={dicomOptions.find(opt => opt.value === rule.action.params?.sourceTag) || null}
                                    onChange={(opt) => handleActionParamChange(ruleIndex, 'sourceTag', opt ? opt.value : '')}
                                    placeholder="Source Tag..."
                                    filterOption={filterDicomOption} // Use filter
                                    classNamePrefix="action-select"   // Use same class prefix
                                    styles={{ container: base => ({ ...base, flexGrow: 1, minWidth: '200px' }), menu: base => ({ ...base, zIndex: 4 }) }} // Basic layout styles + zIndex
                                    isClearable
                                />
                                 <Select
                                    options={dicomOptions}
                                    value={dicomOptions.find(opt => opt.value === rule.action.params?.destinationTag) || null}
                                    onChange={(opt) => handleActionParamChange(ruleIndex, 'destinationTag', opt ? opt.value : '')}
                                    placeholder="Destination Tag..."
                                    filterOption={filterDicomOption} // Use filter
                                    classNamePrefix="action-select"    // Use same class prefix
                                    styles={{ container: base => ({ ...base, flexGrow: 1, minWidth: '200px' }), menu: base => ({ ...base, zIndex: 4 }) }} // Basic layout styles + zIndex
                                    isClearable
                                />
                                </>
                            )}
                             {/* Add inputs for other action types here if needed */}
                         </div>
                    </div>


                    {/* Conditions Editor Section */}
                    <div className="conditions-editor-section" style={{ marginBottom: '15px', padding: '15px', background: '#fefefe', border: '1px solid #eee', borderRadius: '4px' }}>
                       <h4 style={{ marginTop: '0', marginBottom: '10px' }}>Conditions <span style={{fontWeight: 'normal', fontSize: '0.9em'}}>(ALL must match for Action to run)</span></h4>
                       {/* Ensure conditions is an array before mapping/checking length */}
                       {(!Array.isArray(rule.conditions) || rule.conditions.length === 0) && (
                            <p className="no-conditions-message" style={{ fontStyle: 'italic', color: '#666', margin: '10px 0' }}>No conditions defined - action will always apply.</p>
                       )}
                       {Array.isArray(rule.conditions) && rule.conditions.map((condition, conditionIndex) => (
                         <ConditionEditor
                           // Use rule ID + condition index for a potentially more stable key
                           key={condition.id || `${rule.id}-cond-${conditionIndex}`}
                           condition={condition}
                           ruleIndex={ruleIndex}
                           conditionIndex={conditionIndex}
                           dicomOptions={dicomOptions}
                           onConditionChange={handleConditionChange}
                           onRemoveCondition={removeCondition}
                         />
                       ))}
                       <button type="button" onClick={() => addCondition(ruleIndex)} className="add-condition-button" style={{ marginTop: '10px', padding: '6px 12px', fontSize: '0.9em', cursor: 'pointer' }}>
                           + Add Condition
                       </button>
                    </div>

                </div> /* End Rule Card */
            ))}

            {/* Add Rule Button */}
            <button type="button" onClick={addRule} className="add-rule-button" style={{ marginBottom: '20px', padding: '10px 15px', fontWeight: 'bold', cursor: 'pointer' }}>
                + Add New Rule
            </button>

            {/* Save/Cancel Buttons Section */}
            <div className="save-cancel-section" style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #eee' }}>
                <button type="button" onClick={handleSave} disabled={isLoading} className="save-button" style={{ padding: '10px 20px', fontWeight: 'bold', background: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '10px' }}>
                    {isLoading ? 'Saving...' : 'Save Rule Set'}
                </button>
                 <button type="button" onClick={() => navigate('/rulesets')} className="cancel-button" style={{ padding: '10px 20px', background: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                     Cancel
                 </button>
            </div>
        </div>
    );
}

export default RulesEditor;
