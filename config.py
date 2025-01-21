import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://admin:admin@localhost/mydatabase'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')  # Обновленный путь к папке загрузок
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'}
    # Заглушка для Yandex.Kassa
    YANDEX_KASSA_API_KEY = os.environ.get('YANDEX_KASSA_API_KEY') or 'your_yandex_kassa_api_key'
    YANDEX_KASSA_SHOP_ID = 'your_shop_id'
    YANDEX_KASSA_SHOP_PASSWORD = 'your_shop_password'
