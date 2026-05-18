// Dark Mode Toggle Script

// Toggle dark mode function (global)
function toggleDarkMode() {
  const body = document.body;
  const icon = document.getElementById('darkModeIcon');
  
  body.classList.toggle('dark-mode');
  
  if (body.classList.contains('dark-mode')) {
    icon.className = 'fas fa-sun';
    localStorage.setItem('theme', 'dark');
  } else {
    icon.className = 'fas fa-moon';
    localStorage.setItem('theme', 'light');
  }
}

// Apply saved theme on load
(function() {
  const currentTheme = localStorage.getItem('theme') || 'light';
  
  if (currentTheme === 'dark') {
    document.body.classList.add('dark-mode');
    const icon = document.getElementById('darkModeIcon');
    if (icon) icon.className = 'fas fa-sun';
  }
  
  // Keyboard shortcut: Ctrl+Shift+D
  document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.shiftKey && e.key === 'D') {
      e.preventDefault();
      toggleDarkMode();
    }
  });
})();
