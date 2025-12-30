/* Report page JavaScript - Static version */

// ============================================
// Download Functions
// ============================================

function toggleDownloadMenu() {
    const menu = document.getElementById('downloadMenu');
    menu.classList.toggle('show');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('.download-dropdown')) {
        const menu = document.getElementById('downloadMenu');
        if (menu) menu.classList.remove('show');
    }
});

function downloadEmployeeReport(employeeId, employeeName) {
    // Get config from data attributes
    const config = window.reportConfig || {};
    const baseUrl = config.downloadEmployeeReportUrl || '/report/download/employee/';
    const month = config.selectedMonth;
    const year = config.selectedYear;
    
    const url = baseUrl.replace('/0/', '/' + employeeId + '/') + '?month=' + month + '&year=' + year;
    const filename = employeeName.replace(/\s+/g, '_') + '_Attendance_' + year + '_' + month + '.xlsx';

    fetch(url)
        .then(response => response.blob())
        .then(blob => {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
        })
        .catch(error => console.error('Download failed:', error));
}

function downloadReport() {
    const config = window.reportConfig || {};
    const baseUrl = config.downloadReportUrl || '/report/download/';
    const month = config.selectedMonth;
    const year = config.selectedYear;
    const showInactive = config.showInactive ? '&show_inactive=1' : '';
    
    const url = baseUrl + '?month=' + month + '&year=' + year + showInactive;
    const filename = 'Attendance_Report_' + year + '_' + month + '.xlsx';

    fetch(url)
        .then(response => response.blob())
        .then(blob => {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
        })
        .catch(error => console.error('Download failed:', error));
}

// ============================================
// Calendar Day Classification
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const config = window.reportConfig || {};
    const year = config.selectedYear;
    const month = config.selectedMonth;

    document.querySelectorAll('.calendar-day.has-day.no-record').forEach(function(dayEl) {
        if (dayEl.classList.contains('future-day')) return;

        const dayNum = parseInt(dayEl.querySelector('.day-number').textContent);
        const date = new Date(year, month - 1, dayNum);

        if (date.getDay() === 0) { // Sunday
            dayEl.classList.add('sunday');
            const noWorkEl = dayEl.querySelector('.no-work');
            if (noWorkEl) noWorkEl.textContent = 'Holiday';
        }
    });
});

// ============================================
// Edit Modal Functions
// ============================================

