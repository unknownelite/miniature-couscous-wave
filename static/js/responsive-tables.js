// Responsive table handling
function handleResponsiveTables() {
  if (window.innerWidth <= 400) {
    document.querySelectorAll('table').forEach(table => {
      if (!table.classList.contains('responsive-enabled')) {
        table.classList.add('responsive-enabled');
        const headers = [];
        table.querySelectorAll('th').forEach(header => {
          headers.push(header.textContent);
        });
        
        table.querySelectorAll('td').forEach((cell, index) => {
          const headerIndex = index % headers.length;
          cell.setAttribute('data-label', headers[headerIndex]);
        });
      }
    });
  } else {
    document.querySelectorAll('table.responsive-enabled').forEach(table => {
      table.classList.remove('responsive-enabled');
      table.querySelectorAll('td').forEach(cell => {
        cell.removeAttribute('data-label');
      });
    });
  }
}

// Run on load and resize
document.addEventListener('DOMContentLoaded', handleResponsiveTables);
window.addEventListener('resize', function() {
  clearTimeout(this.resizeTimer);
  this.resizeTimer = setTimeout(handleResponsiveTables, 250);
});