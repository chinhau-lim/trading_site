import os

APPLICATION_ROOT = '/'

# Secret key for encrypting cookies
# python3 -c 'import os; print(os.urandom(24))'
SECRET_KEY = b'x\xe8&\xeeF\xa7\xf8x\x17\x0b\x9d0\x19\xc5\xe0\xa2O\x1b?)\xda\xef\xf4y'
SESSION_COOKIE_NAME = 'login'

# File Upload to database/uploads/
UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    'database', 'uploads'
)

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Database file is database/trading_db.sqlite3
DATABASE_FILENAME = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    'database', 'trading_db.sqlite3'
)
