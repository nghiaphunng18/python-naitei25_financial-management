function openPriceModal() {
  document.getElementById('priceModal').classList.remove('hidden');
}
function closePriceModal() {
  document.getElementById('priceModal').classList.add('hidden');
}


// Edit rental_price
function startEdit(id) {
  // Hide span, display input
  document.getElementById('date-text-' + id).classList.add('hidden');
  document.getElementById('value-text-' + id).classList.add('hidden');

  document.getElementById('date-input-' + id).classList.remove('hidden');
  document.getElementById('value-input-' + id).classList.remove('hidden');

  // Dispaly Save/Cancel button
  document.getElementById('save-btn-' + id).classList.remove('hidden');
  document.getElementById('cancel-btn-' + id).classList.remove('hidden');
}

function cancelEdit(id) {
  const row = document.getElementById('row-' + id);
  const oldDate = row.dataset.oldDate;   
  const oldPrice = row.dataset.oldPrice;

  // Back attributes of input & span
  document.getElementById('date-input-' + id).value = oldDate;
  document.getElementById('value-input-' + id).value = oldPrice;

  document.getElementById('date-text-' + id).classList.remove('hidden');
  document.getElementById('value-text-' + id).classList.remove('hidden');

  document.getElementById('date-input-' + id).classList.add('hidden');
  document.getElementById('value-input-' + id).classList.add('hidden');

  // Hide Save/Cancel button
  document.getElementById('save-btn-' + id).classList.add('hidden');
  document.getElementById('cancel-btn-' + id).classList.add('hidden');
}
