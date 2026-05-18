// Confirmation Dialog System
(function() {
  'use strict';

  // Create modal HTML if it doesn't exist
  function createConfirmModal() {
    if (document.getElementById('confirmModal')) return;
    
    const modalHTML = `
      <div class="modal fade" id="confirmModal" tabindex="-1" aria-labelledby="confirmModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="confirmModalLabel">Confirm Action</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body" id="confirmModalBody">
              Are you sure you want to proceed?
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="button" class="btn btn-danger" id="confirmModalConfirm">Confirm</button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }

  // Show confirmation dialog
  window.showConfirmDialog = function(options) {
    createConfirmModal();
    
    const modal = document.getElementById('confirmModal');
    const title = document.getElementById('confirmModalLabel');
    const body = document.getElementById('confirmModalBody');
    const confirmBtn = document.getElementById('confirmModalConfirm');
    
    title.textContent = options.title || 'Confirm Action';
    body.textContent = options.message || 'Are you sure?';
    confirmBtn.textContent = options.confirmText || 'Confirm';
    confirmBtn.className = `btn ${options.confirmClass || 'btn-danger'}`;
    
    // Remove old event listeners
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    // Add new event listener
    newConfirmBtn.addEventListener('click', function() {
      if (options.onConfirm) {
        options.onConfirm();
      }
      bootstrap.Modal.getInstance(modal).hide();
    });
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
  };

  // Attach to delete buttons
  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-confirm-delete]').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        const itemName = this.dataset.itemName || 'this item';
        const url = this.href || this.dataset.url;
        
        showConfirmDialog({
          title: 'Confirm Deletion',
          message: `Are you sure you want to delete ${itemName}? This action cannot be undone.`,
          confirmText: 'Delete',
          confirmClass: 'btn-danger',
          onConfirm: function() {
            if (url) {
              window.location.href = url;
            }
          }
        });
      });
    });
  });
})();
