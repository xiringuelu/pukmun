from app import db
from app.models import User

#ADMIN SETTINGS
### Change the values
USERNAME = 'admin'
EMAIL = 'admin@admin.com'
PASS = 'admin'

user = User(username=USERNAME, email=EMAIL, is_admin= True, confirmed=True)
user.set_password(PASS)

db.session.add(user)
db.session.commit()