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
// --- Record Filtering Logic ---
document.addEventListener('DOMContentLoaded', () => {
    // Find the filter buttons and record items on the page
    const filterButtons = document.querySelectorAll('.filter-btn');
    const recordItems = document.querySelectorAll('.record-item-filterable');

    // If there are no filter buttons on this page, do nothing.
    if (filterButtons.length === 0) {
        return;
    }

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Get the category to filter by from the button's data-filter attribute
            const filterValue = button.dataset.filter;

            // Update the active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // Show or hide record items based on the filter
            recordItems.forEach(item => {
                const itemClassification = item.dataset.classification;

                if (filterValue === 'all' || itemClassification === filterValue) {
                    item.style.display = 'flex'; // Show the item
                } else {
                    item.style.display = 'none'; // Hide the item
                }
            });
        });
    });
});
// REPLACE THE OLD, BROKEN FUNCTION WITH THIS NEW ONE
// REPLACE THE OLD, BROKEN FUNCTION WITH THIS NEW ONE
function openDrugTab(evt, tabName) {
    // Hide all elements with the class "tab-content"
    const tabcontent = document.querySelectorAll(".tab-content");
    tabcontent.forEach(tab => {
        tab.style.display = "none";
        tab.classList.remove("active");
    });

    // Remove the "active" class from all tab-link buttons
    const tablinks = document.querySelectorAll(".tab-link");
    tablinks.forEach(link => {
        link.classList.remove("active");
    });

    // Show the specific tab content that should be visible
    const activeTab = document.getElementById(tabName);
    if (activeTab) {
        activeTab.style.display = "block";
        activeTab.classList.add("active");
    }
    
    // Add the "active" class to the button that was clicked
    evt.currentTarget.classList.add("active");

}
// --- Drug Guide View Switcher Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const listViewBtn = document.getElementById('list-view-btn');
    const gridViewBtn = document.getElementById('grid-view-btn');
    const drugListContainer = document.getElementById('drug-list-container');

    if (listViewBtn && gridViewBtn && drugListContainer) {
        listViewBtn.addEventListener('click', () => {
            drugListContainer.classList.remove('grid-view');
            listViewBtn.classList.add('active');
            gridViewBtn.classList.remove('active');
        });

        gridViewBtn.addEventListener('click', () => {
            drugListContainer.classList.add('grid-view');
            gridViewBtn.classList.add('active');
            listViewBtn.classList.remove('active');
        });
    }
});
// --- NEW: Appointment Tab Switching Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.appt-tab-btn');
    const tabContents = document.querySelectorAll('.appointment-list');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Deactivate all buttons and hide all content
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Activate the clicked button
            button.classList.add('active');

            // Show the corresponding content
            const targetId = button.dataset.target;
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
});