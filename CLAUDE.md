# Teams Transcript Cleaner - Flask Edition Technical Documentation

Flask Edition は軽量性と柔軟性を重視したトランスクリプト処理システムです。

このドキュメントは、Claude AI によって設計・開発された Flask Edition の技術詳細と開発思想を記録します。

## 開発概要

### プロジェクト背景
- **開発目的**: 軽量で高速な Flask ベースのトランスクリプト処理システム
- **設計思想**: シンプルさと柔軟性の両立
- **開発期間**: 2025年7月
- **開発者**: Claude AI (Anthropic)

### Flask アーキテクチャの特徴
- **軽量性**: 最小限の依存関係で高速起動
- **柔軟性**: 必要な機能のみを選択的に実装
- **シンプルさ**: Flask の哲学に従った簡潔な構造
- **拡張性**: Blueprint による モジュラー設計

#### アーキテクチャ設計思想

```
flask/
├── app/                     # Flask アプリケーション
│   ├── auth/               # 認証機能（Blueprint）
│   ├── transcripts/        # トランスクリプト管理
│   ├── corrections/        # 修正処理
│   ├── wordlists/          # ワードリスト管理
│   ├── admin/              # 管理機能
│   ├── api/                # REST API
│   └── models.py           # SQLAlchemy モデル
├── processing/             # ビジネスロジック（独立）
└── config.py               # 設定管理
```

## 技術仕様

### Flask アーキテクチャ

#### アプリケーションファクトリパターン
```python
def create_app(config_name=None):
    app = Flask(__name__)
    
    # 設定の読み込み
    app.config.from_object(config[config_name])
    
    # 拡張機能の初期化
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # ブループリントの登録
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(transcripts_bp, url_prefix='/transcripts')
    
    return app
```

#### Blueprint による機能分離
- **auth**: 認証・ユーザー管理
- **transcripts**: トランスクリプト CRUD
- **corrections**: 修正処理
- **wordlists**: 辞書管理
- **admin**: 管理機能
- **api**: REST API

### データベース設計（SQLAlchemy）

#### User Model
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # API使用量管理
    api_usage_limit = db.Column(db.Numeric(10, 2), default=Decimal('10.00'))
    total_api_cost = db.Column(db.Numeric(10, 4), default=Decimal('0.0000'))
    
    # 関係性
    transcripts = db.relationship('TranscriptDocument', backref='user', lazy='dynamic')
    correction_jobs = db.relationship('CorrectionJob', backref='user', lazy='dynamic')
    wordlists = db.relationship('WordList', backref='user', lazy='dynamic')
```

#### TranscriptDocument Model
```python
class TranscriptDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    character_count = db.Column(db.Integer, default=0)
    word_count = db.Column(db.Integer, default=0)
    
    @property
    def estimated_tokens(self):
        return max(int(self.character_count / 4), self.word_count)
```

#### CorrectionJob Model
```python
class CorrectionJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transcript_id = db.Column(db.Integer, db.ForeignKey('transcript_documents.id'))
    
    # 処理設定
    processing_mode = db.Column(db.String(20), default='proofreading')
    model_used = db.Column(db.String(50), default='gpt-4o')
    custom_prompt = db.Column(db.Text)
    
    # 結果
    status = db.Column(db.String(20), default='pending')
    corrected_content = db.Column(db.Text)
    cost = db.Column(db.Numeric(10, 4), default=Decimal('0.0000'))
```

### 認証システム（Flask-Login）

#### 設定
```python
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'ログインが必要です。'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

#### フォーム処理（Flask-WTF）
```python
class LoginForm(FlaskForm):
    username = StringField('ユーザー名またはメールアドレス', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン状態を保持')
    submit = SubmitField('ログイン')
```

#### セキュリティ機能
- **CSRF保護**: Flask-WTF による自動保護
- **パスワードハッシュ化**: Werkzeug Security
- **セッション管理**: Flask-Login による管理
- **入力検証**: WTForms バリデータ

### OpenAI API 統合

#### Flask用サービス設計
```python
def get_client():
    """Get OpenAI API client."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key is not configured.")
    return OpenAI(api_key=api_key)

def correct_text(processing_mode, user_custom_prompt, input_text, 
                correction_words, model="gpt-4o"):
    """Correct text using OpenAI API."""
    client = get_client()
    # 処理ロジック...
    return corrected_text, cost, prompt_tokens, completion_tokens
```

#### 処理フロー
1. フォームから処理リクエストを受信
2. CorrectionJob レコード作成
3. OpenAI API 呼び出し
4. 結果の保存とコスト計算
5. ユーザーへの通知

### REST API 設計

#### エンドポイント構造
```
/api/v1/
├── health              # ヘルスチェック
├── user               # ユーザー情報
├── transcripts        # トランスクリプト一覧
└── jobs               # 修正ジョブ一覧
```

