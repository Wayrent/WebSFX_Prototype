from app import create_app, db
from app.routes import create_routes

app = create_app()
create_routes(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Убедитесь, что таблицы базы данных созданы
        app.run(debug=True)
