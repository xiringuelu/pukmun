from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.fileadmin import FileAdmin
from flask_ckeditor import CKEditor
from flask_avatars import Avatars
from admin import AdminIndexView

import os.path as op
path = op.join(op.dirname(__file__), 'static')

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True)
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)

bootstrap = Bootstrap(app)
admin = Admin(app, name='Pukmun Admin', index_view=AdminIndexView(), template_mode='bootstrap3')
admin.add_view(FileAdmin(path, '/static/', name='Static Files'))
ckeditor = CKEditor(app)
avatars = Avatars(app)

#with app.app_context():
#    if db.engine.url.drivername == 'sqlite':
#        migrate.init_app(app, db, render_as_batch=True)
#    else:
#        migrate.init_app(app, db)

from app import routes, models, errors
