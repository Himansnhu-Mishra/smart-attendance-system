// Fetch attendance data every 5 seconds and update the table
let allAttendanceData = []; // Store all attendance data globally

function fetchAttendance() {
    fetch('/get_attendance')
        .then(response => response.json())
        .then(data => {
            allAttendanceData = data; // Save all data globally
            displayAttendance(data); // Display all data initially
        })
        .catch(error => console.error('Error fetching attendance:', error));
}

// Display attendance data in the table
function displayAttendance(data) {
    const tbody = document.querySelector('#attendance-table tbody');
    tbody.innerHTML = ''; // Clear existing rows

    data.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${record.Name}</td>
            <td>${record['Roll Number']}</td>
            <td>${record.Department}</td>
            <td>${record.Timestamp}</td>
        `;
        tbody.appendChild(row);
    });
}

// Filter attendance data by date
function filterAttendanceByDate(selectedDate) {
    console.log("Selected Date:", selectedDate); // Debugging statement
    console.log("All Attendance Data:", allAttendanceData); // Debugging statement

    // Filter records where the Timestamp starts with the selected date
    const filteredData = allAttendanceData.filter(record => record.Timestamp.startsWith(selectedDate));
    console.log("Filtered Data:", filteredData); // Debugging statement

    displayAttendance(filteredData);
}

// Initialize the calendar
flatpickr("#date-picker", {
    dateFormat: "Y-m-d", // Format: YYYY-MM-DD
    onChange: (selectedDates, dateStr) => {
        console.log("Calendar Date Selected:", dateStr); // Debugging statement
        filterAttendanceByDate(dateStr);
    }
});

// Toggle visibility of sections
document.getElementById('btn-live-video').addEventListener('click', () => {
    document.getElementById('live-video').style.display = 'block';
    document.getElementById('attendance-table-section').style.display = 'none';
    document.getElementById('modify-records').style.display = 'none';
});

document.getElementById('btn-attendance').addEventListener('click', () => {
    document.getElementById('live-video').style.display = 'none';
    document.getElementById('attendance-table-section').style.display = 'block';
    document.getElementById('modify-records').style.display = 'none';
    fetchAttendance(); // Fetch attendance data when the button is clicked
});

document.getElementById('btn-modify').addEventListener('click', () => {
    document.getElementById('live-video').style.display = 'none';
    document.getElementById('attendance-table-section').style.display = 'none';
    document.getElementById('modify-records').style.display = 'block';
});

// Handle form submission for modifying records
document.getElementById('modify-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('name').value;
    const action = document.getElementById('action').value;

    // Send a POST request to the server to handle the action
    fetch('/modify_records', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, action })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message); // Show success/error message
    })
    .catch(error => console.error('Error modifying records:', error));
});

// Fetch attendance immediately and then every 5 seconds
fetchAttendance();
setInterval(fetchAttendance, 5000); /* Refresh every 5 seconds */