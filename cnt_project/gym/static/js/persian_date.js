// Persian Date Helper Functions
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Persian date inputs
    initPersianDateInputs();
});

function initPersianDateInputs() {
    const persianDateInputs = document.querySelectorAll('.persian-date-input');
    
    persianDateInputs.forEach(input => {
        // Add input validation and formatting
        input.addEventListener('input', function(e) {
            formatPersianDateInput(e.target);
        });
        
        input.addEventListener('blur', function(e) {
            validatePersianDate(e.target);
        });
        
        // Set placeholder with Persian digits
        if (!input.placeholder) {
            input.placeholder = '۱۴۰۳/۰۱/۰۱';
        }
    });
}

function formatPersianDateInput(input) {
    let value = input.value;
    
    // Remove non-digit characters except /
    value = value.replace(/[^\d\/۰-۹]/g, '');
    
    // Convert Persian digits to English
    value = persianToEnglishDigits(value);
    
    // Auto-add slashes
    if (value.length === 4 && !value.includes('/')) {
        value = value + '/';
    } else if (value.length === 7 && value.split('/').length === 2) {
        value = value + '/';
    }
    
    // Limit length
    if (value.length > 10) {
        value = value.substring(0, 10);
    }
    
    input.value = value;
}

function validatePersianDate(input) {
    const value = input.value.trim();
    
    if (!value) return;
    
    const parts = value.split('/');
    if (parts.length !== 3) {
        showDateError(input, 'فرمت تاریخ نادرست است. فرمت صحیح: ۱۴۰۳/۰۱/۰۱');
        return;
    }
    
    const year = parseInt(parts[0]);
    const month = parseInt(parts[1]);
    const day = parseInt(parts[2]);
    
    // Validate year (1300-1450 roughly)
    if (year < 1300 || year > 1450) {
        showDateError(input, 'سال وارد شده نامعتبر است');
        return;
    }
    
    // Validate month
    if (month < 1 || month > 12) {
        showDateError(input, 'ماه وارد شده نامعتبر است');
        return;
    }
    
    // Validate day
    if (day < 1 || day > 31) {
        showDateError(input, 'روز وارد شده نامعتبر است');
        return;
    }
    
    // More specific day validation for Persian calendar
    if (month <= 6 && day > 31) {
        showDateError(input, 'این ماه حداکثر ۳۱ روز دارد');
        return;
    } else if (month > 6 && month <= 11 && day > 30) {
        showDateError(input, 'این ماه حداکثر ۳۰ روز دارد');
        return;
    } else if (month === 12 && day > 29) {
        // Simple leap year check - more accurate check would be better
        if (!isLeapYearPersian(year) && day > 29) {
            showDateError(input, 'ماه اسفند در سال غیر کبیسه حداکثر ۲۹ روز دارد');
            return;
        } else if (day > 30) {
            showDateError(input, 'ماه اسفند حداکثر ۳۰ روز دارد');
            return;
        }
    }
    
    clearDateError(input);
}

function showDateError(input, message) {
    clearDateError(input);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'text-danger mt-1 persian-date-error';
    errorDiv.textContent = message;
    
    input.parentNode.appendChild(errorDiv);
    input.style.borderColor = '#dc3545';
}

function clearDateError(input) {
    const existingError = input.parentNode.querySelector('.persian-date-error');
    if (existingError) {
        existingError.remove();
    }
    input.style.borderColor = '';
}

function persianToEnglishDigits(str) {
    const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    const englishDigits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
    
    for (let i = 0; i < persianDigits.length; i++) {
        str = str.replace(new RegExp(persianDigits[i], 'g'), englishDigits[i]);
    }
    
    return str;
}

function englishToPersianDigits(str) {
    const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    const englishDigits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
    
    for (let i = 0; i < englishDigits.length; i++) {
        str = str.replace(new RegExp(englishDigits[i], 'g'), persianDigits[i]);
    }
    
    return str;
}

function isLeapYearPersian(year) {
    // Simplified Persian leap year calculation
    // More accurate calculation would require proper Persian calendar algorithm
    const cycle = year % 128;
    const breaks = [29, 33, 37, 41, 45, 49, 53, 57, 61, 65, 69, 73, 77, 81, 85, 89, 93, 97, 101, 105, 109, 113, 117, 121, 125];
    
    for (let i = 0; i < breaks.length; i++) {
        if (cycle === breaks[i]) {
            return true;
        }
    }
    
    return false;
}

// Export functions for use in other scripts if needed
window.PersianDateHelper = {
    formatPersianDateInput,
    validatePersianDate,
    persianToEnglishDigits,
    englishToPersianDigits,
    isLeapYearPersian
}; 