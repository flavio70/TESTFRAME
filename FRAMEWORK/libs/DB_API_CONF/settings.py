"""
Django settings for K@TE project.

Generated by 'django-admin startproject' using Django 1.8.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ky5jos-2*0boo_&yo26ibd4x&6dw-8*^6)^9h!ri5^il&(g-q_'

# Application definition

INSTALLED_APPS = (
    'DB_API_LIB',
)

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
	'HOST':'151.98.52.73',
        'NAME': 'KATE' ,
	'USER': 'smosql' ,
	'PASSWORD' : 'sm@ptics' ,
	'PORT': '3306' ,
    }
}
                                    
