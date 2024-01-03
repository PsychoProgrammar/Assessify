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

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # Change to your mail server port
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'shreyaballolli@gmail.com'
app.config['MAIL_PASSWORD'] = 'shreya_66'
app.config['MAIL_DEFAULT_SENDER'] = 'shreyaballolli@gmail.com'
app.config['UPLOAD_FOLDER'] = 'path/to/your/upload/folder'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
mail = Mail(app)
proficiencies = ["C", "C++", "Java","Python"]
questions_by_proficiency = {proficiency: [] for proficiency in proficiencies}
# Assuming you have an Excel file named 'questions.xlsx' with a sheet named 'questions'
SPREADSHEET_PATH = 'questions.xlsx'
SHEET_NAME = 'questions'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

# db.init_app(app)

# from models import Feedback


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
 
 
@app.route('/show_data')
def show_data():
    users = User.query.all()
    return render_template('show_data.html', users=users)
 
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


# Add a global variable to store questions
python_questions = []

@app.route('/create_quiz_questions', methods=['GET', 'POST'])
def create_quiz_questions():
    if request.method == 'POST':
        # Handle form submission and add questions to the global variable or database
        question_text = request.form.get('question')
        options = [
            request.form.get('option1'),
            request.form.get('option2'),
            # Add more options as needed
        ]
        correct_answer = request.form.get('correct_answer')

        # Create a dictionary to represent the question
        question = {
            'text': question_text,
            'options': options,
            'correct_answer': correct_answer
        }

        # Store the question in the global variable or database
        python_questions.append(question)

        # Redirect to Python questions page
        return redirect(url_for('python_questions_page'))

    return render_template('create_quiz_questions.html')



@app.route('/submit_questions', methods=['POST'])
def submit_questions():
    if request.method == 'POST':
        question_text = request.form.get('question')
        options = [request.form.get('option1'), request.form.get('option2')]
        correct_answer = request.form.get('correct_answer')
        category = session.get('quiz_category')

        new_question = QuizQuestion(category=category, question=question_text, options=options, correct_answer=correct_answer)
        db.session.add(new_question)
        db.session.commit()

        # Create a dictionary to represent the question
        question = {
            'text': question_text,
            'options': options,
            'correct_answer': correct_answer
        }

        # Store the question in the global variable
        python_questions.append(question)

        

        # Redirect to Python questions page
        return redirect(url_for('python_questions_page'))

@app.route('/fetch_questions')
def fetch_questions():
    # Replace with your actual file path
    file_path = 'C:/Users/7000035078/Desktop/First Challenge/templates/questions.xlsx'
    
    # Call the function with the file path
    questions = load_questions_from_spreadsheet(file_path)
    
    # Debug statement
    print("Debug: Questions loaded from spreadsheet:", questions)
    
    if questions is not None:
        # Render the HTML template with the questions
        return render_template('questions_template.html', questions=questions)
    else:
        # Render an error template with a generic error message
        return render_template('error_template.html', error_message="Failed to load questions.")

# Function to load questions from the Excel file
def load_questions_from_spreadsheet(file_path):
    try:
        # Load the spreadsheet into a Pandas DataFrame
        df = pd.read_excel(file_path, sheet_name='questions')
        questions = df.to_dict(orient='records')
        return questions

    except Exception as e:
        print(f"Error loading questions from spreadsheet: {str(e)}")
        return None
    
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
        return redirect('/coding_submissions')
    else:
        return jsonify({'message': 'User not found'}), 404

def send_async_email(msg):
    with app.app_context():
        # This context ensures that Flask extensions are properly initialized
        try:
            mail.send(msg)
            # Email sent successfully, update the user's email status in the database
            update_email_status(msg.recipients[0], 'Sent')
        except Exception as e:
            # Handle exceptions
            print(f'Error sending email: {str(e)}')
            # Email sending failed, update the user's email status in the database
            update_email_status(msg.recipients[0], 'Failed')

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
    user = db.session.query(User).get(user_id)

    if user:
        # Create the email message
        msg = Message('Quiz Results for {}'.format(user.name),
                      recipients=['sujata.ballolli@gmail.com'])  # Replace with the actual HR email

        # Customize the email content
        email_content = f"Hello HR,\n\n{user.name}'s quiz results are as follows:\n\n" \
                        f"Quiz Score: {user.quiz_score}/5\n" \
                        f"Coding Score: {user.coding_score}/10\n" \
                        f"Status: {user.status}\n\n" \
                        "Best regards,\nYour App"

        msg.body = email_content

        try:
            # Send the email asynchronously using threading
            t = Thread(target=send_async_email, args=(msg,))
            t.start()

            return 'Email sending task started successfully!'
        except Exception as e:
            # Handle exceptions
            return f'Error starting email sending task: {str(e)}'
    else:
        return jsonify({'message': 'User not found'}), 404



@app.route('/questions_xl')
def questions_xl():
    return render_template('questions_xl.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', error='No file part')

    file = request.files['file']

    if file.filename == '':
        return render_template('index.html', error='No selected file')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        questions = read_excel(file_path)
        return render_template('questions_xl.html', questions=questions)

    return render_template('index.html', error='Invalid file format')

def read_excel(file_path):
    df = pd.read_excel(file_path)
    questions = []

    for index, row in df.iterrows():
        question_data = {
            'question': row['Question'],
            'options': [row['Option A'], row['Option B'], row['Option C'], row['Option D']],
            'correct_option': row['Correct Option']  
        }
        questions.append(question_data)

    return questions

@app.route('/create_quiz_category')
def create_quiz_category():
    return render_template('create_quiz_category.html', proficiencies=proficiencies)
@app.route('/add_question', methods=['POST'])
def add_question():
    data = request.get_json()
    proficiency = data['proficiency']
    question = data['question']
    options = data['options']

    questions_by_proficiency[proficiency].append({'question': question, 'options': options})
    
    return jsonify(status='success')

@app.route('/get_questions', methods=['POST'])
def get_questions():
    proficiency = request.get_json()['proficiency']
    questions = questions_by_proficiency.get(proficiency, [])
    return jsonify(questions=questions)

@app.route('/delete_question', methods=['POST'])
def delete_question():
    data = request.get_json()
    proficiency = data['proficiency']
    question_index = data['index']

    if proficiency in questions_by_proficiency and 0 <= question_index < len(questions_by_proficiency[proficiency]):
        del questions_by_proficiency[proficiency][question_index]

    return jsonify(status='success')

@app.route('/view_questions')
def view_questions():
    return render_template('view_questions.html', questions_by_proficiency=questions_by_proficiency)

if __name__ == '__main__':
    app.run(debug=True , port=1234)