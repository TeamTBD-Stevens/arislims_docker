from flask import Flask
from flask_mysqldb import MySQL
from config import devConfig, deployConfig, godzillaConfig

app = Flask(__name__)
app.config.from_object(godzillaConfig)
mysql = MySQL(app)
