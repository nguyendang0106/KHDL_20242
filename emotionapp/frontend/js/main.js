document.addEventListener('DOMContentLoaded', () => {
    const pages = document.querySelectorAll('.page');
    const navButtons = document.querySelectorAll('[data-targetpage]');
    const themeToggleButton = document.getElementById('theme-toggle-btn');
    let currentPageId = null;
    let activeModule = null;

    // Initialize background effects
    if (document.getElementById('interactive-background') && typeof EffectsModule !== 'undefined' && EffectsModule.init) {
        EffectsModule.init();
    } else {
        console.warn('EffectsModule not initialized or #interactive-background canvas missing.');
    }

    function showPage(pageId) {
        if (currentPageId === pageId && activeModule && pageId !== 'page-landing') return;

        if (activeModule && activeModule.cleanup) {
            activeModule.cleanup();
        }
        // Explicitly stop webcam if navigating away from its page
        if (currentPageId === 'page-webcam' && pageId !== 'page-webcam' && typeof WebcamModule !== 'undefined' && WebcamModule.stop) {
            WebcamModule.stop();
        }

        pages.forEach(page => {
            page.classList.toggle('active', page.id === pageId);
        });

        currentPageId = pageId;
        activeModule = null; // Reset active module

        if (pageId === 'page-webcam' && typeof WebcamModule !== 'undefined' && WebcamModule.init) {
            WebcamModule.init();
            activeModule = WebcamModule;
        } else if (pageId === 'page-video-upload' && typeof VideoModule !== 'undefined' && VideoModule.init) {
            VideoModule.init();
            activeModule = VideoModule;
        }
        // Scroll to top of main content area on page change
        const mainContent = document.getElementById('main-content');
        if (mainContent) mainContent.scrollTop = 0;
    }

    navButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPageId = button.dataset.targetpage;
            if (targetPageId) {
                showPage(targetPageId);
            }
        });
    });

    // Theme Toggle Logic
    if (themeToggleButton) {
        function updateThemeButton(theme) {
            const iconClass = theme === 'light' ? 'fa-moon' : 'fa-sun';
            const text = theme === 'light' ? ' Dark Mode' : ' Light Mode'; // Note leading space
            themeToggleButton.innerHTML = `<i class="fas ${iconClass}"></i>${text}`;
        }

        function applyTheme(theme) {
            document.body.classList.toggle('light-mode', theme === 'light');
            updateThemeButton(theme);
            localStorage.setItem('theme', theme);
            if (typeof EffectsModule !== 'undefined' && EffectsModule.updateTheme) {
                EffectsModule.updateTheme(theme);
            }
        }

        themeToggleButton.addEventListener('click', () => {
            const currentThemeIsLight = document.body.classList.contains('light-mode');
            applyTheme(currentThemeIsLight ? 'dark' : 'light');
        });

        const savedTheme = localStorage.getItem('theme') || 'dark'; // Default to dark
        applyTheme(savedTheme);

    } else {
        console.warn("Theme toggle button #theme-toggle-btn not found.");
    }

    // Initial page load
    const initialPage = 'page-landing';
    showPage(initialPage);
});