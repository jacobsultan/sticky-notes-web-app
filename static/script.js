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

function toggleEditForm(noteId) {
    const form = document.getElementById(`edit-form-${noteId}`);
    if (form.style.display === "none" || form.style.display === "") {
        form.style.display = "block";
    } else {
        form.style.display = "none";
    }
}