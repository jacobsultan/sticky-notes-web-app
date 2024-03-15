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


@app.route('/', methods=['GET', 'POST']) # root accepts these methods to get info from server and post data
def index():
    if request.method == "POST": #if the forms been submitted
        note_content = request.form["note"] #retrieves note
        if note_content: #making sure the note isn't empty
            new_note = Note(content=note_content,archived = False, binned = False) #creates a note instance for the model
            db.session.add(new_note)
            db.session.commit()
        return redirect(url_for('index')) #preventative measure for resubmitting 
    ordered_notes = Note.query.filter_by(archived=False, binned=False).order_by(Note.pinned.desc(), Note.date.desc()).all()
    search_results = {}
    query = request.args.get('query', '')
    if query:
        search_results['main'] = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.archived==False, Note.binned==False).order_by(Note.pinned.desc(),Note.date.desc()).all()
        search_results['archive'] = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.archived==True, Note.binned==False).order_by(Note.pinned.desc(),Note.date.desc()).all()
        search_results['bin'] = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.binned==True).order_by(Note.pinned.desc(),Note.date.desc()).all()
    return render_template('index.html', notes=ordered_notes, search_results=search_results, query=query)

@app.route('/archive',methods=['GET'])
def archive():
    query = request.args.get('query', '')
    archived_notes = Note.query.filter_by(archived=True, binned = False).order_by(Note.pinned.desc(), Note.date.desc()).all()
    search_results_archive = []
    if query:
        search_results_archive = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.archived==True, Note.binned==False).order_by(Note.pinned.desc(),Note.date.desc()).all()
    if archived_notes:
        return render_template('archive.html', notes=archived_notes, search_results = search_results_archive, query = query)
    else:
        return redirect(url_for('index'))

@app.route('/bin', methods = ['GET'])
def bin():
    query = request.args.get('query', '')
    binned_notes = Note.query.filter_by(binned = True).order_by(Note.pinned.desc(), Note.date.desc()).all()
    search_results_bin = []
    if query:
        search_results_bin = Note.query.filter(Note.content.ilike(f'%{query}%'), Note.binned == True).order_by(Note.pinned.desc(),Note.date.desc()).all()
    if binned_notes:
        return render_template('bin.html', notes=binned_notes, search_results = search_results_bin, query = query)
    else:
        return redirect(url_for('index'))



@app.route('/toggle_pin/<int:note_id>', methods=['POST'])
def toggle_pin(note_id):
    note = Note.query.get(note_id)
    note.pinned = not note.pinned  # Toggle pin status
    db.session.commit()
    return redirect(request.headers.get("Referer"))

@app.route('/toggle_bin/<int:note_id>',methods = ["POST"])
def toggle_bin(note_id):
    note = Note.query.get(note_id)
    note.binned = not note.binned
    note.archived = False
    db.session.commit()
    return redirect(request.headers.get("Referer"))

@app.route('/toggle_archived/<int:note_id>',methods = ["POST"])
def toggle_archived(note_id):
    note = Note.query.get(note_id)
    note.archived = not note.archived
    db.session.commit()
    return redirect(request.headers.get("Referer"))  

@app.route('/edit/<int:note_id>', methods=['POST'])
def edit_note(note_id):
    note = Note.query.get(note_id)
    edited_content = request.form['content']
    if edited_content:
        note.content = edited_content
        note.date = note.date = datetime.utcnow()
        db.session.commit()
        return redirect(request.headers.get("Referer"))

@app.route('/delete_note/<int:note_id>',methods = ["POST"])
def delete_note(note_id):
    note_to_delete = Note.query.get(note_id)
    if note_to_delete:
        db.session.delete(note_to_delete)
        db.session.commit()
        return redirect(request.headers.get("Referer"))

@app.route('/cancel_search/<string:page>', methods=['POST'])
def cancel_search(page):
    # Ensure that 'page' is a valid endpoint before redirecting

    return redirect(url_for(page))  # Default redirect if 'page' is not valid



@app.route('/empty_trash/', methods = ["POST"])
def empty_trash():
    notes_to_delete = Note.query.filter_by(binned=True).all()
    for note in notes_to_delete:
        db.session.delete(note)
    db.session.commit()
    return redirect(url_for('index'))
    
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

import os
print("Current working directory:", os.getcwd())