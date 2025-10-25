document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginButton = document.getElementById('loginButton');
    const errorMessage = document.getElementById('error-message');
    const buttonText = loginButton.querySelector('.button-text');
    const buttonLoader = loginButton.querySelector('.button-loader');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        if (!username || !password) {
            showError('Please enter both username and password');
            return;
        }

        // Show loading state
        loginButton.disabled = true;
        buttonText.style.display = 'none';
        buttonLoader.style.display = 'inline-block';
        errorMessage.style.display = 'none';

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Success - redirect to chat
                window.location.href = '/chat';
            } else {
                showError(data.error || 'Invalid username or password');
                resetButton();
            }
        } catch (error) {
            showError('Connection error. Please try again.');
            resetButton();
        }
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }

    function resetButton() {
        loginButton.disabled = false;
        buttonText.style.display = 'inline';
        buttonLoader.style.display = 'none';
    }
});