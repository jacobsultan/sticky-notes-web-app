import sys
import os
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Note, NoteState, NotePin
from datetime import datetime



@pytest.fixture
def test_app():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture
def runner(test_app):
    return test_app.test_cli_runner()

@pytest.fixture
def sample_note(test_app):
    note = Note(
        content='Test note content',
        date=datetime.utcnow(),
        state=NoteState.ACTIVE,
        pin=NotePin.NOTPINNED
    )
    db.session.add(note)
    db.session.commit()
    return note

def test_search_notes(client):
    notes = [
        Note(content='Apple pie recipe', state=NoteState.ACTIVE, pin=NotePin.NOTPINNED),
        Note(content='Banana bread recipe', state=NoteState.ACTIVE, pin=NotePin.NOTPINNED),
        Note(content='Shopping list', state=NoteState.ACTIVE, pin=NotePin.NOTPINNED)
    ]
    with client.application.app_context():
        db.session.bulk_save_objects(notes)
        db.session.commit()

    response = client.get('/?query=recipe')
    assert response.status_code == 200
    assert b'Apple pie recipe' in response.data
    assert b'Banana bread recipe' in response.data
    assert b'Shopping list' not in response.data

def test_create_note(client):
    response = client.post('/', data={'note': 'New test note'})
    assert response.status_code == 302
    with client.application.app_context():
        assert Note.query.count() == 1
        note = Note.query.first()
        assert note.content == 'New test note'
        assert note.state == NoteState.ACTIVE
        assert note.pin == NotePin.NOTPINNED

def test_edit_note(client, sample_note):
    response = client.post(f'/note/{sample_note.id}/edit',
                           data={'content': 'Updated content'})
    assert response.status_code == 302
    with client.application.app_context():
        updated_note = db.session.get(Note,sample_note.id)
        assert updated_note.content == 'Updated content'

def test_delete_note(client, sample_note):
    # delete-note actually deletes the note permanently
    response = client.delete(f'/note/{sample_note.id}/delete-note/')
    assert response.status_code == 204
    with client.application.app_context():
        deleted_note = db.session.get(Note,sample_note.id)
        assert deleted_note is None  # If it's truly deleted from DB

def test_archive_note(client, sample_note):
    #toggle-archived to change state
    response = client.post(f'/note/{sample_note.id}/toggle-archived')
    assert response.status_code == 302
    with client.application.app_context():
        archived_note = db.session.get(Note,sample_note.id)
        assert archived_note.state == NoteState.ARCHIVED

def test_empty_bin(client):
    # Create notes in binned state
    notes = [
        Note(content='Note 1', state=NoteState.BINNED, pin=NotePin.NOTPINNED),
        Note(content='Note 2', state=NoteState.BINNED, pin=NotePin.NOTPINNED)
    ]
    with client.application.app_context():
        db.session.bulk_save_objects(notes)
        db.session.commit()

    #  empty-trash is the correct endpoint
    response = client.post('/empty-trash')
    assert response.status_code == 302
    with client.application.app_context():
        assert Note.query.filter_by(state=NoteState.BINNED).count() == 0

def test_check_bin_status(client):
    response = client.get('/check-bin')
    assert response.status_code == 200
    assert response.json['is_empty'] == True

    # Add a binned note
    note = Note(content='Binned note', state=NoteState.BINNED, pin=NotePin.NOTPINNED)
    with client.application.app_context():
        db.session.add(note)
        db.session.commit()

    response = client.get('/check-bin')
    assert response.status_code == 200
    assert response.json['is_empty'] == False

def test_pin_note(client, sample_note):
    # Use the toggle-pin endpoint
    response = client.post(f'/note/{sample_note.id}/toggle-pin')
    assert response.status_code == 302
    with client.application.app_context():
        pinned_note = db.session.get(Note,sample_note.id)
        assert pinned_note.pin == NotePin.PINNED

def test_pinned_notes_appear_first(client):
    notes = [
        Note(content='Unpinned note 1', state=NoteState.ACTIVE, pin=NotePin.NOTPINNED),
        Note(content='Pinned note 1', state=NoteState.ACTIVE, pin=NotePin.PINNED),
        Note(content='Unpinned note 2', state=NoteState.ACTIVE, pin=NotePin.NOTPINNED)
    ]
    with client.application.app_context():
        db.session.bulk_save_objects(notes)
        db.session.commit()

    response = client.get('/')
    assert response.status_code == 200
    pinned_pos = response.data.find(b'Pinned note 1')
    unpinned_pos = response.data.find(b'Unpinned note 1')
    assert pinned_pos < unpinned_pos

