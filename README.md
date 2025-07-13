# Teams Transcript Cleaner - Flask Edition

軽量で高速な Flask フレームワークを使用した Teams トランスクリプト AI 修正システム

Microsoft Teams の会議録を AI で高精度に修正する軽量 Web アプリケーション

## 機能

- **誤字脱字修正**: カスタム辞書と AI を組み合わせた高精度な修正
- **文法修正**: 自然で読みやすい日本語への修正
- **要約生成**: 会議記録の重要ポイントを抽出した要約
- **ユーザー管理**: 個人用アカウントと API 使用量管理
- **ワードリスト管理**: 頻出する修正パターンの辞書管理
- **処理履歴**: 修正ジョブの履歴と結果管理

## システム要件

- Python 3.8+ (推奨: Python 3.12+)
- MySQL 5.7+ または 8.0+
- OpenAI API キー
- 仮想環境（venv推奨）

## セットアップ手順

### 1. プロジェクトのクローンと環境構築

```bash
# プロジェクトディレクトリに移動
cd transcript-cleaner

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化 (Windows)
venv\Scripts\activate
# 仮想環境の有効化 (macOS/Linux)
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 2. MySQL データベースの設定

#### MySQL サーバーへの接続

**Windows の場合:**

```bash
# MySQL Command Line Client を起動
mysql -u root -p
```

**macOS/Linux の場合:**

```bash
# ターミナルから MySQL に接続
mysql -u root -p
```

**Docker で MySQL を使用する場合:**

```bash
# MySQL コンテナを起動
docker run --name mysql-server -e MYSQL_ROOT_PASSWORD=rootpassword -d -p 3306:3306 mysql:8.0

# コンテナに接続
docker exec -it mysql-server mysql -u root -p
```

#### データベースとユーザーの作成

MySQL に root ユーザーでログイン後、以下のコマンドを実行：

```sql
-- データベース作成
CREATE DATABASE transcript_cleaner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- アプリケーション用ユーザー作成
CREATE USER 'test'@'localhost' IDENTIFIED BY 'secure_password_123';

-- 権限付与
GRANT ALL PRIVILEGES ON transcript_cleaner.* TO 'test'@'localhost';

-- 権限を有効化
FLUSH PRIVILEGES;

-- 作成確認
SHOW DATABASES;
SELECT user, host FROM mysql.user WHERE user = 'test';

-- MySQL からログアウト
EXIT;
```

#### 接続テスト

作成したユーザーでの接続を確認：

```bash
mysql -u test -p ***
```

パスワード入力後、以下のコマンドで接続確認：

```sql
USE transcript_cleaner;
SELECT DATABASE();
SHOW TABLES;
EXIT;
```

### 3. 環境変数の設定

**🔒 セキュリティ重要**: OpenAI APIキーはシステム環境変数での設定を強く推奨します：

```bash
# 推奨: システム環境変数で設定
export OPENAI_API_KEY="your-openai-api-key-here"

# Linux/Mac: ~/.bashrc に永続化
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# Windows: 永続的に設定
setx OPENAI_API_KEY "your-api-key-here"
```

開発環境でのみ `.env` ファイルを使用する場合：

```bash
cp .env.example .env
```

`.env` ファイルを編集（APIキーはコメントアウト推奨）：

```env
SECRET_KEY=your-flask-secret-key-here
FLASK_ENV=development

# データベース設定
DB_NAME=transcript_cleaner
DB_USER=test
DB_PASSWORD=secure_password_123
DB_HOST=localhost
DB_PORT=3306

# OpenAI API 設定（システム環境変数を推奨）
# OPENAI_API_KEY=your-openai-api-key-here
```

### 4. Flask アプリケーションの初期化

#### 必要な Python パッケージの追加インストール

MySQL 8.0 の新しい認証方式に対応するため、追加でパッケージをインストールします：

```bash
# 仮想環境を有効化した状態で実行
pip install cryptography
```

#### データベースの初期化

```bash
# Flask-Migrate の初期化（初回のみ）
flask db init

# マイグレーションファイルの作成
flask db migrate -m "Initial migration"

