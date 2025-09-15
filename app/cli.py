"""Custom Flask CLI commands.

Separated from root-level app.py to avoid ambiguity between the
`app` package and `app.py` file when registering commands.
"""
import click
from flask.cli import with_appcontext

from app import db
from app.models import User, Role, TranscriptDocument, WordList
from flask_babel import gettext
import subprocess
import os


def ensure_basic_roles():
    """Create default roles if they don't exist."""
    created = []
    if not Role.query.filter_by(name='Admin').first():
        db.session.add(Role(name='Admin', description='Administrator',
                            can_manage_users=True,
                            can_manage_roles=True,
                            can_view_all_transcripts=True,
                            can_manage_wordlists=True,
                            can_use_api=True))
        created.append('Admin')
    if not Role.query.filter_by(name='User').first():
        db.session.add(Role(name='User', description='Standard user'))
        created.append('User')
    if created:
        db.session.commit()
    return created


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize database (tables only, no migrations)."""
    db.create_all()
    ensure_basic_roles()
    click.echo('Database initialized.')


@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """Create or update the default admin user."""
    ensure_basic_roles()
    admin = User.query.filter_by(username='admin').first()
    if admin:
        click.echo('Admin user already exists.')
        return
    admin = User(
        username='admin',
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        organization='System Admin',
        is_verified=True
    )
    admin.set_password('admin123')
    # Assign admin role
    admin_role = Role.query.filter_by(name='Admin').first()
    if admin_role:
        admin.role_id = admin_role.id
    db.session.add(admin)
    db.session.commit()
    click.echo('Admin user created: admin@example.com / admin123')


@click.command('create-test-data')
@with_appcontext
def create_test_data_command():
    """Create sample user, transcript, and word list."""
    ensure_basic_roles()
    # Test user
    test_user = User.query.filter_by(username='testuser').first()
    if not test_user:
        test_user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            organization='Test Company',
            is_verified=True
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()

    # Sample transcript
    if not test_user.transcripts.first():
        sample_content = (
            "Sample Meeting Transcript\n\nAgenda:\n1. Updates\n2. Tasks\n3. Issues\n"
        )
        doc = TranscriptDocument(
            user_id=test_user.id,
            title='Sample Transcript',
            original_filename='sample.txt',
            content=sample_content,
            file_size=len(sample_content.encode('utf-8'))
        )
        db.session.add(doc)

    # Sample word list
    if not test_user.wordlists.first():
        csv_content = "incorrect,correct\nTeh,The\nrecieve,receive\n"
        wl = WordList(
            user_id=test_user.id,
            name='Sample Corrections',
            description='Demo correction list',
            csv_content=csv_content,
            is_active=True
        )
        db.session.add(wl)

    db.session.commit()
    click.echo('Test data created.')


def register_cli(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(create_test_data_command)
    
    @app.cli.command('compile-translations')
    @with_appcontext
    def compile_translations_command():
        """Extract, update, and compile message catalogs (i18n)."""
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # project root
        app_dir = os.path.dirname(__file__)
        translations_dir = os.path.join(app_dir, 'translations')  # use app/translations
        os.makedirs(translations_dir, exist_ok=True)
        # 1. Extract messages to POT
        subprocess.run([
            'pybabel', 'extract',
            '-F', os.path.join(root_dir, 'babel.cfg'),
            '-o', os.path.join(translations_dir, 'messages.pot'),
            root_dir
        ], check=True)
        # 2. Update each existing locale
        existing_locales = []
        for name in os.listdir(translations_dir):
            locale_dir = os.path.join(translations_dir, name, 'LC_MESSAGES')
            if os.path.isdir(locale_dir):
                existing_locales.append(name)
        for locale in existing_locales:
            subprocess.run([
                'pybabel', 'update',
                '-i', os.path.join(translations_dir, 'messages.pot'),
                '-d', translations_dir,
                '-l', locale
            ], check=True)
        # 3. Compile
        subprocess.run(['pybabel', 'compile', '-d', translations_dir], check=True)
        click.echo('Translations extracted, updated, and compiled.')
