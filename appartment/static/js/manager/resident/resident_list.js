function toggleDropdown(userId) {
    const dropdown = document.getElementById(`dropdown-${userId}`);
    const button = document.getElementById(`detail-btn-${userId}`);
    const openText = button.getAttribute('data-open-text');
    const closeText = button.getAttribute('data-close-text');

    dropdown.classList.toggle('hidden');
    dropdown.classList.toggle('opacity-0');
    dropdown.classList.toggle('-translate-y-4');

    const isOpen = !dropdown.classList.contains('hidden');

    if (isOpen) {
        button.textContent = openText;
        button.setAttribute('data-state', 'open');
    } else {
        button.textContent = closeText;
        button.setAttribute('data-state', 'closed');
    }
}


function openAssignModal(userId, url) {
    const modal = document.getElementById('assign-room-modal');
    const modalContent = document.getElementById('assign-modal-content');
    const form = document.getElementById('assign-room-form');
    const userIdInput = document.getElementById('assign-user-id');
    userIdInput.value = userId;
    form.action = url;
    modal.classList.remove('hidden');
    setTimeout(() => {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
    }, 10);
}

function closeAssignModal() {
    const modal = document.getElementById('assign-room-modal');
    const modalContent = document.getElementById('assign-modal-content');
    modalContent.classList.add('scale-95', 'opacity-0');
    modalContent.classList.remove('scale-100', 'opacity-100');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

function openLeaveModal(userId, url) {
    const modal = document.getElementById('leave-room-modal');
    const modalContent = document.getElementById('leave-modal-content');
    const form = document.getElementById('leave-room-form');
    const userIdInput = document.getElementById('leave-user-id');
    userIdInput.value = userId;
    form.action = url;
    modal.classList.remove('hidden');
    setTimeout(() => {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
    }, 10);
}

function closeLeaveModal() {
    const modal = document.getElementById('leave-room-modal');
    const modalContent = document.getElementById('leave-modal-content');
    modalContent.classList.add('scale-95', 'opacity-0');
    modalContent.classList.remove('scale-100', 'opacity-100');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}