# データベーステーブルの作成
flask db upgrade
```

#### テストユーザーの作成

READMEに記載の `flask create-test-data` コマンドは一部の環境で認識されない場合があります。その場合は以下の方法でテストユーザーを作成してください：

```bash
# 方法1: Flask CLI（正常に動作する場合）
flask create-test-data

# 方法2: Python スクリプト（CLI が動作しない場合）
python -c "
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    # テストユーザー作成
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
    
    # 管理者ユーザー作成
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
    print('Test users created!')
    print('Admin: admin@example.com / admin123')
    print('User:  test@example.com / test123')
"
```

#### 開発サーバーの起動

```bash
# 開発サーバーの起動
python app.py
# または
flask run

# ブラウザで http://127.0.0.1:5000/ にアクセス
```

## プロジェクト構造

```
transcript-cleaner/
├── app/                        # Flask アプリケーション
│   ├── auth/                  # 認証機能
│   ├── transcripts/           # トランスクリプト管理
│   ├── corrections/           # 修正処理
│   ├── wordlists/             # ワードリスト管理
│   ├── admin/                 # 管理機能
│   ├── api/                   # REST API
│   ├── models.py              # データベースモデル
│   └── __init__.py            # アプリファクトリ
├── processing/                # 処理ロジック
│   ├── openai_service.py      # OpenAI API 統合
│   └── csv_parser.py          # CSV パーサー
├── templates/                 # HTML テンプレート
├── static/                    # 静的ファイル
├── migrations/                # データベースマイグレーション
├── config.py                  # Flask 設定
├── app.py                     # アプリケーションエントリポイント
├── requirements.txt           # Python 依存関係
├── .env.example              # 環境変数テンプレート
└── README.md                 # このファイル
```

## 主要機能の使用方法

### 1. トランスクリプトのアップロード

1. Web UI からログイン
2. 「トランスクリプト」→「アップロード」
3. Teams からエクスポートした .txt ファイルを選択

### 2. ワードリストの作成

1. 「ワードリスト」→「作成」
2. CSV 形式で修正パターンを入力：
   ```csv
   incorrect,correct
   マイクロソフト,Microsoft
   エクセル,Excel
   ```

### 3. 修正処理の実行

1. 「トランスクリプト」→「処理実行」
2. トランスクリプト、処理モード、ワードリストを選択
3. 必要に応じてカスタムプロンプトを入力
4. 「処理実行」ボタンをクリック

### 4. 結果の確認とダウンロード

1. 処理完了後、修正結果を確認
2. 「ダウンロード」で結果を保存

## API エンドポイント

### メイン機能

- `GET /` - ホームページ
- `GET /auth/login` - ログインページ
- `POST /auth/login` - ログイン処理
- `GET /auth/register` - 登録ページ
- `POST /auth/register` - ユーザー登録

### トランスクリプト

- `GET /transcripts/` - トランスクリプト一覧
- `POST /transcripts/upload` - 新規アップロード
- `GET /transcripts/<id>` - 詳細表示
- `POST /transcripts/process` - 処理実行

### API (JSON)

- `GET /api/v1/health` - ヘルスチェック
- `GET /api/v1/user` - ユーザー情報
- `GET /api/v1/transcripts` - トランスクリプト一覧
- `GET /api/v1/jobs` - ジョブ一覧

## Flask CLI コマンド

### データベース管理

```bash
# データベース初期化
flask init-db

# 管理者ユーザー作成
flask create-admin

# テストデータ作成
flask create-test-data
```

### 開発用コマンド

```bash
# 開発サーバー起動
flask run

# デバッグモードで起動
FLASK_ENV=development flask run

# 特定のポートで起動
flask run --port 8080
```

## 本番環境での運用

### 1. 環境設定

```bash
# 本番環境用設定の使用
export FLASK_ENV=production

# セキュリティ設定
export SECRET_KEY=your-production-secret-key
```

### 2. Web サーバー設定

Gunicorn + Nginx での運用例：

```bash
# Gunicorn の起動
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 3. データベースマイグレーション

```bash
# マイグレーション実行
flask db upgrade
```

## Flask の特徴

### ⚡ 軽量・高速

- 最小限の依存関係
- 高速な起動時間
- シンプルな構成

### 🔧 柔軟性

