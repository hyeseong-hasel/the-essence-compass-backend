from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

# --- APP CONFIGURATION ---
app = Flask(__name__)
# This will be your temporary SQLite database file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///the_essence_compass.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app) # This allows your frontend to talk to your backend

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
# These are the "blueprints" for your database tables
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    checkins = db.relationship('CheckIn', backref='user', lazy=True)
    journal_entries = db.relationship('JournalEntry', backref='user', lazy=True)

class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    mood_score = db.Column(db.Integer, nullable=False)
    energy_score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- API ENDPOINTS ---
@app.route('/api/check-in', methods=['POST'])
def add_check_in():
    # Example for receiving data from the frontend
    data = request.json
    mood = data.get('mood_score')
    energy = data.get('energy_score')

    if not mood or not energy:
        return jsonify({'error': 'Missing data'}), 400

    # For now, we will create a dummy user
    # Later you will handle real users
    user = User.query.first()
    if not user:
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

    # Create a new check-in and save it to the database
    new_check_in = CheckIn(mood_score=mood, energy_score=energy, user_id=user.id)
    db.session.add(new_check_in)
    db.session.commit()

    return jsonify({'message': 'Check-in saved successfully'}), 201

# --- RUN THE APP ---
if __name__ == '__main__':
    with app.app_context():
        # This will create the database file and tables defined above
        db.create_all()
    app.run(debug=True)