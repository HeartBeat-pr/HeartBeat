// ==========================================
// APPOINTMENTS — Dynamic Booking
// ==========================================

let selectedDoctorId = null;
let doctorData = null;

function selectDoctor(card, doctorId) {
    // Remove selection from all cards
    document.querySelectorAll('.doctor-select-card').forEach(function (c) {
        c.classList.remove('selected');
    });

    // Select this card
    card.classList.add('selected');
    selectedDoctorId = doctorId;
    document.getElementById('doctor_id').value = doctorId;

    // Show booking form
    document.getElementById('bookingForm').style.display = 'block';

    // Reset date and time
    document.getElementById('appointment_date').value = '';
    document.getElementById('appointment_time').innerHTML = '<option value="">Select a date first</option>';

    // Fetch doctor availability
    fetch('/api/doctor-availability/' + doctorId)
        .then(function (response) { return response.json(); })
        .then(function (data) {
            doctorData = data;

            // Show doctor info
            var infoHtml = '<div class="selected-doctor-banner">';
            infoHtml += '<h3>Booking with: ' + data.doctor.name + '</h3>';
            infoHtml += '<p>' + data.doctor.specialty + ' — ' + data.doctor.medical_centre + '</p>';
            infoHtml += '</div>';
            document.getElementById('selectedDoctorInfo').innerHTML = infoHtml;

            // Show availability schedule
            var availHtml = '<h4>Available Days:</h4><div class="avail-tags">';
            data.availability.forEach(function (a) {
                availHtml += '<span class="avail-tag">' + a.day + ': ' + a.start.slice(0, 5) + ' - ' + a.end.slice(0, 5) + '</span>';
            });
            availHtml += '</div>';
            document.getElementById('availabilityInfo').innerHTML = availHtml;

            // Set min date to today
            var today = new Date().toISOString().split('T')[0];
            document.getElementById('appointment_date').setAttribute('min', today);
        });

    // Scroll to form
    document.getElementById('bookingForm').scrollIntoView({ behavior: 'smooth', block: 'start' });
}


function loadTimeSlots() {
    var dateInput = document.getElementById('appointment_date').value;
    var timeSelect = document.getElementById('appointment_time');

    if (!dateInput || !doctorData) {
        timeSelect.innerHTML = '<option value="">Select a date first</option>';
        return;
    }

    // Get day of week
    var selectedDate = new Date(dateInput);
    var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    var dayName = days[selectedDate.getDay()];

    // Find availability for this day
    var dayAvail = null;
    doctorData.availability.forEach(function (a) {
        if (a.day === dayName) {
            dayAvail = a;
        }
    });

    if (!dayAvail) {
        timeSelect.innerHTML = '<option value="">Doctor not available on ' + dayName + '</option>';
        return;
    }

    // Generate time slots
    var slots = [];
    var startParts = dayAvail.start.split(':');
    var endParts = dayAvail.end.split(':');
    var startMinutes = parseInt(startParts[0]) * 60 + parseInt(startParts[1]);
    var endMinutes = parseInt(endParts[0]) * 60 + parseInt(endParts[1]);
    var duration = dayAvail.slot_duration;

    for (var m = startMinutes; m + duration <= endMinutes; m += duration) {
        var hours = Math.floor(m / 60);
        var mins = m % 60;
        var timeStr = String(hours).padStart(2, '0') + ':' + String(mins).padStart(2, '0');
        slots.push(timeStr);
    }

    // Filter out booked slots
    var bookedOnDate = [];
    doctorData.booked.forEach(function (b) {
        if (b.date === dateInput) {
            bookedOnDate.push(b.time.slice(0, 5));
        }
    });

    var html = '<option value="">Choose a time</option>';
    slots.forEach(function (slot) {
        var isBooked = bookedOnDate.indexOf(slot) !== -1;
        if (isBooked) {
            html += '<option value="" disabled>' + slot + ' — Booked</option>';
        } else {
            html += '<option value="' + slot + '">' + slot + '</option>';
        }
    });

    if (slots.length === 0) {
        html = '<option value="">No slots available on ' + dayName + '</option>';
    }

    timeSelect.innerHTML = html;
}