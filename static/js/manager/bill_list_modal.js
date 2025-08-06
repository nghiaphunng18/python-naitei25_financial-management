document.addEventListener('DOMContentLoaded', function() {
        // --- PHẦN KÍCH HOẠT FLATPICKR ---
        // Script này sẽ tìm tất cả input có class 'month-picker' và biến chúng thành bộ chọn tháng
        flatpickr(".month-picker", {
            plugins: [
                new monthSelectPlugin({
                    shorthand: true,
                    dateFormat: "Y-m-d", // Luôn gửi đi định dạng YYYY-MM-DD
                    altFormat: "F Y",
                    altInput: true,
                })
            ],
        });

        // --- PHẦN LOGIC MỚI CHO MODAL TẠO HÓA ĐƠN ---
        const monthSelectorModal = document.getElementById('bill_month_selector_modal');
        if(monthSelectorModal) {
            const ewBillMonthInput = document.getElementById('form-ew-bill-month-modal');
            const servicesBillMonthInput = document.getElementById('form-services-bill-month-modal');
            const ewBillButton = document.querySelector('#form-ew-bill-modal button');
            const servicesBillButton = document.querySelector('#form-services-bill-modal button');

            // Dùng onchange trên input gốc của Flatpickr
            const flatpickrInstance = monthSelectorModal._flatpickr;
            flatpickrInstance.config.onChange.push(function(selectedDates, dateStr, instance) {
                const selectedMonth = instance.input.value; // Lấy giá trị YYYY-MM-DD
                
                if (selectedMonth) {
                    if(ewBillMonthInput) ewBillMonthInput.value = selectedMonth;
                    if(servicesBillMonthInput) servicesBillMonthInput.value = selectedMonth;
                    if(ewBillButton) ewBillButton.disabled = false;
                    if(servicesBillButton) servicesBillButton.disabled = false;
                } else {
                    if(ewBillMonthInput) ewBillMonthInput.value = '';
                    if(servicesBillMonthInput) servicesBillMonthInput.value = '';
                    if(ewBillButton) ewBillButton.disabled = true;
                    if(servicesBillButton) servicesBillButton.disabled = true;
                }
            });
        }
    });
