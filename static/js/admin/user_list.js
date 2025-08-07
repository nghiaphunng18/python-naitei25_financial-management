function openDeleteModal(userId) {
    let form = document.getElementById("deleteForm");
    form.action = `user/${userId}/delete/`;
    document.getElementById("deleteModal").classList.remove("hidden");
}

function closeDeleteModal() {
    document.getElementById("deleteModal").classList.add("hidden");
}
