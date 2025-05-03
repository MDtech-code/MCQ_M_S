// const FormValidation = {
//     // Regular expressions for validation
//     regex: {
//         username: /^[a-zA-Z0-9@.+_-]{1,150}$/,
//         email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
//         phone: /^\+\d{1,3}\d{9,15}$/, // E.164 format (e.g., +12025550123)
//         date: /^\d{4}-\d{2}-\d{2}$/, // YYYY-MM-DD
//     },

//     // Validation rules for each field
//     validators: {
//         username: (value) => {
//             if (!value) return "Username is required.";
//             if (!FormValidation.regex.username.test(value)) {
//                 return "Username can only contain letters, digits, and @/./+/-/_.";
//             }
//             if (value.length > 150) return "Username must be 150 characters or less.";
//             return "";
//         },
//         email: (value) => {
//             if (!value) return "Email is required.";
//             if (!FormValidation.regex.email.test(value)) {
//                 return "Please enter a valid email address.";
//             }
//             return "";
//         },
//         new_email: (value) => {
//             if (!value) return "Email is required.";
//             if (!FormValidation.regex.email.test(value)) {
//                 return "Please enter a valid email address.";
//             }
//             return "";
//         },
//         role: (value) => {
//             const validRoles = ['ST', 'TE', 'AD'];
//             if (!value) return "Role is required.";
//             if (!validRoles.includes(value)) {
//                 return "Invalid role selected.";
//             }
//             return "";
//         },
//         password: (value) => {
//     // Ensure the password field is not empty.
//     if (!value) return "Password is required.";

//     // Check for a minimum length of 8 characters.
//     if (value.length < 8) return "Password must be at least 8 characters.";

//     // Check for at least one uppercase letter.
//     if (!/[A-Z]/.test(value)) return "Password must include at least one uppercase letter.";

//     // Check for at least one numeric digit.
//     if (!/[0-9]/.test(value)) return "Password must include at least one number.";

//     // Check for at least one special character (anything that is not a letter or digit).
//     // This regex checks for the presence of any non-alphanumeric character.
//     if (!/[^a-zA-Z0-9]/.test(value)) return "Password must include at least one special character.";

//     // All checks passed; return an empty string (indicating no error).
//     return "";
// },
//         password2: (value, password) => {
//             if (!value) return "Please confirm your password.";
//             if (value !== password) return "Passwords do not match.";
//             return "";
//         },
//         old_password: (value) => {
//         if (!value) return "Current password is required.";
//         return "";
//     },
//     confirm_password: (value) => {
//         if (!value) return "Current password is required.";
//         return "";
//     },
//         phone_number: (value) => {
//             if (!value) return ""; // Optional field
//             if (!FormValidation.regex.phone.test(value)) {
//                 return "Please enter a valid phone number in E.164 format (e.g., +12025550123).";
//             }
//             return "";
//         },
//         date_of_birth: (value) => {
//             if (!value) return ""; // Optional field
//             if (!FormValidation.regex.date.test(value)) {
//                 return "Please enter a valid date in YYYY-MM-DD format.";
//             }
//             const date = new Date(value);
//             if (isNaN(date.getTime())) return "Invalid date.";
//             return "";
//         },
//         gender: (value) => {
//             if (!value) return ""; // Optional field
//             const validGenders = ['MA', 'FE', 'UD'];
//             if (!validGenders.includes(value)) return "Invalid gender selected.";
//             return "";
//         },
//         parent_email: (value) => {
//             if (!value) return ""; // Optional field
//             if (!FormValidation.regex.email.test(value)) {
//                 return "Please enter a valid parent email address.";
//             }
//             return "";
//         },
//         confirm_deletion: (value) => {
//             if (!value) return "You must confirm account deletion.";
//             return "";
//         },
//         token: (value) => {
//             if (!value) return "Token is required.";
//             return "";
//         },
//     },

//     // Display error message with Bootstrap styling
//     showError: (field, message) => {
//         const formGroup = field.closest('.form-group, .mb-3');
//         if (!formGroup) return;

//         // Remove existing error
//         const existingError = formGroup.querySelector('.invalid-feedback');
//         if (existingError) existingError.remove();

//         if (message) {
//             // Add Bootstrap error styling
//             field.classList.add('is-invalid');
//             const errorDiv = document.createElement('div');
//             errorDiv.className = 'invalid-feedback';
//             errorDiv.textContent = message;
//             formGroup.appendChild(errorDiv);

