from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
# initialised flask and the root path


notes = []

@app.route('/', methods=['GET', 'POST'])
# root accepts these methods to get info from server and post data

def index():
    if request.method == "POST": #if the forms been submitted
        note = request.form["note"] #retrieves note
        notes.append(note) #stores it 
        return redirect(url_for('index')) #returns client to index page
    else:
        return render_template('index.html', notes=notes) #if its a get request opens index.html

if __name__ == '__main__':
    app.run(debug=True)
