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
// --- NEW: Drug Selector Modal Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const addDrugBtn = document.getElementById('add-drug-btn');
    const modal = document.getElementById('drug-modal');
    const closeBtn = modal?.querySelector('.modal-close-btn');
    const saveBtn = document.getElementById('save-drugs-btn');
    const modalDrugList = document.getElementById('modal-drug-list');
    const chosenDrugsList = document.getElementById('chosen-drugs-list');
    const hiddenInputsContainer = document.getElementById('hidden-drug-inputs');
    const searchInput = document.getElementById('modal-drug-search');

    if (!addDrugBtn) return; // Only run this code on the upload page

    // Open the modal
    addDrugBtn.addEventListener('click', () => modal.classList.add('active'));

    // Close the modal
    const closeModal = () => modal.classList.remove('active');
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    // Handle selecting/deselecting drugs inside the modal
    modalDrugList.addEventListener('click', (e) => {
        const drugItem = e.target.closest('.modal-drug-item');
        if (drugItem) {
            drugItem.classList.toggle('selected');
        }
    });

    // Handle live search inside the modal
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const allDrugs = modalDrugList.querySelectorAll('.modal-drug-item');
        allDrugs.forEach(drug => {
            const name = drug.dataset.drugName.toLowerCase();
            const sciName = drug.dataset.drugSciName.toLowerCase();
            if (name.includes(searchTerm) || sciName.includes(searchTerm)) {
                drug.style.display = 'flex';
            } else {
                drug.style.display = 'none';
            }
        });
    });

    // Handle saving the selection
    saveBtn.addEventListener('click', () => {
        const selectedDrugs = modal.querySelectorAll('.modal-drug-item.selected');
        
        // Clear previous selections
        chosenDrugsList.innerHTML = '';
        hiddenInputsContainer.innerHTML = '';

        selectedDrugs.forEach(drug => {
            // Add to the visible list on the main page
            const drugDiv = document.createElement('div');
            drugDiv.className = 'drug-item';
            drugDiv.innerHTML = `
                <img src="${drug.dataset.drugImg}" alt="${drug.dataset.drugName}">
                <div class="drug-info">
                    <strong>${drug.dataset.drugName}</strong>
                    <span>${drug.dataset.drugSciName}</span>
                </div>
            `;
            chosenDrugsList.appendChild(drugDiv);

            // Add a hidden input for form submission
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'prescribed_drugs';
            hiddenInput.value = drug.dataset.drugId;
            hiddenInputsContainer.appendChild(hiddenInput);
        });

        closeModal();
    });
});
// --- NEW: Drag and Drop Upload Area Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const uploadBox = document.getElementById('upload-box');
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name-display');

    if (!uploadBox) return; // Only run this if the upload box exists on the page

    // Clicking anywhere in the box should trigger the file input
    uploadBox.addEventListener('click', (e) => {
        // Prevent the click from triggering if it's on the label itself
        if (e.target.tagName !== 'LABEL') {
            fileInput.click();
        }
    });

    // Add visual feedback when dragging a file over the box
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('is-dragover');
    });

    // Remove visual feedback when the file leaves the box area
    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('is-dragover');
    });

    // Handle the file drop
    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('is-dragover');
        
        // Get the dropped files and assign them to our hidden input
        const droppedFiles = e.dataTransfer.files;
        if (droppedFiles.length > 0) {
            fileInput.files = droppedFiles;
            // Manually trigger the 'change' event to update the filename display
            const event = new Event('change');
            fileInput.dispatchEvent(event);
        }
    });

    // Update the display text when a file is chosen
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileNameDisplay.textContent = `Selected file: ${fileInput.files[0].name}`;
        } else {
            fileNameDisplay.textContent = '';
        }
    });
});