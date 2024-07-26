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
        // Remove the loading message
        document.querySelector('.container').removeChild(loadingMessage);

        if (data.success) {
            // Display the prediction result
            const resultDiv = document.getElementById('result');
            const predictionP = document.getElementById('prediction');
            predictionP.textContent = data.prediction;
            resultDiv.style.display = 'block';
        } else {
            const errorMessage = document.createElement('p');
            errorMessage.textContent = data.error || 'There was an error analyzing your photo. Please try again.';
            errorMessage.style.color = 'red';
            document.querySelector('.container').appendChild(errorMessage);
        }
    })
    .catch(error => {
        document.querySelector('.container').removeChild(loadingMessage);
        const errorMessage = document.createElement('p');
        errorMessage.textContent = 'An unexpected error occurred. Please try again.';
        errorMessage.style.fontSize = '18px';
        errorMessage.style.color = 'red';
        document.querySelector('.container').appendChild(errorMessage);
    });
});