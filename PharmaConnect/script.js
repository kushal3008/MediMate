// Smooth scroll for navigation
const navLinks = document.querySelectorAll('.nav-links a');
navLinks.forEach(link => {
  link.addEventListener('click', function(e) {
    const targetId = this.getAttribute('href');
    if (targetId.startsWith('#')) {
      e.preventDefault();
      document.querySelector(targetId).scrollIntoView({
        behavior: 'smooth'
      });
    }
  });
});

// Contact form submission
const contactForm = document.getElementById('contactForm');
const formMessage = document.getElementById('formMessage');
if (contactForm) {
  contactForm.addEventListener('submit', function(e) {
    e.preventDefault();
    formMessage.textContent = 'Thank you for contacting us! We will get back to you soon.';
    formMessage.style.color = '#0a6cff';
    contactForm.reset();
  });
}

// Nav indicator logic
const navLinksList = document.querySelectorAll('.nav-links a');
const navIndicator = document.querySelector('.nav-indicator');

function updateIndicator(element) {
  if (!element) return;
  const rect = element.getBoundingClientRect();
  const navRect = element.parentElement.parentElement.getBoundingClientRect();
  navIndicator.style.width = rect.width + 'px';
  navIndicator.style.left = (rect.left - navRect.left) + 'px';
}

function setActiveLink(link) {
  navLinksList.forEach(l => l.classList.remove('active'));
  link.classList.add('active');
  updateIndicator(link);
}

// On click
navLinksList.forEach(link => {
  link.addEventListener('click', function() {
    setActiveLink(this);
  });
});

// On scroll - highlight section in view
const sectionIds = Array.from(navLinksList).map(link => link.getAttribute('href'));
const sections = sectionIds.map(id => document.querySelector(id));

const observerOptions = {
  root: null,
  rootMargin: '0px',
  threshold: 0.6
};

const observer = new window.IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = '#' + entry.target.id;
      const activeLink = Array.from(navLinksList).find(link => link.getAttribute('href') === id);
      if (activeLink) setActiveLink(activeLink);
    }
  });
}, observerOptions);

sections.forEach(section => {
  if (section) observer.observe(section);
});

// On load, set indicator to first link
window.addEventListener('DOMContentLoaded', () => {
  setActiveLink(navLinksList[0]);
});

window.addEventListener('resize', () => {
  const active = document.querySelector('.nav-links a.active');
  if (active) updateIndicator(active);
}); 