const renderDashboardChart = (budget, totalExpenses, difference) => {
    const ctx = document.getElementById('myDashboardChart').getContext('2d');
    
    // Set the size explicitly within the options
    const options = {
        responsive: true,
        maintainAspectRatio: false, // This line allows you to control the size
        scales: {
            y: {
                 suggestedMin: 0, // Set the suggested minimum value for the y-axis to 0
            },
        },
    
    };

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Budget', 'Spent', 'Remaining limit'],
            datasets: [{
                label: 'Spent vs Budget',
                data: [budget, totalExpenses, difference],
                backgroundColor: [
                'rgba(0, 0, 139, 0.65)',  // Dark Blue
                'rgba(139, 0, 0, 0.8)',  // Dark Red
                'rgba(0, 100, 0, 0.8)',  // Dark Green
                ],
                borderColor: [
                'rgba(0, 0, 139, 0.65)',  // Dark Blue
                'rgba(139, 0, 0, 0.8)',  // Dark Red
                'rgba(0, 100, 0, 0.8)',  // Dark Green
                ],

                borderWidth: 1,
            }],
        },
        options: options, // Apply the options
    });
};



document.onload = getDashboardData();