def test_move_note_to_bin(client, sample_note):
    response = client.post(f'/note/{sample_note.id}/move-to-bin')
    assert response.status_code == 302
    with client.application.app_context():
        binned_note = db.session.get(Note, sample_note.id)
        assert binned_note.state == NoteState.BINNED

def test_restore_note_from_bin(client):
    # Create a binned note
    note = Note(content='Binned note', state=NoteState.BINNED, pin=NotePin.NOTPINNED)
    with client.application.app_context():
        db.session.add(note)
        db.session.commit()
        note_id = note.id

    response = client.post(f'/note/{note_id}/restore')
    assert response.status_code == 302
    with client.application.app_context():
        restored_note = db.session.get(Note, note_id)
        assert restored_note.state == NoteState.ACTIVE

def test_note_creation_with_empty_content(client):
    response = client.post('/', data={'note': ''})
    assert response.status_code == 400  

def test_archived_notes_view(client):
    notes = [
        Note(content='Active note', state=NoteState.ACTIVE, pin=NotePin.NOTPINNED),
        Note(content='Archived note', state=NoteState.ARCHIVED, pin=NotePin.NOTPINNED)
    ]
    with client.application.app_context():
        db.session.bulk_save_objects(notes)
        db.session.commit()

    response = client.get('/archived')
    assert response.status_code == 200
    assert b'Archived note' in response.data
    assert b'Active note' not in response.data


def test_note_search_case_insensitive(client):
    notes = [
        Note(content='UPPER CASE NOTE', state=NoteState.ACTIVE, pin=NotePin.NOTPINNED),
        Note(content='lower case note', state=NoteState.ACTIVE, pin=NotePin.NOTPINNED)
    ]
    with client.application.app_context():
        db.session.bulk_save_objects(notes)
        db.session.commit()

    response = client.get('/?query=CASE')
    assert response.status_code == 200
    assert b'UPPER CASE NOTE' in response.data
    assert b'lower case note' in response.data

def test_concurrent_note_updates(client, sample_note):
    """Test handling of concurrent updates to the same note"""
    with client.application.app_context():
        # Simulate two concurrent updates
        note1 = db.session.get(Note, sample_note.id)
        note2 = db.session.get(Note, sample_note.id)
        
        note1.content = 'Update 1'
        note2.content = 'Update 2'
        
        db.session.commit()  
        try:
            db.session.commit()
        except:
            db.session.rollback()

def test_note_max_length(client):
    """Test that notes cannot exceed maximum length"""
    long_content = 'a' * 10001  
    response = client.post('/', data={'note': long_content})
    assert response.status_code == 400

def test_note_date_sorting(client):
    """Test that notes are sorted by date correctly"""
    from datetime import timedelta
    
    older_date = datetime.utcnow() - timedelta(days=1)
    newer_date = datetime.utcnow()
    
    notes = [
        Note(content='Older note', date=older_date, state=NoteState.ACTIVE, pin=NotePin.NOTPINNED),
        Note(content='Newer note', date=newer_date, state=NoteState.ACTIVE, pin=NotePin.NOTPINNED)
    ]
    with client.application.app_context():
        db.session.bulk_save_objects(notes)
        db.session.commit()

    response = client.get('/')
    assert response.status_code == 200
    # Verify newer notes appear first
    newer_pos = response.data.find(b'Newer note')
    older_pos = response.data.find(b'Older note')
    assert newer_pos < older_pos

def test_duplicate_note_content(client):
    """Test creating notes with duplicate content"""
    response = client.post('/', data={'note': 'Duplicate content'})
    assert response.status_code == 302
    
    # Try creating another note with same content
    response = client.post('/', data={'note': 'Duplicate content'})
    assert response.status_code == 302
    
    with client.application.app_context():
        assert Note.query.filter_by(content='Duplicate content').count() == 2

def test_empty_search_results(client):
    """Test behavior when search returns no results"""
    response = client.get('/?query=nonexistentterm')
    assert response.status_code == 200
    assert b'nonexistentterm" :&#40;' in response.data
