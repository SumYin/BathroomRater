from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
import os
from sqlalchemy import func

app = Flask(__name__)

# Database configuration
if os.environ.get('DATABASE_URL'):
    # Production database (PostgreSQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
else:
    # Local development database (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bathroom_ratings.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # Use environment variable in production
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    ratings = db.relationship('BathroomRating', backref='author', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BathroomRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # 'Male' or 'Female'
    cleanliness = db.Column(db.Integer, nullable=False)
    privacy = db.Column(db.Integer, nullable=False)
    accessibility = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.Integer, nullable=False)
    overall_rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    favorites = db.relationship('Favorite', backref='rating', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'location': self.location,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M'),
            'gender': self.gender,
            'cleanliness': self.cleanliness,
            'privacy': self.privacy,
            'accessibility': self.accessibility,
            'amenities': self.amenities,
            'overall_rating': self.overall_rating,
            'comments': self.comments,
            'author': self.author.username,
            'favorite_count': len(self.favorites)
        }

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating_id = db.Column(db.Integer, db.ForeignKey('bathroom_rating.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this feature.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

with app.app_context():
    db.create_all()

@app.route('/')
def landing():
    total_ratings = BathroomRating.query.count()
    total_users = User.query.count()
    total_locations = db.session.query(db.func.count(db.func.distinct(BathroomRating.location))).scalar()
    return render_template('landing.html', 
                         total_ratings=total_ratings,
                         total_users=total_users,
                         total_locations=total_locations)

@app.route('/app')
def index():
    ratings = BathroomRating.query.order_by(BathroomRating.timestamp.desc()).all()
    user_favorites = []
    if 'user_id' in session:
        user_favorites = [f.rating_id for f in Favorite.query.filter_by(user_id=session['user_id']).all()]
    return render_template('index.html', ratings=ratings, user_favorites=user_favorites)

@app.route('/share/<int:rating_id>')
def share_rating(rating_id):
    rating = BathroomRating.query.get_or_404(rating_id)
    share_data = rating.to_dict()
    share_url = request.host_url + f"app?rating={rating_id}"
    return render_template('share.html', rating=rating, share_url=share_url)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('landing'))

@app.route('/submit', methods=['POST'])
@login_required
def submit_rating():
    if request.method == 'POST':
        rating = BathroomRating(
            location=request.form['location'],
            timestamp=datetime.strptime(request.form['timestamp'], '%Y-%m-%dT%H:%M'),
            gender=request.form['gender'],
            cleanliness=int(request.form['cleanliness']),
            privacy=int(request.form['privacy']),
            accessibility=int(request.form['accessibility']),
            amenities=int(request.form['amenities']),
            overall_rating=int(request.form['overall_rating']),
            comments=request.form['comments'],
            user_id=session['user_id']
        )
        db.session.add(rating)
        db.session.commit()
        return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_rating(id):
    rating = BathroomRating.query.get_or_404(id)
    if rating.user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    db.session.delete(rating)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/favorite/<int:rating_id>', methods=['POST'])
@login_required
def toggle_favorite(rating_id):
    rating = BathroomRating.query.get_or_404(rating_id)
    favorite = Favorite.query.filter_by(user_id=session['user_id'], rating_id=rating_id).first()
    
    if favorite:
        db.session.delete(favorite)
        is_favorite = False
    else:
        favorite = Favorite(user_id=session['user_id'], rating_id=rating_id)
        db.session.add(favorite)
        is_favorite = True
    
    db.session.commit()
    return jsonify({
        'success': True,
        'is_favorite': is_favorite,
        'favorite_count': len(rating.favorites)
    })

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/top-bathrooms')
def top_bathrooms():
    # Get bathrooms with highest average ratings and most favorites
    top_rated = db.session.query(
        BathroomRating.location,
        func.avg(BathroomRating.overall_rating).label('avg_rating'),
        func.count(BathroomRating.id).label('rating_count'),
        func.count(Favorite.id).label('favorite_count')
    ).outerjoin(Favorite).group_by(BathroomRating.location)\
    .order_by(func.avg(BathroomRating.overall_rating).desc())\
    .limit(10).all()
    
    return render_template('top_bathrooms.html', top_rated=top_rated)

@app.route('/leaderboard')
def leaderboard():
    # Get users with most ratings
    top_users = db.session.query(
        User.username,
        func.count(BathroomRating.id).label('rating_count'),
        func.avg(BathroomRating.overall_rating).label('avg_rating')
    ).outerjoin(BathroomRating).group_by(User.id, User.username)\
    .order_by(func.count(BathroomRating.id).desc())\
    .limit(10).all()
    
    return render_template('leaderboard.html', top_users=top_users)

@app.route('/messages')
@login_required
def messages():
    received_messages = Message.query.filter_by(recipient_id=session['user_id'])\
        .order_by(Message.timestamp.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=session['user_id'])\
        .order_by(Message.timestamp.desc()).all()
    return render_template('messages.html', 
                         received_messages=received_messages,
                         sent_messages=sent_messages)

@app.route('/send_message/<int:recipient_id>', methods=['POST'])
@login_required
def send_message(recipient_id):
    content = request.form.get('content')
    if content:
        message = Message(
            sender_id=session['user_id'],
            recipient_id=recipient_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
    return redirect(url_for('messages'))

@app.route('/view_rating/<int:rating_id>')
def view_rating(rating_id):
    rating = BathroomRating.query.get_or_404(rating_id)
    return render_template('view_rating.html', rating=rating)

if __name__ == '__main__':
    app.run(debug=True) 