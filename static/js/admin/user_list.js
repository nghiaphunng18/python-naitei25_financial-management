function openDeleteModal(url) {
  const form = document.getElementById("deleteForm");
  form.action = url;

  document.getElementById("deleteModal").classList.remove("hidden");
}

function closeDeleteModal() {
    document.getElementById("deleteModal").classList.add("hidden");
}
