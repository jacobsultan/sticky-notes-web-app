from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db
from models import Note, NoteState, NotePin
from datetime import datetime

# Create the Flask application instance
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app = Flask(__name__) # Initialised flask and the root path
app.secret_key = 'secret_key' # Secret key needed for session handling
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db' #Setting db sqlight
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #Disable Flask-SQLAlchemy event system, which is not needed and helps save resources.'

db.init_app(app) #initialises database


with app.app_context():
    db.create_all() # Creates database


@app.route('/', methods=['GET', 'POST']) # Route accepts these methods to get info from server and post data
def index():
    if request.method == "POST": #If the forms been submitted
        note_content = request.form["note"] # Retrieves note info
        if not note_content or len(note_content) > 10000:
            return 'Note content must be between 1 and 10000 characters', 400
        if note_content.strip():  # Check if content is not empty
            new_note = Note(content=note_content, state=NoteState.ACTIVE)  # Creates a note instance for the model
            db.session.add(new_note) # Adds new note to the database session
            db.session.commit() # Like git
        return redirect(url_for('index')) #Preventative measure for resubmitting 
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
@app.route('/note/<int:note_id>/edit', methods=['POST']) 
def edit_note(note_id):
    note = db.session.get(Note,note_id) #Finds the note from the database from the note id
    edited_content = request.form['content'] # Retrieves the content to update the note to 
    if edited_content:
        note.content = edited_content
        note.date = note.date = datetime.utcnow() #Updates the timestamp on the note
        db.session.commit()
        return redirect(request.headers.get("Referer"))

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
    app.run() # Left to the end so that if all the parts of the script runs successfully it launches the app
