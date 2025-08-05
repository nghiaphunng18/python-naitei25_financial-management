const roomIdInput = document.getElementById('id_room_id');
const feedbackDiv = document.getElementById('room-id-feedback');
let timeoutId;

roomIdInput.addEventListener('input', function() {
    clearTimeout(timeoutId);
    const roomId = this.value.trim();
    
    if (roomId.length === 0) {
        feedbackDiv.classList.add('hidden');
        return;
    }

    timeoutId = setTimeout(() => {
        fetch(`/rooms/check-exists/?room_id=${encodeURIComponent(roomId)}`)
            .then(response => response.json())
            .then(data => {
                feedbackDiv.classList.remove('hidden');
                if (data.exists) {
                    feedbackDiv.className = 'mt-1 text-sm text-red-600';
                    feedbackDiv.innerHTML = '<i class="fas fa-times-circle mr-1"></i>' + data.message;
                } else {
                    feedbackDiv.className = 'mt-1 text-sm text-green-600';
                    feedbackDiv.innerHTML = '<i class="fas fa-check-circle mr-1"></i>' + data.message;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }, 500);
});

function resetForm() {
    document.getElementById('createRoomForm').reset();
    feedbackDiv.classList.add('hidden');
}

document.getElementById('createRoomForm').addEventListener('submit', function(e) {
    const submitBtn = this.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Đang tạo...';
});
