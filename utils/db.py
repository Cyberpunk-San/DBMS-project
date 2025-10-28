# utils/db.py
from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    """Initialize MySQL with the Flask app instance."""
    app.config.from_object('config.Config')
    mysql.init_app(app)