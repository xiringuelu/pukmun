from flask_admin.contrib import sqla
from flask_admin import AdminIndexView, expose, helpers
from flask_login import current_user
from flask import flash, redirect, url_for

class PukmunUserModelView(sqla.ModelView):
    column_list = ('username', 'email', 'is_admin')
    column_filters = ('username', 'email', 'is_admin')
    column_searchable_list = ('username', 'email')
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('You don\'t have access to this area.', 'alert-danger')
        return redirect(url_for('index'))

class PukmunRecipeModelView(sqla.ModelView):
    column_list = ('name', 'author.username', 'category', 'tags', 'approved')
    column_filters = ('name', 'author.username')
    column_searchable_list = ('name', 'author.username')
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('You don\'t have access to this area.', 'alert-danger')
        return redirect(url_for('index'))
    
class PukmunCommentModelView(sqla.ModelView):
    column_list = ('recipe.name', 'author.username', 'content')
    column_filters = ('recipe.name', 'author.username')
    column_searchable_list = ('recipe.name', 'author.username')
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('You don\'t have access to this area.', 'alert-danger')
        return redirect(url_for('index'))

class PukmunNotificationModelView(sqla.ModelView):
    column_list = ('recipient.username', 'content', 'seen')
    column_filters = ('recipient.username', 'content', 'seen')
    column_searchable_list = ('recipient.username', 'content', 'seen')
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('You don\'t have access to this area.', 'alert-danger')
        return redirect(url_for('index'))

class PukmunVoteModelView(sqla.ModelView):
    column_list = ('voter.username', 'recipe.name', 'is_positive')
    column_filters = ('voter.username', 'recipe.name', 'is_positive')
    column_searchable_list = ('voter.username', 'recipe.name')
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('You don\'t have access to this area.', 'alert-danger')
        return redirect(url_for('index'))

class PukmunLikeModelView(sqla.ModelView):
    column_list = ('user.username', 'recipe.name')
    column_filters = ('user.username', 'recipe.name')
    column_searchable_list = ('user.username', 'recipe.name')
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('You don\'t have access to this area.', 'alert-danger')
        return redirect(url_for('index'))

class AdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not (current_user.is_authenticated and current_user.is_admin):
            flash('You don\'t have access to this area.', 'alert-danger')
            return redirect(url_for('index'))
        return super(AdminIndexView, self).index()