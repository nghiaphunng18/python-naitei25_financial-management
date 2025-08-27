/**
 * Profile Page JavaScript
 * Handles profile form interactions, validation, and modal dialogs
 */

class ProfileManager {
    constructor() {
        this.config = window.profileConfig || {};
        this.elements = {};
        this.originalValues = {};
        
        this.init();
    }

    /**
     * Initialize the profile manager
     */
    init() {
        this.bindElements();
        this.storeOriginalValues();
        this.bindEvents();
    }

    /**
     * Bind DOM elements
     */
    bindElements() {
        this.elements = {
            cancelBtn: document.getElementById('cancelBtn'),
            confirmModal: document.getElementById('confirmModal'),
            confirmCancel: document.getElementById('confirmCancel'),
            cancelCancel: document.getElementById('cancelCancel'),
            profileForm: document.getElementById('profileForm'),
            emailField: document.getElementById(this.config.emailFieldId),
            phoneField: document.getElementById(this.config.phoneFieldId)
        };
    }

    /**
     * Store original form values for change detection
     */
    storeOriginalValues() {
        if (!this.elements.profileForm) return;

        const formData = new FormData(this.elements.profileForm);
        for (let [key, value] of formData.entries()) {
            this.originalValues[key] = value;
        }
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Only bind events if elements exist (edit mode)
        if (this.elements.cancelBtn) {
            this.elements.cancelBtn.addEventListener('click', (e) => this.handleCancelClick(e));
        }

        if (this.elements.confirmCancel) {
            this.elements.confirmCancel.addEventListener('click', () => this.handleConfirmCancel());
        }

        if (this.elements.cancelCancel) {
            this.elements.cancelCancel.addEventListener('click', () => this.handleCancelCancel());
        }

        if (this.elements.confirmModal) {
            this.elements.confirmModal.addEventListener('click', (e) => this.handleModalClick(e));
        }

        if (this.elements.profileForm) {
            this.elements.profileForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Global events
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    /**
     * Check if form has changes
     * @returns {boolean}
     */
    hasFormChanges() {
        if (!this.elements.profileForm) return false;

        const currentFormData = new FormData(this.elements.profileForm);
        for (let [key, value] of currentFormData.entries()) {
            if (key === 'csrfmiddlewaretoken') continue;
            if (this.originalValues[key] !== value) {
                return true;
            }
        }
        return false;
    }

    /**
     * Handle cancel button click
     * @param {Event} e
     */
    handleCancelClick(e) {
        e.preventDefault();
        
        if (this.hasFormChanges()) {
            this.showModal();
        } else {
            this.redirectToProfile();
        }
    }

    /**
     * Handle confirm cancel button click
     */
    handleConfirmCancel() {
        this.redirectToProfile();
    }

    /**
     * Handle cancel cancel button click (close modal)
     */
    handleCancelCancel() {
        this.hideModal();
    }

    /**
     * Handle modal background click
     * @param {Event} e
     */
    handleModalClick(e) {
        if (e.target === this.elements.confirmModal) {
            this.hideModal();
        }
    }

    /**
     * Handle keydown events
     * @param {Event} e
     */
    handleKeyDown(e) {
        if (e.key === 'Escape' && this.isModalVisible()) {
            this.hideModal();
        }
    }

    /**
     * Handle form submit
     * @param {Event} e
     */
    handleFormSubmit(e) {
        if (!this.validateForm()) {
            e.preventDefault();
        }
    }

    /**
     * Show confirmation modal
     */
    showModal() {
        if (this.elements.confirmModal) {
            this.elements.confirmModal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }

    /**
     * Hide confirmation modal
     */
    hideModal() {
        if (this.elements.confirmModal) {
            this.elements.confirmModal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    }

    /**
     * Check if modal is visible
     * @returns {boolean}
     */
    isModalVisible() {
        return this.elements.confirmModal && 
               !this.elements.confirmModal.classList.contains('hidden');
    }

    /**
     * Redirect to profile page
     */
    redirectToProfile() {
        window.location.href = this.config.profileUrl;
    }

    /**
     * Validate form fields
     * @returns {boolean}
     */
    validateForm() {
        let isValid = true;

        // Validate email
        if (this.elements.emailField) {
            const emailValue = this.elements.emailField.value.trim();
            if (!emailValue) {
                this.showFieldError(this.elements.emailField, this.config.messages.emailRequired);
                isValid = false;
            } else if (!this.isValidEmail(emailValue)) {
                this.showFieldError(this.elements.emailField, this.config.messages.emailInvalid);
                isValid = false;
            } else {
                this.clearFieldError(this.elements.emailField);
            }
        }

        // Validate phone
        if (this.elements.phoneField) {
            const phoneValue = this.elements.phoneField.value.trim();
            if (!phoneValue) {
                this.showFieldError(this.elements.phoneField, this.config.messages.phoneRequired);
                isValid = false;
            } else if (!this.isValidPhone(phoneValue)) {
                this.showFieldError(this.elements.phoneField, this.config.messages.phoneInvalid);
                isValid = false;
            } else {
                this.clearFieldError(this.elements.phoneField);
            }
        }

        return isValid;
    }

    /**
     * Validate email format
     * @param {string} email
     * @returns {boolean}
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Validate Vietnamese phone number
     * @param {string} phone
     * @returns {boolean}
     */
    isValidPhone(phone) {
        const phoneRegex = /^(\+84|0)(3[2-9]|5[689]|7[06-9]|8[1-689]|9[0-46-9])[0-9]{7}$/;
        const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
        return phoneRegex.test(cleanPhone);
    }

    /**
     * Show field error
     * @param {HTMLElement} field
     * @param {string} message
     */
    showFieldError(field, message) {
        this.clearFieldError(field);
        
        // Add error styling
        field.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        
        // Create error message
        const errorDiv = document.createElement('p');
        errorDiv.className = 'mt-1 text-sm text-red-600 field-error';
        errorDiv.textContent = message;
        
        // Append to field container
        field.parentNode.appendChild(errorDiv);
    }

    /**
     * Clear field error
     * @param {HTMLElement} field
     */
    clearFieldError(field) {
        // Remove error styling
        field.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    }
}

/**
 * Utility functions
 */
const ProfileUtils = {
    /**
     * Debounce function
     * @param {Function} func
     * @param {number} wait
     * @returns {Function}
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Format phone number for display
     * @param {string} phone
     * @returns {string}
     */
    formatPhoneNumber: function(phone) {
        const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
        if (cleanPhone.startsWith('84')) {
            return `+84 ${cleanPhone.slice(2, 5)} ${cleanPhone.slice(5, 8)} ${cleanPhone.slice(8)}`;
        } else if (cleanPhone.startsWith('0')) {
            return `${cleanPhone.slice(0, 4)} ${cleanPhone.slice(4, 7)} ${cleanPhone.slice(7)}`;
        }
        return phone;
    },

    /**
     * Show toast notification
     * @param {string} message
     * @param {string} type - success, error, info, warning
     */
    showToast: function(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-opacity duration-300 ${this.getToastClasses(type)}`;
        toast.textContent = message;
        
        // Add to DOM
        document.body.appendChild(toast);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    },

    /**
     * Get toast CSS classes based on type
     * @param {string} type
     * @returns {string}
     */
    getToastClasses: function(type) {
        const classes = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-white',
            info: 'bg-blue-500 text-white'
        };
        return classes[type] || classes.info;
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.profileManager = new ProfileManager();
});

// Export for potential use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ProfileManager, ProfileUtils };
}
