const renderDashboardChart = (totalExpenses, budget, difference) => {
    const ctx = document.getElementById('myDashboardChart').getContext('2d');
    
    // Set the size explicitly within the options
    const options = {
        responsive: true,
        maintainAspectRatio: false, // This line allows you to control the size
    };

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Total Expenses', 'Budget', 'Difference'],
            datasets: [{
                label: 'Expense vs Budget',
                data: [totalExpenses, budget, difference],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                ],
                borderWidth: 1,
            }],
        },
        options: options, // Apply the options
    });
};



document.onload = getDashboardData();
