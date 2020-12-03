from flask import render_template, flash, redirect, url_for, request, session, send_from_directory, Markup
from app import login, app, db, avatars
from app.forms import ConfirmationRequestForm, LoginForm, RegistrationForm, EditProfileForm, EmptyForm, RecipeForm, ResetPasswordRequestForm, ResetPasswordForm, CropAvatarForm, UploadAvatarForm, CommentForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Recipe, Comment, Notification, Vote, RecipeLike
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from email_tools import send_password_reset_email, send_confirmation_email
from sqlalchemy import and_, or_, func
import os, timeago, sys
from random import randint
from PIL import Image

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.template_filter('timeago')
def fromnow(date):
    return timeago.format(date, datetime.utcnow())

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/recipe/<recipe_name>/<recipe_id>', methods=['GET', 'POST'])
def recipe(recipe_name, recipe_id):
    form = CommentForm()
    recipe = Recipe.query.filter_by(id=recipe_id, approved=True).first_or_404()
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(recipe_id=recipe.id).order_by(Comment.timestamp.asc()).paginate(
        page, app.config['COMMENTS_PER_PAGE'], False)
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, author=current_user, recipe_id=recipe.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.', 'alert-success')
        last_page = len(comments.items)
        return redirect(url_for('recipe', page=last_page, recipe_name=recipe.urlify(), recipe_id=recipe.id, _anchor='comments'))
    return render_template('recipe.html', recipe_name=recipe_name, recipe_id=recipe_id, form=form, title=recipe.name, recipe=recipe, user=recipe.author, comments=comments, clean_desc=Markup(recipe.description.replace('&nbsp;', ' ')).striptags())


@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        uploaded_file = request.files['image']
        extension = uploaded_file.filename.split('.')[-1].lower()
        listTags = ','.join([tag.strip() for tag in form.tags.data.split(',')])
        recipe = Recipe(name=form.name.data, category=form.category.data, tags=listTags, serves=int(form.serves.data), description=form.description.data, ingredients=form.ingredients.data, steps=form.steps.data, author=current_user)
        seed = "{:0>5d}".format(randint(0,99999))
        filename = f'{recipe.urlify()}-by-{recipe.author.username.lower()}-{seed}.{extension}'
        uploaded_file.save(os.path.join(app.config['IMG_UPLOAD_PATH'], filename))
        resized_image = Image.open(os.path.join(app.config['IMG_UPLOAD_PATH'], filename))
        resized_image.thumbnail((1100, sys.maxsize),Image.ANTIALIAS)
        resized_image.save(os.path.join(app.config['IMG_UPLOAD_PATH'], filename))
        thumb = Image.open(os.path.join(app.config['IMG_UPLOAD_PATH'], filename))
        o_width, o_height = thumb.size
        if 1.0 * o_height / o_width > 0.75:
            thumb.thumbnail((500, sys.maxsize),Image.ANTIALIAS)
        else:
            thumb.thumbnail((sys.maxsize ,375),Image.ANTIALIAS)
        width, height = thumb.size
        thumb = thumb.crop(((width - 500)/2, (height - 375)/2, (width + 500)/2, (height + 375)/2))
        thumb.save(os.path.join(app.config['THUMBNAIL_PATH'], filename))
        recipe.image = filename
        db.session.add(recipe)
        current_user.notifications.append(Notification(content=f"Your \"{recipe.name}\" recipe is now being moderated by our community.<br>No worries, that's normal! Every single recipe follows the same proccess.<br> What's next? Read our FAQ."))
        db.session.commit()
        flash('Your recipe has been sent for moderation! (Read FAQ)', 'alert-warning')
        return redirect(url_for('index'))  
    return render_template('add_recipe.html', title='Add Recipe', form=form)

@app.route('/index', methods=['GET'])
@app.route('/', methods=['GET'])
def index():
    if not current_user.is_authenticated:
        flash(f'Please <a class="alert-link" href="{url_for("login")}">log in</a> to enjoy the full Pukmun experience', 'alert-info')
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).filter(Recipe.approved == True).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = Recipe.query.filter(Recipe.approved == True).order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    return render_template("index.html", title='Home', recipes=recipes, url="index",
                          comments=latest_comments, top_users=top_users)

