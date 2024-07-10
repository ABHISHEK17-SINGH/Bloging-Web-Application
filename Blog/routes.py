import secrets
import os
from PIL import Image  # Module that we downloaded using pip Pillow iss mai hum image resize karte hai matlab chotti bana dete hai
from flask import  render_template,url_for,flash,redirect,request,abort
from Blog.forms  import RegistrationForm,Loginform,UpdateAccountForm,PostForm ,RequestResetForm,ResetPasswordForm
from Blog import app,db,bcrypt,mail
from Blog.models import Post ,User
from flask_login import login_user,current_user,logout_user,login_required
from flask_mail import Message
@app.route("/")
@app.route("/home")
def home():
    page =request.args.get('page',1,type= int) # args yaha pe ek dictionary hota hai or ye act akrta hai ek qury parameter of the URL query parameter key value hote hai jo ? ye baad aate hai
    # where yaha pe page as a key of the query parameter ke jaisa kaam karta hai fir 1 is the defaukt value aga kisi ne URl mai stirng daal di ya fuch or int ke alava
    # or tesra parameter ye hai ke type ye hai ke e dekhage ke jo bhe value url ami dalenge vo hum integer ke form mai daalenge
    posts =Post.query.order_by(Post.date_posted.desc()).paginate(page = page ,per_page=1)# or yaha pe ye paginate method hai
    return render_template('home.html',posts = posts)
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password =bcrypt.generate_password_hash(form.password.data).decode('utf-8')   # utf-8 kyu ki agar hum ko string chahiye bits ke jagah pe
        user = User(username=form.username.data , email=form.email.data , password= hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account created Now you can login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login",methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=Loginform()
    if form.validate_on_submit():
        user = User.query.filter_by(email= form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.remember.data)
            next_page =request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))


        else:
            flash('Login Unsuccessful.Please check email','danger')
    return render_template('login.html', title='Login',   form=form)


@app.route("/logout")
def logout():
    logout_user()  # it is function that is imported form the flask_login
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex= secrets.token_hex(8)  # used hex here becaue imgae file ka naam collide ho skta hai na to tab hum ne hex use kara hai
    _,f_ext=os.path.splitext(form_picture.filename)     # This line uses tuple unpacking to assign the first element of the tuple (path) to the variable f_name and the second element (filename) to the variable f_ext.
    picture_fn=random_hex + f_ext
    picture_path = os.path.join(app.root_path,'static/profile_pics',picture_fn)
    output_size= (125,125)
    i= Image.open( form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn
@app.route("/account",methods=['GET', 'POST'])
@login_required
def account():
    form =UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file= save_picture(form.picture.data)
            current_user.image_file = picture_file # yaha pe current_user.image_file aaya na ke current_user.image_file kyu ke models mai hum ne image_file kar ke store kar re  hai par hum jo forms hai ous mai pictures kar ke input mai save kar re hai

        current_user.username= form.username.data
        current_user.email= form.email.data
        db.session.commit()
        flash(' Your accout have been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method=='GET':
        form.username.data=current_user.username
        form.email.data = current_user.email
    image_file= url_for('static', filename='profile_pics/'+ current_user.image_file)
    return render_template('account.html',title ='Account',image_file=image_file, form=form)

@app.route("/post/new",methods=['GET', 'POST'])
@login_required
def new_post():
    form= PostForm()
    if form.validate_on_submit():
        post=Post(title=form.title.data,content=form.content.data,author= current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post has been created','success')
        return redirect(url_for('home'))
    return render_template('create_post.html',title ='New Post',form= form,legend='New Post')


@app.route("/post/<int:post_id>") # yaha pe hum aisa kar ke hai ke na hum bata re hai ke agar user to post 1 mai jana hai ya fir 2,3,4 jis mai to aise ja skta hai
def post(post_id):
    post=Post.query.get_or_404(post_id)
    return render_template('post.html',title= Post.title,post=post)



@app.route("/post/<int:post_id>/update",methods=['GET','POST'])
@login_required
def update_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()     #yaha pe hum ne db.session.add()kyu ni kara kyu ki ye sab to phele se hi database mai hai to hum bas update kar re hai
        flash('Post Has Been Updated','success')
        return redirect(url_for('post',post_id=post.id))
    elif request.method=='GET':
        form.title.data=post.title
        form.content.data=post.content
    return render_template('create_post.html',title ='Update Post',form= form,legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted ','success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page =request.args.get('page',1,type= int)
    user= User.query.filter_by(username= username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=1)
    return render_template('user_post.html', posts=posts,user=user)

def send_reset_email(user):
    token=user.get_reset_token()
    msg=Message('Password Reset Request',sender='noreply@gmail.com',recipients=[user.email]) #Message class mai pehle argument hum Subject body pass karte hai fir senders mail id yaha pe na kuch aisa rakhna hai ke na jo humahe domain ya aisa kuch ke jis ko dekh ke lage ke ye humare domain se aara hai
    msg.body=f''' To reset password visit the following link :
    {url_for('reset_token',token=token,_external=True)} 
    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    # here _external=True means that the generated URL will include the full external URL, including the protocol (HTTP/HTTPS), hostname, and port number (if applicable).
    # For example, if your application is running locally on port 5000 and accessed via http://localhost:5000, setting _external=True will generate URLs like http://localhost:5000/reset_token/<token>.

    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form =RequestResetForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An emailhas been sent to your email ID ','info')
        return redirect(url_for('login'))
    return render_template('reset_request.html',title='Reset Password',form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user= User.verify_reset_token(token)  # agar hum model.py file dekhe to verify_reset_token ye ek token leta hai as an argument or baaki jo ous mai likha hai vo hum dekh skte hai
    if user is None:
        flash('That is an invalid or expired token','warning')
        return redirect(url_for('reset_request'))
    form=ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password=hashed_password
        db.session.commit()
        flash(f'Your password has been updated', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html',title='Reset Password',form=form)


