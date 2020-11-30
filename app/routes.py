from flask import render_template, flash, redirect, url_for, request, session, send_from_directory, Markup
from app import login, app, db, avatars
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, RecipeForm, ResetPasswordRequestForm, ResetPasswordForm, CropAvatarForm, UploadAvatarForm, CommentForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Recipe, Comment, Notification
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from email_tools import send_password_reset_email
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

@app.route('/<recipe_name>/<recipe_id>', methods=['GET', 'POST'])
def recipe(recipe_name, recipe_id):
    form = CommentForm()
    recipe = Recipe.query.filter_by(id=recipe_id).first_or_404()
    #comments = Comment.query.filter_by(recipe_id=recipe.id).order_by(Comment.timestamp.asc()).all()
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(recipe_id=recipe.id).order_by(Comment.timestamp.asc()).paginate(
        page, app.config['COMMENTS_PER_PAGE'], False)
    next_url = url_for('recipe', page=comments.next_num, recipe_name=recipe.urlify(), recipe_id=recipe.id, _anchor='comments') \
        if comments.has_next else None
    prev_url = url_for('recipe', page=comments.prev_num, recipe_name=recipe.urlify(), recipe_id=recipe.id, _anchor='comments')  \
        if comments.has_prev else None

    if form.validate_on_submit():
        comment = Comment(content=form.content.data, author=current_user, recipe_id=recipe.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.', 'alert-success')
        return redirect(url_for('recipe', next_url=next_url, prev_url=prev_url, recipe_name=recipe.urlify(), recipe_id=recipe.id, _anchor='comments'))
    return render_template('recipe.html', next_url=next_url, prev_url=prev_url, form=form, title=recipe.name, recipe=recipe, user=recipe.author, comments=comments.items, clean_desc=Markup(recipe.description.replace('&nbsp;', ' ')).striptags())

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
        current_user.notifications.append(Notification(content=f"Your \"{recipe.name}\" recipe has been submitted. What's next? Read our FAQ."))
        db.session.commit()
        flash('Your recipe has been sent for moderation! (Read FAQ)', 'alert-warning')
        return redirect(url_for('recipe', recipe_name=recipe.urlify(), recipe_id=recipe.id))  
    return render_template('add_recipe.html', title='Add Recipe', form=form)

@app.route('/index', methods=['GET'])
@app.route('/', methods=['GET'])
#@login_required
def index():
    if not current_user.is_authenticated:
        flash(f'Please <a class="font-weight-bold" href="{url_for("login")}">log in</a> to enjoy the full Pukmun experience', 'alert-info')
        return render_template('index.html', title='Home')
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = current_user.followed_recipes().paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    next_url = url_for('index', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('index', page=recipes.prev_num) \
        if recipes.has_prev else None
    return render_template('index.html', title='Home',
                           recipes=recipes.items, next_url=next_url,
                           prev_url=prev_url, comments=latest_comments, top_users=top_users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('Already logged in.', 'alert-warning')
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.username.ilike(form.username.data)).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'alert-danger')
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
        flash('Congratulations, you are now a registered user!', 'alert-success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter(User.username.ilike(username)).first_or_404()
    page = request.args.get('page', 1, type=int)
    recipes = user.recipes.order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('user', username=user.username, page=recipes.prev_num) \
        if recipes.has_prev else None
    form = EmptyForm()
    return render_template('user.html', title=user.username, user=user, recipes=recipes.items,
                           next_url=next_url, prev_url=prev_url, form=form, clean_about_me=Markup(user.about_me.replace('&nbsp;', ' ')).striptags())

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form_edit_profile = EditProfileForm(current_user.username)
    form_edit_avatar = UploadAvatarForm()
    if form_edit_avatar.validate_on_submit() and form_edit_avatar.submit.data:
        f = request.files.get('image')
        raw_filename = avatars.save_avatar(f)
        session['raw_filename'] = raw_filename
        return redirect(url_for('crop'))
    elif form_edit_profile.validate_on_submit() and form_edit_profile.submit.data:
        current_user.username = form_edit_profile.username.data
        current_user.about_me = form_edit_profile.about_me.data
        db.session.commit()
        flash('Your changes have been saved.', 'alert-success')
        return redirect(url_for('user', username=current_user.username.lower()))
    elif request.method == 'GET':
        form_edit_profile.username.data = current_user.username
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
        return redirect(url_for('index'))

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
            flash(f'Message marked as seen!', 'alert-success')
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
        return redirect(url_for('index'))

@app.route('/explore')
#@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = Recipe.query.order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    next_url = url_for('explore', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('explore', page=recipes.prev_num) \
        if recipes.has_prev else None
    return render_template("explore.html", title='Explore', recipes=recipes.items,
                          next_url=next_url, prev_url=prev_url,
                          comments=latest_comments, top_users=top_users)

@app.route('/msg')
@login_required
def msg():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(recipient_id=current_user.id).order_by(Notification.timestamp.desc()).paginate(
        page, app.config['NOTIFICATIONS_PER_PAGE'], False)
    next_url = url_for('msg', page=notifications.next_num) \
        if notifications.has_next else None
    prev_url = url_for('msg', page=notifications.prev_num) \
        if notifications.has_prev else None
    form = EmptyForm()
    return render_template("notifications.html", title='Notifications', form=form, notifications=notifications.items,
                          next_url=next_url, prev_url=prev_url)                        

@app.route('/liked')
def liked():
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = Recipe.query.filter(Recipe.likes.any(user_id=current_user.id)).order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    next_url = url_for('explore', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('explore', page=recipes.prev_num) \
        if recipes.has_prev else None
    return render_template("explore.html", title='Liked', recipes=recipes.items,
                          next_url=next_url, prev_url=prev_url, label="Favourites",
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
    top_users = User.query.join(Recipe).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = Recipe.query.filter(or_(Recipe.name.like('%' + search + '%'), Recipe.tags.like('%' + search + '%'))).order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    next_url = url_for('search', search=search, page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('search', search=search, page=recipes.prev_num) \
        if recipes.has_prev else None
    return render_template("explore.html", title="Search: "+search, recipes=recipes.items,
                          next_url=next_url, prev_url=prev_url, label="Search", value=search,
                          comments=latest_comments, top_users=top_users)

@app.route('/category/<category>')
def category(category):
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = Recipe.query.filter(Recipe.category.like('%' + category + '%')).order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    next_url = url_for('category', category=category, page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('category', category=category, page=recipes.prev_num) \
        if recipes.has_prev else None
    return render_template("explore.html", title="Category: "+category, recipes=recipes.items,
                          next_url=next_url, prev_url=prev_url, label='Category', value=category,
                          comments=latest_comments, top_users=top_users)

@app.route('/tag/<tag>')
def tag(tag):
    page = request.args.get('page', 1, type=int)
    top_users = User.query.join(Recipe).group_by(User).order_by(func.count(User.recipes).desc()).limit(3).all()
    latest_comments = Comment.query.order_by(Comment.timestamp.desc()).limit(5).all()
    recipes = Recipe.query.filter(Recipe.tags.like('%' + tag + '%')).order_by(Recipe.timestamp.desc()).paginate(
        page, app.config['RECIPES_PER_PAGE'], False)
    next_url = url_for('tag', tag=tag, page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('tag', tag=tag, page=recipes.prev_num) \
        if recipes.has_prev else None
    return render_template("explore.html", title="Tag: "+tag, recipes=recipes.items,
                          next_url=next_url, prev_url=prev_url, label="Tag", value=tag,
                          comments=latest_comments, top_users=top_users)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', 'alert-info')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'alert-success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

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
    recipe = Recipe.query.filter_by(id=recipe_id).first_or_404()
    if action == 'like':
        current_user.like_recipe(recipe)
        db.session.commit()
        flash('You now like this recipe.', 'alert-success')
    if action == 'unlike':
        current_user.unlike_recipe(recipe)
        db.session.commit()
        flash('You don\'t like this recipe anymore.', 'alert-success')
    return redirect(request.referrer)