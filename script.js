document.addEventListener('DOMContentLoaded', () => {
    const noteForm = document.getElementById('note_form');
    const noteInput = document.getElementById('note_input');
    const notesList = document.getElementById('notes_list');

    noteForm.addEventListener('submit', function(e) {
        e.preventDefault(); // Prevent the form from submitting in the traditional way
        const noteText = noteInput.value.trim();

        if (noteText) {
            // Create a new note element
            const noteEl = document.createElement('div');
            noteEl.classList.add('note');
            noteEl.innerText = noteText;

            // Add a delete button for the note
            const deleteBtn = document.createElement('button');
            deleteBtn.innerText = 'Delete';
            deleteBtn.onclick = function() {
                notesList.removeChild(noteEl);
            };
            noteEl.appendChild(deleteBtn);

            // Append the note to the notes list
            notesList.appendChild(noteEl);

            // Clear the input
            noteInput.value = '';
        }
    });
});
