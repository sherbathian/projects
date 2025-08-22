// filepath: /Users/tahir/dev-python/projects/core/project/static/project/js/dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    // Function to fetch data for the dashboard
    async function fetchDashboardData() {
        try {
            const response = await fetch('/api/dashboard-data/');
            const data = await response.json();
            renderCharts(data);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        }
    }

    // Function to render charts using Chart.js or any other chart library
    function renderCharts(data) {
        const ctxSaddqah = document.getElementById('saddqahChart').getContext('2d');
        const ctxProjectLedgers = document.getElementById('projectLedgersChart').getContext('2d');
        const ctxPartyProjectLedgers = document.getElementById('partyProjectLedgersChart').getContext('2d');

        // Example data structure for charts
        const saddqahData = {
            labels: data.saddqah.months,
            datasets: [{
                label: 'Saddqah Amount',
                data: data.saddqah.amounts,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        };

        const projectLedgersData = {
            labels: data.projectLedgers.months,
            datasets: [{
                label: 'Paid Amount',
                data: data.projectLedgers.paidAmounts,
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }, {
                label: 'Received Amount',
                data: data.projectLedgers.receivedAmounts,
                backgroundColor: 'rgba(255, 159, 64, 0.2)',
                borderColor: 'rgba(255, 159, 64, 1)',
                borderWidth: 1
            }]
        };

        const partyProjectLedgersData = {
            labels: data.partyProjectLedgers.months,
            datasets: [{
                label: 'Paid Amount',
                data: data.partyProjectLedgers.paidAmounts,
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }, {
                label: 'Received Amount',
                data: data.partyProjectLedgers.receivedAmounts,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        };

        new Chart(ctxSaddqah, {
            type: 'bar',
            data: saddqahData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        new Chart(ctxProjectLedgers, {
            type: 'line',
            data: projectLedgersData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        new Chart(ctxPartyProjectLedgers, {
            type: 'line',
            data: partyProjectLedgersData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Fetch data when the page loads
    fetchDashboardData();
});