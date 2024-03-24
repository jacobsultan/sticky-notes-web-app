from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db
from models import Note, NoteState, NotePin
from datetime import datetime


app = Flask(__name__) # initialised flask and the root path
app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db' #setting db sqlight
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #' disable Flask-SQLAlchemy event system, which is not needed and helps save resources.'

db.init_app(app)


with app.app_context():# push context manually to app
    db.create_all()


@app.route('/', methods=['GET', 'POST']) # root accepts these methods to get info from server and post data
def index():
    if request.method == "POST": #if the forms been submitted
        note_content = request.form["note"] #retrieves note
        if note_content: #making sure the note isn't empty
            new_note = Note(content=note_content, state=NoteState.ACTIVE)  # creates a note instance for the model
            db.session.add(new_note)
            db.session.commit()
        return redirect(url_for('index')) #preventative measure for resubmitting 
    ordered_notes = Note.query.filter(Note.state == NoteState.ACTIVE).order_by(Note.pin != NotePin.PINNED, Note.date.desc()).all()
    search_results = {'main': [], 'archive': [], 'bin': []}
    query = request.args.get('query', '')
    if query:
        search_results['main'] = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.state==NoteState.ACTIVE).order_by(Note.pin != NotePin.PINNED,Note.date.desc()).all()
        search_results['archive'] = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.state == NoteState.ARCHIVED).order_by(Note.pin != NotePin.PINNED,Note.date.desc()).all()
        search_results['bin'] = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.state == NoteState.BINNED).order_by(Note.pin != NotePin.PINNED,Note.date.desc()).all()
    return render_template('index.html', notes=ordered_notes, search_results=search_results, query=query,STATE_ACTIVE=NoteState.ACTIVE.value, STATE_ARCHIVED=NoteState.ARCHIVED.value, STATE_BINNED=NoteState.BINNED.value,PIN_NOTPINNED=NotePin.NOTPINNED.value, PIN_PINNED=NotePin.PINNED.value)


@app.route('/archive',methods=['GET'])
def archive():
    query = request.args.get('query', '')
    archived_notes = Note.query.filter(Note.state == NoteState.ARCHIVED).order_by(Note.pin != NotePin.PINNED, Note.date.desc()).all()
    search_results_archive = []
    if query:
        search_results_archive = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.state == NoteState.ARCHIVED).order_by(Note.pin != NotePin.PINNED,Note.date.desc()).all()
    if archived_notes:
        return render_template('archive.html', notes=archived_notes, search_results = search_results_archive, query = query,STATE_ACTIVE=NoteState.ACTIVE.value, STATE_ARCHIVED=NoteState.ARCHIVED.value, STATE_BINNED=NoteState.BINNED.value,PIN_NOTPINNED=NotePin.NOTPINNED.value, PIN_PINNED=NotePin.PINNED.value)
    else:
        return redirect(url_for('index'))

@app.route('/bin', methods = ['GET'])
def bin():
    query = request.args.get('query', '')
    binned_notes = Note.query.filter(Note.state == NoteState.BINNED).order_by(Note.pin != NotePin.PINNED, Note.date.desc()).all()
    search_results_bin = []
    if query:
        search_results_bin = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.state == NoteState.BINNED).order_by(Note.pin != NotePin.PINNED,Note.date.desc()).all()
    if binned_notes:
        return render_template('bin.html', notes=binned_notes, search_results = search_results_bin, query = query,STATE_ACTIVE=NoteState.ACTIVE.value, STATE_ARCHIVED=NoteState.ARCHIVED.value, STATE_BINNED=NoteState.BINNED.value,PIN_NOTPINNED=NotePin.NOTPINNED.value, PIN_PINNED=NotePin.PINNED.value)
    else:
        return redirect(url_for('index'))



@app.route('/note/<int:note_id>/toggle-pin', methods=['POST'])
def toggle_pin(note_id):
    note = Note.query.get(note_id)
    if note.pin == NotePin.PINNED:
        note.pin = NotePin.NOTPINNED
    else:
        note.pin = NotePin.PINNED
    db.session.commit()
    return redirect(request.headers.get("Referer"))
"""

@app.route('/note/<int:note_id>/toggle-pin', methods=['POST'])
def toggle_pin(note_id):
    note = Note.query.get(note_id)
    if note:
        if note.pin == NotePin.PINNED:
            note.pin = NotePin.NOTPINNED
        else:
            note.pin = NotePin.PINNED
        db.session.commit()
    return redirect(request.headers.get("Referer"))"""


@app.route('/note/<int:note_id>/toggle-bin',methods = ["POST"]) 
def toggle_bin(note_id):
    note = Note.query.get(note_id)
    if note.state == NoteState.BINNED:
        note.state = NoteState.ACTIVE
    else:
        note.state = NoteState.BINNED
    db.session.commit()
    return redirect(request.headers.get("Referer"))

@app.route('/note/<int:note_id>/toggle-archived',methods = ["POST"])
def toggle_archived(note_id):
    note = Note.query.get(note_id)
    if note.state == NoteState.ACTIVE:
        note.state = NoteState.ARCHIVED
    else:
        note.state = NoteState.ACTIVE
    db.session.commit()
    return redirect(request.headers.get("Referer"))  

@app.route('/note/<int:note_id>/edit', methods=['POST']) 
def edit_note(note_id):
    note = Note.query.get(note_id)
    edited_content = request.form['content']
    if edited_content:
        note.content = edited_content
        note.date = note.date = datetime.utcnow()
        db.session.commit()
        return redirect(request.headers.get("Referer"))

@app.route('/note/<int:note_id>/delete-note/', methods=["DELETE"])
def delete_note(note_id):
    note_to_delete = Note.query.get(note_id)
    if note_to_delete:
        db.session.delete(note_to_delete)
        db.session.commit()
        return '', 204  # Return an empty response with a 204 status code

@app.route('/<string:page>/cancel-search', methods=['POST'])
def cancel_search(page):
    return redirect(url_for(page))  



@app.route('/empty-trash', methods = ["POST"])
def empty_trash():
    notes_to_delete = Note.query.filter(Note.state ==NoteState.BINNED).all()
    for note in notes_to_delete:
        db.session.delete(note)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/check-bin', methods = ['GET','POST'])
def check_bin():
    if Note.query.filter(Note.state == NoteState.BINNED).count() == 0:
        return jsonify({"is_empty": True})
    else:
        return jsonify({"is_empty": False})
    

@app.route('/check-archive',methods = ['GET'])
def check_archive():
    if Note.query.filter(Note.state == NoteState.ARCHIVED).count() == 0:
        return jsonify({"is_empty": True})
    else:
        return jsonify({"is_empty": False})

    

if __name__ == '__main__':
    app.run()
