// ==========================================
// CALENDAR — Interactive Calendar View
// ==========================================

var currentDate = new Date();
var currentMonth = currentDate.getMonth();
var currentYear = currentDate.getFullYear();

var monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];

function renderCalendar() {
    var monthYearEl = document.getElementById('calendarMonthYear');
    var daysEl = document.getElementById('calendarDays');

    monthYearEl.textContent = monthNames[currentMonth] + ' ' + currentYear;

    // First day of month (0=Sun, adjust for Mon start)
    var firstDay = new Date(currentYear, currentMonth, 1).getDay();
    firstDay = firstDay === 0 ? 6 : firstDay - 1; // Convert to Mon=0

    // Days in month
    var daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    var html = '';

    // Empty cells before first day
    for (var i = 0; i < firstDay; i++) {
        html += '<div class="calendar-day calendar-day-empty"></div>';
    }

    // Day cells
    var today = new Date();
    for (var d = 1; d <= daysInMonth; d++) {
        var dateStr = currentYear + '-' +
            String(currentMonth + 1).padStart(2, '0') + '-' +
            String(d).padStart(2, '0');

        // Check if this day has appointments
        var dayEvents = getEventsForDate(dateStr);
        var hasEvents = dayEvents.length > 0;

        var isToday = (d === today.getDate() &&
            currentMonth === today.getMonth() &&
            currentYear === today.getFullYear());

        var classes = 'calendar-day';
        if (isToday) classes += ' calendar-day-today';
        if (hasEvents) classes += ' calendar-day-has-event';

        html += '<div class="' + classes + '" onclick="showDayDetails(\'' + dateStr + '\')">';
        html += '<span class="calendar-day-number">' + d + '</span>';
        if (hasEvents) {
            html += '<div class="calendar-day-dots">';
            for (var e = 0; e < Math.min(dayEvents.length, 3); e++) {
                html += '<span class="calendar-dot"></span>';
            }
            html += '</div>';
        }
        html += '</div>';
    }

    daysEl.innerHTML = html;
}

function getEventsForDate(dateStr) {
    var matches = [];
    for (var i = 0; i < calendarEvents.length; i++) {
        if (calendarEvents[i].date === dateStr) {
            matches.push(calendarEvents[i]);
        }
    }
    return matches;
}

function changeMonth(direction) {
    currentMonth += direction;
    if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    } else if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    }
    renderCalendar();
    document.getElementById('dayDetails').style.display = 'none';
}

function showDayDetails(dateStr) {
    var events = getEventsForDate(dateStr);
    var detailsEl = document.getElementById('dayDetails');
    var titleEl = document.getElementById('dayDetailsTitle');
    var listEl = document.getElementById('dayDetailsList');

    // Format the date nicely
    var parts = dateStr.split('-');
    var dateObj = new Date(parts[0], parts[1] - 1, parts[2]);
    var options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
    titleEl.textContent = dateObj.toLocaleDateString('en-GB', options);

    if (events.length === 0) {
        listEl.innerHTML = '<div class="empty-state"><div class="empty-state-icon">&#128197;</div><h3>No appointments</h3><p>You have no appointments on this day.</p></div>';
    } else {
        var html = '';
        for (var i = 0; i < events.length; i++) {
            var ev = events[i];
            html += '<div class="record-item">';
            html += '<div class="record-header">';
            html += '<h3>' + ev.title + '</h3>';
            html += '<span class="record-badge badge-upcoming">' + ev.time + '</span>';
            html += '</div>';
            html += '<p>&#127973; ' + ev.location + '</p>';
            if (ev.notes) html += '<p>&#128221; ' + ev.notes + '</p>';
            html += '</div>';
        }
        listEl.innerHTML = html;
    }

    detailsEl.style.display = 'block';
    detailsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Highlight selected day
    document.querySelectorAll('.calendar-day').forEach(function (day) {
        day.classList.remove('calendar-day-selected');
    });
    event.currentTarget.classList.add('calendar-day-selected');
}

// Init
document.addEventListener('DOMContentLoaded', function () {
    var daysEl = document.getElementById('calendarDays');
    if (daysEl) renderCalendar();
});