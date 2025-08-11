from pathlib import Path
import environ

env = environ.Env(
    DEBUG=(bool, False)
)

BASE_DIR = Path(__file__).parent.parent.parent.absolute()
LOG_DIR = Path.joinpath(BASE_DIR, "logs")
APP_DIR = Path.joinpath(BASE_DIR, "app")
CONFIG_DIR = Path.joinpath(BASE_DIR, 'config')
IN_DIR = Path.joinpath(BASE_DIR, "data/in")
OUT_DIR = Path.joinpath(BASE_DIR, "data/out")

environ.Env.read_env(Path(BASE_DIR, ".env"))

RABBITMQ_DEFAULT_USER=env('RABBITMQ_DEFAULT_USER')
RABBITMQ_DEFAULT_PASS=env('RABBITMQ_DEFAULT_PASS')
RABBITMQ_HOST=env('RABBITMQ_HOST')
RABBITMQ_PORT=env('RABBITMQ_PORT')
RABBITMQ_HEARTBEAT=18000
RABBITMQ_BLOCKED_CONNECTION_TIMEOUT=10800

WDM_PROXY = "la.residential.rayobyte.com:8000"


DB_NAME = env('DB_NAME')
DB_USER = env('DB_USER')
DB_PASSWORD = env('DB_PASSWORD')
DB_HOST = env('DB_HOST')
DB_PORT = env('DB_PORT')

GRPC_HOST = env('GRPC_HOST')
GRPC_PORT = env('GRPC_PORT')

REDIS_HOST = env('REDIS_HOST')
REDIS_PASS = env('REDIS_PASS')
REDIS_PORT = env('REDIS_PORT')

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
DBENGINE = 'psqlextra.backend'
DATABASES = {
    'default': {
        'ENGINE': DBENGINE,
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'POOL_OPTIONS': {
                    'POOL_SIZE': 100,
                    'MAX_OVERFLOW': 10,
                    'RECYCLE': 3600
                }
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    "django.contrib.postgres",
    "psqlextra",
    'app.infrastructure'
]

FACEBOOK_THREADS = 22
