from flask import render_template, flash, redirect, url_for, request, current_app as app
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Sound, Collection, Favorite, Notification
from app.forms import LoginForm, RegistrationForm
from urllib.parse import urlparse
from datetime import datetime
from werkzeug.utils import secure_filename
import os

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'wav', 'mp3', 'ogg'}

def create_routes(app):

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password')
                return redirect(url_for('login'))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        return render_template('login.html', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/collections')
    @login_required
    def collections():
        collections = Collection.query.filter_by(user_id=current_user.id).all()
        return render_template('collections.html', collections=collections)

    @app.route('/collections/create', methods=['GET', 'POST'])
    @login_required
    def create_collection():
        if request.method == 'POST':
            name = request.form['name']
            collection = Collection(name=name, user_id=current_user.id)
            db.session.add(collection)
            db.session.commit()
            flash('Collection created successfully!')
            return redirect(url_for('collections'))
        return render_template('create_collection.html')

    @app.route('/collections/add/<int:sound_id>', methods=['POST'])
    @login_required
    def add_to_collection(sound_id):
        collection_id = request.form['collection_id']
        collection = Collection.query.get(collection_id)
        sound = Sound.query.get(sound_id)
        if sound not in collection.sounds:
            collection.sounds.append(sound)
            db.session.commit()
            flash('Sound added to collection.')
        else:
            flash('Sound already in collection.')
        return redirect(url_for('collections'))

    @app.route('/collections/remove/<int:sound_id>', methods=['POST'])
    @login_required
    def remove_from_collection(sound_id):
        collection_id = request.form['collection_id']
        collection = Collection.query.get(collection_id)
        sound = Sound.query.get(sound_id)
        if sound in collection.sounds:
            collection.sounds.remove(sound)
            db.session.commit()
            flash('Sound removed from collection.')
        else:
            flash('Sound not found in collection.')
        return redirect(url_for('collections'))

    @app.route('/collections/delete/<int:collection_id>', methods=['POST'])
    @login_required
    def delete_collection(collection_id):
        collection = Collection.query.get_or_404(collection_id)
        db.session.delete(collection)
        db.session.commit()
        flash('Collection deleted.')
        return redirect(url_for('collections'))

    @app.route('/download/<int:sound_id>')
    @login_required
    def download_sound(sound_id):
        sound = Sound.query.get_or_404(sound_id)
        if not current_user.check_download_limit():
            flash('Download limit exceeded. Please subscribe to download more sounds.')
            return redirect(url_for('index'))
        current_user.daily_downloads += 1
        current_user.last_download = datetime.utcnow()
        db.session.commit()
        return redirect(sound.url)

    @app.route('/sounds', methods=['GET'])
    def sounds():
        search_query = request.args.get('search')
        if search_query:
            sounds = Sound.query.filter(
                Sound.title.ilike(f'%{search_query}%') |
                Sound.category.ilike(f'%{search_query}%') |
                Sound.tags.ilike(f'%{search_query}%')
            ).all()
        else:
            sounds = Sound.query.all()
        return render_template('sounds.html', sounds=sounds)

    @app.route('/favorite/<int:sound_id>', methods=['POST'])
    @login_required
    def add_favorite(sound_id):
        favorite = Favorite.query.filter_by(user_id=current_user.id, sound_id=sound_id).first()
        if not favorite:
            favorite = Favorite(user_id=current_user.id, sound_id=sound_id)
            db.session.add(favorite)
            notification = Notification(user_id=current_user.id,
                                        message=f'You added {Sound.query.get(sound_id).title} to your favorites.')
            db.session.add(notification)
            db.session.commit()
            flash('Added to favorites.')
        else:
            db.session.delete(favorite)
            db.session.commit()
            flash('Removed from favorites.')
        return redirect(url_for('sounds'))

    @app.route('/favorites')
    @login_required
    def favorites():
        favorites = Favorite.query.filter_by(user_id=current_user.id).all()
        favorite_sounds = [Sound.query.get(fav.sound_id) for fav in favorites]
        return render_template('favorites.html', sounds=favorite_sounds)

    @app.route('/admin/upload', methods=['GET', 'POST'])
    @login_required
    def upload_sound():
        if not current_user.is_admin:
            flash('Only administrators can upload sounds.')
            return redirect(url_for('index'))
        if request.method == 'POST':
            title = request.form['title']
            category = request.form['category']
            tags = request.form['tags']
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                sound = Sound(title=title, category=category, tags=tags, url=filename, user_id=current_user.id)
                db.session.add(sound)
                db.session.commit()
                flash('Sound uploaded successfully!')
                return redirect(url_for('index'))
        return render_template('upload.html')

    from flask import send_from_directory

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/subscribe', methods=['GET', 'POST'])
    @login_required
    def subscribe():
        flash('Оплата подписки временно невозможна по техническим причинам.')
        return redirect(url_for('index'))

    @app.route('/subscription_success')
    def subscription_success():
        flash('Оплата подписки временно невозможна по техническим причинам.')
        return redirect(url_for('index'))

    @app.route('/subscription_fail')
    def subscription_fail():
        flash('Оплата подписки временно невозможна по техническим причинам.')
        return redirect(url_for('index'))

    @app.route('/subscription_callback')
    def subscription_callback():
        flash('Оплата подписки временно невозможна по техническим причинам.')
        return redirect(url_for('index'))

    @app.route('/notifications')
    @login_required
    def notifications():
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
            Notification.timestamp.desc()).all()
        return render_template('notifications.html', notifications=notifications)

    @app.route('/notifications/read/<int:notification_id>', methods=['POST'])
    @login_required
    def mark_notification_as_read(notification_id):
        notification = Notification.query.get_or_404(notification_id)
        notification.is_read = True
        db.session.commit()
        flash('Notification marked as read.')
        return redirect(url_for('notifications'))

    @app.route('/notifications/create', methods=['POST'])
    @login_required
    def create_notification():
        user_id = request.form['user_id']
        message = request.form['message']
        notification = Notification(user_id=user_id, message=message)
        db.session.add(notification)
        db.session.commit()
        flash('Notification created successfully!')
        return redirect(url_for('index'))