@app.route('/top_global', methods=['GET'])
def top_global():
    top_users = User.query.join(Recipe).filter(Recipe.approved == True).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    top_recipes = Recipe.query.filter(Recipe.approved == True).outerjoin(RecipeLike).group_by(Recipe).order_by(func.count(Recipe.likes).desc())
    page = request.args.get('page', 1, type=int)
    recipes = top_recipes.paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    return render_template("top.html", title="Top Global", recipes=recipes,
                            label="Top", value="Global", url='top_global',
                            comments=latest_comments, top_users=top_users)

@app.route('/top_month', methods=['GET'])
def top_month():
    top_users = User.query.join(Recipe).filter(Recipe.approved == True).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    top_recipes = Recipe.query.filter(Recipe.approved == True).outerjoin(RecipeLike).group_by(Recipe).order_by(func.count(RecipeLike.timestamp >= datetime.utcnow() - timedelta(days=30)).desc())
    page = request.args.get('page', 1, type=int)
    recipes = top_recipes.paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    return render_template("top.html", title="Top last 30 days", recipes=recipes,
                          url='top_month', label="Top", value="last 30 days",
                          comments=latest_comments, top_users=top_users)

@app.route('/top_week', methods=['GET'])
def top_week():
    top_users = User.query.join(Recipe).filter(Recipe.approved == True).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    top_recipes = Recipe.query.filter(Recipe.approved == True).outerjoin(RecipeLike).group_by(Recipe).order_by(func.count(RecipeLike.timestamp >= datetime.utcnow() - timedelta(days=7)).desc())
    page = request.args.get('page', 1, type=int)
    recipes = top_recipes.paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    return render_template("top.html", title="Top last 7 days", recipes=recipes,
                          url="top_week", label="Top", value="last 7 days",
                          comments=latest_comments, top_users=top_users)

@app.route('/top_24h', methods=['GET'])
def top_24h():
    top_users = User.query.join(Recipe).filter(Recipe.approved == True).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    top_recipes = Recipe.query.filter(Recipe.approved == True).outerjoin(RecipeLike).group_by(Recipe).order_by(func.count(RecipeLike.timestamp >= datetime.utcnow() - timedelta(days=1)).desc())
    page = request.args.get('page', 1, type=int)
    recipes = top_recipes.paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    return render_template("top.html", title="Top last 24 hours", recipes=recipes,
                          url="top_24h", label="Top", value="last 24 hours",
                          comments=latest_comments, top_users=top_users)

@app.route('/cookbook', methods=['GET'])
@login_required
def cookbook():
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).filter(Recipe.approved == True).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = current_user.followed_recipes().paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    return render_template('cookbook.html', title='Cookbook',
                            recipes=recipes, url="cookbook",
                            comments=latest_comments, top_users=top_users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('Already logged in.', 'alert-warning')
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(or_(User.username.ilike(form.username_or_email.data), User.email.ilike(form.username_or_email.data))).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'alert-danger')
            return redirect(url_for('login'))
        elif not user.confirmed:
            flash(f'You still need to confirm your email. Didn\'t get the email. <a class="alert-link" href="{url_for("confirmation_request")}"><strong>Send me another confirmation email</strong></a>', 'alert-danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        flash('Logged in successfully!', 'alert-success')
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('Already logged in', 'alert-warning')
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User registered! Please check your e-mail to confirm your account.', 'alert-success')
        send_confirmation_email(user)
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter(User.username.ilike(username)).first_or_404()
    page = request.args.get('page', 1, type=int)
    recipes = user.my_approved_recipes().order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    form = EmptyForm()
    return render_template('user.html', title=user.username, user=user, recipes=recipes,
                           url="user", form=form,
                           clean_about_me=Markup(user.about_me.replace('&nbsp;', ' ')).striptags())

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form_edit_profile = EditProfileForm(current_user.username, current_user.email)
    form_edit_avatar = UploadAvatarForm()
    if form_edit_avatar.validate_on_submit() and form_edit_avatar.submit.data:
        f = request.files.get('image')
        raw_filename = avatars.save_avatar(f)
        session['raw_filename'] = raw_filename
        return redirect(url_for('crop'))
    elif form_edit_profile.validate_on_submit() and form_edit_profile.submit.data:
        current_user.username = form_edit_profile.username.data
        current_user.about_me = form_edit_profile.about_me.data
        flash('Your changes have been saved.', 'alert-success')
        if current_user.email.lower() != form_edit_profile.email.data.lower():
            current_user.email = form_edit_profile.email.data
            current_user.confirmed = False
            db.session.commit()
            flash('Please check your e-mail to confirm your new e-mail address.', 'alert-info')
            send_confirmation_email(current_user)
            logout_user()
            return redirect(url_for('login'))
        current_user.email = form_edit_profile.email.data
        db.session.commit()
        return redirect(url_for('user', username=current_user.username.lower()))
    elif request.method == 'GET':
        form_edit_profile.username.data = current_user.username
        form_edit_profile.email.data = current_user.email
        form_edit_profile.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form_avatar=form_edit_avatar, form_profile=form_edit_profile)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter(User.username.ilike(username)).first()
        if user is None:
            flash(f'User {username} not found.', 'alert-danger')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!', 'alert-danger')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!', 'alert-success')
        return redirect(url_for('user', username=username))
    else:
        flash(f'Something went wrong.', 'alert-danger')
        return redirect(url_for('index'))

