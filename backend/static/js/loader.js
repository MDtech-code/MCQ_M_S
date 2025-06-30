let isNavigating = false;

document.addEventListener('DOMContentLoaded', function() {
  const loader = document.getElementById('spinner-overlay'); // Use spinner-overlay from test_list.html
  const mainContent = document.getElementById('main-content'); // Keep for compatibility with other pages

  // Check if loader exists before manipulating
  if (!loader) {
    console.warn('Loader element (spinner-overlay) not found on this page');
    return; // Exit early to prevent errors
  }

  // Only show loader for direct loads (not after navigation)
  if (!isNavigating && !loader.classList.contains('active')) {
    console.log('Direct page load: Showing loader');
    loader.style.display = 'flex'; // Use style.display to match test_list.html
    if (mainContent) {
      mainContent.classList.add('content-hidden');
    }
  }

  // Hide loader when page is fully loaded
  window.addEventListener('load', function() {
    console.log('Page loaded: Hiding loader');
    loader.style.display = 'none';
    if (mainContent) {
      mainContent.classList.remove('content-hidden');
    }
    isNavigating = false;
  });

  // Intercept link clicks (GET requests), excluding modal triggers
  document.querySelectorAll('a:not([data-bs-toggle="modal"])').forEach(link => {
    link.addEventListener('click', function(e) {
      if (!e.ctrlKey && !e.metaKey && link.getAttribute('href') && !link.getAttribute('href').startsWith('#') && !link.hasAttribute('hx-get')) {
        e.preventDefault();
        console.log('Link clicked:', link.getAttribute('href'));
        isNavigating = true;
        loader.style.display = 'flex';
        if (mainContent) {
          mainContent.classList.add('content-hidden');
        }
        // Navigate without delay to avoid unload issues
        window.location.href = link.getAttribute('href');
      }
    });
  });

  // Intercept form submissions (POST requests), excluding modal forms
  document.querySelectorAll('form:not(#modal-start-test-form)').forEach(form => {
    form.addEventListener('submit', function(e) {
      if (!form.hasAttribute('hx-post')) {
        console.log('Form submitted');
        isNavigating = true;
        loader.style.display = 'flex';
        if (mainContent) {
          mainContent.classList.add('content-hidden');
        }
      }
    });
  });

  // HTMX support (optional, keep only if HTMX is used)
  if (document.body.hasAttribute('hx-boost')) {
    document.body.addEventListener('htmx:beforeRequest', function() {
      console.log('HTMX request started');
      loader.style.display = 'flex';
      if (mainContent84) {
        mainContent.classList.add('content-hidden');
      }
    });
    document.body.addEventListener('htmx:afterRequest', function() {
      console.log('HTMX request completed');
      loader.style.display = 'none';
      if (mainContent) {
        mainContent.classList.remove('content-hidden');
      }
    });
  }
});// let isNavigating = false;

