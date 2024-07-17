// Get all navigation links
const navLinks = document.querySelectorAll('.nav-link');

// Function to add active class to the link corresponding to the section in view
function highlightActiveLink() {
    const scrollPosition = window.scrollY;

    // Loop through each section and check if it is in view
    document.querySelectorAll('section').forEach(section => {
        const top = section.offsetTop - 100; // Adjusted for header height
        const bottom = top + section.offsetHeight;

        if (scrollPosition >= top && scrollPosition < bottom) {
            // Get the corresponding navigation link by href
            const href = `#${section.id}`;
            const matchingLink = document.querySelector(`a[href="${href}"]`);

            // Remove active class from all links
            navLinks.forEach(link => link.classList.remove('active'));

            // Add active class to the matching link
            if (matchingLink) {
                matchingLink.classList.add('active');
            }
        }
    });

    // Update header based on scroll position
    const header = document.querySelector('header');
    const scrollChangePosition = 400; // Adjust as needed

    if (scrollPosition >= scrollChangePosition) {
        header.classList.add('scrolled'); // Add class 'scrolled' to header
    } else {
        header.classList.remove('scrolled'); // Remove class 'scrolled' from header
    }
}

// Highlight active link on page load and scroll
document.addEventListener('DOMContentLoaded', () => {
    highlightActiveLink(); // Highlight on load

    window.addEventListener('scroll', () => {
        highlightActiveLink(); // Highlight on scroll
    });
});
