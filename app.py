from flask import Flask, render_template, request, redirect, url_for, jsonify,flash
from flask_migrate import Migrate
from models import db
from models import Note, NoteState, NotePin
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

# Create the Flask application instance
app = Flask(__name__)
import os
app.secret_key = os.getenv('SECRET_KEY', 'fallback_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',  # Use DATABASE_URL if it exists
    'postgresql://flask_user:hello@localhost:5432/sticky_notes'  # Hardcode for fallback if necessary
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



db.init_app(app) #initialises database

# Initialize Flask-Migrate
migrate = Migrate(app, db)


@app.route('/', methods=['GET', 'POST']) # Route accepts these methods to get info from server and post data
def index():
    if request.method == "POST":
        note_content = request.form.get("note", "").strip()
        if not note_content:
            return '', 400
        if len(note_content) > 10000:
            return '', 400
            
        new_note = Note(content=note_content, state=NoteState.ACTIVE)
        db.session.add(new_note)
        db.session.commit()
        return redirect(url_for('index'))
        
    ordered_notes = Note.query.filter(Note.state == NoteState.ACTIVE).order_by(Note.pin != NotePin.PINNED, Note.date.desc()).all() # Filtering notes to get active, and pinned first then by date
    search_results = {'main': [], 'archive': [], 'bin': []}
    query = request.args.get('query', '') # Receive the search query
    if query: # Filters for the query from different sections of the notes
        search_results['main'] = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.state==NoteState.ACTIVE).order_by(Note.pin != NotePin.PINNED,Note.date.desc()).all()
        search_results['archive'] = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.state == NoteState.ARCHIVED).order_by(Note.pin != NotePin.PINNED,Note.date.desc()).all()
        search_results['bin'] = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.state == NoteState.BINNED).order_by(Note.pin != NotePin.PINNED,Note.date.desc()).all()
    return render_template('index.html', notes=ordered_notes, search_results=search_results,
                            query=query,STATE_ACTIVE=NoteState.ACTIVE.value, STATE_ARCHIVED=NoteState.ARCHIVED.value,
                              STATE_BINNED=NoteState.BINNED.value,PIN_NOTPINNED=NotePin.NOTPINNED.value, PIN_PINNED=NotePin.PINNED.value)
    # Renders the template with the various different notes and states

# Same as index but specifically for archived notes
@app.route('/archive',methods=['GET'])
def archive():
    query = request.args.get('query', '')
    archived_notes = Note.query.filter(Note.state == NoteState.ARCHIVED).order_by(Note.pin != NotePin.PINNED, Note.date.desc()).all()
    search_results_archive = []
    if query:
        search_results_archive = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.state == NoteState.ARCHIVED).order_by(Note.pin != NotePin.PINNED,Note.date.desc()).all()
    if archived_notes:
        return render_template('archived.html', notes=archived_notes, search_results = search_results_archive,
                                query = query,STATE_ACTIVE=NoteState.ACTIVE.value, STATE_ARCHIVED=NoteState.ARCHIVED.value,
                                  STATE_BINNED=NoteState.BINNED.value,PIN_NOTPINNED=NotePin.NOTPINNED.value, PIN_PINNED=NotePin.PINNED.value)
    else:
        # If there aren't any archived notes left it'll redirect you to index
        return redirect(url_for('index'))

#Same as index but specifically for binned notes
@app.route('/bin', methods = ['GET'])
def bin():
    query = request.args.get('query', '')
    binned_notes = Note.query.filter(Note.state == NoteState.BINNED).order_by(Note.pin != NotePin.PINNED, Note.date.desc()).all()
    search_results_bin = []
    if query:
        search_results_bin = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.state == NoteState.BINNED).order_by(Note.pin != NotePin.PINNED,Note.date.desc()).all()
    if binned_notes:
        return render_template('bin.html', notes=binned_notes, search_results = search_results_bin, query = query,
                               STATE_ACTIVE=NoteState.ACTIVE.value, STATE_ARCHIVED=NoteState.ARCHIVED.value,
                                 STATE_BINNED=NoteState.BINNED.value,PIN_NOTPINNED=NotePin.NOTPINNED.value, PIN_PINNED=NotePin.PINNED.value)
    else:
        return redirect(url_for('index'))


