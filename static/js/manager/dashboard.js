const canvas = document.getElementById('roomsPieChart');
const occupied = parseInt(canvas.dataset.occupied);
const total = parseInt(canvas.dataset.total);
const empty = total - occupied;

const ctx = canvas.getContext('2d');

new Chart(ctx, {
    type: 'pie',
    data: {
        labels: ['Đã thuê', 'Còn trống'],
        datasets: [{
            data: [occupied, empty],
            backgroundColor: ['rgba(75, 192, 192, 0.6)', 'rgba(255, 99, 132, 0.6)'],
            borderColor: ['rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)'],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'right',
                align: 'center',
                labels: {
                    boxWidth: 20,
                    padding: 15
                }
            }
        }
    }
});

const moneyCanvas = document.getElementById('moneyPieChart');
const paid = parseFloat(moneyCanvas.dataset.paid);
const totalMoney = parseFloat(moneyCanvas.dataset.total);
const unpaid = totalMoney - paid;

const moneyCtx = moneyCanvas.getContext('2d');

new Chart(moneyCtx, {
    type: 'pie',
    data: {
        labels: ['Đã trả', 'Chưa trả'],
        datasets: [{
            data: [paid, unpaid],
            backgroundColor: ['rgba(54, 162, 235, 0.6)', 'rgba(255, 159, 64, 0.6)'],
            borderColor: ['rgba(54, 162, 235, 1)', 'rgba(255, 159, 64, 1)'],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'right',
                align: 'center',
                labels: {
                    boxWidth: 20,
                    padding: 15
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        // Format số tiền có dấu phẩy
                        let value = context.raw;
                        return value.toLocaleString('vi-VN') + ' VND';
                    }
                }
            }
        }
    }
});

const billsCanvas = document.getElementById('billsPieChart');
const paidBills = parseInt(billsCanvas.dataset.paid);
const totalBills = parseInt(billsCanvas.dataset.total);
const unpaidBills = totalBills - paidBills;

const billsCtx = billsCanvas.getContext('2d');

new Chart(billsCtx, {
    type: 'pie',
    data: {
        labels: ['Đã trả', 'Chưa trả'],
        datasets: [{
            data: [paidBills, unpaidBills],
            backgroundColor: ['rgba(0, 200, 83, 0.6)', 'rgba(244, 67, 54, 0.6)'],
            borderColor: ['rgba(0, 200, 83, 1)', 'rgba(244, 67, 54, 1)'],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'right',
                align: 'center',
                labels: {
                    boxWidth: 20,
                    padding: 15
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let value = context.raw;
                        return value.toLocaleString('vi-VN') + ' hóa đơn';
                    }
                }
            }
        }
    }
});

const current_6_month_bill_canvas = document.getElementById("billsBarChart");

// Lấy dữ liệu từ data-* attributes
const barLabels = JSON.parse(current_6_month_bill_canvas.dataset.labels);
const barValues = JSON.parse(current_6_month_bill_canvas.dataset.values);

const current_6_month_bill_ctx = current_6_month_bill_canvas.getContext("2d");

new Chart(current_6_month_bill_ctx, {
    type: "bar",
    data: {
        labels: barLabels,
        datasets: [{
            label: "Tổng tiền hóa đơn",
            data: barValues,
            backgroundColor: "rgba(54, 162, 235, 0.6)",
            borderColor: "rgba(54, 162, 235, 1)",
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { display: false }
        },
        scales: {
            y: { beginAtZero: true }
        }
    }
});
