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