@app.route('/upvote/<recipe>', methods=['POST'])
@login_required
def upvote(recipe):
    form = EmptyForm()
    if form.validate_on_submit():
        recipe_voted = Recipe.query.filter_by(id=recipe, approved=False).first()
        if recipe_voted is None:
            flash(f'[ERROR] Recipe doesn\'t exist or it has already been approved.', 'alert-danger')
        elif Vote.query.filter_by(voter_id=current_user.id, recipe_id=recipe_voted.id).first() is not None:
            flash(f'[ERROR] You\'ve already voted this recipe.', 'alert-danger')
        else:
            vote = Vote(voter_id=current_user.id, recipe_id=recipe, is_positive=True)
            db.session.add(vote)
            flash(f'Thanks for your vote!', 'alert-success')
            if recipe_voted.upvotes() >= app.config['VOTES_TO_APPROVE']:
                recipe_voted.approve()
                for vote_to_remove in recipe_voted.votes_received():
                    db.session.delete(vote_to_remove)
                new_notification = Notification(content=f'Congraulations, your <a href="{url_for("recipe", recipe_name=recipe_voted.name, recipe_id=recipe_voted.id)}">{recipe_voted.name}</a> recipe has just been approved by the community and is online.<br>Thanks for keep Pukmun going!', recipient_id=recipe_voted.author.id)
                db.session.add(new_notification)
            db.session.commit()
    else:
        flash(f'That\'s not the way it works!', 'alert-danger')
        return redirect(url_for('index'))
    return redirect(url_for('moderate'))

@app.route('/downvote/<recipe>', methods=['POST'])
@login_required
def downvote(recipe):
    form = EmptyForm()
    if form.validate_on_submit():
        recipe_voted = Recipe.query.filter_by(id=recipe, approved=False).first()
        if recipe_voted is None:
            flash(f'[ERROR] Recipe does\'t exist or it has already been approved.', 'alert-danger')
        elif Vote.query.filter_by(voter_id=current_user.id, recipe_id=recipe_voted.id).first() is not None:
            flash(f'[ERROR] You\'ve already voted this recipe.', 'alert-danger')
        else:
            vote = Vote(voter_id=current_user.id, recipe_id=recipe, is_positive=False)
            db.session.add(vote)
            flash(f'Thanks for your vote!', 'alert-success')
            if recipe_voted.downvotes() >= app.config['VOTES_TO_REJECT']:
                new_notification = Notification(content=f'Dear user, your {recipe_voted.name} recipe has sadly been rejected by the community.<br>Read our FAQ to understand more about the process.', recipient_id=recipe_voted.author.id)
                db.session.add(new_notification)
                db.session.delete(recipe_voted)
                os.remove(os.path.join(app.config['IMG_UPLOAD_PATH'], recipe_voted.image))
                os.remove(os.path.join(app.config['THUMBNAIL_PATH'], recipe_voted.image))
            db.session.commit()
    else:
        flash(f'That\'s not the way it works!', 'alert-danger')
        return redirect(url_for('index'))
    return redirect(url_for('moderate'))

