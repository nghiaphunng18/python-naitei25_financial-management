function billingWorkspace() {
        return {
            isModalOpen: false,
            selectedMonth: '{{ selected_month|date:"Y-m-d" }}',
            modalData: {},
            
            get modalStatusText() {
                if (!this.modalData || !this.modalData.billing_status) return 'Đang tải...';

                // Lấy các giá trị trạng thái và chuyển thành chữ hoa để so sánh
                const billingStatus = this.modalData.billing_status.toUpperCase();
                const finalBillStatus = this.modalData.final_bill_status ? this.modalData.final_bill_status.toUpperCase() : null;

                if (finalBillStatus === 'PAID') return 'Đã thanh toán - Không thể chỉnh sửa';
                if (billingStatus === 'FINALIZED') return 'Đã chốt sổ - Không thể chỉnh sửa';
                if (billingStatus === 'READY_TO_FINALIZE') return 'Sẵn sàng để tổng hợp';
                if (billingStatus === 'PENDING_CONFIRMATION') return 'Đang chờ cư dân xác nhận';
                if (billingStatus === 'IN_PROGRESS') return 'Đang ghi nhận hóa đơn nháp';
                if (billingStatus === 'NOT_STARTED') return 'Chưa có hóa đơn nháp';
                
                return 'Không xác định'; // Trường hợp dự phòng
            },
            
            // Getter để tự động nhóm và đếm dịch vụ
            get summarizedServices() {
                if (!this.modalData.subscribed_services) return [];
                
                const summary = {};
                this.modalData.subscribed_services.forEach(service => {
                    if (!summary[service.service_id]) {
                        summary[service.service_id] = { ...service, quantity: 0, total_cost: 0 };
                    }
                    summary[service.service_id].quantity += 1;
                    summary[service.service_id].total_cost += service.cost;
                });
                return Object.values(summary);
            },

            openModal(jsonString) {
                this.modalData = JSON.parse(jsonString); 
                this.isModalOpen = true;
            },
            closeModal() { this.isModalOpen = false; },
            
            // Hàm xử lý AJAX để thêm dịch vụ
            addService(event) {
                console.log("addService function called.");
                
                const form = event.target;
                const formData = new FormData(form);
                const csrfToken = formData.get('csrfmiddlewaretoken');
                
                if (!formData.get('service')) {
                    alert('Vui lòng chọn một dịch vụ.');
                    return;
                }
                
                console.log("Form data to be sent:", Object.fromEntries(formData));

                const url = "{% url 'add_adhoc_service' %}";
                
                fetch(url, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Cập nhật lại dữ liệu trong modal mà không cần tải lại trang
                        this.modalData.subscribed_services = data.updated_services_summary;
                        this.modalData.services_draft_pk = data.services_draft_pk;
                        form.querySelector('select[name="service"]').value = ''; // Reset dropdown
                    } else {
                        alert('Lỗi: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Fetch Error:', error);
                    alert('Đã có lỗi kết nối xảy ra. Vui lòng kiểm tra Console (F12).');
                });
            },
            // Hàm xử lý AJAX để xóa dịch vụ
            removeService(serviceId) {
                if (!confirm('Bạn có chắc muốn xóa dịch vụ này?')) return;

                const draftPk = this.modalData.services_draft_pk;
                if (!draftPk) {
                    alert('Không tìm thấy hóa đơn nháp để xóa dịch vụ.');
                    return;
                }
                
                // Tạo URL động
                const url = `{% url 'remove_service_from_draft' pk=9999 %}`.replace('9999', draftPk);
                
                const formData = new FormData();
                formData.append('service_id', serviceId);
                formData.append('csrfmiddlewaretoken', '{{ csrf_token }}');

                fetch(url, { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Cập nhật lại dữ liệu trong modal mà không cần tải lại trang
                        window.location.href = `{% url 'billing_workspace' %}?month=${this.selectedMonth}`;
                    } else {
                        alert('Lỗi: ' + data.message);
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        }
    }
