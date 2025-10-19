document.addEventListener('DOMContentLoaded', function() {
    const availabilityElement = document.getElementById('availability');
    
    function fetchAvailability() {
        fetch('/api/availability/')
            .then(response => response.json())
            .then(data => {
                availabilityElement.innerHTML = '';
                data.forEach(classInfo => {
                    const classDiv = document.createElement('div');
                    classDiv.className = 'class-info';
                    classDiv.innerHTML = `
                        <h3>${classInfo.name}</h3>
                        <p>Available Spots: ${classInfo.available_spots}</p>
                        <button onclick="bookClass(${classInfo.id})">Book Now</button>
                    `;
                    availabilityElement.appendChild(classDiv);
                });
            })
            .catch(error => console.error('Error fetching availability:', error));
    }

    function bookClass(classId) {
        fetch(`/api/book/${classId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({}),
        })
        .then(response => {
            if (response.ok) {
                alert('Class booked successfully!');
                fetchAvailability(); // Refresh availability after booking
            } else {
                alert('Failed to book class.');
            }
        })
        .catch(error => console.error('Error booking class:', error));
    }

    function getCookie(name) {
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

    // Fetch availability on page load
    fetchAvailability();
    
    // Optionally, set an interval to refresh availability every minute
    setInterval(fetchAvailability, 60000);
});