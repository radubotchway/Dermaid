document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();

    // Display a loading spinner or message
    const loadingMessage = document.createElement('p');
    loadingMessage.textContent = 'Analyzing your photo... Please wait.';
    loadingMessage.style.fontSize = '18px';
    loadingMessage.style.color = '#004080';
    document.querySelector('.container').appendChild(loadingMessage);

    const formData = new FormData(this);

    fetch(this.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Redirect to the prediction result page
            window.location.href = '/diagnosis-result';
        } else {
            loadingMessage.textContent = 'There was an error analyzing your photo. Please try again.';
            loadingMessage.style.color = 'red';
        }
    })
    .catch(error => {
        loadingMessage.textContent = 'An unexpected error occurred. Please try again.';
        loadingMessage.style.color = 'red';
    });
});