@app.route('/moderate', methods=['GET'])
@login_required
def moderate():
    #left-join
    recipe = Recipe.query.outerjoin(Vote).filter(Recipe.approved == False, Recipe.author != current_user, or_(Vote.voter_id == None, Vote.voter_id != current_user.id)).order_by(func.random()).first()
    form = EmptyForm()
    return render_template('moderate.html', title='Moderation Area',
                                            recipe=recipe, form=form)

@app.route('/see/<notification>', methods=['POST'])
@login_required
def see(notification):
    form = EmptyForm()
    if form.validate_on_submit():
        notif = Notification.query.filter(Notification.id == notification, Notification.recipient_id == current_user.id, Notification.seen == False).first()
        if notif is None:
            flash(f'[ERROR] Message does not exist or was already marked as seen.', 'alert-danger')
        else:
            notif.seen = True
            db.session.commit()
            flash(f'Message marked as seen!', 'alert-success')
    return redirect(url_for('msg'))

@app.route('/see_all', methods=['POST'])
@login_required
def see_all():
    form = EmptyForm()
    if form.validate_on_submit():
        notifications = Notification.query.filter(Notification.recipient_id == current_user.id, Notification.seen == False).all()
        for notification in notifications:
            notification.seen = True
        db.session.commit()
        flash(f'Everything marked as seen!', 'alert-success')
    return redirect(url_for('msg'))

@app.route('/remove_all', methods=['POST'])
@login_required
def remove_all():
    form = EmptyForm()
    if form.validate_on_submit():
        notifications = Notification.query.filter(Notification.recipient_id == current_user.id).all()
        for notification in notifications:
            db.session.delete(notification)
        db.session.commit()
        flash(f'All notifications removed', 'alert-success')
    return redirect(url_for('msg'))

@app.route('/unsee/<notification>', methods=['POST'])
@login_required
def unsee(notification):
    form = EmptyForm()
    if form.validate_on_submit():
        notif = Notification.query.filter(Notification.id == notification, Notification.recipient_id == current_user.id, Notification.seen == True).first()
        if notif is None:
            flash(f'[ERROR] Message does not exist or was already marked as unseen.', 'alert-danger')
        else:
            notif.seen = False
            db.session.commit()
            flash(f'Message marked as unseen!', 'alert-success')
    return redirect(url_for('msg'))

@app.route('/remove_notification/<notification>', methods=['POST'])
@login_required
def remove_notification(notification):
    form = EmptyForm()
    if form.validate_on_submit():
        notif = Notification.query.filter(Notification.id == notification, Notification.recipient_id == current_user.id).first()
        if notif is None:
            flash(f'[ERROR] Message does not exist or was already removed', 'alert-danger')
        else:
            db.session.delete(notif)
            db.session.commit()
            flash(f'Message removed!', 'alert-success')
    return redirect(url_for('msg'))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter(User.username.ilike(username)).first()
        if user is None:
            flash(f'User {username} not found.', 'alert-danger')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username), 'alert-danger')
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.', 'alert-success')
        return redirect(url_for('user', username=username))
    else:
        flash(f'Something went wrong.', 'alert-danger')
        return redirect(url_for('index'))

@app.route('/msg')
@login_required
def msg():
    form = EmptyForm()
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(recipient_id=current_user.id).order_by(Notification.timestamp.desc()).paginate(
        page, app.config['NOTIFICATIONS_PER_PAGE'], False)
    return render_template("notifications.html", title='Notifications', form=form,
                            notifications=notifications, url="msg")                        

@app.route('/liked')
@login_required
def liked():
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).filter(Recipe.approved == True).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = Recipe.query.filter(Recipe.likes.any(user_id=current_user.id)).order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    return render_template("index.html", title='Liked', recipes=recipes,
                          url="liked", label="Favourites",
                          comments=latest_comments, top_users=top_users)

