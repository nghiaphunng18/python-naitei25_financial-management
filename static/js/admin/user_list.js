function openDeleteModal(url) {
  const form = document.getElementById("deleteForm");
  form.action = url;

  document.getElementById("deleteModal").classList.remove("hidden");
}

function closeDeleteModal() {
    document.getElementById("deleteModal").classList.add("hidden");
}

function onProvinceChange() {
    document.getElementById("id_district").selectedIndex = 0;
    document.getElementById("id_ward").selectedIndex = 0;
}

function onDistrictChange() {
    document.getElementById("id_ward").selectedIndex = 0;
}

function closeModalForm(modalId) {
    document.getElementById(modalId).innerHTML = "";
}