- 必要な機能のみを選択
- カスタマイズが容易
- 小規模から中規模に最適

## ログイン機能について

### 実装されている認証機能

✅ **ユーザー登録**

- メールアドレスとパスワードによる新規登録
- 組織名の設定（任意）
- Flask-Login による認証管理

✅ **ログイン・ログアウト**

- メールアドレスまたはユーザー名でログイン
- セッション管理
- Remember Me 機能

✅ **アクセス制御**

- @login_required デコレータによる保護
- ユーザー別データ分離
- API使用量管理

✅ **テストアカウント**
開発・テスト用のアカウントが自動作成されます：

- **管理者**: `admin@example.com` / `admin123`
- **一般ユーザー**: `test@example.com` / `test123`

### セキュリティ機能

- Flask-WTF による CSRF 保護
- Werkzeug によるパスワードハッシュ化
- 入力値検証
- セッション管理

## トラブルシューティング

### よくある問題と解決方法

#### 1. データベース関連の問題

**MySQL 接続エラー**
```
(1045, "Access denied for user 'test'@'localhost' (using password: YES)")
```
- **原因**: `.env` ファイルの MySQL 認証情報が正しくない
- **解決策**: データベース管理者に正しいユーザー名・パスワードを確認し、`.env` ファイルを更新

**cryptography パッケージエラー**
```
'cryptography' package is required for sha256_password or caching_sha2_password auth methods
```
- **原因**: MySQL 8.0 の新しい認証方式に必要なパッケージが未インストール
- **解決策**: `pip install cryptography` を実行

**設定ファイルエラー**
```
ValueError: Database configuration is incomplete
```
- **原因**: 本番環境の設定検証が開発環境でも実行される
- **解決策**: `export FLASK_ENV=development` で開発環境を明示的に指定

#### 2. Flask CLI コマンドの問題

**Flask CLI コマンドが認識されない**
```
Error: No such command 'create-test-data'
```
- **原因**: アプリケーションファクトリパターンでの CLI コマンド登録の問題
- **解決策**: Python スクリプトによる直接実行（上記の「テストユーザーの作成」参照）

#### 3. OpenAI API エラー

- **API キーエラー**: システム環境変数 `OPENAI_API_KEY` が正しく設定されているか確認
- **API 使用量制限**: OpenAI のダッシュボードで使用量と制限を確認

#### 4. インポートエラー

- 仮想環境が有効化されているか確認: `which python` でパスをチェック
- 依存関係の再インストール: `pip install -r requirements.txt`

### 詳細なデバッグ方法

#### 開発モードでの起動
```bash
# デバッグモードで起動
export FLASK_ENV=development
flask run --debug

# または app.py で直接起動
python app.py
```

#### データベース接続テスト
```bash
# MySQL 接続テスト
mysql -u [username] -p[password] -e "USE transcript_cleaner; SHOW TABLES;"

# Python での接続テスト
python -c "
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()
try:
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

#### ログ出力の有効化
```bash
# SQLAlchemy のクエリログを有効化
export SQLALCHEMY_ECHO=True

# Flask のログレベル設定
export FLASK_DEBUG=1
```

### 開発環境セットアップのチェックリスト

- [ ] Python 3.8+ がインストールされている
- [ ] MySQL 5.7+ または 8.0+ が動作している
- [ ] 仮想環境が作成・有効化されている
- [ ] `requirements.txt` からパッケージがインストールされている
- [ ] `cryptography` パッケージがインストールされている
- [ ] `.env` ファイルが作成され、正しい認証情報が設定されている
- [ ] `FLASK_ENV=development` が設定されている
- [ ] OpenAI API キーがシステム環境変数に設定されている
- [ ] データベースマイグレーションが完了している
- [ ] テストユーザーが作成されている

## 開発・拡張

### 新機能の追加

1. 新しいブループリントを作成
2. `app/__init__.py` でブループリントを登録
3. 必要に応じてモデルを追加
4. テンプレートとルートを実装

### データベースマイグレーション

```bash
# 新しいマイグレーション作成
flask db migrate -m "Add new feature"

# マイグレーション適用
flask db upgrade
```

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## サポート

問題や質問がある場合は、GitHub Issues でお知らせください。
