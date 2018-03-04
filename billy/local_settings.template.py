DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': ''
    }
}

BUGSNAG_API_KEY='YOUR_API_KEY'

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = False

CORS_ORIGIN_WHITELIST = (
    '127.0.0.1:9090',
    'http://127.0.0.1:9090',
    'localhost:9090',
    'http://localhost:9090',
)
