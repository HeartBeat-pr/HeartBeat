// ==========================================
// HEARTBEAT - Main JavaScript
// ==========================================

// --- Mobile Menu Toggle ---
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('open');
}

// Close mobile menu when clicking a link
document.addEventListener('DOMContentLoaded', function () {
    const mobileLinks = document.querySelectorAll('.nav-mobile-link');
    mobileLinks.forEach(function (link) {
        link.addEventListener('click', function () {
            const menu = document.getElementById('mobileMenu');
            if (menu) {
                menu.classList.remove('open');
            }
        });
    });

    // --- Active Nav Link Highlighting ---
    const currentPath = window.location.pathname;

    // Desktop nav links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(function (link) {
        // Remove all active/highlight states
        link.classList.remove('active', 'nav-link-highlight');

        // Check if this link matches the current page
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('nav-link-highlight');
        }
    });

    // Mobile nav links
    const mobileNavLinks = document.querySelectorAll('.nav-mobile-link');
    mobileNavLinks.forEach(function (link) {
        link.classList.remove('active');

        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Bottom nav links
    const bottomNavLinks = document.querySelectorAll('.bottom-nav-item');
    bottomNavLinks.forEach(function (link) {
        link.classList.remove('active');

        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});