# Button to toggle pinned back and forth in database
@app.route('/note/<int:note_id>/toggle-pin', methods=['POST'])
def toggle_pin(note_id):
    note =  db.session.get(Note,note_id)
    if note.pin == NotePin.PINNED:
        note.pin = NotePin.NOTPINNED
    else:
        note.pin = NotePin.PINNED
    db.session.commit()
    return redirect(request.headers.get("Referer")) # Returns to page that was previously on

# Button to toggle state in database to binned or if binned back to active(main)
@app.route('/note/<int:note_id>/toggle-bin',methods = ["POST"]) 
def toggle_bin(note_id):
    note =  db.session.get(Note,note_id)
    if note.state == NoteState.BINNED:
        note.state = NoteState.ACTIVE
    else:
        note.state = NoteState.BINNED
    db.session.commit()
    return redirect(request.headers.get("Referer"))

# Button to toggle state in database to archived or if archived back to active(main)
@app.route('/note/<int:note_id>/toggle-archived',methods = ["POST"])
def toggle_archived(note_id):
    note =  db.session.get(Note,note_id)
    if note.state == NoteState.ACTIVE:
        note.state = NoteState.ARCHIVED
    else:
        note.state = NoteState.ACTIVE
    db.session.commit()
    return redirect(request.headers.get("Referer"))  

# Route for editing notes
@app.route('/note/<int:note_id>/edit', methods=['GET', 'POST'])
def edit_note(note_id):
    note = db.session.get(Note, note_id)  # Finds the note from the database using the note id
    
    if request.method == 'POST':
        edited_content = request.form['content']  # Retrieves the content to update the note to 
        
        # Check for validation: content should not be empty and should be between 1 and 10,000 characters
        if not edited_content or len(edited_content) > 10000:
            flash("Note content must be between 1 and 10000 characters", "error")
            return render_template('edit_note.html', note=note)  # Re-render the edit page with error message
        
        # If the content is valid, update the note and commit to the database
        note.content = edited_content
        note.date = datetime.utcnow()  # Updates the timestamp on the note
        db.session.commit()
        
        return redirect(request.headers.get("Referer"))  # Redirects back to the previous page

    # Render the edit form with the current note's content for the GET request
    return render_template('edit_note.html', note=note)

# Function for deleting a note
@app.route('/note/<int:note_id>/delete-note/', methods=["DELETE"])
def delete_note(note_id):
    note_to_delete =  db.session.get(Note,note_id)
    if note_to_delete:
        db.session.delete(note_to_delete)
        db.session.commit()
        return '', 204  # Return an empty response with a 204 status code
# If cancellin a search return to page it was called from (trying different means)
@app.route('/<string:page>/cancel-search', methods=['POST'])
def cancel_search(page):
    return redirect(url_for(page))  


# Deletes all notes with in binned state
@app.route('/empty-trash', methods = ["POST"])
def empty_trash():
    notes_to_delete = Note.query.filter(Note.state ==NoteState.BINNED).all()
    for note in notes_to_delete: # Loops through binned notes to delete them individually
        db.session.delete(note)
    db.session.commit()
    return redirect(url_for('index'))

# Checks if there are any binned notes
@app.route('/check-bin', methods = ['GET','POST'])
def check_bin():
    if Note.query.filter(Note.state == NoteState.BINNED).count() == 0:
        return jsonify({"is_empty": True}) #To be passed back to JS so a JSON response
    else:
        return jsonify({"is_empty": False})
    
# Checks if there are any archived notes
@app.route('/check-archive',methods = ['GET'])
def check_archive():
    if Note.query.filter(Note.state == NoteState.ARCHIVED).count() == 0:
        return jsonify({"is_empty": True})
    else:
        return jsonify({"is_empty": False})

@app.route('/note/<int:note_id>/move-to-bin', methods=['POST'])
def move_to_bin(note_id):
    note = db.session.get(Note, note_id)
    if note:
        note.state = NoteState.BINNED
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/note/<int:note_id>/restore', methods=['POST'])
def restore_from_bin(note_id):
    note = db.session.get(Note, note_id)
    if note:
        note.state = NoteState.ACTIVE
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/archived')
def archived_notes():
    notes = Note.query.filter_by(state=NoteState.ARCHIVED).all()
    return render_template('archived.html', notes=notes)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
