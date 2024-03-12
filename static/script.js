document.addEventListener('DOMContentLoaded', () => {
    const noteForm = document.getElementById('note_form');
    const noteInput = document.getElementById('note_input');
    noteForm.addEventListener('submit', function(e) {
        const noteText = noteInput.value.trim();
        if (!noteText) {
            e.preventDefault(); // Prevent form submission
            alert('Note content cannot be blank.');
        }
    });
});


document.querySelectorAll('.edit-button').forEach(button => {
    button.addEventListener('click', function() {
        const noteId = button.getAttribute('data-note-id');
        toggleEditForm(noteId);
    });
});


document.addEventListener('DOMContentLoaded', function() {
    const binLink = document.getElementById('bin-link');
    const binUrl = binLink.getAttribute('data-bin-url');
    binLink.addEventListener('click', function(e) {
        e.preventDefault();
        fetch('/check_bin')
            .then(response => response.json())
            .then(data => {
                if (data.is_empty) {
                    alert('Bin is empty!');
                } else {
                    window.location.href = binUrl;
                }
            })
            .catch(error => console.error('Error:', error));
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const archiveLink = document.getElementById('archive-link');
    const archiveUrl = archiveLink.getAttribute('data-archive-url');
    archiveLink.addEventListener('click', function(e) {
        e.preventDefault();
        fetch('/check_archive')
            .then(response => response.json())
            .then(data => {
                if (data.is_empty) {
                    alert('Archive is empty!');
                } else {
                    window.location.href = archiveUrl;
                }
            })
            .catch(error => console.error('Error:', error));
    });
});




function toggleEditForm(noteId) {
    const form = document.getElementById(`edit-form-${noteId}`);
    if (form.style.display === "none" || form.style.display === "") {
        form.style.display = "block";
    } else {
        form.style.display = "none";
    }
}

function confirmDelete() {
    return confirm('Are you certain you want to delete this permenantly?');
}

function confirmEmptyTrash() {
    return confirm("Selecting 'Yes' will permenantly delete all notes in your bin (this is irreversible)")
}