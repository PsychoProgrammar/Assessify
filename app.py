from flask import Flask, request,render_template, redirect,session, send_file, url_for,render_template_string, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import jsonify
import random as random
import os
from io import BytesIO
import io
from datetime import datetime, timedelta
import pytz
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import pandas as pd
from flask_bootstrap import Bootstrap
from threading import Thread
from flask import copy_current_request_context
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for
from models import db, Question, init_app
import openpyxl
from flask import request

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # Change to your mail server port
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEBUG'] = True
app.config['MAIL_USERNAME'] = 'shreyaballolli@gmail.com'
app.config['MAIL_PASSWORD'] = 'vmktqedkpifzwuqg'
app.config['MAIL_DEFAULT_SENDER'] = 'shreyaballolli@gmail.com'
app.config['UPLOAD_FOLDER'] = 'path/to/your/upload/folder'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
mail = Mail(app)
proficiencies = ["C", "C++", "Java","Python"]
questions_by_proficiency = {proficiency: [] for proficiency in proficiencies}


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///questions.db'

init_app(app)
# db = SQLAlchemy(app)

# db.init_app(app)

migrate = Migrate(app, db)
app.secret_key = 'secret_key'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=True)  
    correct_answer = db.Column(db.String(255), nullable=False) 

    def __init__(self, category, question, options,correct_answer):
        self.category = category
        self.question = question
        self.options = options
        self.correct_answer=correct_answer

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, email, feedback):
        self.name = name
        self.email = email
        self.feedback = feedback

    @staticmethod
    def feedback_exists(email):
        return db.session.query(db.exists().where(Feedback.email == email)).scalar()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    phone = db.Column(db.String(20) , unique=True, nullable=True)
    proficiency = db.Column(db.String(20))
    quiz_score = db.Column(db.Integer, nullable=True)
    resume_filename = db.Column(db.String(255), nullable=True)
    resume_data = db.Column(db.LargeBinary, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=True)
    coding_score = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='Pending') 

    def update_coding_score(self, new_coding_score):
        self.coding_score = new_coding_score
        db.session.commit()
    
 
    def __init__(self,name,email,password, phone , proficiency,resume_filename=None, resume_data=None,image_filename=None, image_data=None, status=None):
        self.name = name
        self.email = email
        self.password = password
        self.phone=phone
        self.proficiency=proficiency
        self.resume_filename = resume_filename
        self.resume_data = resume_data
        self.image_filename=image_filename
        self.image_data=image_data
        self.status=status
   
    def check_password(self,password):
        return password

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def custom_sort(feedbacks):
     return sorted(feedbacks, key=lambda x: x.timestamp if x.timestamp else datetime.min, reverse=True)

# Function to convert UTC time to IST
def convert_utc_to_ist(utc_time_str):
    if isinstance(utc_time_str, datetime):
        # If utc_time_str is already a datetime object, format it and return
        return utc_time_str.strftime('%Y-%m-%d %H:%M:%S')

    if utc_time_str:
        utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
        utc_time = pytz.utc.localize(utc_time)
        ist_time = utc_time.astimezone(pytz.timezone('Asia/Kolkata'))
        return ist_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return 'N/A'
app.jinja_env.filters['custom_sort'] = custom_sort
app.jinja_env.filters['convert_utc_to_ist'] = convert_utc_to_ist   

class UserCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, code):
        self.user_id = user_id
        self.code = code


   
# Hardcoded admin credentials
ADMIN_EMAIL = 'admin@example.com'
ADMIN_PASSWORD = 'admin_password'
ADMIN_NAME = 'Admin'
 
with app.app_context():
    db.create_all()


    # Dictionary of questions, options, and their respective correct answers
