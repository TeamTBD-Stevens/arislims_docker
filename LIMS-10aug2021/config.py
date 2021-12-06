import os

class devConfig(object):
    DEBUG = True
    TESTING = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or "J@NcRfTjWnZr4u7x!A%D*G-KaPdSgVkXp2s5v8y/B?E(H+MbQeThWmZq4t6w9z$C"
    
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'arisDB'

    FILE_UPLOADS = "./application/input"

class godzillaConfig(object):
    DEBUG = True
    TESTING = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or "J@NcRfTjWnZr4u7x!A%D*G-KaPdSgVkXp2s5v8y/B?E(H+MbQeThWmZq4t6w9z$C"
    
    MYSQL_HOST = 'db' #11/24/2021: changing from 'localhost' to 'db' to match the name of container.
    MYSQL_USER = 'lims_admin'
    MYSQL_PASSWORD = 'Nephros413Aris'
    MYSQL_DB = 'arisDB'

    FILE_UPLOADS = "./application/input"

class deployConfig(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'arisDB'

    FILE_UPLOADS = "./application/input"
