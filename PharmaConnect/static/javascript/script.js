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
            // Clear all input fields in both forms
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

    // Handle form submissions
    const signInForms = document.querySelectorAll('#chemist-form, #doctor-form');
    const signUpForms = document.querySelectorAll('#chemist-signup-form, #doctor-signup-form');

    // signInForms.forEach(form => {
    //     form.addEventListener('submit', function(e) {
    //         e.preventDefault();
    //         const formData = new FormData(form);
    //         const data = Object.fromEntries(formData.entries());
    //         console.log('Sign In Data:', data);
    //         alert('Sign In functionality will be implemented with backend integration');
    //     });
    // });

    // signUpForms.forEach(form => {
    //     form.addEventListener('submit', function(e) {
    //         e.preventDefault();
    //         const formData = new FormData(form);
    //         const data = Object.fromEntries(formData.entries());
    //         console.log('Sign Up Data:', data);
    //         alert('Sign Up functionality will be implemented with backend integration');
    //     });
    // });

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