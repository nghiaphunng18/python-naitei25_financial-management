// static/js/room_filter.js

class RoomFilter {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.setupTransitions();
    }

    initializeElements() {
        this.statusFilter = document.getElementById('statusFilter');
        this.occupancyFilter = document.getElementById('occupancyFilter');
        this.areaFilter = document.getElementById('areaFilter');
        this.maxOccupantsFilter = document.getElementById('maxOccupantsFilter');
        this.applyFiltersBtn = document.getElementById('applyFilters');
        this.resetFiltersBtn = document.getElementById('resetFilters');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.roomsContainer = document.getElementById('roomsContainer');
        this.resultsCount = document.getElementById('resultsCount');
        this.filterStatus = document.getElementById('filterStatus');
        
        this.allFilters = [
            this.statusFilter, 
            this.occupancyFilter, 
            this.areaFilter, 
            this.maxOccupantsFilter
        ];
    }

    bindEvents() {
        // Only apply filters when button is clicked
        this.applyFiltersBtn.addEventListener('click', () => this.applyFilters());
        
        // Reset filters
        this.resetFiltersBtn.addEventListener('click', () => this.resetFilters());
        
        // Allow Enter key to apply filters
        this.allFilters.forEach(filter => {
            filter.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.applyFilters();
                }
            });
        });
    }

    setupTransitions() {
        // Add smooth transitions
        this.roomsContainer.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
    }

    applyFilters() {
        const filters = {
            status: this.statusFilter.value,
            occupancy: this.occupancyFilter.value,
            area: this.areaFilter.value,
            max_occupants: this.maxOccupantsFilter.value
        };

        this.updateURLParameters(filters);
        this.showLoading();
        this.performAjaxRequest();
    }

    resetFilters() {
        this.statusFilter.value = '';
        this.occupancyFilter.value = '';
        this.areaFilter.value = '';
        this.maxOccupantsFilter.value = '';
        
        this.clearURLParameters();
        this.applyFilters();
    }

    updateURLParameters(filters) {
        const url = new URL(window.location);
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                url.searchParams.set(key, filters[key]);
            } else {
                url.searchParams.delete(key);
            }
        });
        history.pushState(null, '', url);
    }

    clearURLParameters() {
        const url = new URL(window.location);
        url.search = '';
        history.pushState(null, '', url);
    }

    showLoading() {
        this.loadingSpinner.classList.remove('hidden');
        this.roomsContainer.style.opacity = '0.5';
    }

    hideLoading() {
        this.loadingSpinner.classList.add('hidden');
        this.roomsContainer.style.opacity = '1';
    }

    performAjaxRequest() {
        fetch(window.location.href, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            this.hideLoading();
            this.updateContent(html);
        })
        .catch(error => {
            console.error('Filter error:', error);
            this.hideLoading();
            this.showErrorMessage('Có lỗi xảy ra khi lọc dữ liệu. Vui lòng thử lại.');
        });
    }

    updateContent(html) {
        // Fade out old content
        this.roomsContainer.style.opacity = '0';
        this.roomsContainer.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            this.roomsContainer.innerHTML = html;
            this.updateResultsCount();
            this.updateFilterStatus();
            
            // Fade in new content
            this.roomsContainer.style.opacity = '1';
            this.roomsContainer.style.transform = 'translateY(0)';
        }, 150);
    }

    updateResultsCount() {
        const roomCards = this.roomsContainer.querySelectorAll('.room-card');
        this.resultsCount.textContent = roomCards.length;
    }

    updateFilterStatus() {
        const filters = {
            status: this.statusFilter.value,
            occupancy: this.occupancyFilter.value,
            area: this.areaFilter.value,
            max_occupants: this.maxOccupantsFilter.value
        };
        
        const activeFilters = Object.values(filters).filter(value => value).length;
        
        if (activeFilters > 0) {
            this.filterStatus.textContent = `${activeFilters} bộ lọc đang áp dụng`;
            this.filterStatus.classList.add('text-blue-600');
            this.filterStatus.classList.remove('text-gray-500');
        } else {
            this.filterStatus.textContent = '';
            this.filterStatus.classList.remove('text-blue-600');
            this.filterStatus.classList.add('text-gray-500');
        }
    }

    showErrorMessage(message) {
        // Create temporary error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50';
        errorDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-red-500 hover:text-red-700">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }
}

// Global function for reset button in empty state
function resetFilters() {
    if (window.roomFilterInstance) {
        window.roomFilterInstance.resetFilters();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.roomFilterInstance = new RoomFilter();
});
