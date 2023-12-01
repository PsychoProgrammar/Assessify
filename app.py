from flask import Flask, request,render_template, redirect,session, send_file, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import jsonify
import random as random
import os
from io import BytesIO
import io

 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
# db.init_app(app)

# from models import Feedback
migrate = Migrate(app, db)
app.secret_key = 'secret_key'

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    feedback = db.Column(db.Text, nullable=False)

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
    
 
    def __init__(self,name,email,password, phone , proficiency,resume_filename=None, resume_data=None):
        self.name = name
        self.email = email
        self.password = password
        self.phone=phone
        self.proficiency=proficiency
        self.resume_filename = resume_filename
        self.resume_data = resume_data
        # self.quiz_score=quiz_score
        # self.feedback=feedback
        # self.quiz_experience=quiz_experience
        # self.quiz_difficulty
   
    def check_password(self,password):
        return password
   
   
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
        # proficiency = request.form['proficiency']
        proficiencies=request.form.getlist('proficiency[]')
        proficiency_str=','.join(proficiencies)
        # quiz_score=request.form['quiz_score']

        new_user = User(name=name,email=email,password=password,phone=phone,proficiency=proficiency_str)

        # Handle file upload for the resume
        if 'resume' in request.files:
            resume_file = request.files['resume']
            if resume_file and resume_file.filename != '':
                # Save resume details in the database
                new_user.resume_filename = resume_file.filename
                new_user.resume_data = resume_file.read()
       
        
        
        
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
        user = User.query.filter_by(email=session['email']).first()
        if user:
         return render_template('user_dashboard.html',user=user)
   
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
    # if 'admin' in session:
    #     feedbacks = Feedback.query.all()
    #     return render_template('view_feedback.html', feedbacks=feedbacks)
    # return redirect('/login/admin')

    with app.app_context():
        feedback_entries= Feedback.query.all()
        return render_template('view_feedback.html', feedbacks=feedback_entries)
 
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
 
@app.route('/edit', methods=['GET', 'POST'])
def edit_details():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
       
        if request.method == 'POST':
           
            user.name = request.form['name']
            # user.password=request.form['password']
            user.email = request.form['email']
            user.phone = request.form['phone']
            user.proficiency = None

             # Add selected proficiencies
            selected_proficiencies = request.form.getlist('proficiency[]')
            user.proficiency = ','.join(selected_proficiencies)
           
            db.session.commit()
            return redirect('/user_dashboard')
       
        return render_template('edit.html', user=user)
    # return redirect('/login')
 
 
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
 
    # return "Error submitting feedback"

@app.route('/quiz_page')
def index2():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if user.quiz_score is not None:
            return "You have already taken the assessment."
    # Select 3 random questions for the quiz each time the page is refreshed
    selected_questions = random.sample(list(questions.items()), 5)
    return render_template('quiz_page.html', questions=selected_questions)


@app.route('/quiz', methods=['POST'])
def quiz():
    score = 0
    user_answers = request.form

    # Retrieve the user based on the session email
    user = User.query.filter_by(email=session['email']).first()
 
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
 
 
@app.route('/coding-eligibility/<int:score>')
def coding_eligibility(score):
    return render_template('coding_eligibility.html', score=score)
 
@app.route('/not-eligible')
def not_eligible():
    return render_template('not_eligible.html')


@app.route('/view_quiz_results')
def view_quiz_results():
    with app.app_context():
        users= User.query.all()
        return render_template('view_quiz_results.html', users=users)
    
@app.route('/see_resumes')
def see_resumes():
        with app.app_context():
         users = User.query.all()
        return render_template('see_resumes.html', users=users)
        return redirect('/login/admin')

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
     
if __name__ == '__main__':
    app.run(debug=True , port=1234)