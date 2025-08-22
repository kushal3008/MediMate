document.addEventListener('DOMContentLoaded', function() {
    // Handle tab switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    const forms = document.querySelectorAll('.form');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            forms.forEach(form => form.classList.remove('active'));
            button.classList.add('active');
            const formId = button.getAttribute('data-tab');
            const targetForm = document.getElementById(`${formId}-form`);
            if (targetForm) {
                targetForm.classList.add('active');
            }
            // Clear all input fields in all forms
            forms.forEach(form => {
                const inputs = form.querySelectorAll('input');
                inputs.forEach(input => {
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        input.checked = false;
                    } else if(input.type != "hidden") {
                        input.value = '';
                    }
                });
            });
        });
    });

    // Handle form submissions for all forms
    const allForms = document.querySelectorAll('#chemist-form, #doctor-form, #patient-form');

    // Floating label effect
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        if (input.value) {
            input.parentElement.classList.add('focused');
        }
    });
}); 