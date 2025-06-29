from flask import Flask, request, jsonify, render_template,url_for,redirect,flash,session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import google.generativeai as genai







app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite Database
app.config['SECRET_KEY'] = 'temp@364050'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


genai.configure(api_key="AIzaSyBNp-AEEq7KPVNo2iAceay1qbgXia4eu58")



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)



class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())  # Auto timestamp

# ✅ Table create karne ke liye migrate/run karo
with app.app_context():
    db.create_all()


with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('login.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:  # User logged in nahi hai
            flash('Please login first!', 'danger')
            return redirect(url_for('home'))  # ✅ FIXED
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
@login_required 
def dashboard():
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
# def register():
#     return render_template('register.html')
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # 🔴 **Check if username already exists**
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists! Please choose another.', 'danger')
            return render_template('register.html')  # Redirect back to register page

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return render_template('register.html')

        # ✅ Create new user and save in DB
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()  # ✅ Save user in database

        flash('Registration successful! Welcome to the dashboard.', 'success')
        return redirect(url_for('dashboard'))   # ✅ Redirect to dashboard

    return render_template('register.html')



@app.route('/login_validation', methods=['GET','POST'])
def login():

    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()

    if user is None:
        flash('No account found with this email. Please sign up first!', 'warning')
        return redirect(url_for('home'))  # Redirect to sign-up page

    if user.password == password:  # Direct comparison without hashing
        session['user_id'] = user.id
        session['username'] = user.username
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))  # Redirect to dashboard
    else:
        flash('Invalid email or password!', 'danger')
        return redirect(url_for('home'))

@app.route('/profile')
@login_required
def user_profile():
    user = User.query.get(session['user_id'])  # Get user details from DB
    return render_template('user.html', username=user.username, email=user.email)

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    response_text = ""  # Default response
    user_id = session.get('user_id')  # Current logged-in user

    # ✅ System Prompt Define Karo

    if request.method == 'POST':
        user_query = request.form.get("query")  # User input
        if user_query:
            try:
                model = genai.GenerativeModel("gemini-1.5-pro-latest")  # AI Model Load
                chat_session = model.start_chat(history=[])  # ✅ Start Chat Session
                response = chat_session.send_message(user_query)  # ✅ Pass system prompt
                
                response_text = response.text  # AI Response
                
                # ✅ Save chat in database
                new_chat = ChatHistory(user_id=user_id, user_message=user_query, ai_response=response_text)
                db.session.add(new_chat)
                db.session.commit()  # ✅ Save to database

            except Exception as e:
                response_text = f"Error: {str(e)}"

    # ✅ Fetch previous chat history
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


if __name__ == '__main__':
    app.run(debug=True)


