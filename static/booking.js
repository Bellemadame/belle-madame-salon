/**
 * Belle Madame Salon Online Booking System
 * Frontend JavaScript
 * 
 * Handles all client-side booking functionality including:
 * - Multi-step form navigation
 * - Service and staff selection
 * - Time slot availability checking
 * - Form validation
 * - API communication
 */

class BookingSystem {
  constructor() {
    // Booking state
    this.state = {
      step: 1,
      service: null,
      staff: null,
      date: null,
      time: null,
      clientName: '',
      phone: '',
      notes: ''
    };

    // API base URL
    this.apiBase = '/api';

    // Initialize
    this.init();
  }

  /**
   * Initialize the booking system
   */
  init() {
    this.bindElements();
    this.bindEvents();
    this.loadServices();
    this.setMinDate();
    this.updateProgress();
  }

  /**
   * Cache DOM elements
   */
  bindElements() {
    // Steps
    this.step1 = document.getElementById('step-1');
    this.step2 = document.getElementById('step-2');
    this.step3 = document.getElementById('step-3');
    this.step4 = document.getElementById('step-4');
    this.steps = document.querySelectorAll('.booking-step');

    // Progress
    this.progressCircles = document.querySelectorAll('.step-circle');
    this.progressLines = document.querySelectorAll('.progress-line');

    // Service selection
    this.serviceList = document.getElementById('service-list');

    // Staff selection
    this.staffSelect = document.getElementById('staff-select');

    // Date selection
    this.dateInput = document.getElementById('booking-date');

    // Time slots
    this.timeSlotsContainer = document.getElementById('time-slots');

    // Client form
    this.clientNameInput = document.getElementById('client-name');
    this.phoneInput = document.getElementById('client-phone');
    this.notesInput = document.getElementById('booking-notes');

    // Buttons
    this.nextBtn = document.getElementById('next-btn');
    this.backBtn = document.getElementById('back-btn');
    this.submitBtn = document.getElementById('submit-btn');
    this.confirmAnotherBtn = document.getElementById('confirm-another');

    // Loading & Toast
    this.loadingOverlay = document.getElementById('loading-overlay');
    this.toastContainer = document.getElementById('toast-container');

    // Confirmation screen
    this.confirmationScreen = document.getElementById('confirmation-screen');
    this.bookingSummary = document.getElementById('booking-summary');
  }

