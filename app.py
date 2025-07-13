#!/usr/bin/env python
"""
Flask application entry point for Teams Transcript Cleaner.
"""
import os
from app import create_app, db
from app.models import User, TranscriptDocument, CorrectionJob, WordList, SharedWordList

app = create_app()


@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')


@app.cli.command()
def create_admin():
    """Create an admin user."""
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('Admin user already exists.')
        return
    
    admin = User(
        username='admin',
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        organization='System Admin'
    )
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    print('Admin user created: admin@example.com / admin123')


@app.cli.command()
def create_test_data():
    """Create test data for development."""
    # Create test user
    test_user = User.query.filter_by(username='testuser').first()
    if not test_user:
        test_user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            organization='Test Company'
        )
        test_user.set_password('test123')
        db.session.add(test_user)
    
    # Create admin user
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            organization='System Admin'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
    
    db.session.commit()
    
    # Create sample transcript
    if not test_user.transcripts.first():
        sample_content = """
Teams 会議議事録

参加者：
- 田中さん（プロジェクトマネージャー）
- 佐藤さん（エンジニア）
- 鈴木さん（デザイナー）

議題：
1. プロジェクトの進捗確認
2. 次週のタスク分担
3. 問題点の洗い出し

内容：
田中：皆さん、今日はお疲れ様です。まず、今週の進捗を確認しましょう。
佐藤：フロントエンドの実装は80%程度完了しています。ただ、一部のコンポーネントでエラーが発生しています。
鈴木：デザインは全て完了しました。修正依頼があれば対応します。
田中：ありがとうございます。来週までに残りのタスクを完了させましょう。
""".strip()
        
        transcript = TranscriptDocument(
            user_id=test_user.id,
            title='サンプル会議議事録',
            original_filename='sample_meeting.txt',
            content=sample_content,
            file_size=len(sample_content.encode('utf-8'))
        )
        db.session.add(transcript)
    
    # Create sample word list
    if not test_user.wordlists.first():
        csv_content = """incorrect,correct
田中,田中
佐藤,佐藤
鈴木,鈴木
フロントエンド,フロントエンド
コンポーネント,コンポーネント
エラー,エラー
タスク,タスク"""
        
        wordlist = WordList(
            user_id=test_user.id,
            name='サンプル修正リスト',
            description='テスト用の修正リスト',
            csv_content=csv_content,
            is_active=True
        )
        db.session.add(wordlist)
    
    db.session.commit()
    print('Test data created successfully!')
    print('Test accounts:')
    print('  Admin: admin@example.com / admin123')
    print('  User:  test@example.com / test123')


if __name__ == '__main__':
    app.run(debug=True)