questions = {
   
    "Which of the following is not a valid variable name in Python?": {
        "options": ["my_var", "2var", "_var", "myVar"],
        "answer": "2var"
    },
    "In C, what is the size of the 'int' data type?": {
        "options": ["4 bytes", "2 bytes", "8 bytes", "Depends on the compiler"],
        "answer": "Depends on the compiler"
    },
    "Which of the following is a correct way to declare a pointer in C++?": {
        "options": ["int *ptr;", "ptr = &x;", "int ptr = &x;", "int ptr();"],
        "answer": "int *ptr;"
    },
    "In Java, which keyword is used to create a subclass of a class?": {
        "options": ["this", "extends", "super", "subclass"],
        "answer": "extends"
    },
    "What does HTTP stand for in the context of web development?": {
        "options": ["HyperText Transfer Protocol", "Highly Transferable Text Protocol", "Hyper Transfer Text Protocol", "Highly Textual Transfer Protocol"],
        "answer": "HyperText Transfer Protocol"
    },
    "Which of the following is NOT a valid HTTP request method?": {
        "options": ["GET", "PULL", "POST", "DELETE"],
        "answer": "PULL"
    },
    "Which data structure in Python is a Last-In-First-Out (LIFO) data structure?": {
        "options": ["Queue", "Stack", "Deque", "Heap"],
        "answer": "Stack"
    },
    "In C++, what is the default access specifier for members of a class?": {
        "options": ["public", "protected", "private", "depends on the compiler settings"],
        "answer": "private"
    },
    "Which of the following is a correct Flask route decorator for displaying a webpage?": {
        "options": ["@app.route('/page')", "@route('/display')", "@url('/show')", "@display.route('/')"],
        "answer": "@app.route('/page')"
    },
    "What is the use of 'self' in Python classes?": {
        "options": ["Refers to the current class object", "A keyword for iteration", "Used to define class methods", "Represents a static variable"],
        "answer": "Refers to the current class object"
    },
    
    "What is the output of the following Python code? x = 5 print(x > 3 and x < 10) ?": {
        "options": ["True", "False", "5", "SyntaxError"],
        "answer": "True"
    }
}
 
 
@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/register',methods=['GET','POST'])
def register():
     if request.method == 'POST':
        # handle request
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']  
        proficiencies=request.form.getlist('proficiency[]')
        proficiency_str=','.join(proficiencies)

        new_user = User(name=name,email=email,password=password,phone=phone,proficiency=proficiency_str)

        # Handle file upload for the resume
        if 'resume' in request.files:
            resume_file = request.files['resume']
            if resume_file and resume_file.filename != '':
                # Save resume details in the database
                new_user.resume_filename = resume_file.filename
                new_user.resume_data = resume_file.read()

         # Handle image upload
        if 'image' in request.files:
         image = request.files['image']
        if image.filename != '':
            filename = secure_filename(image.filename)
            new_user.image_filename = filename
            new_user.image_data = image.read()
       
          
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login/user')
   

     return render_template('register.html')
 
# with app.app_context():
#     db.drop_all()
 
 
with app.app_context():
    db.create_all()
 
 
 
@app.route('/login', methods=['GET'])
def login():
    if 'admin' in request.args:
        # Redirect to Admin Login page (assuming you have an admin login route)
        return redirect('/login/admin')
    if 'user' in request.args:
        # Redirect to User Login page (assuming you have a user login route)
        return redirect('/login/user')
    # else:
    #     # Handle cases where no option is selected (You can render a specific error page)
    #     return render_template('error.html', error='Please select an option to login.')
    
    # Ensure session is initialized
    session.clear()

    # Add a return statement for cases where no option is selected
    return render_template('admin_dashboard.html')
 
 
 
 
