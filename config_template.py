import os
basedir = os.path.abspath(os.path.dirname(__file__))

########
# Change the values and rename to config.py
########
class Config(object):
    # CHANGE KEY
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    ### DB
    # Local Testing
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    # MYSQL
    #SQLALCHEMY_DATABASE_URI = 'mysql://USER:PASS@HOST/DB_NAME'
    #SQLALCHEMY_POOL_RECYCLE = 299
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Page Layout and rules
    RECIPES_PER_PAGE = 6
    COMMENTS_PER_PAGE = 4
    NOTIFICATIONS_PER_PAGE = 4
    VOTES_TO_APPROVE = 1
    VOTES_TO_REJECT = 1
    
    # Mail config
    # Local
    MAIL_SERVER='localhost'
    MAIL_PORT=8025
    # Remote
    #MAIL_SERVER = 'smtp.***.***'
    #MAIL_PORT = 465
    #MAIL_USE_SSL = True
    #MAIL_USERNAME = 'email@email.com'
    #MAIL_PASSWORD = 'password'

    ADMINS = ['email@email.com']
    CKEDITOR_PKG_TYPE = 'basic'
    AVATARS_SAVE_PATH = os.path.join(basedir, 'avatars')
    AVATARS_SIZE_TUPLE = (48, 128, 256)
    IMG_UPLOAD_PATH = os.path.join(basedir, 'img')
    THUMBNAIL_PATH = os.path.join(IMG_UPLOAD_PATH, 'thumbs')
    
    # Enter URL
    URL_BASE = 'URL'

    ### BOOTSTRAP THEMES
    #BOOTSTRAP_BOOTSWATCH_THEME = 'sketchy'
    #BOOTSTRAP_BOOTSWATCH_THEME = 'cerulean'
    #BOOTSTRAP_BOOTSWATCH_THEME = 'journal'
    BOOTSTRAP_BOOTSWATCH_THEME = 'minty'
    #BOOTSTRAP_BOOTSWATCH_THEME = 'yeti'

    ### FILE UPLOAD SIZE LIMIT = 5MB
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024