"""
Routes for wordlist management.
"""
from flask import render_template, flash, redirect, url_for, request, make_response
from flask_login import login_required, current_user
from app import db
from app.wordlists import bp
from app.models import WordList
from processing.csv_parser import validate_csv_format


@bp.route('/')
@login_required
def list():
    """List all word lists for the current user."""
    wordlists = current_user.wordlists.order_by(WordList.updated_at.desc()).all()
    return render_template('wordlists/list.html', wordlists=wordlists, title='ワードリスト一覧')


@bp.route('/<int:id>')
@login_required
def detail(id):
    """Display word list details."""
    wordlist = WordList.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    word_pairs = wordlist.get_word_pairs()
    return render_template('wordlists/detail.html', wordlist=wordlist, 
                         word_pairs=word_pairs, title=wordlist.name)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new word list."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        csv_content = request.form.get('csv_content', '').strip()
        
        if not name:
            flash('ワードリスト名を入力してください。', 'error')
            return render_template('wordlists/create.html', title='ワードリスト作成')
        
        # Check if name already exists
        if current_user.wordlists.filter_by(name=name).first():
            flash('この名前のワードリストは既に存在します。', 'error')
            return render_template('wordlists/create.html', title='ワードリスト作成')
        
        if not csv_content:
            csv_content = "incorrect,correct\n"  # Default header
        
        # Validate CSV format
        errors = validate_csv_format(csv_content)
        if errors:
            for error in errors:
                flash(f'CSV形式エラー: {error}', 'error')
            return render_template('wordlists/create.html', title='ワードリスト作成')
        
        wordlist = WordList(
            user_id=current_user.id,
            name=name,
            description=description,
            csv_content=csv_content
        )
        
        db.session.add(wordlist)
        db.session.commit()
        
        flash('ワードリストが作成されました。', 'success')
        return redirect(url_for('wordlists.detail', id=wordlist.id))
    
    return render_template('wordlists/create.html', title='ワードリスト作成')


@bp.route('/<int:id>/download')
@login_required
def download(id):
    """Download word list as CSV file."""
    wordlist = WordList.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    response = make_response(wordlist.csv_content)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    filename = f"{wordlist.name}.csv"
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response