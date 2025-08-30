from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- APP CONFIGURATION ---
# The Flask app is initialized only once here.
app = Flask(__name__)

# NOTE: For deployment, you will need to change this to a PostgreSQL URL.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///the_essence_compass.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_super_secret_key_here' # This is required for Flask-Login

CORS(app) # This allows your frontend to talk to your backend

db = SQLAlchemy(app)

# --- FLASK-LOGIN SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)

# --- DATABASE MODELS ---
# This User model is now fully configured for Flask-Login with password hashing.
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # Stores the securely hashed password
    checkins = db.relationship('CheckIn', backref='user', lazy=True)
    journal_entries = db.relationship('JournalEntry', backref='user', lazy=True)

    def set_password(self, password):
        """Hashes the password and sets it to the password_hash field."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks the provided password against the stored hash."""
        return check_password_hash(self.password_hash, password)

# This is a required callback for Flask-Login to load a user from the session.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not username or not password:
        return jsonify({"message": "Missing email, username, or password"}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"message": "User with this email already exists"}), 409

    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid email or password"}), 401

    login_user(user)
    return jsonify({"message": "Login successful", "user": {"username": user.username, "email": user.email}}), 200

@app.route('/logout', methods=['POST'])
@login_required # This decorator ensures only logged-in users can access this route
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/check-in', methods=['POST'])
@login_required # Only logged-in users can create check-ins
def add_check_in():
    # The `current_user` object is provided by Flask-Login and holds the logged-in user.
    # We no longer need to create a dummy user.
    data = request.json
    mood = data.get('mood_score')
    energy = data.get('energy_score')

    if not mood or not energy:
        return jsonify({'error': 'Missing data'}), 400

    new_check_in = CheckIn(mood_score=mood, energy_score=energy, user_id=current_user.id)
    db.session.add(new_check_in)
    db.session.commit()

    return jsonify({'message': 'Check-in saved successfully'}), 201

# --- RUN THE APP ---
if __name__ == '__main__':
    with app.app_context():
        # This will create the database file and tables defined above
        db.create_all()
    app.run(debug=True)
