from flask import Flask, render_template, request, redirect, url_for,flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime



app = Flask(__name__) # initialised flask and the root path
app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db' #setting db sqlight
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #' disable Flask-SQLAlchemy event system, which is not needed and helps save resources.'

db = SQLAlchemy(app) #creating db instance


class Note(db.Model): #db.model is a class that you inherit from for all models for flask sqlachemy
    id = db.Column(db.Integer, primary_key=True) #first column using id(int) as a key
    content = db.Column(db.String(200), nullable=False) #second column sets max input as 200chars and cant be empty
    archived = db.Column(db.Boolean, default=False, nullable=False)
    binned = db.Column(db.Boolean, default=False, nullable=False)
    date = db.Column(db.DateTime, default =datetime.utcnow)
    pinned = db.Column(db.Boolean,default = False)


with app.app_context():# push context manually to app
    db.create_all()

def ref():
    return request.headers.get("Referer")

@app.route('/', methods=['GET', 'POST']) # root accepts these methods to get info from server and post data
def index():
    if request.method == "POST": #if the forms been submitted
        note_content = request.form["note"] #retrieves note
        if note_content: #making sure the note isn't empty
            new_note = Note(content=note_content,archived = False, binned = False) #creates a note instance for the model
            try:
                db.session.add(new_note)
                db.session.commit()
            except Exception as e:
                print("Failed to add note:", e)
                db.session.rollback()  # Rollback the session in case of error
        return redirect(url_for('index')) #preventative measure for resubmitting 
    ordered_notes = Note.query.filter_by(archived=False, binned=False).order_by(Note.pinned.desc(), Note.date.desc()).all()
    return render_template('index.html', notes=ordered_notes) #this renders all the notes found in the db though index


@app.route('/toggle_pin/<int:note_id>', methods=['POST'])
def toggle_pin(note_id):
    note = Note.query.get(note_id)
    note.pinned = not note.pinned  # Toggle pin status
    db.session.commit()
    return redirect(ref())

@app.route('/toggle_bin/<int:note_id>',methods = ["POST"])
def toggle_bin(note_id):
    note = Note.query.get(note_id)
    note.binned = not note.binned
    db.session.commit()
    return redirect(ref())

@app.route('/toggle_archived/<int:note_id>',methods = ["POST"])
def toggle_archived(note_id):
    note = Note.query.get(note_id)
    note.archived = not note.archived
    db.session.commit()
    return redirect(ref())  

@app.route('/archive_note/<int:note_id>', methods=['POST'])
def archive_note(note_id):
    note_to_archive = Note.query.get(note_id)
    if note_to_archive:
        note_to_archive.archived = True
        db.session.commit()
        flash('Note archived successfully.')
    else:
        flash('Note not found.')
    referrer = request.headers.get("Referer")
    return redirect(referrer)

@app.route('/unarchive_note/<int:note_id>', methods=['POST'])
def unarchive_note(note_id):
    note_to_unarchive = Note.query.get(note_id)
    if note_to_unarchive:
        note_to_unarchive.archived = False
        db.session.commit()
        flash('Note removed from archive successfully.')
    else:
        flash('Note not found.')
    
    if Note.query.filter_by(archived = True).count() == 0:
        return redirect(url_for('index'))
    else:
        return redirect(ref())


@app.route('/bin_note/<int:note_id>', methods=['POST']) #new route for deleting notes, passes the note_id an int into the delete_note function
def bin_note(note_id):
    note_to_bin = Note.query.get(note_id) #query gets the note from db to delete from the id
    if note_to_bin: #makes sure the note exists and is found from the id 
        note_to_bin.binned = True  #like staging
        note_to_bin.archived = False
        db.session.commit() #acc passes through (likely issue found here if present)
        flash('Note moved to bin.')
    if '/archive' in request.referrer:
        if Note.query.filter_by(archived=True, binned=False).count() == 0:
            return redirect(url_for('index'))
        
    return redirect(ref())

@app.route('/unbin_note/<int:note_id>', methods = ['POST'])
def unbin_note(note_id):
    note_to_undelete = Note.query.get(note_id)
    if note_to_undelete:
        note_to_undelete.binned = False
        db.session.commit()
    if Note.query.filter_by(binned = True).count() == 0:
        return redirect(url_for('index'))
    return redirect(ref())

@app.route('/edit/<int:note_id>', methods=['POST'])
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    edited_content = request.form['content'].strip()
    if edited_content:
        note.content = edited_content
        note.date = note.date = datetime.utcnow()
        db.session.commit()

        flash('Note updated successfully.', 'success')
    else:
        flash('Note content cannot be blank.', 'error')
    return redirect(ref())

@app.route('/delete/<int:note_id>',methods = ["POST"])
def delete_note(note_id):
    note_to_delete = Note.query.get(note_id)
    if note_to_delete:
        db.session.delete(note_to_delete)
        db.session.commit()
        flash("Note successfully deleted")
    else:
        flash("Note not found :'(")
    if Note.query.filter_by(binned = True).count() == 0:
        return redirect(url_for('index'))
    else:
        return redirect(ref())

@app.route('/empty_trash/', methods = ["POST"])
def empty_trash():
    notes_to_delete = Note.query.filter_by(binned=True).all()
    for note in notes_to_delete:
        db.session.delete(note)
    db.session.commit()
    flash("Trash successfully emptied")
    return redirect(url_for('index'))
    



@app.route('/bin')
def bin():
    binned_notes = Note.query.filter_by(binned = True).order_by(Note.pinned.desc(), Note.date.desc()).all()
    return render_template('bin.html', notes=binned_notes)

@app.route('/archive')
def archive():
    archived_notes = Note.query.filter_by(archived=True, binned = False).order_by(Note.pinned.desc(), Note.date.desc()).all()
    return render_template('archive.html',notes = archived_notes)



if __name__ == '__main__':
    app.run(debug=True)


@app.route('/check_bin')
def check_bin():
    if Note.query.filter_by(binned = True).count() == 0:
        return jsonify({"is_empty": True})
    else:
        return jsonify({"is_empty": False})
    



@app.route('/check_archive')
def check_archive():
    if Note.query.filter_by(archived = True).count() == 0:
        return jsonify({"is_empty": True})
    else:
        return jsonify({"is_empty": False})

@app.route('/search')
def search():
    query = request.args.get('query', '')
    search_notes_main = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.archived == False, Note.binned == False)
    search_notes_main_ord = search_notes_main.order_by(Note.pinned.desc(), Note.date.desc()).all()
    search_notes_archive = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.archived == True, Note.binned == False)
    search_notes_archive_ord = search_notes_archive.order_by(Note.pinned.desc(), Note.date.desc()).all()
    search_notes_bin = Note.query.filter(Note.content.ilike(f'%{query}%'),Note.binned == True)
    search_notes_bin_ord = search_notes_bin.order_by(Note.pinned.desc(), Note.date.desc()).all()

    return render_template('search.html', notes_main=search_notes_main_ord,notes_archive = search_notes_archive_ord,notes_bin = search_notes_bin_ord, searchcontent = query)





import os
print("Current working directory:", os.getcwd())