from flask import Flask, render_template, request, redirect, url_for,flash
from flask_sqlalchemy import SQLAlchemy


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
    notes = Note.query.filter_by(archived=False, binned = False).all() #sqlachemy to request all notes to show
    return render_template('index.html', notes=notes) #this renders all the notes found in the db though index



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
    referrer = request.headers.get("Referer")
    return redirect(referrer)


@app.route('/bin_note/<int:note_id>', methods=['POST']) #new route for deleting notes, passes the note_id an int into the delete_note function
def bin_note(note_id):
    note_to_delete = Note.query.get(note_id) #query gets the note from db to delete from the id
    if note_to_delete: #makes sure the note exists and is found from the id 
        note_to_delete.binned = True  #like staging
        db.session.commit() #acc passes through (likely issue found here if present)
        flash('Note moved to bin.')
    referrer = request.headers.get("Referer")
    return redirect(referrer)

@app.route('/unbin_note/<int:note_id>', methods = ['POST'])
def unbin_note(note_id):
    note_to_undelete = Note.query.get(note_id)
    if note_to_undelete:
        note_to_undelete.binned = False
        db.session.commit()
    referrer = request.headers.get("Referer")
    return redirect(referrer)

@app.route('/edit/<int:note_id>', methods=['POST'])
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    edited_content = request.form['content'].strip()
    if edited_content:
        note.content = edited_content
        db.session.commit()
        flash('Note updated successfully.', 'success')
    else:
        flash('Note content cannot be blank.', 'error')
    referrer = request.headers.get("Referer")
    return redirect(referrer)

@app.route('/delete/<int:note_id>',methods = ["POST"])
def delete_note(note_id):
    note_to_delete = Note.query.get(note_id)
    if note_to_delete:
        db.session.delete(note_to_delete)
        db.session.commit()
        flash("Note successfully deleted")
    else:
        flash("Note not found :'(")
    return redirect(ref())
    



@app.route('/bin')
def bin():
    binned_notes = Note.query.filter_by(binned = True).all()
    return render_template('bin.html', notes=binned_notes)

@app.route('/archive')
def archive():
    archived_notes = Note.query.filter_by(archived=True, binned = False).all()
    return render_template('archive.html',notes = archived_notes)



if __name__ == '__main__':
    app.run(debug=True)


import os
print("Current working directory:", os.getcwd())