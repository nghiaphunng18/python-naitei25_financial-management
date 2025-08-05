document.addEventListener('DOMContentLoaded', function() {
    const progressBar = document.getElementById('occupancy-progress');
    const width = progressBar.getAttribute('data-width');
    progressBar.style.width = width + '%';
});