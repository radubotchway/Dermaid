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


document.addEventListener('DOMContentLoaded', () => {
    const featuresSection = document.querySelector('.features');
    const steps = featuresSection.querySelectorAll('.step');
    const images = featuresSection.querySelectorAll('.images img');

    steps.forEach(step => {
        step.addEventListener('mouseover', () => {
            // Hide all images
            images.forEach(image => image.classList.remove('active'));
            
            // Show the corresponding image
            const imageId = step.getAttribute('data-image');
            featuresSection.querySelector(`#${imageId}`).classList.add('active');
        });

        // Optional: Hide the image when the mouse leaves the step
        step.addEventListener('mouseout', () => {
            const imageId = step.getAttribute('data-image');
            featuresSection.querySelector(`#${imageId}`).classList.remove('active');
        });
    });
});


//Gallery 
let currentIndex = 0;
const slides = document.querySelectorAll('.gallery-slide');
const dots = document.querySelectorAll('.nav-dot');

function showSlide(index) {
    slides.forEach((slide, idx) => {
        if (idx === index) {
            slide.classList.add('active');
        } else {
            slide.classList.remove('active');
        }
        slide.style.transform = `translateX(-${index * 100}%)`;
    });

    dots.forEach((dot, idx) => {
        if (idx === index) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

function nextSlide() {
    currentIndex = (currentIndex + 1) % slides.length;
    showSlide(currentIndex);
}

let startX;
let isDragging = false;
const gallery = document.querySelector('.gallery');

gallery.addEventListener('mousedown', (e) => {
    startX = e.pageX - gallery.offsetLeft;
    isDragging = true;
    gallery.style.cursor = 'grabbing';
});

gallery.addEventListener('mouseup', () => {
    isDragging = false;
    gallery.style.cursor = 'grab';
});

gallery.addEventListener('mouseleave', () => {
    isDragging = false;
    gallery.style.cursor = 'grab';
});

gallery.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    e.preventDefault();
    const x = e.pageX - gallery.offsetLeft;
    const walk = (x - startX) * 3; // Adjust the multiplier as needed
    gallery.scrollLeft -= walk;
    startX = x;
});

function currentSlide(n) {
    currentIndex = n - 1;
    showSlide(currentIndex);
}

document.querySelectorAll('.nav-dot').forEach((dot, index) => {
    dot.addEventListener('click', () => currentSlide(index + 1));
});

// Auto-slide functionality
setInterval(nextSlide, 5000); // Change slides every 5 seconds

// Initialize the first slide
showSlide(currentIndex);