//             // Ensure error is accessible
//             field.setAttribute('aria-describedby', `${field.id}-error`);
//             errorDiv.id = `${field.id}-error`;
//         } else {
//             // Clear error
//             field.classList.remove('is-invalid');
//             field.removeAttribute('aria-describedby');
//         }
//     },

//     // Clear all errors in a form
//     clearErrors: (form) => {
//         form.querySelectorAll('.is-invalid').forEach((field) => {
//             field.classList.remove('is-invalid');
//             field.removeAttribute('aria-describedby');
//         });
//         form.querySelectorAll('.invalid-feedback').forEach((error) => error.remove());
//     },

//     // Validate a single field
//     validateField: (field) => {
//         const name = field.name;
//         const value = field.value.trim();
//         let error = "";

//         if (name === "username") {
//             error = FormValidation.validators.username(value);
//         } else if (name === "email" || name === "new_email") {
//             error = FormValidation.validators.email(value);
//         } else if (name === "role") {
//             error = FormValidation.validators.role(value);
//         } else if (name === "password" || name === "new_password") {
//             error = FormValidation.validators.password(value);
//         } else if (name === "password2" || name === "new_password2") {
//             const passwordField = field.form.querySelector('[name="password"], [name="new_password"]');
//             error = FormValidation.validators.password2(value, passwordField ? passwordField.value : "");
//         } else if (name === "old_password") {
//             error = FormValidation.validators.old_password(value);
//         } else if (name === "confirm_password") {
//             error = FormValidation.validators.old_password(value);
//         }else if (name === "phone_number") {
//             error = FormValidation.validators.phone_number(value);
//         } else if (name === "date_of_birth") {
//             error = FormValidation.validators.date_of_birth(value);
//         } else if (name === "gender") {
//             error = FormValidation.validators.gender(value);
//         } else if (name === "parent_email") {
//             error = FormValidation.validators.parent_email(value);
//         } else if (name === "confirm_deletion") {
//             error = FormValidation.validators.confirm_deletion(value === "true" || field.checked);
//         } else if (name === "token") {
//             error = FormValidation.validators.token(value);
//         } else {
//         console.warn(`No validator found for field: ${name}`);
//     }

//         FormValidation.showError(field, error);
//         return !error;
//     },

//     // Validate entire form
//     validateForm: (form) => {
//         FormValidation.clearErrors(form);
//         let isValid = true;

//         form.querySelectorAll('input, select').forEach((field) => {
//             if (!FormValidation.validateField(field)) {
//                 isValid = false;
//             }
//         });

//         return isValid;
//     },

//     // Initialize validation for a form
//     init: (formSelector) => {
//         const form = document.querySelector(formSelector);
//         if (!form) return;

//         // Real-time validation on blur
//         form.querySelectorAll('input, select').forEach((field) => {
//             field.addEventListener('blur', () => FormValidation.validateField(field));
//         });

//         // Validate on submit
//         form.addEventListener('submit', (e) => {
//             if (!FormValidation.validateForm(form)) {
//                 e.preventDefault();
//                 // Show a Bootstrap alert for form-level error
//                 const alert = document.createElement('div');
//                 alert.className = 'alert alert-danger alert-dismissible fade show';
//                 alert.role = 'alert';
//                 alert.innerHTML = `
//                     Please fix the errors in the form before submitting.
//                     <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
//                 `;
//                 form.prepend(alert);
//                 setTimeout(() => alert.remove(), 5000); // Auto-dismiss after 5s
//             }
//         });
//     },
// };

