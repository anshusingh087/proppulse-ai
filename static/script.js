let chartInstance = null;

// Fetch previous searches from the SQLite database
async function fetchHistory() {
    try {
        const res = await fetch('/get_history');
        const data = await res.json();
        const feed = document.getElementById('history-feed');
        feed.innerHTML = '';

        if (!data.history || data.history.length === 0) {
            feed.innerHTML = '<span style="color:#64748b; font-size:11px;">No valuation history found.</span>';
            return;
        }

        data.history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerHTML = `
                <span><strong>${item.location}</strong> (${item.sqft} sqft, ${item.bhk} BHK)</span>
                <span style="color:#f59e0b; font-weight:600;">${item.price}</span>
            `;
            feed.appendChild(div);
        });
    } catch(err) {
        console.error("History fetch error:", err);
    }
}

// Handle form submission and update dashboard
document.getElementById('prop-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const btn = document.getElementById('submit-btn');
    btn.innerText = "Processing Market Analytics...";
    btn.disabled = true;

    const formData = new FormData();
    formData.append('location', document.getElementById('location').value);
    formData.append('sqft', document.getElementById('sqft').value);
    formData.append('bhk', document.getElementById('bhk').value);
    formData.append('bath', document.getElementById('bath').value);
    formData.append('furnishing', document.getElementById('furnishing').value);

    try {
        const response = await fetch('/predict_analytics', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.status === 'success') {
            // Hide empty placeholder and show analytics panel
            document.getElementById('initial-state').classList.add('hidden');
            document.getElementById('analytics-content').classList.remove('hidden');

            // Populate metrics
            document.getElementById('out-price').innerText = data.price_lakhs;
            document.getElementById('out-tag').innerText = data.tag;
            document.getElementById('out-rent').innerText = data.monthly_rent;
            document.getElementById('out-yield').innerText = data.rental_yield;
            document.getElementById('out-emi').innerText = data.emi;

            // Populate locality insights
            document.getElementById('out-rate').innerText = data.rate_per_sqft + " / sqft";
            document.getElementById('out-metro').innerText = data.metro;
            document.getElementById('out-growth').innerText = data.growth;

            // Render interactive financing donut chart
            renderChart(data.principal_raw, data.interest_raw);

            // Refresh recent history table
            fetchHistory();
        }
    } catch (err) {
        alert("Failed to compute analytics.");
    } finally {
        btn.innerText = "Generate Valuation Analytics";
        btn.disabled = false;
    }
});

// Render Chart.js Donut Chart
function renderChart(principal, interest) {
    const ctx = document.getElementById('loanChart').getContext('2d');

    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Principal Loan (80%)', 'Total Payable Interest (20 Yrs)'],
            datasets: [{
                data: [principal, interest],
                backgroundColor: ['#3b82f6', '#f59e0b'],
                borderColor: '#111827',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#cbd5e1', font: { family: 'Plus Jakarta Sans', size: 12 } }
                }
            }
        }
    });
}

// Load initial history upon page load
window.onload = fetchHistory;