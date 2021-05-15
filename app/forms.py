from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Regexp
from app.models import User, Recipe
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_login import current_user
from app import app

class UploadAvatarForm(FlaskForm):
    image = FileField('Select Image (Max. size 3MB)', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'The file format should be .jpg or .png.')
    ])
    submit = SubmitField('Upload')

class CropAvatarForm(FlaskForm):
    x = HiddenField()
    y = HiddenField()
    w = HiddenField()
    h = HiddenField()
    submit = SubmitField('Crop')

class LoginForm(FlaskForm):
    username_or_email = StringField('Username or E-mail', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    if app.config['RECAPTCHA_PUBLIC_KEY']:
        recaptcha = RecaptchaField()
    submit = SubmitField('Sign In')

class CommentForm(FlaskForm):
    content = CKEditorField('(2500 character max.)', validators=[Length(min=12, max=2500, message="5 characters min. - 2500 characters max.")])
    submit = SubmitField('Send')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Regexp(r'^\w+$', message="Username must contain only letters numbers or underscore"), Length(min=5, max=25, message="Username must be betwen 5 & 25 characters")])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5, max=25, message="Password must be betwen 5 & 25 characters")])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    if app.config['RECAPTCHA_PUBLIC_KEY']:
        recaptcha = RecaptchaField()
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter(User.username.ilike(username.data)).first()
        if user is not None:
            raise ValidationError('Username already in use.')

    def validate_email(self, email):
        user = User.query.filter(User.email.ilike(email.data)).first()
        if user is not None:
            raise ValidationError('Email address already in use.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Regexp(r'^\w+$', message="Username must contain only letters numbers or underscore"), Length(min=5, max=25, message="Username must be betwen 5 & 25 characters")])
    email = StringField('E-mail (you will need to confirm your new e-mail)', validators=[DataRequired(), Email()])
    about_me = CKEditorField('About me (500 max.)', validators=[Length(min=0, max=500)])
    submit = SubmitField('Submit')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data.lower() != self.original_username.lower():
            user = User.query.filter(User.username.ilike(self.username.data)).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        if email.data.lower() != self.original_email.lower():
            user = User.query.filter(User.email.ilike(self.email.data)).first()
            if user is not None:
                raise ValidationError('Please use a different e-mail.')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class RecipeForm(FlaskForm):
    image = FileField('Select Image (Max. size 5 MB)', validators=[
        FileRequired(),
        FileAllowed(['jpeg', 'jpg', 'png'], 'The formats accepted are .jpg and .png.')
    ])
    name = StringField('Name', validators=[
        DataRequired(), Length(min=1, max=64)])
    category = SelectField('Category', validators=[
        DataRequired()], choices=['Starter', 'Main', 'Dessert', 'Snack', 'Sauce', 'Bread'])
    tags = StringField('Tags (separated by a comma)', validators=[
        DataRequired(), Length(min=1, max=120)])
    serves = SelectField('Servings', validators=[
        DataRequired()], choices=['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24'])
    description = CKEditorField('Description', validators=[
        DataRequired(), Length(min=1, max=2000)])
    ingredients = CKEditorField('Ingredients', validators=[
        DataRequired(), Length(min=1, max=2500)], default="<ul><li></li></ul>")
    steps = CKEditorField('Steps', validators=[
        DataRequired(), Length(min=1, max=5000)], default="<ol><li></li></ol>")
    submit = SubmitField('Submit')

    def validate_name(self, name):
        recipe = Recipe.query.filter(Recipe.name.ilike(name.data), Recipe.user_id == current_user.id).first()
        if recipe is not None:
            raise ValidationError('You have already submitted a recipe with this name.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ConfirmationRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Confirmation E-mail')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5, max=25, message="Password must be betwen 5 & 25 characters")])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')