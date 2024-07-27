document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const formData = new FormData(this);

    // Show a loading spinner or message
    const loadingMessage = document.createElement('p');
    loadingMessage.textContent = 'Uploading and analyzing the file, please wait...';
    document.body.appendChild(loadingMessage);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Response received:', response);
        return response.json();
    })
    .then(data => {
        console.log('Data received:', data);
        if (data.success) {
            const result = data.prediction;
            const info = data.info;

            // Find the result section
            const resultSection = document.getElementById('resultSection');
            if (!resultSection) {
                console.error('Result section not found in the DOM.');
                return;
            }

            // Update the result section with disease information
            resultSection.innerHTML = `
                <h2>Diagnosis Result: ${result}</h2>
                <p><strong>Description:</strong> ${info.description || 'No description available.'}</p>
                <p><strong>Recommendations:</strong> ${info.recommendations || 'No recommendations available.'}</p>
                <p><strong>Treatment:</strong> ${info.treatment || 'No treatment information available.'}</p>
                <p><strong>Advice:</strong> ${info.advice || 'No advice available.'}</p>
            `;

            // Automatically scroll to the result section
            resultSection.style.display = 'block';
            resultSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            console.error('Error:', data.error);
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        alert('An error occurred while uploading the file.');
    })
    .finally(() => {
        // Remove the loading spinner or message
        loadingMessage.remove();
    });
});
