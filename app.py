from flask import Flask, render_template, request, redirect, url_for,flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__) # initialised flask and the root path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db' #setting db sqlight
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #' disable Flask-SQLAlchemy event system, which is not needed and helps save resources.'

db = SQLAlchemy(app) #creating db instance


class Note(db.Model): #db.model is a class that you inherit from for all models for flask sqlachemy
    id = db.Column(db.Integer, primary_key=True) #first column using id(int) as a key
    content = db.Column(db.String(200), nullable=False) #second column sets max input as 200chars and cant be empty


with app.app_context():# push context manually to app
    db.create_all()

@app.route('/', methods=['GET', 'POST']) # root accepts these methods to get info from server and post data
def index():
    if request.method == "POST": #if the forms been submitted
        note_content = request.form["note"] #retrieves note
        if note_content: #making sure the note isn't empty
            new_note = Note(content=note_content) #creates a note instance for the model
            print(new_note)
            try:
                db.session.add(new_note)
                db.session.commit()
            except Exception as e:
                print("Failed to add note:", e)
                db.session.rollback()  # Rollback the session in case of error
        return redirect(url_for('index')) #preventative measure for resubmitting 
    notes = Note.query.all() #sqlachemy to request all notes to show
    return render_template('index.html', notes=notes) #this renders all the notes found in the db though index


@app.route('/delete/<int:note_id>', methods=['POST']) #new route for deleting notes, passes the note_id an int into the delete_note function
def delete_note(note_id):
    note_to_delete = Note.query.get(note_id) #query gets the note from db to delete from the id
    if note_to_delete: #makes sure the note exists and is found from the id 
        db.session.delete(note_to_delete)  #like staging
        db.session.commit() #acc passes through (likely issue found here if present)
    return redirect(url_for('index')) # takes back to index

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
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)


import os
print("Current working directory:", os.getcwd())