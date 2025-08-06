document.addEventListener('DOMContentLoaded', function() {
    // Tìm tất cả các input có class 'month-picker'
    flatpickr(".month-picker", {
        // Kích hoạt plugin chọn tháng
        plugins: [
            new monthSelectPlugin({
                shorthand: true, 
                dateFormat: "Y-m-d", 
                altFormat: "m/Y", 
                altInput: true, 
            })
        ]
    });
});
