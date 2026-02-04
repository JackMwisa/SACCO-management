/**
 * Form Utilities for SACCO Management System
 * Provides loading states, validation helpers, and form enhancements
 */

(function() {
    'use strict';

    // Initialize all forms with loading states
    function initFormLoadingStates() {
        const forms = document.querySelectorAll('form[data-loading="true"]');

        forms.forEach(function(form) {
            form.addEventListener('submit', function(e) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    // Disable button
                    submitBtn.disabled = true;

                    // Store original text
                    const originalText = submitBtn.innerHTML;
                    submitBtn.setAttribute('data-original-text', originalText);

                    // Get loading text from data attribute or use default
                    const loadingText = submitBtn.getAttribute('data-loading-text') || 'Processing...';

                    // Show loading state
                    submitBtn.innerHTML = `
                        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        ${loadingText}
                    `;
                }
            });
        });
    }

    // Initialize PIN input mask (4 digits only)
    function initPinInputs() {
        const pinInputs = document.querySelectorAll('input[data-pin="true"], input[name="pin-number"]');

        pinInputs.forEach(function(input) {
            input.setAttribute('inputmode', 'numeric');
            input.setAttribute('pattern', '[0-9]{4}');
            input.setAttribute('maxlength', '4');
            input.setAttribute('autocomplete', 'off');

            input.addEventListener('input', function(e) {
                // Allow only numbers
                this.value = this.value.replace(/[^0-9]/g, '');
            });
        });
    }

    // Initialize amount input formatting
    function initAmountInputs() {
        const amountInputs = document.querySelectorAll('input[data-amount="true"], input[name*="amount"]');

        amountInputs.forEach(function(input) {
            input.setAttribute('inputmode', 'decimal');
            input.setAttribute('min', '0');

            // Format on blur
            input.addEventListener('blur', function(e) {
                let value = parseFloat(this.value);
                if (!isNaN(value) && value > 0) {
                    this.value = value.toFixed(2);
                }
            });
        });
    }

    // Initialize phone number formatting
    function initPhoneInputs() {
        const phoneInputs = document.querySelectorAll('input[type="tel"], input[name*="phone"]');

        phoneInputs.forEach(function(input) {
            input.setAttribute('inputmode', 'tel');

            input.addEventListener('input', function(e) {
                // Allow only numbers, plus, and spaces
                this.value = this.value.replace(/[^0-9+\s-]/g, '');
            });
        });
    }

    // Confirm before delete actions
    function initDeleteConfirmations() {
        const deleteLinks = document.querySelectorAll('a[data-confirm], button[data-confirm]');

        deleteLinks.forEach(function(element) {
            element.addEventListener('click', function(e) {
                const message = this.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
                if (!confirm(message)) {
                    e.preventDefault();
                    return false;
                }
            });
        });
    }

    // Password strength indicator
    function initPasswordStrength() {
        const passwordInputs = document.querySelectorAll('input[type="password"][data-strength="true"]');

        passwordInputs.forEach(function(input) {
            const strengthDiv = document.createElement('div');
            strengthDiv.className = 'password-strength mt-1';
            strengthDiv.innerHTML = '<small class="text-muted">Password strength: <span class="strength-text">-</span></small>';
            input.parentNode.appendChild(strengthDiv);

            input.addEventListener('input', function(e) {
                const strength = calculatePasswordStrength(this.value);
                const strengthText = strengthDiv.querySelector('.strength-text');

                if (this.value.length === 0) {
                    strengthText.textContent = '-';
                    strengthText.className = 'strength-text text-muted';
                } else if (strength < 2) {
                    strengthText.textContent = 'Weak';
                    strengthText.className = 'strength-text text-danger';
                } else if (strength < 4) {
                    strengthText.textContent = 'Medium';
                    strengthText.className = 'strength-text text-warning';
                } else {
                    strengthText.textContent = 'Strong';
                    strengthText.className = 'strength-text text-success';
                }
            });
        });
    }

    function calculatePasswordStrength(password) {
        let strength = 0;

        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        if (/[a-z]/.test(password)) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^a-zA-Z0-9]/.test(password)) strength++;

        return strength;
    }

    // Password confirmation matching
    function initPasswordConfirmation() {
        const confirmInputs = document.querySelectorAll('input[name="confirm_password"], input[id="confirm-password"]');

        confirmInputs.forEach(function(confirmInput) {
            const form = confirmInput.closest('form');
            const passwordInput = form.querySelector('input[name="new_password"], input[id="new-password"]');

            if (passwordInput) {
                confirmInput.addEventListener('input', function(e) {
                    if (this.value !== passwordInput.value) {
                        this.setCustomValidity('Passwords do not match');
                    } else {
                        this.setCustomValidity('');
                    }
                });
            }
        });
    }

    // Auto-dismiss alerts after 5 seconds
    function initAlertAutoDismiss() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');

        alerts.forEach(function(alert) {
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    }

    // Initialize all utilities on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        initFormLoadingStates();
        initPinInputs();
        initAmountInputs();
        initPhoneInputs();
        initDeleteConfirmations();
        initPasswordStrength();
        initPasswordConfirmation();
        initAlertAutoDismiss();
    });

})();
