import pydicom
import json
# Import keyword_dict and the specific lookup functions
from pydicom.datadict import (
    keyword_dict,
    dictionary_VR,
    dictionary_VM,
    dictionary_description
)

output_data = []

# Iterate through the keyword dictionary to get keyword -> tag_integer mapping
for keyword, tag_int in keyword_dict.items():
    try:
        # Create a Tag object from the integer value
        tag_obj = pydicom.tag.Tag(tag_int)

        # Filter out group length tags and private tags *before* lookups
        if tag_obj.element == 0x0000 or tag_obj.is_private:
            continue # Skip this tag

        # Look up VR, VM, and Name (description) using the Tag object
        # Add error handling for lookups in case a tag from keyword_dict
        # somehow doesn't have standard entries (should be rare).
        try:
            vr = dictionary_VR(tag_obj)
            vm = dictionary_VM(tag_obj)
            name = dictionary_description(tag_obj)
        except KeyError:
            # print(f"Warning: Could not find VR/VM/Name for tag {tag_obj} (Keyword: {keyword})")
            continue # Skip if lookup fails

        # Append data if all lookups were successful
        output_data.append({
            "tag": str(tag_obj),      # Format as "(gggg, eeee)"
            "keyword": keyword,
            "name": name,
            "vr": vr,
            "vm": vm
        })

    except Exception as e:
        # Catch any other unexpected errors during processing a specific keyword/tag
        print(f"Error processing keyword '{keyword}' with tag value {hex(tag_int)}: {e}")
        # Continue processing other keywords

# Sort alphabetically by name for potentially better lookup presentation
output_data.sort(key=lambda x: x['name'])

# Save to a JSON file
output_filename = 'dicom_dictionary.json'
with open(output_filename, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"DICOM dictionary saved to {output_filename}. Total entries: {len(output_data)}")
