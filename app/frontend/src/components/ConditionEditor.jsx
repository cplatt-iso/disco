// app/frontend/src/components/ConditionEditor.jsx
import React from 'react';
import Select from 'react-select';

const operatorOptions = [ /* ... keep options as before ... */ ];
const filterDicomOption = (option, inputValue) => { /* ... keep filter as before ... */ };

function ConditionEditor({
  condition,
  ruleIndex,
  conditionIndex,
  dicomOptions,
  onConditionChange,
  onRemoveCondition,
}) {
  const selectedAttributeOption = dicomOptions.find(opt => opt.value === condition.attribute) || null;
  const selectedOperatorOption = operatorOptions.find(opt => opt.value === condition.operator) || null;
  const isValueDisabled = condition.operator === 'exists' || condition.operator === 'not_exists';

  // Use classNames for potential external styling, remove opinionated flex styles here
  return (
    <div className="condition-editor-row" style={{ marginBottom: '10px' }}> {/* Basic spacing */}
        {/* Wrap elements for potential grid/flex layout defined in CSS if needed */}
        <div className="condition-attribute" style={{ display: 'inline-block', marginRight: '10px', minWidth: '250px', verticalAlign: 'bottom' }}> {/* Use inline-block or CSS */}
            {/* <label htmlFor={`attribute-${ruleIndex}-${conditionIndex}`} style={{ display: 'block', marginBottom: '4px', fontSize: '0.9em' }}>Attribute</label> */} {/* Optionally remove label */}
            <Select
                inputId={`attribute-${ruleIndex}-${conditionIndex}`}
                options={dicomOptions}
                value={selectedAttributeOption}
                onChange={(selectedOption) => onConditionChange(ruleIndex, conditionIndex, 'attribute', selectedOption ? selectedOption.value : '')}
                placeholder="Attribute..." // Shorter placeholder?
                isClearable
                filterOption={filterDicomOption}
                getOptionLabel={(option) => option.label}
                getOptionValue={(option) => option.value}
                // classNamePrefix allows targeting with CSS: .condition-select__control, .condition-select__menu etc.
                classNamePrefix="condition-select"
                 styles={{ menu: base => ({ ...base, zIndex: 5 }) }}
            />
        </div>

        <div className="condition-operator" style={{ display: 'inline-block', marginRight: '10px', minWidth: '130px', verticalAlign: 'bottom' }}>
             {/* <label htmlFor={`operator-${ruleIndex}-${conditionIndex}`} style={{ display: 'block', marginBottom: '4px', fontSize: '0.9em' }}>Operator</label> */} {/* Optionally remove label */}
            <select
                id={`operator-${ruleIndex}-${conditionIndex}`}
                value={condition.operator || ''}
                onChange={(e) => onConditionChange(ruleIndex, conditionIndex, 'operator', e.target.value)}
                // Use classes or basic styles to match height/appearance
                style={{ width: '100%', padding: '8px', height: '38px' }} // Basic styling
                className="condition-operator-select" // Add class for CSS
            >
                <option value="" disabled>Operator...</option>
                {operatorOptions.map(op => <option key={op.value} value={op.value}>{op.label}</option>)}
            </select>
        </div>

        <div className="condition-value" style={{ display: 'inline-block', marginRight: '10px', minWidth: '150px', verticalAlign: 'bottom' }}>
             {/* <label htmlFor={`value-${ruleIndex}-${conditionIndex}`} style={{ display: 'block', marginBottom: '4px', fontSize: '0.9em' }}>Value</label> */} {/* Optionally remove label */}
            <input
                id={`value-${ruleIndex}-${conditionIndex}`}
                type="text"
                value={isValueDisabled ? '' : condition.value || ''}
                disabled={isValueDisabled}
                onChange={(e) => onConditionChange(ruleIndex, conditionIndex, 'value', e.target.value)}
                placeholder={isValueDisabled ? 'N/A' : 'Value...'}
                // Use classes or basic styles
                style={{ width: '100%', padding: '8px', height: '38px', boxSizing: 'border-box' }} // Basic styling
                className="condition-value-input" // Add class for CSS
            />
        </div>

        <div className="condition-remove" style={{ display: 'inline-block', verticalAlign: 'bottom' }}>
            <button
                type="button"
                onClick={() => onRemoveCondition(ruleIndex, conditionIndex)}
                title="Remove Condition"
                // Use classes or basic style
                style={{ height: '38px', padding: '0 15px', cursor: 'pointer', marginLeft: '5px' }}
                className="condition-remove-button" // Add class for CSS
            >
                ×
            </button>
        </div>
    </div>
  );
}

export default ConditionEditor;
