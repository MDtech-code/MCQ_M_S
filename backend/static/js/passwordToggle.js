document.addEventListener('DOMContentLoaded', () => {
    // Select all password toggle buttons
    document.querySelectorAll('.password-toggle').forEach((button) => {
        button.addEventListener('click', () => {
            // Find the closest password input
            const container = button.closest('.form-floating, .mb-3');
            const input = container.querySelector('.password-input');
            const icon = button.querySelector('i');

            if (input && icon) {
                // Toggle input type and icon
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.replace('bi-eye', 'bi-eye-slash');
                    button.setAttribute('aria-label', 'Hide password');
                } else {
                    input.type = 'password';
                    icon.classList.replace('bi-eye-slash', 'bi-eye');
                    button.setAttribute('aria-label', 'Show password');
                }
            }
        });
    });
});