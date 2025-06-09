from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import sigmoid_kernel
import difflib
from flask import Flask,request, url_for, redirect, render_template
from markupsafe import Markup

app = Flask(__name__)
app.config['SECRET_KEY'] = '9xf0?kpx9ahjsjffixd4;kx0c,xcbHi'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite database file
db = SQLAlchemy(app)


login_manager = LoginManager(app)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<ContactMessage from {self.name}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    profession = db.Column(db.String(120), nullable=False)  # Remove 'unique=True' for profession
    phone_number = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


# Define the User model for the database



def create_sim(search):
    df_org=pd.read_csv('Coursera.csv')
    df=df_org.copy()
    df.drop(['University','Difficulty Level','Course Rating','Course URL','Course Description'], axis=1,inplace=True)
    tfv = TfidfVectorizer(min_df=3,  max_features=None, 
            strip_accents='unicode', analyzer='word',token_pattern=r'\w{1,}',
            ngram_range=(1, 3),
            stop_words = 'english')

    # Filling NaNs with empty string
    df['cleaned'] = df['Skills'].fillna('')
    # Fitting the TF-IDF on the 'cleaned' text
    tfv_matrix = tfv.fit_transform(df['cleaned'])
    # Compute the sigmoid kernel
    sig = sigmoid_kernel(tfv_matrix, tfv_matrix)
    # Reverse mapping of indices and titles
    indices = pd.Series(df.index, index=df['Course Name']).drop_duplicates()
    
    def give_rec(title, sig=sig):
        # Get the index corresponding to original_title
        idx = indices[title]

        # Get the pairwsie similarity scores 
        sig_scores = list(enumerate(sig[idx]))

        # Sort the courses
        sig_scores = sorted(sig_scores, key=lambda x: x[1], reverse=True)

        # Scores of the 10 most similar courses
        sig_scores = sig_scores[1:11]

        # courses indices
        course_indices = [i[0] for i in sig_scores]

        # Top 10 most similar courses
        return df_org.iloc[course_indices]

    namelist=df['Course Name'].tolist()
    word=search
    simlist=difflib.get_close_matches(word, namelist)
    try: 
        findf=give_rec(simlist[0])
        findf=findf.reset_index(drop=True)
    except:
        findf=pd.DataFrame()
    
    return findf

def get_most_rated_courses():
    # Read the original DataFrame from the 'Coursera.csv' file
    df = pd.read_csv('Coursera.csv')

    # Sort the DataFrame by 'Course Rating' in descending order
    most_rated_courses = df.sort_values(by='Course Rating', ascending=False)

    # Return the top 10 most rated courses
    return most_rated_courses.head(20)

@app.route('/most_rated_courses')
def most_rated_courses():
    most_rated = get_most_rated_courses()

    # Convert the DataFrame to a list of dictionaries for rendering in the template
    most_rated_courses_list = most_rated.to_dict(orient='records')

    return render_template('most_rated_courses.html', most_rated_courses=most_rated_courses_list)

    
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/co')
def co():
    return render_template('co.html')


@app.route('/hello')
def hello_world():
    return render_template("index.html")


import pandas as pd

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'POST':
        namec = request.form['course']

    output = create_sim(namec)
    if output.empty:
        ms = 'Sorry! We did not find any matching courses. Try adding more keywords to your search.'
        pred = []  # Set 'pred' to an empty list when there are no course recommendations
    else:
        ms = 'Here are some recommendations:'
        pred = output.to_dict(orient='records')

    # Pass the 'pred' variable to the template along with 'ms'
    return render_template('index.html', message=ms, pred=pred)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        profession = request.form['email']
        phone_number = request.form['phone_number']

        # Check if the username or email already exists
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
        elif existing_email:
            flash('Email already registered. Please use a different email address.', 'danger')
        elif password != confirm_password:
            flash('Password and Confirm Password do not match. Please try again.', 'danger')
        else:
            new_user = User(username=username, password=password, email=email,profession=profession, phone_number=phone_number)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ... (other routes and configurations)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check user credentials in the database
        user = User.query.filter_by(username=username, password=password).first()

        if user and user.username == 'admin' and user.password == 'admin123':
            login_user(user)
            flash('Admin login successful!', 'success')
            return redirect(url_for('all_users'))
        elif user:
            # Log in the user using Flask-Login's login_user function
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('hello_world'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    # If the user is not logged in or the login failed, pass 'user_is_logged_in' as False
    return render_template('login.html', user_is_logged_in=False)

@app.route('/logout')
@login_required
def logout():
    # Log out the user using Flask-Login's logout_user function
    logout_user()
    flash('Logout successful!', 'success')
    return redirect(url_for('home'))



@app.route('/save_contact_message', methods=['GET', 'POST'])
def save_contact_message():
    if request.method == 'POST':
        name = request.form['name']
        phone_number = request.form['phone_nu']
        email = request.form['email']
        message = request.form['message']

        # Create a new instance of the ContactMessage model and save it to the database
        new_message = ContactMessage(name=name, phone_number=phone_number, email=email, message=message)
        db.session.add(new_message)
        db.session.commit()

        # Optionally, you can add a flash message to notify the user that the message has been saved successfully.
        flash('Your message has been sent successfully!', 'success')

        # You can redirect the user to another page after the message is saved if desired.
        return redirect(url_for('contact'))
    return redirect(url_for('contact'))

@app.route('/all_users')
def all_users():
    # Retrieve all users from the User table
    users = User.query.all()

    # Retrieve all contact messages from the ContactMessage table
    contact_messages = ContactMessage.query.all()

    return render_template('all_users.html', users=users, contact_messages=contact_messages)


@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        user = current_user  # Get the currently logged-in user

        # Retrieve the updated profile information from the form
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']

        # Check if the new username or email already exists (excluding the current user)
        existing_user = User.query.filter(User.username == username, User.id != user.id).first()
        existing_email = User.query.filter(User.email == email, User.id != user.id).first()

        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
        elif existing_email:
            flash('Email already registered. Please use a different email address.', 'danger')
        else:
            # Update the user's profile information in the database
            user.username = username
            user.email = email
            user.phone_number = phone_number
            db.session.commit()

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))

    # If the request method is GET or the form submission failed, display the profile update form
    return render_template('update_profile.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.template_filter('star_rating')
def star_rating(rating):
    if rating == 'N/A':
        return rating  # If rating is 'N/A', return it as is
    else:
        try:
            rating_value = float(rating)  # Convert the rating to a float
            full_stars = int(rating_value)
            half_star = rating_value - full_stars >= 0.5
            return '★' * full_stars + ('½' if half_star else '')
        except ValueError:
            return rating  # If conversion to float fails, return the original value
        

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database tables
    app.run(debug=True)
