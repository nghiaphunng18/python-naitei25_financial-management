document.addEventListener('DOMContentLoaded', function () {
    const roomContext = document.getElementById('room-context');
    const originalValues = {
        area: roomContext.dataset.area,
        status: roomContext.dataset.status,
        max_occupants: roomContext.dataset.maxOccupants,
        description: roomContext.dataset.description
    };    

    // Reset form function
    const resetBtn = document.getElementById('resetButton');
    function resetForm() {
        document.getElementById('updateRoomForm').reset();
        updateChangePreview();
    }
    resetBtn.addEventListener('click', resetForm);
    // Update change preview
    function updateChangePreview() {
        const form = document.getElementById('updateRoomForm');
        const preview = document.getElementById('changePreview');
        const changes = [];

        const currentValues = {
            area: form.querySelector('[name="area"]').value,
            status: form.querySelector('[name="status"]').value,
            max_occupants: form.querySelector('[name="max_occupants"]').value,
            description: form.querySelector('[name="description"]').value
        };

        if (originalValues.area !== currentValues.area) {
            changes.push(`Diện tích: ${originalValues.area || 'Chưa có'} → ${currentValues.area || 'Chưa có'} m²`);
        }

        if (originalValues.status !== currentValues.status) {
            const statusNames = {
                'available': 'Có sẵn',
                'occupied': 'Đã có người ở',
                'maintenance': 'Bảo trì',
                'unavailable': 'Không khả dụng'
            };
            
            changes.push(`Trạng thái: ${statusNames[originalValues.status]} → ${statusNames[currentValues.status]}`);
        }

        if (originalValues.max_occupants !== currentValues.max_occupants) {
            changes.push(`Số người tối đa: ${originalValues.max_occupants} → ${currentValues.max_occupants} người`);
        }

        if (originalValues.description !== currentValues.description) {
            changes.push(`Mô tả: ${originalValues.description ? 'Đã có' : 'Chưa có'} → ${currentValues.description ? 'Đã có' : 'Chưa có'}`);
        }

        if (changes.length > 0) {
            preview.innerHTML = '<p class="font-medium mb-2">Các thay đổi sẽ được áp dụng:</p><ul class="list-disc list-inside space-y-1">' +
                changes.map(change => `<li>${change}</li>`).join('') + '</ul>';
        } else {
            preview.innerHTML = '<p>Chưa có thay đổi nào.</p>';
        }
    }

    // Add listeners
    const form = document.getElementById('updateRoomForm');
    const fields = form.querySelectorAll('input, select, textarea');

    fields.forEach(field => {
        field.addEventListener('input', updateChangePreview);
        field.addEventListener('change', updateChangePreview);
    });

    updateChangePreview();

    form.addEventListener('submit', function (e) {
        const submitBtn = this.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Đang cập nhật...';
    });
});
