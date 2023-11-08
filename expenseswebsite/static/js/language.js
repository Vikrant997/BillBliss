/*$(document).ready(function() {
    // button with id="changeLanguageButton" for changing the language
    $('#changeLanguageen, #changeLanguagesw').on('click', function() {
        var selectedLanguage = this.id.replace('changeLanguage', ''); // language to switch to
        console.log('lang: ', selectedLanguage);

        // Send a request to change the language
        $.post('/change-language/', { language: selectedLanguage }, function(data) {
            if (data.status === 'success') {
                // Reload the page if the language was changed successfully
                location.reload();
            } else {
                // Handle the case where language change failed (optional)
                console.error('Language change failed:', data.message);
            }
        });
    });
});*/

document.addEventListener('DOMContentLoaded', function() {
    // button with id="changeLanguageButton" for changing the language
    document.getElementById('changeLanguageen').addEventListener('click', function() {
        changeLanguage('en');
    });

    document.getElementById('changeLanguagesw').addEventListener('click', function() {
        changeLanguage('sw');
    });

    function changeLanguage(language) {
        console.log('Selected language:', language);

        const formData = new FormData();
        formData.append('language', language);
        const csrfToken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
        const url = '/change-language/?language=' + language;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
            body: formData,
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Language change response:', data);
            // Add a delay of 1 second (1000 milliseconds) before reloading the page
            location.reload();
        })
        .catch(error => {
            console.error('Error changing language:', error);
        });
    }
});

