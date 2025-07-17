document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');
    const dashboardSidebar = document.getElementById('dashboard-sidebar');
    const dashboardMain = document.getElementById('dashboard-main');
    
    // Create overlay element
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);
    
    // Toggle sidebar
    function toggleSidebar() {
        dashboardSidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
    
    // Open sidebar
    mobileMenuBtn.addEventListener('click', toggleSidebar);
    
    // Close sidebar
    closeSidebarBtn.addEventListener('click', toggleSidebar);
    
    // Close sidebar when clicking outside
    overlay.addEventListener('click', toggleSidebar);
    
    // Close sidebar when clicking on a nav item (optional)
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                toggleSidebar();
            }
        });
    });
});