function openEditModal(employeeId, employeeName, day, firstIn, lastOut) {
    const modal = document.getElementById('editModal');
    if (!modal) return;

    const config = window.reportConfig || {};
    const selectedYear = config.selectedYear;
    const selectedMonth = config.selectedMonth;

    // Format date as YYYY-MM-DD
    const dateStr = `${selectedYear}-${String(selectedMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const displayDate = new Date(selectedYear, selectedMonth - 1, day).toLocaleDateString('en-US', {
        weekday: 'short', month: 'short', day: 'numeric'
    });

    document.getElementById('modalEmployeeName').textContent = employeeName;
    document.getElementById('modalDate').textContent = displayDate;
    document.getElementById('editEmployeeId').value = employeeId;
    document.getElementById('editDate').value = dateStr;
    document.getElementById('editFirstIn').value = firstIn || '';
    document.getElementById('editLastOut').value = lastOut || '';

    // Clear any previous messages
    const msgEl = document.getElementById('modalMessage');
    msgEl.style.display = 'none';
    msgEl.className = 'modal-message';

    modal.classList.add('show');
}

function closeEditModal() {
    const modal = document.getElementById('editModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// Handle edit form submission
document.addEventListener('DOMContentLoaded', function() {
    const editForm = document.getElementById('editAttendanceForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const saveBtn = document.getElementById('saveBtn');
            const msgEl = document.getElementById('modalMessage');
            const config = window.reportConfig || {};

            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';

            const formData = {
                employee_id: document.getElementById('editEmployeeId').value,
                date: document.getElementById('editDate').value,
                first_in: document.getElementById('editFirstIn').value || null,
                last_out: document.getElementById('editLastOut').value || null
            };

            fetch(config.updateAttendanceUrl || '/api/update-attendance/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';

                if (data.success) {
                    msgEl.className = 'modal-message success';
                    msgEl.textContent = '✓ ' + data.message;
                    msgEl.style.display = 'block';

                    setTimeout(() => { window.location.reload(); }, 1000);
                } else {
                    msgEl.className = 'modal-message error';
                    msgEl.textContent = '✗ ' + (data.error || 'Failed to save');
                    msgEl.style.display = 'block';
                }
            })
            .catch(error => {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';
                msgEl.className = 'modal-message error';
                msgEl.textContent = '✗ Network error. Please try again.';
                msgEl.style.display = 'block';
            });
        });
    }

    // Close modal when clicking outside
    document.getElementById('editModal')?.addEventListener('click', function(e) {
        if (e.target === this) {
            closeEditModal();
        }
    });
});

// ============================================
// Request Approval Modal Functions
// ============================================

function openApprovalModal(requestId) {
    fetch(`/request/${requestId}/data/`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert('Error: ' + (data.error || 'Failed to load request data'));
                return;
            }

            document.getElementById('currentRequestId').value = requestId;
            document.getElementById('approvalEmployeeName').textContent = data.employee_name;
            document.getElementById('approvalRequestDate').textContent = data.request_date;
            document.getElementById('approvalDestination').textContent = data.destination;
            document.getElementById('approvalCustomer').textContent = data.customer_name;

            if (data.reason) {
                document.getElementById('approvalReason').textContent = data.reason;
                document.getElementById('approvalReasonRow').style.display = 'flex';
            } else {
                document.getElementById('approvalReasonRow').style.display = 'none';
            }

            const noDataWarning = document.getElementById('noDataWarning');
            const timeEditSection = document.getElementById('timeEditSection');
            const remoteNotice = document.getElementById('remoteNotice');
            const approveBtn = document.getElementById('approveBtn');

            if (data.employee_type === 'remote') {
                noDataWarning.style.display = 'none';
                timeEditSection.style.display = 'none';
                remoteNotice.style.display = 'flex';
                approveBtn.disabled = !data.has_data;
            } else {
                remoteNotice.style.display = 'none';

                if (data.has_data) {
                    noDataWarning.style.display = 'none';
                    timeEditSection.style.display = 'block';
                    approveBtn.disabled = false;

                    document.getElementById('originalFirstIn').textContent = data.first_in || '--:--';
                    document.getElementById('originalLastOut').textContent = data.last_out || '--:--';
                    document.getElementById('newFirstIn').value = data.first_in || '';

                    // Pre-fill last out: use the later of return_time or last_out
                    let newLastOutValue = data.last_out || '';
                    if (data.return_time && data.last_out) {
                        newLastOutValue = (data.return_time > data.last_out) ? data.return_time : data.last_out;
                    } else if (data.return_time && !data.last_out) {
                        newLastOutValue = data.return_time;
                    }
                    document.getElementById('newLastOut').value = newLastOutValue;
                } else {
                    noDataWarning.style.display = 'flex';
                    timeEditSection.style.display = 'none';
                    approveBtn.disabled = true;
                }
            }

            document.getElementById('approvalMessage').style.display = 'none';
            document.getElementById('approvalModal').classList.add('show');
        })
        .catch(error => {
            console.error('Error fetching request data:', error);
            alert('Network error. Please try again.');
        });
}

function closeApprovalModal() {
    document.getElementById('approvalModal').classList.remove('show');
}

function submitApproval() {
    const requestId = document.getElementById('currentRequestId').value;
    const approveBtn = document.getElementById('approveBtn');
    const msgEl = document.getElementById('approvalMessage');

    const newFirstIn = document.getElementById('newFirstIn')?.value || '';
    const newLastOut = document.getElementById('newLastOut')?.value || '';

    approveBtn.disabled = true;
    approveBtn.textContent = 'Approving...';

    const formData = new FormData();
    formData.append('new_first_in', newFirstIn);
    formData.append('new_last_out', newLastOut);

    fetch(`/request/${requestId}/approve/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        approveBtn.disabled = false;
        approveBtn.textContent = '✓ Approve & Update';

        if (data.success) {
            msgEl.className = 'approval-message success';
            msgEl.textContent = '✓ ' + data.message;
            msgEl.style.display = 'block';
            setTimeout(() => { window.location.reload(); }, 1000);
        } else {
            msgEl.className = 'approval-message error';
            msgEl.textContent = '✗ ' + (data.error || 'Failed to approve');
            msgEl.style.display = 'block';
        }
    })
    .catch(error => {
        approveBtn.disabled = false;
        approveBtn.textContent = '✓ Approve & Update';
        msgEl.className = 'approval-message error';
        msgEl.textContent = '✗ Network error. Please try again.';
        msgEl.style.display = 'block';
    });
}

function declineRequest(requestId) {
    if (!confirm('Are you sure you want to decline this request?')) {
        return;
    }

    const actionsDiv = document.getElementById(`request-actions-${requestId}`);
    if (actionsDiv) {
        actionsDiv.querySelectorAll('button').forEach(btn => btn.disabled = true);
    }

    fetch(`/request/${requestId}/decline/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert('Error: ' + (data.error || 'Failed to decline'));
            if (actionsDiv) {
                actionsDiv.querySelectorAll('button').forEach(btn => btn.disabled = false);
            }
        }
    })
    .catch(error => {
        alert('Network error. Please try again.');
        if (actionsDiv) {
            actionsDiv.querySelectorAll('button').forEach(btn => btn.disabled = false);
        }
    });
}

// Close approval modal when clicking outside
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('approvalModal')?.addEventListener('click', function(e) {
        if (e.target === this) {
            closeApprovalModal();
        }
    });
});

// ============================================
// Utility Functions
// ============================================

function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
