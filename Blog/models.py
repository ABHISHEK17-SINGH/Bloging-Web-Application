from datetime import datetime
from Blog import db,login_manager,app
from itsdangerous import  TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# noinspection PyTypeChecker
class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username= db.Column(db.String(20),unique=True,nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file= db.Column(db.String(20), unique=False, nullable=False,default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post',backref='author',lazy=True)


    def get_reset_token(self,expires_sec=1800): # ye time humesha seconds mai hoga
        s= Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id':self.id}).decode('utf-8') #this line generate token @staticmethod

    @staticmethod
    def verify_reset_token(token):
        s= Serializer(app.config['SECRET_KEY'])  #Serialization involves converting a Python object into a format suitable for transmission or storage. This format is often a string or byte representation.
        #  For example, if you have a Python dictionary representing user data, you might want to serialize it into a JSON string before sending it over the network or storing it in a database.
        try:
            user_id=s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)



    def __repr__(self):
        return f"User('{self.username}','{self.email}','{self.image_file}') "

class Post(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(100),nullable=False)
    date_posted = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)

    def __repr__(self):
        return f"Post('{self.title}','{self.date_posted}')"