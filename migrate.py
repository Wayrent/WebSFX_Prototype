from app import create_app, db
from flask_migrate import Migrate
from app.models import User, Sound, Collection, Favorite, Notification

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        import sys
        if 'db' in sys.argv:
            from flask.cli import FlaskGroup
            cli = FlaskGroup(create_app=create_app)
            cli.main()
        else:
            app.run(debug=True)
