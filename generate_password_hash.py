from werkzeug.security import generate_password_hash

password = 'admin125378'  # Замените на ваш пароль
hashed_password = generate_password_hash(password)
print(hashed_password)
