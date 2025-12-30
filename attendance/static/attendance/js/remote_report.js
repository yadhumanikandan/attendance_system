/* Remote Report page JavaScript */

// ====================================
// Download Functions
// ====================================

function toggleDownloadMenu() {
    const menu = document.getElementById('downloadMenu');
    menu.classList.toggle('show');
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('.download-dropdown')) {
        const menu = document.getElementById('downloadMenu');
        if (menu) menu.classList.remove('show');
    }
});

function downloadRemoteEmployeeReport(employeeId, employeeName) {
    const config = window.remoteReportConfig || {};
    const baseUrl = config.downloadEmployeeReportUrl || '/report/remote/download/employee/';
    const month = config.selectedMonth;
    const year = config.selectedYear;
    
    const url = baseUrl.replace('/0/', '/' + employeeId + '/') + '?month=' + month + '&year=' + year;
    const filename = employeeName.replace(/\s+/g, '_') + '_Remote_Stats_' + year + '_' + month + '.xlsx';

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

function downloadRemoteReport() {
    const config = window.remoteReportConfig || {};
    const baseUrl = config.downloadReportUrl || '/report/remote/download/';
    const month = config.selectedMonth;
    const year = config.selectedYear;
    const showInactive = config.showInactive ? '&show_inactive=1' : '';
    
    const url = baseUrl + '?month=' + month + '&year=' + year + showInactive;
    const filename = 'Remote_Attendance_Report_' + year + '_' + month + '.xlsx';

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

// ====================================
// Calendar Day Classification
// ====================================

document.addEventListener('DOMContentLoaded', function() {
    const config = window.remoteReportConfig || {};
    const year = config.selectedYear;
    const month = config.selectedMonth;

    document.querySelectorAll('.calendar-day.has-day.no-record').forEach(function(dayEl) {
        if (dayEl.classList.contains('future-day')) return;

        const dayNum = parseInt(dayEl.querySelector('.day-number').textContent);
        const date = new Date(year, month - 1, dayNum);

        if (date.getDay() === 0) {
            dayEl.classList.add('sunday');
            const noWorkEl = dayEl.querySelector('.no-work');
            if (noWorkEl) noWorkEl.textContent = 'Holiday';
        }
    });
});
