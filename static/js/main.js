// Main JavaScript file for Law Firm website

document.addEventListener('DOMContentLoaded', function() {
    initFloatingNavbar();
    initMegaMenus();
    initMobileNav();

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 4 seconds (4000ms)
    const alertDismissList = document.querySelectorAll('.alert-dismissible');
    alertDismissList.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 4000);
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
                
                // Mark as read via API if it was unread
                if (this.classList.contains('table-warning')) {
                    const messageId = this.getAttribute('data-message-id');
                    fetch(`/admin/messages/${messageId}/read`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                        },
                        body: JSON.stringify({})
                    }).catch(err => console.error('Failed to mark message read:', err));

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

function initFloatingNavbar() {
    var floatWrap = document.getElementById('doaNavbarFloat');
    var spacer = document.getElementById('doaNavbarSpacer');
    if (!floatWrap) return;

    var desktopQuery = window.matchMedia('(min-width: 1200px)');

    function clearDesktopNavState() {
        floatWrap.classList.remove('is-scrolled', 'is-fixed');
        if (spacer) {
            spacer.classList.remove('is-active');
        }
    }

    function onScroll() {
        if (!desktopQuery.matches) {
            clearDesktopNavState();
            return;
        }

        var scrolled = window.scrollY > 40;
        floatWrap.classList.toggle('is-scrolled', scrolled);

        var shouldFix = scrolled;
        floatWrap.classList.toggle('is-fixed', shouldFix);
        if (spacer) {
            spacer.classList.toggle('is-active', shouldFix);
        }
    }

    desktopQuery.addEventListener('change', onScroll);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
}

function initMegaMenus() {
    var megaItems = document.querySelectorAll('.doa-nav-item.has-mega');
    if (!megaItems.length) return;

    var HOVER_OPEN_DELAY = 120;
    var HOVER_CLOSE_DELAY = 200;
    var openTimer = null;
    var closeTimer = null;

    function isDesktop() {
        return window.matchMedia('(min-width: 1200px)').matches;
    }

    function closeAll() {
        megaItems.forEach(function(item) {
            item.classList.remove('is-open');
        });
    }

    function scheduleOpen(item) {
        clearTimeout(closeTimer);
        clearTimeout(openTimer);
        openTimer = setTimeout(function() {
            if (!isDesktop()) return;
            closeAll();
            item.classList.add('is-open');
        }, HOVER_OPEN_DELAY);
    }

    function scheduleClose(item) {
        clearTimeout(openTimer);
        clearTimeout(closeTimer);
        closeTimer = setTimeout(function() {
            if (!isDesktop()) return;
            item.classList.remove('is-open');
        }, HOVER_CLOSE_DELAY);
    }

    megaItems.forEach(function(item) {
        var panel = item.querySelector('.doa-mega-panel');

        item.addEventListener('mouseenter', function() {
            scheduleOpen(item);
        });

        item.addEventListener('mouseleave', function() {
            scheduleClose(item);
        });

        if (panel) {
            panel.addEventListener('mouseenter', function() {
                clearTimeout(closeTimer);
            });
            panel.addEventListener('mouseleave', function() {
                scheduleClose(item);
            });
        }
    });

    document.addEventListener('click', function(e) {
        if (!e.target.closest('.doa-nav-item.has-mega')) {
            closeAll();
        }
    });

    window.addEventListener('resize', function() {
        closeAll();
    });

    var navbarCollapse = document.getElementById('navbarNav');
    if (navbarCollapse) {
        navbarCollapse.addEventListener('hidden.bs.collapse', closeAll);
    }
}

function initMobileNav() {
    var navbarCollapse = document.getElementById('navbarNav');
    if (!navbarCollapse) return;

    var desktopQuery = window.matchMedia('(min-width: 1200px)');

    function setMobileNavOpen(isOpen) {
        document.documentElement.classList.toggle('mobile-nav-open', isOpen);
        document.body.classList.toggle('mobile-nav-open', isOpen);
    }

    function hideMobileMenu() {
        if (desktopQuery.matches) return;
        var instance = bootstrap.Collapse.getInstance(navbarCollapse);
        if (instance) {
            instance.hide();
        } else if (navbarCollapse.classList.contains('show')) {
            navbarCollapse.classList.remove('show');
        }
    }

    navbarCollapse.addEventListener('show.bs.collapse', function() {
        if (!desktopQuery.matches) {
            setMobileNavOpen(true);
        }
    });

    navbarCollapse.addEventListener('hidden.bs.collapse', function() {
        setMobileNavOpen(false);
    });

    navbarCollapse.querySelectorAll('.doa-nav-trigger').forEach(function(link) {
        link.addEventListener('click', function() {
            if (!desktopQuery.matches) {
                hideMobileMenu();
            }
        });
    });

    desktopQuery.addEventListener('change', function() {
        setMobileNavOpen(false);
        hideMobileMenu();
    });
}

// Confirmation dialogs for delete actions
function confirmDelete(formId, itemName) {
    if (confirm(`Are you sure you want to delete this ${itemName}? This action cannot be undone.`)) {
        document.getElementById(formId).submit();
    }
    return false;
}
