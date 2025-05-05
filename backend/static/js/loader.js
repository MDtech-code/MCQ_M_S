let isNavigating = false;

document.addEventListener('DOMContentLoaded', function() {
  const loader = document.getElementById('loader');
  const mainContent = document.getElementById('main-content');

  // Only show loader for direct loads (not after navigation)
  if (!isNavigating && !loader.classList.contains('active')) {
    console.log('Direct page load: Showing loader'); // Debug
    loader.classList.add('active');
    mainContent.classList.add('content-hidden');
  }

  // Hide loader when page is fully loaded
  window.addEventListener('load', function() {
    console.log('Page loaded: Hiding loader'); // Debug
    loader.classList.remove('active');
    mainContent.classList.remove('content-hidden');
    isNavigating = false; // Reset flag
  });

  // Intercept link clicks (GET requests)
  document.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', function(e) {
      if (!e.ctrlKey && !e.metaKey && link.getAttribute('href') && !link.getAttribute('href').startsWith('#') && !link.hasAttribute('hx-get')) {
        e.preventDefault(); // Prevent immediate navigation
        console.log('Link clicked:', link.getAttribute('href')); // Debug
        isNavigating = true; // Set navigation flag
        loader.classList.add('active');
        mainContent.classList.add('content-hidden');
        // Navigate after a minimal delay for rendering
        setTimeout(() => {
          window.location.href = link.getAttribute('href');
        }, 50);
      }
    });
  });

  // Intercept form submissions (POST requests)
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
      if (!form.hasAttribute('hx-post')) {
        console.log('Form submitted'); // Debug
        isNavigating = true; // Set navigation flag
        loader.classList.add('active');
        mainContent.classList.add('content-hidden');
      }
    });
  });

  // Intercept HTMX requests
  document.body.addEventListener('htmx:beforeRequest', function() {
    console.log('HTMX request started'); // Debug
    loader.classList.add('active');
    mainContent.classList.add('content-hidden');
  });
  document.body.addEventListener('htmx:afterRequest', function() {
    console.log('HTMX request completed'); // Debug
    loader.classList.remove('active');
    mainContent.classList.remove('content-hidden');
  });
});
// document.addEventListener('DOMContentLoaded', function() {
//   const loader = document.getElementById('loader');
//   const mainContent = document.getElementById('main-content');

//   // Show loader on page load
//   loader.classList.add('active');
//   mainContent.classList.add('content-hidden');

//   // Hide loader when page is fully loaded
//   window.addEventListener('load', function() {
//     setTimeout(() => {
//       loader.classList.remove('active');
//       mainContent.classList.remove('content-hidden');
//     }, 500); // Small delay for smoothness
//   });

//   // Intercept link clicks (GET requests)
//   document.querySelectorAll('a').forEach(link => {
//     link.addEventListener('click', function(e) {
//       if (!e.ctrlKey && !e.metaKey && link.getAttribute('href') && !link.getAttribute('href').startsWith('#')) {
//         loader.classList.add('active');
//         mainContent.classList.add('content-hidden');
//       }
//     });
//   });

//   // Intercept form submissions (POST requests)
//   document.querySelectorAll('form').forEach(form => {
//     form.addEventListener('submit', function() {
//       loader.classList.add('active');
//       mainContent.classList.add('content-hidden');
//     });
//   });

//   // Intercept HTMX requests
//   document.body.addEventListener('htmx:beforeRequest', function() {
//     loader.classList.add('active');
//     mainContent.classList.add('content-hidden');
//   });
//   document.body.addEventListener('htmx:afterRequest', function() {
//     setTimeout(() => {
//       loader.classList.remove('active');
//       mainContent.classList.remove('content-hidden');
//     }, 500);
//   });
// });