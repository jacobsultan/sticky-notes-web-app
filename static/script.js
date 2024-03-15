// new note
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

// edit button for listening to clicks
document.querySelectorAll('.edit-button').forEach(button => {
    button.addEventListener('click', function() {
        const noteId = button.getAttribute('data-note-id');
        toggleEditForm(noteId);
    });
});

// showing the edit button form
function toggleEditForm(noteId) {
    const form = document.getElementById(`edit-form-${noteId}`);
    if (form.style.display === "none" || form.style.display === "") {
        form.style.display = "block";
    } else {
        form.style.display = "none";
    }
}

// Bin link if empty
document.addEventListener('DOMContentLoaded', function() {
    const binLink = document.getElementById('bin-link');
    binLink.addEventListener('click', function(e) {
        fetch('/check_bin')
            .then(response => response.json())
            .then(data => {
                if (data.is_empty) {
                    e.preventDefault(); 
                    alert('Bin is empty!');
                }
            })
    });
});

// Archive Link if empty
document.addEventListener('DOMContentLoaded', function() {
    const archiveLink = document.getElementById('archive-link');
    archiveLink.addEventListener('click', function(e) {
        fetch('/check_archive')
            .then(response => response.json())
            .then(data => {
                if (data.is_empty) {
                    e.preventDefault(); // Only prevent the default behavior if the bin is empty
                    alert('Archive is empty!');
                }
            })
    });
});






function confirmDelete() {
    return confirm('Are you certain you want to delete this permenantly?');
}

function confirmEmptyTrash() {
    return confirm("Selecting 'Yes' will permenantly delete all notes in your bin (this is irreversible)")
}

