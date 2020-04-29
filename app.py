from  flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

# app instance
app = Flask(__name__)
db = SQLAlchemy(app)
login = LoginManager(app)


"""
LoginManager comes with
is_authenticated
is_active
is_anonymous
get_id()
"""
@login.user_loader
def load_user(id):
    return User.query.get(id)
#############DB CONF ############
# db location
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "blog.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['POST_UPLOAD_FOLDER'] = os.path.join(basedir, 'static/images/posts/')
app.config['SECRET_KEY'] = 'husdagavafvaafbafbfbaavvuavafvfdbbfafabboavbav'
#############DB CONF ############


#################db tables########
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), index=True, nullable=True)
    last_name = db.Column(db.String(255), index=True, nullable=True)
    username = db.Column(db.String(255), index=True, nullable=False)
    email = db.Column(db.String(255), index=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    avater = db.Column(db.String(255), index=True, nullable=True)
    bio = db.Column(db.String(350), index=True, nullable=True)


    def __repr__(self):
        return self.username


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    avater = db.Column(db.String(255), index=True, nullable=True)
    title = db.Column(db.String(100), index=True, nullable=True)
    category = db.Column(db.String(100), index=True, nullable=True)
    content = db.Column(db.String(350), index=True, nullable=True)
    create_at = db.Column(db.DateTime, index=True, default=datetime.utcnow())

#################db tables########

# http://127.0.0.1:5000/
@app.route('/')
def index():
    posts = Post.query.all()
    return render_template("index.html",title = "Blog app | Home page", posts = posts)


# CRUD
# http://127.0.0.1:5000/posts/add: Create
@app.route('/posts/add', methods=['GET', 'POST'])
def add_post():
    # check request method
    if request.method == 'POST' and request.files:
        # POST request(TEXT data)
        title = request.form.get('the_title')
        category = request.form.get('category')
        content = request.form.get('description')
        # POST request(FILE/IMAGE data)
        file = request.files['the_avater']
        # file: name, extenstion , mimetype
        filename = secure_filename(file.filename)

        # post object
        user_post = Post(
            title = title,
            category = category,
            content = content.strip(),
            avater = filename
        )
        # add post in to db table(Post())
        db.session.add(user_post)
        # upload image into images folder
        file.save(os.path.join(app.config['POST_UPLOAD_FOLDER'], filename))
        # save post into the db
        db.session.commit()
        return redirect('/')
    else:
        #GET request
        return render_template("add_posts.html",title = "Blog app | Add post page")

# http://127.0.0.1:5000/posts/100: read
@app.route('/posts/detail/<int:post_id>')
def post_detail(post_id):
    found_post = Post.query.get(post_id)
    return render_template("posts_details.html", title = "Blog app | {} Blog".format(found_post.title) , found_post=found_post)

# http://127.0.0.1:5000/posts/delete/100: update
# /posts/update/{{post.id}}
@app.route('/posts/update/<int:post_id>', methods =['GET', 'POST'])
def add_delete(post_id):
    update_post = Post.query.get(post_id)
    if request.method == 'POST':
        title = request.form.get('the_title')
        category = request.form.get('category')
        content = request.form.get('description')

        # update post with new data
        update_post.title = title
        update_post.category = category
        update_post.content = content

        # save changes into db
        db.session.commit()
        return redirect('/posts/detail/{}'.format(post_id))

    return render_template("account.html",title = "Blog app | Post page")

# /posts/delete/{{found_post.id}}
# http://127.0.0.1:5000/posts/100: delete
@app.route('/posts/delete/<int:post_id>')
def post_delete(post_id):
    found_post = Post.query.get(post_id)
    db.session.delete(found_post)
    db.session.commit()
    return redirect('/')


################ USER AUTH ######################
# http://127.0.0.1:5000/signup
@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("signup.html",title = "Blog app | Signup page")
    elif request.method == 'POST':
        # 1. grab data from form
        username = request.form['username']
        firstname = request.form['first_name']
        lastname = request.form['last_name']
        email = request.form['email']
        password1 = request.form['password1']
        password2 = request.form['password2']

        # 2. check if user exists, username, email
        user_with_username = User.query.filter_by(username=username).first()
        user_with_email = User.query.filter_by(email=email).first()

        if user_with_username or user_with_email:
            return redirect('/signup')
        # 3.0 hash password
        # 3.1 check if passwords are the same
        if password1 == password2:
            # hash password
            if len(password2) >= 8:
                password_hash = generate_password_hash(password2)
                # 4. add user into db
                user_obj = User(
                    first_name = firstname,
                    last_name = lastname,
                    username = username,
                    email = email,
                    password = password_hash
                )
                # add user into db
                db.session.add(user_obj)
                # save user into db
                db.session.commit()
                return redirect('/login')
            else:
                return redirect('/signup')
        return redirect('/signup')

        # 5.take user to login page




# http://127.0.0.1:5000/login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html",title = "Blog app | login page")
    elif request.method == 'POST':
        # process user data
        # grab email and password
        email = request.form.get('email')
        password = request.form.get('password')
        # check if we have a user with the given email
        user = User.query.filter_by(email=email).first()
        if user is None:
            # return user login with the right email
            return  redirect('/login')
        else:
            if check_password_hash(user.password,password ):
                # return true if user is found with the right password
                login_user(user)
                return redirect('/account')
            else:
                # return false if user is found with the right password
                return  redirect('/login')


# http://127.0.0.1:5000/account
@app.route('/account')
def account():

    return render_template("account.html",title = "Blog app | account page")

# http://127.0.0.1:5000/logout
@app.route('/logout')
def logout():
    user = current_user
    logout_user()
    return render_template("index.html",title = "Blog app | Home page")


# Error handlers routes
@app.errorhandler(404)
def page_not_found(e):
    return "page not found", 404


# Error handlers routes
@app.errorhandler(500)
def internal_error(e):
    return "page not found", 500


if __name__ == '__main__':
    app.run(debug=True)