@app.route('/search', methods=['POST'])
def searchPost():
    search = request.form['search']
    return redirect(url_for('search', search=search.lower()))

@app.route('/search/<search>', methods=['GET'])
def search(search):
    if not search:
        search = request.get_data()
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).filter(Recipe.approved == True).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = Recipe.query.filter(Recipe.approved == True, or_(Recipe.name.like('%' + search + '%'), Recipe.tags.like('%' + search + '%'))).order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    return render_template("index.html", title="Search: "+search, recipes=recipes,
                          url="search", label="Search", value=search,
                          comments=latest_comments, top_users=top_users)

@app.route('/category/<category>')
def category(category):
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).filter(Recipe.approved == True).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = Recipe.query.filter(Recipe.approved == True, Recipe.category.like('%' + category + '%')).order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    return render_template("index.html", title="Category: "+category, recipes=recipes,
                          url="category", label='Category', value=category,
                          comments=latest_comments, top_users=top_users)

@app.route('/tag/<tag>')
def tag(tag):
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).filter(Recipe.approved == True).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = Recipe.query.filter(Recipe.approved == True, Recipe.tags.like('%' + tag + '%')).order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    return render_template("index.html", title="Tag: "+tag, recipes=recipes,
                          url="tag", label="Tag", value=tag,
                          comments=latest_comments, top_users=top_users)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email.ilike(form.email.data)).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', 'alert-info')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/confirmation_request', methods=['GET', 'POST'])
def confirmation_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ConfirmationRequestForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email.ilike(form.email.data)).first()
        if user:
            send_confirmation_email(user)
        flash('Check your email for the instructions to confirm your account', 'alert-info')
        return redirect(url_for('login'))
    return render_template('confirmation_request.html',
                           title='Confirmation Request', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid request (Link expired?)', 'alert-danger')
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'alert-success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/confirmation/<token>', methods=['GET', 'POST'])
def confirmation(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_confirmation_token(token)
    if not user:
        flash('Invalid request (Link expired?)', 'alert-danger')
        return redirect(url_for('index'))
    else:
        user.confirmed = True
        db.session.commit()
        flash('Your e-mail has been confirmed.', 'alert-success')
        return redirect(url_for('login'))

@app.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(app.config['AVATARS_SAVE_PATH'], filename)

@app.route('/img/<path:filename>')
def get_img(filename):
    if filename == '':
        return send_from_directory(app.config['IMG_UPLOAD_PATH'], "no_img.png")
    return send_from_directory(app.config['IMG_UPLOAD_PATH'], filename)

@app.route('/img/thumbs/<path:filename>')
def get_thumb(filename):
    if filename == '':
        return send_from_directory(app.config['THUMBNAIL_PATH'], "no_img.png")
    return send_from_directory(app.config['THUMBNAIL_PATH'], filename)

@app.route('/crop', methods=['GET', 'POST'])
@login_required
def crop():
    form = CropAvatarForm()
    if form.validate_on_submit():
        filenames = avatars.crop_avatar(session['raw_filename'], form.x.data, form.y.data, form.w.data, form.h.data)
        current_user.avatar_s = url_for('get_avatar', filename=filenames[0])
        current_user.avatar_m = url_for('get_avatar', filename=filenames[1])
        current_user.avatar_l = url_for('get_avatar', filename=filenames[2])
        db.session.commit()
        os.remove(os.path.join(app.config['AVATARS_SAVE_PATH'], session['raw_filename']))
        flash('Your changes have been saved.', 'alert-success')
        return redirect(url_for('edit_profile'))
    return render_template('crop.html', title='Crop Image', form=form)

@app.route('/like/<int:recipe_id>/<action>')
@login_required
def like_action(recipe_id, action):
    recipe = Recipe.query.filter_by(id=recipe_id, approved=True).first_or_404()
    if action == 'like':
        current_user.like_recipe(recipe)
        db.session.commit()
        flash('You now like this recipe.', 'alert-success')
    if action == 'unlike':
        current_user.unlike_recipe(recipe)
        db.session.commit()
        flash('You don\'t like this recipe anymore.', 'alert-success')
    return redirect(request.referrer)