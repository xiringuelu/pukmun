from hashlib import md5
from app import db, app, admin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
from time import time
import jwt, re
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib import sqla
from admin import PukmunUserModelView, PukmunRecipeModelView, PukmunCommentModelView, PukmunNotificationModelView

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    seen = db.Column(db.Boolean, default=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class RecipeLike(db.Model):
    __tablename__ = 'recipe_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    recipes = db.relationship('Recipe', backref='author', lazy='dynamic')
    about_me = db.Column(db.Text, default='')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_s = db.Column(db.String(64))
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic')

    def unread_count(self):
        return self.notifications.filter(Notification.seen == False).count()

    def __repr__(self):
        return '<User {}>'.format(self.username)   
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_recipes(self):
        followed = Recipe.query.join(
            followers, (followers.c.followed_id == Recipe.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Recipe.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Recipe.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    liked = db.relationship(
        'RecipeLike',
        foreign_keys='RecipeLike.user_id',
        backref='user', lazy='dynamic')

    def like_recipe(self, recipe):
        if not self.has_liked_recipe(recipe):
            like = RecipeLike(user_id=self.id, recipe_id=recipe.id)
            db.session.add(like)

    def unlike_recipe(self, recipe):
        if self.has_liked_recipe(recipe):
            RecipeLike.query.filter_by(
                user_id=self.id,
                recipe_id=recipe.id).delete()

    def has_liked_recipe(self, recipe):
        return RecipeLike.query.filter(
            RecipeLike.user_id == self.id,
            RecipeLike.recipe_id == recipe.id).count() > 0

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(64), default="no_img.png")
    name = db.Column(db.String(64))
    category = db.Column(db.String(32))
    tags = db.Column(db.String(120))
    serves = db.Column(db.Integer)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text)
    steps = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved = db.Column(db.Boolean, default=False)

    likes = db.relationship('RecipeLike', backref='recipe', lazy='dynamic')

    comments = db.relationship('Comment', backref='recipe', lazy='dynamic')

    def __repr__(self):
        return '<Recipe {}>'.format(self.name)

    def urlify(self):
        url = re.sub(r"[^\w\s]", '', self.name)
        url = re.sub(r"\s+", '-', url)
        return url.lower()

admin.add_view(PukmunUserModelView(User, db.session))
admin.add_view(PukmunRecipeModelView(Recipe, db.session))
admin.add_view(PukmunCommentModelView(Comment, db.session))
admin.add_view(PukmunNotificationModelView(Notification, db.session))