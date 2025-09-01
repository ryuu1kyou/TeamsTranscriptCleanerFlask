"""
Routes for wordlist management.
"""
from flask import render_template, flash, redirect, url_for, request, make_response, jsonify
from flask_login import login_required, current_user
from app import db
from app.wordlists import bp
from app.models import WordList


def validate_csv_format(csv_content):
    """Validate CSV format and return any errors."""
    import csv
    import io
    
    errors = []
    try:
        csv_reader = csv.reader(io.StringIO(csv_content))
        header = next(csv_reader, None)
        
        if not header or len(header) < 2:
            errors.append("CSV must have at least 2 columns")
        
        row_count = 0
        for row_num, row in enumerate(csv_reader, start=2):
            if len(row) < 2:
                errors.append(f"Row {row_num}: Must have at least 2 columns")
            elif not row[0].strip() or not row[1].strip():
                errors.append(f"Row {row_num}: Both columns must have values")
            row_count += 1
        
        if row_count == 0:
            errors.append("CSV must contain at least one data row")
            
    except Exception as e:
        errors.append(f"CSV parsing error: {str(e)}")
    
    return errors


@bp.route('/')
@login_required
def list():
    """List all word lists for the current user with usage history."""
    wordlists = WordList.get_user_wordlists_with_history(current_user.id)
    return render_template('wordlists/list.html', wordlists=wordlists, title='ワードリスト管理')


