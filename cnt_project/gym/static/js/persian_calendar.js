// Persian Calendar Widget
class PersianCalendar {
    constructor(input, options = {}) {
        this.input = input;
        this.options = {
            showToday: true,
            showClear: true,
            showClose: true,
            ...options
        };
        this.isOpen = false;
        this.currentYear = 1403; // Default to current Persian year
        this.currentMonth = 1;
        this.selectedDate = null;
        
        this.init();
    }
    
    init() {
        this.createCalendar();
        this.bindEvents();
        this.setInitialDate();
    }
    
    createCalendar() {
        // Create calendar container
        this.calendar = document.createElement('div');
        this.calendar.className = 'persian-calendar';
        this.calendar.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            display: none;
            font-family: 'Tahoma', sans-serif;
            direction: rtl;
        `;
        
        // Create calendar header
        this.createHeader();
        
        // Create calendar body
        this.createBody();
        
        // Create calendar footer
        this.createFooter();
        
        // Insert calendar after input
        this.input.parentNode.style.position = 'relative';
        this.input.parentNode.appendChild(this.calendar);
    }
    
    createHeader() {
        const header = document.createElement('div');
        header.className = 'calendar-header';
        header.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            border-radius: 8px 8px 0 0;
        `;
        
        // Previous month button
        const prevBtn = document.createElement('button');
        prevBtn.innerHTML = '‹';
        prevBtn.className = 'calendar-nav-btn';
        prevBtn.style.cssText = `
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
        `;
        prevBtn.addEventListener('click', () => this.previousMonth());
        
        // Month/Year display
        this.monthYearDisplay = document.createElement('div');
        this.monthYearDisplay.className = 'calendar-month-year';
        this.monthYearDisplay.style.cssText = `
            font-weight: bold;
            font-size: 16px;
        `;
        
        // Next month button
        const nextBtn = document.createElement('button');
        nextBtn.innerHTML = '›';
        nextBtn.className = 'calendar-nav-btn';
        nextBtn.style.cssText = `
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
        `;
        nextBtn.addEventListener('click', () => this.nextMonth());
        
        header.appendChild(prevBtn);
        header.appendChild(this.monthYearDisplay);
        header.appendChild(nextBtn);
        
        this.calendar.appendChild(header);
    }
    
    createBody() {
        const body = document.createElement('div');
        body.className = 'calendar-body';
        body.style.cssText = `
            padding: 16px;
        `;
        
        // Create weekdays header
        const weekdays = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];
        const weekdaysRow = document.createElement('div');
        weekdaysRow.className = 'calendar-weekdays';
        weekdaysRow.style.cssText = `
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            margin-bottom: 8px;
        `;
        
        weekdays.forEach(day => {
            const dayElement = document.createElement('div');
            dayElement.textContent = day;
            dayElement.style.cssText = `
                text-align: center;
                font-weight: bold;
                padding: 8px 4px;
                color: #6c757d;
                font-size: 14px;
            `;
            weekdaysRow.appendChild(dayElement);
        });
        
        body.appendChild(weekdaysRow);
        
        // Create days grid
        this.daysGrid = document.createElement('div');
        this.daysGrid.className = 'calendar-days';
        this.daysGrid.style.cssText = `
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
        `;
        
