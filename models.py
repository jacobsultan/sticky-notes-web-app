from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Enum
import enum

# Creates an instance to manipulate the database
db = SQLAlchemy()

# Creates an enumerated class for the three states
class NoteState(enum.Enum):
    ACTIVE = 1
    ARCHIVED = 2
    BINNED = 3

# Creates an enumerated class for the two pin states
class NotePin(enum.Enum):
    NOTPINNED = 1
    PINNED = 2

# Note class created to hold the ID for finding notes, the content of the notes, the timestamp, the state and whether pinned
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    state = db.Column(db.Enum(NoteState), default=NoteState.ACTIVE, nullable=False)
    pin = db.Column(db.Enum(NotePin), default=NotePin.NOTPINNED, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, content, state=NoteState.ACTIVE, pin=NotePin.NOTPINNED, date=None):
        self.content = content
        self.state = state
        self.pin = pin
        self.date = date or datetime.utcnow()