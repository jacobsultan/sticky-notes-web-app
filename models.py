from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Enum
import enum

db = SQLAlchemy()


class NoteState(enum.Enum):
    ACTIVE = 1
    ARCHIVED = 2
    BINNED = 3

class NotePin(enum.Enum):
    NOTPINNED = 1
    PINNED = 2


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    state = db.Column(Enum(NoteState), default=NoteState.ACTIVE, nullable=False)
    pin = db.Column(Enum(NotePin), default=NotePin.NOTPINNED, nullable=False)

    date = db.Column(db.DateTime, default=datetime.utcnow)