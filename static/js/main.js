function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tab-link");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

document.getElementById('loginForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    // This part is new: it reads the JSON response from the backend
    const result = await response.json();

    if (response.ok) {
        // Redirect to the URL provided by the backend
        window.location.href = result.redirect_url;
    } else {
        alert(result.message || 'Login failed!');
    }
});


document.getElementById('signupForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    const response = await fetch('/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (response.ok) {
        alert('Signup successful! Please login.');
        openTab(event, 'Login');
    } else {
        alert('Signup failed!');
    }
});


document.getElementById('uploadForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);

    const response = await fetch('/upload_record', {
        method: 'POST',
        body: formData
    });

    if (response.ok) {
        alert('Record uploaded successfully!');
        location.reload();
    } else {
        alert('Upload failed!');
    }
});