        body.appendChild(this.daysGrid);
        this.calendar.appendChild(body);
    }
    
    createFooter() {
        const footer = document.createElement('div');
        footer.className = 'calendar-footer';
        footer.style.cssText = `
            display: flex;
            justify-content: space-between;
            padding: 12px 16px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            border-radius: 0 0 8px 8px;
        `;
        
        if (this.options.showToday) {
            const todayBtn = document.createElement('button');
            todayBtn.textContent = 'امروز';
            todayBtn.className = 'calendar-today-btn';
            todayBtn.style.cssText = `
                background: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            `;
            todayBtn.addEventListener('click', () => this.selectToday());
            footer.appendChild(todayBtn);
        }
        
        if (this.options.showClear) {
            const clearBtn = document.createElement('button');
            clearBtn.textContent = 'پاک کردن';
            clearBtn.className = 'calendar-clear-btn';
            clearBtn.style.cssText = `
                background: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            `;
            clearBtn.addEventListener('click', () => this.clearDate());
            footer.appendChild(clearBtn);
        }
        
        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'بستن';
        closeBtn.className = 'calendar-close-btn';
        closeBtn.style.cssText = `
            background: #dc3545;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        `;
        closeBtn.addEventListener('click', () => this.close());
        footer.appendChild(closeBtn);
        
        this.calendar.appendChild(footer);
    }
    
    bindEvents() {
        // Toggle calendar on input click
        this.input.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggle();
        });
        
        // Close calendar when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.calendar.contains(e.target) && e.target !== this.input) {
                this.close();
            }
        });
        
        // Prevent input focus when calendar is open
        this.input.addEventListener('focus', (e) => {
            if (this.isOpen) {
                e.preventDefault();
            }
        });
    }
    
    setInitialDate() {
        const currentValue = this.input.value;
        if (currentValue) {
            const parts = currentValue.split('/');
            if (parts.length === 3) {
                this.currentYear = parseInt(parts[0]);
                this.currentMonth = parseInt(parts[1]);
                this.selectedDate = {
                    year: this.currentYear,
                    month: this.currentMonth,
                    day: parseInt(parts[2])
                };
            }
        } else {
            // Set to current Persian date
            const now = new Date();
            const persianDate = this.gregorianToPersian(now);
            this.currentYear = persianDate.year;
            this.currentMonth = persianDate.month;
        }
        
        this.updateDisplay();
    }
    
    updateDisplay() {
        // Update month/year display
        const monthNames = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ];
        this.monthYearDisplay.textContent = `${monthNames[this.currentMonth - 1]} ${this.currentYear}`;
        
        // Clear days grid
        this.daysGrid.innerHTML = '';
        
        // Get first day of month and number of days
        const firstDay = this.getFirstDayOfMonth(this.currentYear, this.currentMonth);
        const daysInMonth = this.getDaysInMonth(this.currentYear, this.currentMonth);
        
        // Add empty cells for days before first day of month
        for (let i = 0; i < firstDay; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.style.cssText = `
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
            `;
            this.daysGrid.appendChild(emptyDay);
        }
        
        // Add days of month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = document.createElement('div');
            dayElement.textContent = day;
            dayElement.className = 'calendar-day';
            dayElement.style.cssText = `
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                border-radius: 4px;
                font-size: 14px;
                transition: all 0.2s;
            `;
            
            // Check if this is the selected date
            if (this.selectedDate && 
                this.selectedDate.year === this.currentYear &&
                this.selectedDate.month === this.currentMonth &&
                this.selectedDate.day === day) {
                dayElement.style.background = '#007bff';
                dayElement.style.color = 'white';
            }
            
            // Check if this is today
            const today = this.getTodayPersian();
            if (today.year === this.currentYear && 
                today.month === this.currentMonth && 
                today.day === day) {
                dayElement.style.border = '2px solid #28a745';
            }
            
            dayElement.addEventListener('click', () => this.selectDate(day));
            dayElement.addEventListener('mouseenter', () => {
                if (!dayElement.style.background) {
                    dayElement.style.background = '#e9ecef';
                }
            });
            dayElement.addEventListener('mouseleave', () => {
                if (dayElement.style.background === 'rgb(233, 236, 239)') {
                    dayElement.style.background = '';
                }
            });
            
            this.daysGrid.appendChild(dayElement);
        }
    }
    
    selectDate(day) {
        this.selectedDate = {
            year: this.currentYear,
            month: this.currentMonth,
            day: day
        };
        
        // Update input value
        this.input.value = `${this.currentYear}/${this.currentMonth.toString().padStart(2, '0')}/${day.toString().padStart(2, '0')}`;
        
        // Trigger change event
        this.input.dispatchEvent(new Event('change', { bubbles: true }));
        
        this.close();
    }
    
    selectToday() {
        const today = this.getTodayPersian();
        this.currentYear = today.year;
        this.currentMonth = today.month;
        this.selectDate(today.day);
    }
    
    clearDate() {
        this.selectedDate = null;
        this.input.value = '';
        this.input.dispatchEvent(new Event('change', { bubbles: true }));
        this.close();
    }
    
    previousMonth() {
        this.currentMonth--;
        if (this.currentMonth < 1) {
            this.currentMonth = 12;
            this.currentYear--;
        }
        this.updateDisplay();
    }
    
    nextMonth() {
        this.currentMonth++;
        if (this.currentMonth > 12) {
            this.currentMonth = 1;
            this.currentYear++;
        }
        this.updateDisplay();
    }
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
    
    open() {
        this.calendar.style.display = 'block';
        this.isOpen = true;
        this.updateDisplay();
    }
    
    close() {
        this.calendar.style.display = 'none';
        this.isOpen = false;
    }
    
    // Persian calendar utility functions
    getFirstDayOfMonth(year, month) {
        // Simplified calculation - in a real implementation, you'd use proper Persian calendar algorithms
        const gregorianDate = this.persianToGregorian(year, month, 1);
        return gregorianDate.getDay();
    }
    
    getDaysInMonth(year, month) {
        if (month <= 6) return 31;
        if (month <= 11) return 30;
        // Esfand (month 12) - check for leap year
        return this.isLeapYear(year) ? 30 : 29;
    }
    
    isLeapYear(year) {
        // Simplified Persian leap year calculation
        const cycle = year % 128;
        const breaks = [29, 33, 37, 41, 45, 49, 53, 57, 61, 65, 69, 73, 77, 81, 85, 89, 93, 97, 101, 105, 109, 113, 117, 121, 125];
        return breaks.includes(cycle);
    }
    
    getTodayPersian() {
        const today = new Date();
        return this.gregorianToPersian(today);
    }
    
    gregorianToPersian(gregorianDate) {
        // Simplified conversion - for production use a proper Persian calendar library
        const year = gregorianDate.getFullYear();
        const month = gregorianDate.getMonth() + 1;
        const day = gregorianDate.getDate();
        
        let persianYear = year - 621;
        let persianMonth = month + 3;
        let persianDay = day;
        
        if (persianMonth > 12) {
            persianMonth -= 12;
            persianYear += 1;
        }
        
        return { year: persianYear, month: persianMonth, day: persianDay };
    }
    
    persianToGregorian(year, month, day) {
        // Simplified conversion - for production use a proper Persian calendar library
        let gregorianYear = year + 621;
        let gregorianMonth = month - 3;
        let gregorianDay = day;
        
        if (gregorianMonth < 1) {
            gregorianMonth += 12;
            gregorianYear -= 1;
        }
        
        return new Date(gregorianYear, gregorianMonth - 1, gregorianDay);
    }
}

// Initialize Persian calendars for all inputs with the class
document.addEventListener('DOMContentLoaded', function() {
    const persianDateInputs = document.querySelectorAll('.persian-date-input');
    persianDateInputs.forEach(input => {
        new PersianCalendar(input);
    });
});

// Export for use in other scripts
window.PersianCalendar = PersianCalendar;
