// Main JavaScript file for Law Firm website

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // For service filtering on case studies page
    const serviceFilter = document.getElementById('serviceFilter');
    if (serviceFilter) {
        serviceFilter.addEventListener('change', function() {
            const serviceId = this.value;
            const caseStudies = document.querySelectorAll('.case-study-item');
            
            if (serviceId === 'all') {
                // Show all case studies
                caseStudies.forEach(study => {
                    study.style.display = 'block';
                });
            } else {
                // Filter case studies by service
                caseStudies.forEach(study => {
                    const studyServiceId = study.getAttribute('data-service-id');
                    study.style.display = (studyServiceId === serviceId || (!studyServiceId && serviceId === 'none')) ? 'block' : 'none';
                });
            }
        });
    }

    // Slug generator for admin forms
    const titleInputs = document.querySelectorAll('.slug-source');
    titleInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const slugField = document.querySelector('.slug-target');
            if (slugField && !slugField.value) {
                // Generate slug from title
                const slug = this.value.toLowerCase()
                    .replace(/[^\w\s-]/g, '') // Remove special characters
                    .replace(/\s+/g, '-')     // Replace spaces with hyphens
                    .replace(/-+/g, '-');     // Replace multiple hyphens with single hyphen
                
                slugField.value = slug;
            }
        });
    });
    
    // Contact form service selection
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        const serviceSelect = document.getElementById('service');
        if (serviceSelect) {
            // Set default value if coming from a service page
            const urlParams = new URLSearchParams(window.location.search);
            const serviceParam = urlParams.get('service');
            if (serviceParam) {
                serviceSelect.value = serviceParam;
            }
        }
    }
    
    // Message read toggle in admin
    const messageRows = document.querySelectorAll('.message-row');
    messageRows.forEach(row => {
        row.addEventListener('click', function() {
            const messageId = this.getAttribute('data-message-id');
            const detailsSection = document.getElementById(`message-details-${messageId}`);
            
            if (detailsSection) {
                // Toggle message details visibility
                const allDetails = document.querySelectorAll('.message-details');
                allDetails.forEach(detail => {
                    if (detail.id !== `message-details-${messageId}`) {
                        detail.classList.add('d-none');
                    }
                });
                
                detailsSection.classList.toggle('d-none');
                
                // Mark as read if it was unread
                if (this.classList.contains('table-warning')) {
                    this.classList.remove('table-warning');
                    
                    // Update unread count in badge
                    const unreadBadge = document.querySelector('.unread-count');
                    if (unreadBadge) {
                        let count = parseInt(unreadBadge.textContent) - 1;
                        if (count < 0) count = 0;
                        unreadBadge.textContent = count;
                        
                        if (count === 0) {
                            unreadBadge.classList.add('d-none');
                        }
                    }
                }
            }
        });
    });
});

// Confirmation dialogs for delete actions
function confirmDelete(formId, itemName) {
    if (confirm(`Are you sure you want to delete this ${itemName}? This action cannot be undone.`)) {
        document.getElementById(formId).submit();
    }
    return false;
}