#### レスポンス形式
```json
{
    "transcripts": [
        {
            "id": 1,
            "title": "サンプル議事録",
            "character_count": 1250,
            "word_count": 180,
            "is_processed": false,
            "created_at": "2025-01-13T10:30:00Z"
        }
    ]
}
```

## Flask特有の実装

### 設定管理システム

#### 環境別設定
```python
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

class DevelopmentConfig(Config):
    DEBUG = True
    # 開発環境用設定

class ProductionConfig(Config):
    DEBUG = False
    # 本番環境用設定

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

### CLI コマンド

#### カスタムコマンド実装
```python
@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')

@app.cli.command()
def create_test_data():
    """Create test data for development."""
    # テストデータ作成ロジック
    print('Test data created successfully!')
```

### エラーハンドリング

#### カスタムエラーページ
```python
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500
```

## 開発プロセス

### Flask開発の特徴

#### 段階的構築
1. **最小限のアプリ**: Flask + SQLAlchemy
2. **認証追加**: Flask-Login + Flask-WTF
3. **機能実装**: Blueprint による機能分離
4. **API追加**: RESTful エンドポイント
5. **最適化**: キャッシュ・セキュリティ強化

#### Blueprint設計パターン
```python
# Blueprint定義
bp = Blueprint('transcripts', __name__)

# ルート実装
@bp.route('/')
@login_required
def list():
    return render_template('transcripts/list.html')

# アプリへの登録
app.register_blueprint(transcripts_bp, url_prefix='/transcripts')
```

### 品質管理

#### Flask-specific ベストプラクティス
- **Application Factory**: 設定の柔軟性
- **Blueprint分離**: 機能のモジュール化
- **CLI Integration**: 管理タスクの自動化
- **Error Handling**: 適切なエラーレスポンス

## デプロイメント

### 開発環境
```bash
# Flask開発サーバー
flask run --debug

# または
python app.py
```

### 本番環境
```bash
# Gunicorn + Nginx
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 環境変数
```bash
export FLASK_ENV=production
export SECRET_KEY=production-secret-key
export DATABASE_URL=mysql://user:pass@host/db
```

## Flask アーキテクチャの利点

### 開発効率
- **軽量性**: 高速な開発開始とデプロイ
- **柔軟性**: 必要な機能のみを選択して実装

### 学習・保守性
- **シンプルさ**: 理解しやすい構造
- **拡張性**: Blueprint による機能分離

### 適用範囲
- **プロトタイプ開発**: 迅速な概念実証
- **API サーバー**: RESTful サービス
- **軽量 Web アプリ**: 高速レスポンス重視

## パフォーマンス最適化

### Flask特有の最適化
- **App Context**: リクエスト毎の適切なコンテキスト管理
- **Blueprint Lazy Loading**: 必要時のみモジュール読み込み
- **SQLAlchemy最適化**: クエリ最適化とコネクションプール

### キャッシュ戦略
```python
from flask_caching import Cache

cache = Cache()
cache.init_app(app)

@cache.cached(timeout=300)
def expensive_function():
    # 重い処理
    return result
```

## 今後の拡張計画

### Flask生態系活用
1. **Flask-RESTful**: より高度なAPI開発
2. **Flask-SocketIO**: リアルタイム機能
3. **Flask-Admin**: 管理画面の自動生成
4. **Flask-Celery**: 非同期タスク処理

### 機能拡張
1. **WebSocket**: リアルタイム処理状況
2. **Background Tasks**: Celery統合
3. **API Rate Limiting**: Flask-Limiter
4. **Advanced Auth**: Flask-Security

## 運用・監視

### ログ管理
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)
```

### ヘルスチェック
```python
@bp.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })
```

## 開発者向け情報

### Flask開発環境
```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 開発用インストール
pip install -r requirements.txt

# 開発サーバー起動
export FLASK_ENV=development
flask run
```

### デバッグ
```python
# デバッグモードでの詳細エラー
app.config['DEBUG'] = True

# SQLAlchemyクエリログ
app.config['SQLALCHEMY_ECHO'] = True
```

## トラブルシューティング・開発記録

### データベース初期化問題（2025年7月13日）

#### 問題1: 本番設定が開発環境でも評価される問題
- **症状**: `flask init-db` 実行時に `ValueError: Database configuration is incomplete` エラー
- **原因**: `config.py` の `ProductionConfig` クラスで環境変数の検証がクラス定義時に実行される
- **解決策**: 検証ロジックを `@classmethod` に移動し、実際に使用される時にのみ実行

```python
# 修正前（問題のあるコード）
class ProductionConfig(Config):
    if not Config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")

# 修正後
class ProductionConfig(Config):
    @classmethod
    def validate_config(cls):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