@app.route('/login/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
       
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['email'] = email
            session['admin'] = True
            return redirect('/admin_dashboard')
        else:
            return render_template('admin_login.html', error='Invalid admin credentials')
   
    return render_template('admin_login.html')
 
@app.route('/login/user', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
       
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/user_dashboard')
        else:
            return render_template('user_login.html', error='Invalid user credentials')
   
    return render_template('user_login.html')
 
@app.route('/user_dashboard')
def user_dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session["email"]).first()
        if user:
         return render_template('user_dashboard.html',user=user)
    else:
         # Handle the case when 'email' is not in the session
         print("Email not found in session.")
    # You might want to redirect the user to a login page or handle it in some way

    return redirect('/login')
 
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if 'admin' in session and user:  # Check if the logged-in user is an admin
            feedbacks = Feedback.query.all()
            return render_template('admin_dashboard.html', user=user,feedbacks=feedbacks)
        # else:
        #     return render_template('dashboard.html', user=user)
    return redirect('/login')

@app.route('/view_feedback')
def view_feedback():
    with app.app_context():
        # Calculate the date 5 days ago from the current date
        five_days_ago = datetime.utcnow() - timedelta(days=5)

        # Query for feedback entries given in the past 5 days
        feedback_entries = Feedback.query.filter(Feedback.timestamp >= five_days_ago).all()
        
        return render_template('view_feedback.html', feedbacks=feedback_entries, convert_utc_to_ist=convert_utc_to_ist)
 
@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect('/login/user')

@app.route('/top_score')
def top_score():
    users = User.query.order_by(User.quiz_score.desc()).all()
    return render_template('top_score.html', users=users)
 
 
@app.route('/show_data')
def show_data():
    users = User.query.all()
    return render_template('show_data.html', users=users)

@app.template_filter('utc_to_ist')
def convert_utc_to_ist(utc_time):
    if utc_time:
        utc_time = utc_time.replace(tzinfo=pytz.utc)
        ist_time = utc_time.astimezone(pytz.timezone('Asia/Kolkata'))
        return ist_time.strftime('%Y-%m-%d %H:%M:%S IST')
    return 'N/A'
 
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return redirect('/show_data')
    else:
        return jsonify({'message': 'User not found'}), 404
 

@app.route('/collect_feedback')
def show_feedback_form():
    return render_template('collect_feedback.html')
 
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        feedback_text = request.form['feedback']
       
        app.logger.info(f"Received feedback from {name} ({email}): {feedback_text}")

        # Check if feedback already exists for the given email
        existing_feedback = Feedback.feedback_exists(email)
        if existing_feedback:
            return "You have already provided feedback :)"
        
        # Create a new Feedback instance or use your existing User model to store feedback
        feedback_instance = Feedback(name=name, email=email, feedback=feedback_text)
        db.session.add(feedback_instance)
        db.session.commit()
       
        return "Thank you for your feedback!"

@app.route('/quiz_page')
def index2():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if user.quiz_score is not None:
            return render_template('already_taken.html')
    # Select 3 random questions for the quiz each time the page is refreshed
    selected_questions = random.sample(list(questions.items()), 5)
    return render_template('quiz_page.html', questions=selected_questions)


@app.route('/quiz', methods=['POST'])
def quiz():
    score = 0
    user_answers = request.form

    # Retrieve the user based on the session email
    user = User.query.filter_by(email=session["email"]).first()
    
    for question, answer in user_answers.items():
        if questions[question]["answer"] == answer:
            score += 1

    
    # Update the user's quiz score in the database
    user.quiz_score = score
    db.session.commit()

    if score >= 3 and score <= 5:
        return redirect(url_for('coding_eligibility', score=score))
    elif score < 3:
        return redirect(url_for('not_eligible'))
    # else:
    #     return render_template('quiz_result.html', score=score)
    
@app.route('/coding-questions')
def coding_questions():
    # Logic to display coding questions goes here
    return render_template('coding_questions.html')  # or the actual template for coding questions
 
 
@app.route('/coding_eligibility/<int:score>')
def coding_eligibility(score):
    return render_template('coding_eligibility.html', score=score)
 
@app.route('/not_eligible')
def not_eligible():
    return render_template('not_eligible.html')


@app.route('/view_quiz_results')
def view_quiz_results():
    with app.app_context():
        users = User.query.all()
        return render_template('view_quiz_results.html', users=users)

@app.route('/download_resume/<int:user_id>')
def download_resume(user_id):
    user = User.query.get(user_id)
    if user and user.resume_filename and user.resume_data:
        # return send_file(BytesIO(user.resume_data),
        #                  attachment_filename=user.resume_filename,
        #                  as_attachment=True)
        return send_file(
            io.BytesIO(user.resume_data),
            download_name=user.resume_filename,
            as_attachment=True
        )
    else:
        return jsonify({'message': 'Resume not found'}), 404
    
@app.route('/get_image/<filename>')
def get_image(filename):
    user = User.query.filter_by(image_filename=filename).first()
    if user:
        return send_file(BytesIO(user.image_data), mimetype='image/jpeg')  # Adjust mimetype as needed
    return 'Image not found', 404



    
@app.route('/submit_code', methods=['POST'])
def submit_code():
    if request.method == 'POST':
        # Get the user's email from the session
        email = session.get('email')
        if not email:
            return jsonify({'message': 'User not logged in'}), 403

        # Find the user in the database
        user = User.query.filter_by(email=email).first()

        if user:
        # Get the code from the form submission
         user_code_1 = request.form.get('user_code_1')
         user_code_2 = request.form.get('user_code_2')

        # Save the code in the database
        new_user_code_1 = UserCode(user_id=user.id, code=user_code_1)
        new_user_code_2 = UserCode(user_id=user.id, code=user_code_2)
        
        db.session.add(new_user_code_1)
        db.session.add(new_user_code_2)
        
        db.session.commit()

        return redirect('/coding_submissions')

    # Handle the case where the form submission fails
    return jsonify({'message': 'Error submitting codes'}), 500

@app.route('/coding_submissions')
def coding_submissions():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if user:
            # Retrieve user's submitted codes
            user_codes = UserCode.query.filter_by(user_id=user.id).all()
            return render_template('coding_submissions.html', user=user, user_codes=user_codes)

    return redirect('/login/user')

@app.route('/view_coding/<int:user_id>')
def view_coding(user_id):
    user = User.query.get(user_id)
    if user:
        # Retrieve user's submitted codes
        user_codes = UserCode.query.filter_by(user_id=user.id).all()
        return render_template('view_coding.html', user=user, user_codes=user_codes)
    else:
        return jsonify({'message': 'User not found'}), 404
    
@app.route('/update_coding_score/<int:user_id>', methods=['POST'])
def update_coding_score(user_id):
    # Retrieve the user from the database
    user = User.query.get(user_id)
    if user:
        # Update the coding score
        new_coding_score = int(request.form.get('codingScore'))
        user.update_coding_score(new_coding_score)

        # Redirect or render as needed
        return redirect('/view_quiz_results')
    else:
        return jsonify({'message': 'User not found'}), 404
    

def send_email1(user):
    # Create the email message
    msg = Message('Quiz Results for {}'.format(user.name),
                    sender='shreyaballolli@gmail.com',
                    recipients=['shreyaballolli@gmail.com'])  

    # Customize the email content
    email_content = f"Hello HR,\n\n{user.name}'s quiz results are as follows:\n\n" \
                    f"Quiz Score: {user.quiz_score}/5\n" \
                    f"Coding Score: {user.coding_score}/10\n" \
                    "Best regards,\nAssessify"

    msg.body = email_content

    try:
        # Send the email
        mail.send(msg)

        # Email sent successfully, update the user's email status in the database
        update_email_status(user.email, 'Sent')

        return 'Email sent successfully!'
    except Exception as e:
        # Handle exceptions
        print(f'Error sending email: {str(e)}')

        # Email sending failed, update the user's email status in the database
        update_email_status(user.email, 'Failed')

        return 'Error sending email'

def update_email_status(email, status):
    user = User.query.filter_by(email=email).first()
    if user:
        user.email_status = status
        db.session.commit()
    else:
        print(f'User with email {email} not found in the database')

@app.route('/send_email/<int:user_id>', methods=['POST'])
def send_email(user_id):
    # Retrieve the user from the database
    user = User.query.get(user_id)

    if user:
        result = send_email1(user)
        return result
    else:
        return jsonify({'message': 'User not found'}), 404
    
@app.route('/upload_questions')
def upload_questions():
    return render_template('upload_questions.html')
    
@app.route('/add_question', methods=['POST'])
def add_question():
    question_text = request.form['question_text']
    option_a = request.form['option_a']
    option_b = request.form['option_b']
    option_c = request.form['option_c']
    option_d = request.form['option_d']
    correct_option = request.form['correct_option']

    new_question = Question(
        question_text=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct_option
    )

    db.session.add(new_question)
    db.session.commit()

    return redirect(url_for('view_questions'))

@app.route('/view_questions')
def view_questions():
    questions = Question.query.all()
    return render_template('view_questions.html', questions=questions)

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    file = request.files['file']
    workbook = openpyxl.load_workbook(file)
    sheet = workbook.active

    for row in sheet.iter_rows(min_row=2, values_only=True):
        question = Question(
            question_text=row[0],
            option_a=row[1],
            option_b=row[2],
            option_c=row[3],
            option_d=row[4],
            correct_option=row[5]
        )

        db.session.add(question)

    db.session.commit()

    return redirect(url_for('view_questions'))

@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('view_questions'))


if __name__ == '__main__':
    app.run(debug=True , port=1234)