@bp.route('/<int:id>')
@login_required
def detail(id):
    """Display word list details with history."""
    wordlist = WordList.query.filter_by(id=id, user_id=current_user.id, is_active=True).first_or_404()
    word_pairs = wordlist.get_word_pairs()
    history = wordlist.get_history()
    return render_template('wordlists/detail.html', wordlist=wordlist, 
                         word_pairs=word_pairs, history=history, title=wordlist.name)


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
        
        # Check if name already exists among active wordlists
        if current_user.wordlists.filter_by(name=name, is_active=True).first():
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
    
    # Mark as used
    wordlist.mark_as_used()
    
    response = make_response(wordlist.csv_content)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    filename = f"{wordlist.name}_v{wordlist.version}.csv"
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit word list and create new version."""
    wordlist = WordList.query.filter_by(id=id, user_id=current_user.id, is_active=True).first_or_404()
    
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        csv_content = request.form.get('csv_content', '').strip()
        
        if not csv_content:
            flash('CSVコンテンツを入力してください。', 'error')
            return render_template('wordlists/edit.html', wordlist=wordlist, title=f'{wordlist.name} を編集')
        
        # Validate CSV format
        errors = validate_csv_format(csv_content)
        if errors:
            for error in errors:
                flash(f'CSV形式エラー: {error}', 'error')
            return render_template('wordlists/edit.html', wordlist=wordlist, title=f'{wordlist.name} を編集')
        
        # Create new version if content has changed
        if csv_content != wordlist.csv_content:
            new_version = wordlist.create_version(csv_content, description)
            flash(f'ワードリストが更新されました。(バージョン {new_version.version})', 'success')
            return redirect(url_for('wordlists.detail', id=new_version.id))
        else:
            # Update description only
            wordlist.description = description
            db.session.commit()
            flash('説明が更新されました。', 'success')
            return redirect(url_for('wordlists.detail', id=wordlist.id))
    
    return render_template('wordlists/edit.html', wordlist=wordlist, title=f'{wordlist.name} を編集')


@bp.route('/<int:id>/history')
@login_required
def history(id):
    """View version history of word list."""
    wordlist = WordList.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    # Get the parent wordlist if this is a version
    root_wordlist = wordlist.parent_wordlist if wordlist.parent_wordlist_id else wordlist
    
    # Get all versions including the root
    all_versions = [root_wordlist] + list(root_wordlist.history_versions.all())
    all_versions.sort(key=lambda x: x.version, reverse=True)
    
    return render_template('wordlists/history.html', 
                         wordlist=wordlist,
                         all_versions=all_versions,
                         title=f'{root_wordlist.name} の履歴')


@bp.route('/<int:id>/restore/<int:version_id>')
@login_required
def restore_version(id, version_id):
    """Restore a specific version as the current active version."""
    wordlist = WordList.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    version_to_restore = WordList.query.filter_by(id=version_id, user_id=current_user.id).first_or_404()
    
    # Create new version with the content from the version to restore
    new_version = wordlist.create_version(
        version_to_restore.csv_content, 
        f'バージョン {version_to_restore.version} から復元'
    )
    
    flash(f'バージョン {version_to_restore.version} から復元しました。(新バージョン {new_version.version})', 'success')
    return redirect(url_for('wordlists.detail', id=new_version.id))


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload CSV file to create new wordlist."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('ファイルが選択されていません。', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if file.filename == '':
            flash('ファイルが選択されていません。', 'error')
            return redirect(request.url)
        
        if not name:
            # Use filename without extension as default name
            name = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename
        
        # Check if name already exists
        if current_user.wordlists.filter_by(name=name, is_active=True).first():
            flash('この名前のワードリストは既に存在します。', 'error')
            return render_template('wordlists/upload.html', title='ワードリストアップロード')
        
        if file and file.filename.lower().endswith('.csv'):
            try:
                csv_content = file.read().decode('utf-8')
                
                # Validate CSV format
                errors = validate_csv_format(csv_content)
                if errors:
                    for error in errors:
                        flash(f'CSV形式エラー: {error}', 'error')
                    return render_template('wordlists/upload.html', title='ワードリストアップロード')
                
                wordlist = WordList(
                    user_id=current_user.id,
                    name=name,
                    description=description,
                    csv_content=csv_content
                )
                
                db.session.add(wordlist)
                db.session.commit()
                
                flash(f'ワードリスト "{name}" がアップロードされました。', 'success')
                return redirect(url_for('wordlists.detail', id=wordlist.id))
                
            except UnicodeDecodeError:
                flash('ファイルの文字エンコーディングが正しくありません。UTF-8で保存してください。', 'error')
            except Exception as e:
                flash(f'ファイルの処理中にエラーが発生しました: {str(e)}', 'error')
        else:
            flash('CSVファイルをアップロードしてください。', 'error')
    
    return render_template('wordlists/upload.html', title='ワードリストアップロード')


# API Endpoints for WordList Management

@bp.route('/api/wordlists', methods=['GET'])
@login_required
def api_list_wordlists():
    """Get list of user's wordlists with history."""
    try:
        # Get user's wordlists with history
        wordlists = WordList.get_user_wordlists_with_history(current_user.id)
        
        wordlists_data = []
        for wordlist in wordlists:
            wordlists_data.append({
                'id': wordlist.id,
                'name': wordlist.name,
                'description': wordlist.description or '',
                'word_count': wordlist.word_count,
                'version': wordlist.version,
                'usage_count': wordlist.usage_count,
                'is_active': wordlist.is_active,
                'is_shared': wordlist.is_shared,
                'last_used_at': wordlist.last_used_at.strftime('%Y-%m-%d %H:%M') if wordlist.last_used_at else 'Never',
                'created_at': wordlist.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': wordlist.updated_at.strftime('%Y-%m-%d %H:%M') if wordlist.updated_at else wordlist.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'success': True,
            'wordlists': wordlists_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/wordlists/<int:wordlist_id>', methods=['GET'])
@login_required
def api_get_wordlist(wordlist_id):
    """Get specific wordlist details."""
    try:
        wordlist = WordList.query.filter_by(id=wordlist_id, user_id=current_user.id).first()
        if not wordlist:
            return jsonify({'success': False, 'error': 'WordList not found'}), 404
        
        # Get word pairs
        word_pairs = wordlist.get_word_pairs()
        
        # Get version history
        history = []
        for version in wordlist.get_history():
            history.append({
                'id': version.id,
                'version': version.version,
                'created_at': version.created_at.strftime('%Y-%m-%d %H:%M'),
                'word_count': version.word_count,
                'usage_count': version.usage_count,
                'is_active': version.is_active
            })
        
        return jsonify({
            'success': True,
            'wordlist': {
                'id': wordlist.id,
                'name': wordlist.name,
                'description': wordlist.description or '',
                'word_count': wordlist.word_count,
                'version': wordlist.version,
                'usage_count': wordlist.usage_count,
                'is_active': wordlist.is_active,
                'is_shared': wordlist.is_shared,
                'csv_content': wordlist.csv_content,
                'word_pairs': word_pairs,
                'last_used_at': wordlist.last_used_at.strftime('%Y-%m-%d %H:%M') if wordlist.last_used_at else 'Never',
                'created_at': wordlist.created_at.strftime('%Y-%m-%d %H:%M'),
                'history': history
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/wordlists', methods=['POST'])
@login_required
def api_create_wordlist():
    """Create a new wordlist."""
    try:
        data = request.get_json()
        
        name = data.get('name')
        description = data.get('description', '')
        csv_content = data.get('csv_content', '')
        
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        if not csv_content:
            return jsonify({'success': False, 'error': 'CSV content is required'}), 400
        
        # Check for duplicate names
        existing = WordList.query.filter_by(user_id=current_user.id, name=name, is_active=True).first()
        if existing:
            return jsonify({'success': False, 'error': 'WordList name already exists'}), 400
        
        # Validate CSV format
        errors = validate_csv_format(csv_content)
        if errors:
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400
        
        # Create wordlist
        wordlist = WordList(
            user_id=current_user.id,
            name=name,
            description=description,
            csv_content=csv_content
        )
        
        db.session.add(wordlist)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'wordlist': {
                'id': wordlist.id,
                'name': wordlist.name,
                'description': wordlist.description,
                'word_count': wordlist.word_count
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/wordlists/<int:wordlist_id>', methods=['PUT'])
@login_required
def api_update_wordlist(wordlist_id):
    """Update a wordlist."""
    try:
        wordlist = WordList.query.filter_by(id=wordlist_id, user_id=current_user.id).first()
        if not wordlist:
            return jsonify({'success': False, 'error': 'WordList not found'}), 404
        
        data = request.get_json()
        
        name = data.get('name', wordlist.name)
        description = data.get('description', wordlist.description)
        csv_content = data.get('csv_content')
        
        # Check for duplicate names (excluding current wordlist)
        if name != wordlist.name:
            existing = WordList.query.filter_by(user_id=current_user.id, name=name, is_active=True).first()
            if existing:
                return jsonify({'success': False, 'error': 'WordList name already exists'}), 400
        
        # If CSV content is being updated
        if csv_content and csv_content != wordlist.csv_content:
            # Validate CSV format
            errors = validate_csv_format(csv_content)
            if errors:
                return jsonify({'success': False, 'error': '; '.join(errors)}), 400
            
            # Create new version
            new_wordlist = wordlist.create_version(csv_content, description)
            new_wordlist.name = name
            db.session.commit()
            
            return jsonify({
                'success': True,
                'wordlist': {
                    'id': new_wordlist.id,
                    'name': new_wordlist.name,
                    'description': new_wordlist.description,
                    'word_count': new_wordlist.word_count,
                    'version': new_wordlist.version
                }
            })
        else:
            # Just update metadata
            wordlist.name = name
            wordlist.description = description
            db.session.commit()
            
            return jsonify({
                'success': True,
                'wordlist': {
                    'id': wordlist.id,
                    'name': wordlist.name,
                    'description': wordlist.description,
                    'word_count': wordlist.word_count,
                    'version': wordlist.version
                }
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/wordlists/<int:wordlist_id>', methods=['DELETE'])
@login_required
def api_delete_wordlist(wordlist_id):
    """Delete a wordlist."""
    try:
        wordlist = WordList.query.filter_by(id=wordlist_id, user_id=current_user.id).first()
        if not wordlist:
            return jsonify({'success': False, 'error': 'WordList not found'}), 404
        
        name = wordlist.name
        
        # Delete the wordlist and its history
        # First, delete all versions
        if wordlist.parent_wordlist_id:
            # If this is a version, delete all versions of the parent
            parent = WordList.query.get(wordlist.parent_wordlist_id)
            versions_to_delete = parent.history_versions.all() if parent else []
            versions_to_delete.append(parent)
        else:
            # If this is the parent, delete all its versions
            versions_to_delete = wordlist.history_versions.all()
            versions_to_delete.append(wordlist)
        
        for version in versions_to_delete:
            if version:
                db.session.delete(version)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'WordList "{name}" and all its versions have been deleted'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500