  /**
   * Bind event listeners
   */
  bindEvents() {
    // Navigation buttons
    if (this.nextBtn) {
      this.nextBtn.addEventListener('click', () => this.handleNext());
    }
    if (this.backBtn) {
      this.backBtn.addEventListener('click', () => this.handleBack());
    }
    if (this.submitBtn) {
      this.submitBtn.addEventListener('click', () => this.handleSubmit());
    }
    if (this.confirmAnotherBtn) {
      this.confirmAnotherBtn.addEventListener('click', () => this.resetBooking());
    }

    // Form inputs
    if (this.clientNameInput) {
      this.clientNameInput.addEventListener('input', (e) => {
        this.state.clientName = e.target.value.trim();
        this.validateStep4();
      });
    }

    if (this.phoneInput) {
      this.phoneInput.addEventListener('input', (e) => {
        this.state.phone = e.target.value.trim();
        this.validateStep4();
      });
    }

    if (this.notesInput) {
      this.notesInput.addEventListener('input', (e) => {
        this.state.notes = e.target.value.trim();
      });
    }

    // Date change
    if (this.dateInput) {
      this.dateInput.addEventListener('change', (e) => {
        this.state.date = e.target.value;
        this.loadTimeSlots();
      });
    }

    // Staff change
    if (this.staffSelect) {
      this.staffSelect.addEventListener('change', (e) => {
        this.state.staff = e.target.value ? parseInt(e.target.value) : null;
        if (this.state.date) {
          this.loadTimeSlots();
        }
        this.validateStep2();
      });
    }

    // Close modal on backdrop click
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-backdrop')) {
        this.closeModal(e.target.closest('.modal'));
      }
    });
  }

  /**
   * Set minimum date to today
   */
  setMinDate() {
    if (this.dateInput) {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      this.dateInput.min = `${year}-${month}-${day}`;
    }
  }

  /**
   * Update progress indicator
   */
  updateProgress() {
    const step = this.state.step;

    this.progressCircles.forEach((circle, index) => {
      circle.classList.remove('active', 'completed');
      if (index + 1 < step) {
        circle.classList.add('completed');
        circle.innerHTML = '✓';
      } else if (index + 1 === step) {
        circle.classList.add('active');
        circle.innerHTML = index + 1;
      } else {
        circle.innerHTML = index + 1;
      }
    });

    this.progressLines.forEach((line, index) => {
      if (index + 1 < step) {
        line.classList.add('active');
      } else {
        line.classList.remove('active');
      }
    });
  }

  /**
   * Show specific step
   */
  showStep(stepNumber) {
    this.steps.forEach((step, index) => {
      step.classList.remove('active');
      if (index + 1 === stepNumber) {
        step.classList.add('active');
      }
    });

    this.state.step = stepNumber;
    this.updateProgress();
    this.updateButtonVisibility();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /**
   * Update button visibility based on step
   */
  updateButtonVisibility() {
    if (!this.nextBtn || !this.backBtn) return;

    this.nextBtn.classList.remove('hidden');
    this.backBtn.classList.remove('hidden');

    if (this.state.step === 1) {
      this.backBtn.classList.add('hidden');
    } else if (this.state.step === 4) {
      this.nextBtn.classList.add('hidden');
    }

    // Update next button text
    if (this.state.step === 3) {
      this.nextBtn.textContent = 'Review Booking';
    } else if (this.state.step === 4) {
      this.nextBtn.textContent = 'Confirm Booking';
    }
  }

  /**
   * Load services from API
   */
  async loadServices() {
    this.showLoading(true);

    try {
      const response = await fetch(`${this.apiBase}/services`);
      const services = await response.json();

      this.renderServices(services);
    } catch (error) {
      console.error('Error loading services:', error);
      this.showToast('Failed to load services. Please refresh the page.', 'error');
    } finally {
      this.showLoading(false);
    }
  }

  /**
   * Render services list
   */
  renderServices(services) {
    if (!this.serviceList) return;

    this.serviceList.innerHTML = '';

    // Group by category
    const categories = {};
    services.forEach(service => {
      if (!categories[service.category]) {
        categories[service.category] = [];
      }
      categories[service.category].push(service);
    });

    // Render categories
    Object.keys(categories).forEach(category => {
      const categoryDiv = document.createElement('div');
      categoryDiv.className = 'service-category-group';
      categoryDiv.innerHTML = `<h3 class="category-title">${this.escapeHtml(category)}</h3>`;

      const listDiv = document.createElement('div');
      listDiv.className = 'service-list';

      categories[category].forEach(service => {
        const card = document.createElement('div');
        card.className = 'service-card';
        card.dataset.serviceId = service.id;
        card.dataset.serviceName = service.name;
        card.dataset.price = service.price;
        card.dataset.duration = service.duration;

        card.innerHTML = `
          <div class="service-category">${this.escapeHtml(category)}</div>
          <div class="service-name">${this.escapeHtml(service.name)}</div>
          <div class="service-details">
            <span class="service-price">R${service.price.toFixed(2)}</span>
            <span class="service-duration">${this.formatDuration(service.duration)}</span>
          </div>
        `;

        card.addEventListener('click', () => this.selectService(card, service));
        listDiv.appendChild(card);
      });

      categoryDiv.appendChild(listDiv);
      this.serviceList.appendChild(categoryDiv);
    });
  }

  /**
   * Select a service
   */
  selectService(card, service) {
    // Remove previous selection
    document.querySelectorAll('.service-card').forEach(c => {
      c.classList.remove('selected');
    });

    // Add selection
    card.classList.add('selected');
    this.state.service = {
      id: service.id,
      name: service.name,
      price: service.price,
      duration: service.duration
    };

    // Move to next step
    this.loadStaff();
    this.showStep(2);
  }

  /**
   * Load staff for selected service
   */
  async loadStaff() {
    if (!this.staffSelect) return;

    this.staffSelect.innerHTML = '<option value="">Select staff member</option>';
    this.staffSelect.disabled = true;

    try {
      const params = new URLSearchParams();
      if (this.state.service) {
        params.append('service_id', this.state.service.id);
      }

      const response = await fetch(`${this.apiBase}/staff?${params}`);
      const staff = await response.json();

      staff.forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = s.name;
        this.staffSelect.appendChild(option);
      });

      this.staffSelect.disabled = false;

    } catch (error) {
      console.error('Error loading staff:', error);
      this.showToast('Failed to load staff members.', 'error');
    }
  }

  /**
   * Load available time slots
   */
  async loadTimeSlots() {
    if (!this.timeSlotsContainer || !this.state.service || !this.state.staff || !this.state.date) {
      return;
    }

    this.showLoading(true);

    try {
      const params = new URLSearchParams({
        date: this.state.date,
        staff_id: this.state.staff,
        service_id: this.state.service.id
      });

      const response = await fetch(`${this.apiBase}/slots?${params}`);
      const data = await response.json();

      if (data.error) {
        this.renderNoSlots(data.error);
        return;
      }

      this.renderTimeSlots(data.slots);

    } catch (error) {
      console.error('Error loading slots:', error);
      this.showToast('Failed to load available times.', 'error');
    } finally {
      this.showLoading(false);
    }
  }

  /**
   * Render time slots
   */
  renderTimeSlots(slots) {
    if (!this.timeSlotsContainer) return;

    this.timeSlotsContainer.innerHTML = '';

    if (!slots || slots.length === 0) {
      this.timeSlotsContainer.innerHTML = `
        <div class="no-slots-message">
          <p>No available times for this date.</p>
          <p>Please select another date or staff member.</p>
        </div>
      `;
      return;
    }

    const grid = document.createElement('div');
    grid.className = 'time-slots-grid';

    slots.forEach(slot => {
      const btn = document.createElement('button');
      btn.className = 'time-slot';
      btn.textContent = slot;
      btn.dataset.time = slot;

      btn.addEventListener('click', () => this.selectTimeSlot(btn, slot));
      grid.appendChild(btn);
    });

    this.timeSlotsContainer.appendChild(grid);
  }

  /**
   * Render no slots message
   */
  renderNoSlots(message) {
    if (!this.timeSlotsContainer) return;

    this.timeSlotsContainer.innerHTML = `
      <div class="no-slots-message">
        <p>${this.escapeHtml(message)}</p>
      </div>
    `;
  }

  /**
   * Select a time slot
   */
  selectTimeSlot(btn, time) {
    document.querySelectorAll('.time-slot').forEach(b => {
      b.classList.remove('selected');
    });

    btn.classList.add('selected');
    this.state.time = time;

    // Update button state
    if (this.nextBtn) {
      this.nextBtn.disabled = false;
    }
  }

  /**
   * Validate step 1
   */
  validateStep1() {
    return this.state.service !== null;
  }

  /**
   * Validate step 2
   */
  validateStep2() {
    return this.state.staff !== null && this.state.date && this.state.time;
  }

  /**
   * Validate step 3 (client details)
   */
  validateStep3() {
    // Step 3 doesn't have validation - just review
    return true;
  }

  /**
   * Validate step 4 (final validation before submit)
   */
  validateStep4() {
    if (!this.clientNameInput || !this.phoneInput) return false;

    const nameValid = this.state.clientName.length >= 2;
    const phoneValid = this.validatePhone(this.state.phone);

    // Update input styles
    this.clientNameInput.classList.toggle('error', !nameValid);
    this.phoneInput.classList.toggle('error', !phoneValid);

    // Show/hide error messages
    const nameError = document.getElementById('name-error');
    const phoneError = document.getElementById('phone-error');

    if (nameError) {
      nameError.classList.toggle('visible', !nameValid);
    }
    if (phoneError) {
      phoneError.classList.toggle('visible', !phoneValid);
    }

    // Update button
    if (this.submitBtn) {
      this.submitBtn.disabled = !(nameValid && phoneValid);
    }

    return nameValid && phoneValid;
  }

  /**
   * Validate phone number
   */
  validatePhone(phone) {
    const cleaned = phone.replace(/[\s\-]/g, '');
    const pattern = /^(?:\+?27|0)?[0-9]{9,10}$/;
    return pattern.test(cleaned);
  }

  /**
   * Handle next button click
   */
  handleNext() {
    switch (this.state.step) {
      case 1:
        if (this.validateStep1()) {
          this.showStep(2);
        } else {
          this.showToast('Please select a service.', 'error');
        }
        break;

      case 2:
        if (this.validateStep2()) {
          this.updateReviewSummary();
          this.showStep(3);
        } else {
          this.showToast('Please complete all selections.', 'error');
        }
        break;

      case 3:
        this.showStep(4);
        break;

      case 4:
        this.handleSubmit();
        break;
    }
  }

  /**
   * Handle back button click
   */
  handleBack() {
    if (this.state.step > 1) {
      this.showStep(this.state.step - 1);
    }
  }

  /**
   * Update review summary
   */
  updateReviewSummary() {
    if (!this.bookingSummary) return;

    const staffSelect = this.staffSelect;
    const staffName = staffSelect.options[staffSelect.selectedIndex]?.text || 'Staff';

    this.bookingSummary.innerHTML = `
      <div class="summary-row">
        <span class="summary-label">Service</span>
        <span class="summary-value">${this.escapeHtml(this.state.service.name)}</span>
      </div>
      <div class="summary-row">
        <span class="summary-label">Staff</span>
        <span class="summary-value">${this.escapeHtml(staffName)}</span>
      </div>
      <div class="summary-row">
        <span class="summary-label">Date</span>
        <span class="summary-value">${this.formatDate(this.state.date)}</span>
      </div>
      <div class="summary-row">
        <span class="summary-label">Time</span>
        <span class="summary-value">${this.state.time}</span>
      </div>
      <div class="summary-row">
        <span class="summary-label">Duration</span>
        <span class="summary-value">${this.formatDuration(this.state.service.duration)}</span>
      </div>
      <div class="summary-row">
        <span class="summary-label">Price</span>
        <span class="summary-value summary-total">R${this.state.service.price.toFixed(2)}</span>
      </div>
    `;
  }

  /**
   * Handle form submission
   */
  async handleSubmit() {
    if (!this.validateStep4()) {
      this.showToast('Please fill in all required fields correctly.', 'error');
      return;
    }

    this.showLoading(true);

    try {
      const staffSelect = this.staffSelect;
      const hour = parseInt(this.state.time.split(':')[0]);

      const bookingData = {
        client_name: this.state.clientName,
        phone: this.state.phone,
        service_id: this.state.service.id,
        staff_id: this.state.staff,
        date: this.state.date,
        hour: hour,
        notes: this.state.notes
      };

      const response = await fetch(`${this.apiBase}/book`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(bookingData)
      });

      const result = await response.json();

      if (response.ok && result.success) {
        this.showConfirmation(result.booking);
      } else {
        this.showToast(result.error || 'Booking failed. Please try again.', 'error');
      }

    } catch (error) {
      console.error('Booking error:', error);
      this.showToast('An error occurred. Please try again.', 'error');
    } finally {
      this.showLoading(false);
    }
  }

  /**
   * Show confirmation screen
   */
  showConfirmation(booking) {
    this.showStep(5);

    if (this.confirmationScreen) {
      this.confirmationScreen.classList.remove('hidden');
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /**
   * Reset booking for another appointment
   */
  resetBooking() {
    this.state = {
      step: 1,
      service: null,
      staff: null,
      date: null,
      time: null,
      clientName: '',
      phone: '',
      notes: ''
    };

    // Reset form elements
    if (this.clientNameInput) this.clientNameInput.value = '';
    if (this.phoneInput) this.phoneInput.value = '';
    if (this.notesInput) this.notesInput.value = '';
    if (this.dateInput) this.dateInput.value = '';

    // Reset service cards
    document.querySelectorAll('.service-card').forEach(c => {
      c.classList.remove('selected');
    });

    // Reset time slots
    if (this.timeSlotsContainer) {
      this.timeSlotsContainer.innerHTML = '';
    }

    // Hide confirmation
    if (this.confirmationScreen) {
      this.confirmationScreen.classList.add('hidden');
    }

    // Show step 1
    this.showStep(1);
  }

  /**
   * Show loading overlay
   */
  showLoading(show) {
    if (this.loadingOverlay) {
      this.loadingOverlay.classList.toggle('visible', show);
    }
  }

  /**
   * Show toast notification
   */
  showToast(message, type = 'info') {
    if (!this.toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    this.toastContainer.appendChild(toast);

    // Auto remove after 4 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-20px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  /**
   * Format duration for display
   */
  formatDuration(duration) {
    if (duration >= 1) {
      return duration === 1 ? '1 hour' : `${duration} hours`;
    } else {
      const minutes = Math.round(duration * 60);
      return `${minutes} min`;
    }
  }

  /**
   * Format date for display
   */
  formatDate(dateStr) {
    try {
      const date = new Date(dateStr + 'T00:00:00');
      return date.toLocaleDateString('en-ZA', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  }

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Open modal
   */
  openModal(modal) {
    if (modal) {
      modal.classList.add('visible');
      document.body.style.overflow = 'hidden';
    }
  }

  /**
   * Close modal
   */
  closeModal(modal) {
    if (modal) {
      modal.classList.remove('visible');
      document.body.style.overflow = '';
    }
  }
}

// Initialize booking system when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.bookingSystem = new BookingSystem();
});
