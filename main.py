from flask import Flask, request, jsonify, render_template,url_for,redirect,flash,session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import google.generativeai as genai
import os

app = Flask(__name__)

# ✅ Use environment variables for production
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'temp@364050')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ✅ Use environment variable for API key
genai.configure(api_key=os.environ.get('GEMINI_API_KEY', "AIzaSyBNp-AEEq7KPVNo2iAceay1qbgXia4eu58"))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# ✅ Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('login.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first!', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
@login_required 
def dashboard():
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists! Please choose another.', 'danger')
            return render_template('register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return render_template('register.html')

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Welcome to the dashboard.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/login_validation', methods=['GET','POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()

    if user is None:
        flash('No account found with this email. Please sign up first!', 'warning')
        return redirect(url_for('home'))

    if user.password == password:
        session['user_id'] = user.id
        session['username'] = user.username
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid email or password!', 'danger')
        return redirect(url_for('home'))

@app.route('/profile')
@login_required
def user_profile():
    user = User.query.get(session['user_id'])
    return render_template('user.html', username=user.username, email=user.email)

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    response_text = ""
    user_id = session.get('user_id')

    if request.method == 'POST':
        user_query = request.form.get("query")
        if user_query:
            try:
                model = genai.GenerativeModel("gemini-1.5-pro-latest")
                chat_session = model.start_chat(history=[])
                response = chat_session.send_message(user_query)
                
                response_text = response.text
                
                new_chat = ChatHistory(user_id=user_id, user_message=user_query, ai_response=response_text)
                db.session.add(new_chat)
                db.session.commit()

            except Exception as e:
                response_text = f"Error: {str(e)}"

    chat_history = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp.desc()).all()
    return render_template("chat.html", title="Chat", response=response_text, chat_history=chat_history)

@app.route('/resources')
@login_required
def resources():
    return render_template('resources.html', title="Resources")

@app.route('/courses')
@login_required
def courses():
    return render_template('courses.html')

# ✅ Production-ready run configuration
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
