Guidelines for Commenting Python Code for LLMs

To enhance understanding and facilitate modifications by language models (LLMs) like ChatGPT, please follow these commenting guidelines:

1. Describe Functions and Classes

	•	Purpose: Provide a high-level overview of each function and class.
	•	How: Add a brief comment above each definition explaining its role and main tasks.
	•	Example:

# Represents a user with name and email attributes
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

2. Explain Complex Logic

	•	Purpose: Clarify non-trivial or unconventional code sections.
	•	How: Comment on the reasoning behind specific implementations, focusing on “why” rather than “what”.
	•	Example:

# Using insertion sort for better performance on small datasets
def sort_small_dataset(data):
    ...

3. State Assumptions and Dependencies

	•	Purpose: Inform about underlying assumptions and external dependencies.
	•	How: Include comments about input expectations and required libraries at the start of the file or relevant sections.
	•	Example:

# Assumption: Input data is a list of integers
# Dependency: Requires numpy for numerical operations
import numpy as np

4. Document Specific Requirements and Constraints

	•	Purpose: Outline business or technical requirements affecting the code.
	•	How: Describe any specific conditions or formats the code must adhere to.
	•	Example:

# Must return time in UTC format as per project requirements
def get_current_time_utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)

5. Highlight Areas Requiring Attention

	•	Purpose: Mark sections that need modification or further development.
	•	How: Use tags like # TODO, # FIXME with clear descriptions.
	•	Example:

def process_data(data):
    # TODO: Optimize processing algorithm for large datasets
    pass

6. Provide Modification Instructions

	•	Purpose: Specify precise changes needed in the code.
	•	How: Offer clear, actionable instructions near the relevant code.
	•	Example:

def calculate_discount(price, discount):
    # Update discount logic to cap at 50%
    return price - (price * discount)

7. Avoid Redundant Comments

	•	Description: Do not comment on obvious code actions that are self-explanatory.
	•	Example of Unnecessary Comment:

# Increment x by 1
x += 1

8. Best Practices

	•	Clarity and Brevity: Keep comments concise and to the point.
	•	Consistent Style: Use a uniform format for all comments.
	•	Value Addition: Ensure comments add meaningful context or explanation.

9. When to Comment vs. When to Skip

	•	Comment When:
	•	Explaining intent or purpose behind code sections.
	•	Clarifying complex or non-obvious logic.
	•	Providing context related to business or technical requirements.
	•	Highlighting special assumptions or dependencies.
	•	Skip Commenting When:
	•	The code is straightforward and self-explanatory.
	•	Comments merely repeat what the code does without adding value.
	•	Overloading the code with excessive comments that obscure readability.

10. Examples of Well and Poorly Commented Code

Well-Commented:

# Manages user registration process
class RegistrationManager:
    def register_user(self, user_data):
        # Validates user data before registration
        if self.validate(user_data):
            self.save(user_data)

Poorly Commented:

class RegistrationManager:
    def register_user(self, user_data):
        # Checks if data is valid
        if self.validate(user_data):
            # Saves data
            self.save(user_data)

Summary

Effective commenting for LLMs involves providing clear, purposeful annotations that explain the why and context behind the code, especially for complex or non-obvious sections. Avoid redundant comments that merely state what the code does. By following these guidelines, your Python code will be more accessible and easier to work with for both humans and language models.