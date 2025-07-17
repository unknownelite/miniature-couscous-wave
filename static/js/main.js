// This would contain additional interactive elements for the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Copy wallet address functionality
    const copyButtons = document.querySelectorAll('.copy-address');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const address = this.parentElement.textContent.trim();
            navigator.clipboard.writeText(address).then(() => {
                const originalText = this.textContent;
                this.textContent = 'Copied!';
                setTimeout(() => {
                    this.textContent = originalText;
                }, 2000);
            });
        });
    });
    
    // File input display
    const fileInputs = document.querySelectorAll('.file-input');
    fileInputs.forEach(input => {
        const label = input.nextElementSibling;
        const fileName = label.nextElementSibling;
        
        input.addEventListener('change', function() {
            if (this.files.length > 0) {
                fileName.textContent = this.files[0].name;
            } else {
                fileName.textContent = '';
            }
        });
    });
    
    // Investment plan selection
    const planCards = document.querySelectorAll('.plan-card');
    planCards.forEach(card => {
        card.addEventListener('click', function() {
            planCards.forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
        });
    });

    // Animate plan cards on page load
document.addEventListener('DOMContentLoaded', function() {
    const planCards = document.querySelectorAll('.plan-card');
    planCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * index); // Stagger the animation
    });
});
    
    // Countdown timer for funding
    function startCountdown(duration, display) {
        let timer = duration, minutes, seconds;
        const interval = setInterval(function () {
            minutes = parseInt(timer / 60, 10);
            seconds = parseInt(timer % 60, 10);
            
            minutes = minutes < 10 ? "0" + minutes : minutes;
            seconds = seconds < 10 ? "0" + seconds : seconds;
            
            display.textContent = minutes + ":" + seconds;
            
            if (--timer < 0) {
                clearInterval(interval);
                display.textContent = "Expired";
            }
        }, 1000);
    }
    
    const countdownDisplay = document.getElementById('countdown');
    if (countdownDisplay) {
        startCountdown(600, countdownDisplay); // 10 minutes
    }
    
    // Chart for dashboard
    const ctx = document.getElementById('balanceChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Investment Growth',
                    data: [500, 800, 1200, 1500, 2000, 2500],
                    borderColor: '#ffd700',
                    backgroundColor: 'rgba(255, 215, 0, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#aaa'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#aaa'
                        }
                    }
                }
            }
        });
    }
});