// // Initialize validation on page load for all forms with class 'needs-validation'
// document.addEventListener('DOMContentLoaded', () => {
//     document.querySelectorAll('form.needs-validation').forEach((form) => {
//         FormValidation.init(`#${form.id}`);
//     });
// });
const FormValidation = {
    // Regular expressions for validation
    regex: {
        username: /^[a-zA-Z0-9@.+_-]{1,150}$/,
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        phone: /^\+\d{1,3}\d{9,15}$/, // E.164 format (e.g., +12025550123)
        date: /^\d{4}-\d{2}-\d{2}$/, // YYYY-MM-DD
        json: /^{.*}$/,
    },

    // Validation rules for each field
    validators: {
        username: (value) => {
            if (!value) return "Username is required.";
            if (!FormValidation.regex.username.test(value)) {
                return "Username can only contain letters, digits, and @/./+/-/_.";
            }
            if (value.length > 150) return "Username must be 150 characters or less.";
            return "";
        },
        email: (value) => {
            if (!value) return "Email is required.";
            if (!FormValidation.regex.email.test(value)) {
                return "Please enter a valid email address.";
            }
            return "";
        },
        role: (value) => {
            const validRoles = ['ST', 'TE', 'AD'];
            if (!value) return "Role is required.";
            if (!validRoles.includes(value)) {
                return "Invalid role selected.";
            }
            return "";
        },
        password: (value) => {
            if (!value) return "Password is required.";
            if (value.length < 8) return "Password must be at least 8 characters.";
            if (!/[A-Z]/.test(value)) return "Password must include at least one uppercase letter.";
            if (!/[0-9]/.test(value)) return "Password must include at least one number.";
            if (!/[^a-zA-Z0-9]/.test(value)) return "Password must include at least one special character.";
            return "";
        },
        password2: (value, password) => {
            if (!value) return "Please confirm your password.";
            if (value !== password) return "Passwords do not match.";
            return "";
        },
        old_password: (value) => {
            if (!value) return "Current password is required.";
            return "";
        },
        phone_number: (value) => {
            if (!value) return ""; // Optional field
            if (!FormValidation.regex.phone.test(value)) {
                return "Please enter a valid phone number in E.164 format (e.g., +12025550123).";
            }
            return "";
        },
        date_of_birth: (value) => {
            if (!value) return ""; // Optional field
            if (!FormValidation.regex.date.test(value)) {
                return "Please enter a valid date in YYYY-MM-DD format.";
            }
            const date = new Date(value);
            if (isNaN(date.getTime())) return "Invalid date.";
            return "";
        },
        gender: (value) => {
            if (!value) return ""; // Optional field
            const validGenders = ['MA', 'FE', 'UD'];
            if (!validGenders.includes(value)) return "Invalid gender selected.";
            return "";
        },
        parent_email: (value) => {
            if (!value) return ""; // Optional field
            if (!FormValidation.regex.email.test(value)) {
                return "Please enter a valid parent email address.";
            }
            return "";
        },
        confirm_deletion: (value) => {
            if (!value) return "You must confirm account deletion.";
            return "";
        },
        token: (value) => {
            if (!value) return "Token is required.";
            return "";
        },
        avatar: (value, field) => {
            if (!field.files || field.files.length === 0) return "";
            const file = field.files[0];
            const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
            if (!validTypes.includes(file.type)) {
                return "Please upload a valid image (JPEG, PNG, or GIF).";
            }
            return "";
        },
        grade_level: (value, field) => {
            const form = field.form;
            const role = form.querySelector('[name="role"]')?.value || 'ST'; // Assume student if no role field
            if (role === 'ST' && !value) return "Grade level is required for students.";
            return "";
        },
        department: (value, field) => {
            const form = field.form;
            const role = form.querySelector('[name="role"]')?.value || 'TE'; // Assume teacher if no role field
            if (['TE', 'AD'].includes(role) && !value) return "Department is required for teachers/admins.";
            return "";
        },
        office_number: (value) => {
            if (!value) return "";
            return "";
        },
        qualifications: (value) => {
            if (!value) return "";
            return "";
        },
        question_type: (value) => {
            if (!value) return "Question type is required.";
            if (value !== 'MCQ') return "Only MCQ is supported.";
            return "";
        },
        difficulty: (value) => {
            if (!value) return "Difficulty is required.";
            const validDifficulties = ['E', 'M', 'H'];
            if (!validDifficulties.includes(value)) return "Invalid difficulty selected.";
            return "";
        },
        topics: (value, field) => {
            if (!field.selectedOptions || field.selectedOptions.length === 0) {
                return "At least one topic is required.";
            }
            return "";
        },
        question_text: (value) => {
            if (!value) return "Question text is required.";
            if (value.length < 10) return "Question text is too short.";
            return "";
        },
        'options.A': (value) => {
            if (!value) return "Option A is required.";
            return "";
        },
        'options.B': (value) => {
            if (!value) return "Option B is required.";
            return "";
        },
        'options.C': (value) => {
            if (!value) return "Option C is required.";
            return "";
        },
        'options.D': (value) => {
            if (!value) return "Option D is required.";
            return "";
        },
        correct_answer: (value) => {
            if (!value) return "Correct answer is required.";
            const validAnswers = ['A', 'B', 'C', 'D'];
            if (!validAnswers.includes(value)) return "Correct answer must be A, B, C, or D.";
            return "";
        },
        metadata: (value) => {
            if (!value) return ""; // Optional
            try {
                JSON.parse(value);
                return "";
            } catch (e) {
                return "Metadata must be valid JSON.";
            }
        },
    },

    // Display error message with Bootstrap styling
    showError: (field, message) => {
        const formGroup = field.closest('.form-group, .mb-3');
        if (!formGroup) {
            console.warn(`No .form-group or .mb-3 found for field: ${field.name}`);
            return;
        }

        const existingError = formGroup.querySelector('.invalid-feedback');
        if (existingError) existingError.remove();

        if (message) {
            field.classList.add('is-invalid');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = message;
            formGroup.appendChild(errorDiv);
            field.setAttribute('aria-describedby', `${field.id}-error`);
            errorDiv.id = `${field.id}-error`;
        } else {
            field.classList.remove('is-invalid');
            field.removeAttribute('aria-describedby');
        }
    },

    // Clear all errors in a form
    clearErrors: (form) => {
        form.querySelectorAll('.is-invalid').forEach((field) => {
            field.classList.remove('is-invalid');
            field.removeAttribute('aria-describedby');
        });
        form.querySelectorAll('.invalid-feedback').forEach((error) => error.remove());
    },

    // Validate a single field
    validateField: (field) => {
        const name = field.name;
        const value = field.value.trim();
        let error = "";

        if (name === "username") {
            error = FormValidation.validators.username(value);
        } else if (name === "email" || name === "new_email") {
            error = FormValidation.validators.email(value);
        } else if (name === "role") {
            error = FormValidation.validators.role(value);
        } else if (name === "password" || name === "new_password") {
            error = FormValidation.validators.password(value);
        } else if (name === "password2" || name === "new_password2") {
            const passwordField = field.form.querySelector('[name="password"], [name="new_password"]');
            error = FormValidation.validators.password2(value, passwordField ? passwordField.value : "");
        } else if (name === "old_password") {
            error = FormValidation.validators.old_password(value);
        } else if (name === "phone_number") {
            error = FormValidation.validators.phone_number(value);
        } else if (name === "date_of_birth") {
            error = FormValidation.validators.date_of_birth(value);
        } else if (name === "gender") {
            error = FormValidation.validators.gender(value);
        } else if (name === "parent_email") {
            error = FormValidation.validators.parent_email(value);
        } else if (name === "confirm_deletion") {
            error = FormValidation.validators.confirm_deletion(value === "true" || field.checked);
        } else if (name === "token") {
            error = FormValidation.validators.token(value);
        }else if (name === "avatar") {
            error = FormValidation.validators.avatar(value, field);
        } else if (name === "grade_level") {
            error = FormValidation.validators.grade_level(value, field);
        } else if (name === "department") {
            error = FormValidation.validators.department(value, field);
        } else if (name === "office_number") {
            error = FormValidation.validators.office_number(value);
        } else if (name === "qualifications") {
            error = FormValidation.validators.qualifications(value);
        }else if (name === "question_type") {
            error = FormValidation.validators.question_type(value);
        } else if (name === "difficulty") {
            error = FormValidation.validators.difficulty(value);
        } else if (name === "topics") {
            error = FormValidation.validators.topics(value, field);
        } else if (name === "question_text") {
            error = FormValidation.validators.question_text(value);
        } else if (name.startsWith("options.")) {
            error = FormValidation.validators[name](value);
        } else if (name === "correct_answer") {
            error = FormValidation.validators.correct_answer(value);
        } else if (name === "metadata") {
            error = FormValidation.validators.metadata(value);
        }else {
            console.warn(`No validator found for field: ${name}`);
        }

        FormValidation.showError(field, error);
        return !error;
    },

    // Validate entire form
    validateForm: (form) => {
        FormValidation.clearErrors(form);
        let isValid = true;

        form.querySelectorAll('input, select').forEach((field) => {
            if (!FormValidation.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    },

    // Initialize validation for a form
    init: (formSelector) => {
        const form = document.querySelector(formSelector);
        if (!form) {
            console.warn(`Form not found for selector: ${formSelector}`);
            return;
        }

        form.querySelectorAll('input, select').forEach((field) => {
            field.addEventListener('blur', () => FormValidation.validateField(field));
        });

        form.addEventListener('submit', (e) => {
            if (!FormValidation.validateForm(form)) {
                e.preventDefault();
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger alert-dismissible fade show';
                alert.role = 'alert';
                alert.innerHTML = `
                    Please fix the errors in the form before submitting.
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                form.prepend(alert);
                setTimeout(() => alert.remove(), 5000);
            }
        });
    },
};

// Initialize validation on page load for all forms with class 'needs-validation'
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('form.needs-validation').forEach((form) => {
        FormValidation.init(`#${form.id}`);
    });
});