```

#### 問題2: MySQL認証エラー
- **症状**: `(1045, "Access denied for user 'test'@'localhost' (using password: YES)")`
- **原因**: `.env` ファイルの MySQL パスワードが実際のデータベース設定と不一致
- **解決策**: 正しい認証情報への更新

#### 問題3: cryptography パッケージ不足
- **症状**: `'cryptography' package is required for sha256_password or caching_sha2_password auth methods`
- **原因**: MySQL 8.0 の新しい認証方式に必要な cryptography パッケージが未インストール
- **解決策**: `pip install cryptography` で追加インストール

#### 問題4: Flask CLI コマンドが認識されない
- **症状**: `flask create-test-data` コマンドが「No such command」エラー
- **原因**: Flask アプリケーションファクトリパターンでの CLI コマンド登録の問題
- **解決策**: Python スクリプトで直接実行する代替方法を使用

### 解決手順まとめ

```bash
# 1. 設定ファイル修正（検証ロジックの移動）
# 2. 正しい MySQL 認証情報の設定
# 3. 必要パッケージの追加インストール
pip install cryptography

# 4. データベース初期化
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 5. テストデータ作成（Python スクリプト経由）
python -c "from app import create_app, db; from app.models import User; app = create_app(); ..."
```

### OpenAI API統合問題（2025年7月13日）

#### 問題5: OpenAI クライアント初期化エラー
- **症状**: `Client.__init__() got an unexpected keyword argument 'proxies'`
- **原因**: OpenAI ライブラリ v1.7.2 と httpx の互換性問題
- **解決策**: OpenAI ライブラリをアップグレード

```bash
# 仮想環境でライブラリ更新
source venv/bin/activate
pip install --upgrade openai
# v1.7.2 → v1.95.1 に更新
```

#### 問題6: JavaScript コストエラー
- **症状**: `result.cost.toFixed is not a function`
- **原因**: API レスポンスの cost が Decimal 型で返されていた
- **解決策**: API 側で float に変換

```python
# app/api/routes.py の修正
return jsonify({
    'cost': float(cost),  # Decimal から float に変換
    'prompt_tokens': prompt_tokens,
    'completion_tokens': completion_tokens,
    # ...
})
```

### UI/UX 改善記録（2025年7月13日）

#### 差分表示機能の実装
- **要件**: 修正前後のテキストの差分をビジュアル表示
- **実装方法**: JavaScript での動的HTML生成
- **機能**: 
  - 削除部分: 赤背景 + 取り消し線
  - 追加部分: 緑背景
  - チェックボックスでOn/Off切り替え

```javascript
// 差分表示関数の実装
function showDiff(original, corrected) {
    const originalWords = original.split(/(\s+)/);
    const correctedWords = corrected.split(/(\s+)/);
    // 単語レベルでの差分比較とHTML生成
}
```

#### セッションコスト表示の修正
- **問題**: DOM要素の特定が不正確
- **解決策**: より具体的なCSSセレクタを使用

```javascript
// 修正前
const currentCost = parseFloat(document.querySelector('.text-muted').textContent.match(/\$([0-9.]+)/)?.[1] || 0);

// 修正後
const sessionCostElement = document.querySelector('.text-muted.small.mb-2');
```

### 学習ポイント

1. **設定管理**: Flask の設定クラスでは、実行時検証を避けてメソッドベースの検証を使用
2. **MySQL 8.0**: 新しい認証方式には cryptography パッケージが必須
3. **Flask-Migrate**: SQLite から MySQL への移行時は migrations フォルダの再作成が必要
4. **CLI コマンド**: アプリケーションファクトリパターンでの CLI 登録には注意が必要
5. **OpenAI 互換性**: ライブラリの版数管理は重要（v1.7.2 → v1.95.1で解決）
6. **データ型変換**: Decimal型は JavaScript で直接操作できないため float 変換が必要
7. **DOM操作**: 複数の類似要素がある場合は具体的なセレクタが必要

### 性能最適化記録

#### API レスポンス最適化
- Decimal → float 変換でJavaScript処理を高速化
- エラーハンドリングの強化
- リアルタイムステータス更新の実装

#### フロントエンド改善
- ファイルアップロード時のリアルタイム情報表示
- 処理中の視覚的フィードバック
- エラー表示の改善

### 依存関係管理

#### 重要な更新
- **OpenAI**: `1.7.2` → `1.95.1`
- **cryptography**: MySQL 8.0 対応で追加
- **requirements.txt**: 自動更新確認

#### 互換性確認
- Python 3.12+ での動作確認
- MySQL 8.0 認証プラグイン: `mysql_native_password`
- Flask 3.0.0 との互換性維持

---

**作成者**: Claude AI (Anthropic)  
**最終更新**: 2025年7月13日（トラブルシューティング追加）  
**バージョン**: 1.1.0  
**Framework**: Flask 3.0.0