# セキュリティガイドライン

## 🔒 API キー管理

### ❌ 避けるべき方法
- `.env` ファイルにAPIキーを記載
- コードに直接APIキーをハードコーディング
- バージョン管理システムにAPIキーをコミット

### ✅ 推奨方法

#### 1. システム環境変数（推奨）
```bash
# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"

# Windows
set OPENAI_API_KEY=your-api-key-here
# または
setx OPENAI_API_KEY "your-api-key-here"  # 永続化
```

#### 2. Docker環境での管理
```bash
# Docker run時に環境変数を渡す
docker run -e OPENAI_API_KEY="your-api-key-here" your-app

# Docker Composeでのsecrets使用
version: '3.8'
services:
  app:
    image: your-app
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_key
    secrets:
      - openai_key

secrets:
  openai_key:
    file: ./secrets/openai_key.txt
```

#### 3. 本番環境での設定例

**Systemd サービス:**
```ini
[Unit]
Description=Transcript Cleaner Flask App
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/opt/transcript-cleaner
Environment=OPENAI_API_KEY=your-api-key-here
Environment=FLASK_ENV=production
ExecStart=/opt/transcript-cleaner/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Docker Compose（本番）:**
```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - FLASK_ENV=production
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    env_file:
      - .env.production  # APIキーは含まない
```

## 🐳 Docker対応

### Dockerfile例
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 環境変数で設定を受け取る
ENV FLASK_ENV=production

# APIキーは実行時に渡す
CMD ["python", "app.py"]
```

### Docker使用時の環境変数設定
```bash
# 方法1: 実行時に直接指定
docker run -e OPENAI_API_KEY="$OPENAI_API_KEY" transcript-cleaner

# 方法2: 環境ファイル使用（APIキーは別管理）
docker run --env-file .env.docker transcript-cleaner

# 方法3: Docker secrets使用
docker service create \
  --secret openai-key \
  --env OPENAI_API_KEY_FILE=/run/secrets/openai-key \
  transcript-cleaner
```

## 🛡️ セキュリティ設定の確認

### 設定確認コマンド
```python
# アプリ内でのAPIキー確認
def check_api_key_source():
    import os
    
    # システム環境変数から取得できるか
    system_key = os.environ.get('OPENAI_API_KEY')
    
    # .envファイルから取得する場合
    from dotenv import load_dotenv
    load_dotenv()
    dotenv_key = os.getenv('OPENAI_API_KEY')
    
    if system_key:
        print("✅ APIキーはシステム環境変数から取得")
        return system_key
    elif dotenv_key:
        print("⚠️  APIキーは.envファイルから取得（開発環境のみ推奨）")
        return dotenv_key
    else:
        print("❌ APIキーが設定されていません")
        return None
```

## 📋 環境別設定

### 開発環境
- `.env`ファイルの使用可（個人開発のみ）
- **重要**: `.env`をgitignoreに追加

### ステージング環境
- システム環境変数を使用
- CI/CDパイプラインでsecrets管理

### 本番環境
- **必須**: システム環境変数のみ
- KMS、HashiCorp Vault等のシークレット管理サービス推奨

## ⚠️ .envファイル使用時の注意

1. **gitignoreに追加**
```gitignore
.env
.env.local
.env.*.local
```

2. **ファイル権限設定**
```bash
chmod 600 .env  # 所有者のみ読み書き可能
```

3. **テンプレートファイルの提供**
- `.env.example` でテンプレートを提供
- 実際のキーは含めない

## 🚀 クイック設定手順

### 1. システム環境変数設定（推奨）
```bash
# ~/.bashrc または ~/.zshrc に追加
export OPENAI_API_KEY="your-api-key-here"
source ~/.bashrc
```

### 2. アプリケーション起動
```bash
python app.py
# APIキーはシステム環境変数から自動取得
```

### 3. Docker使用時
```bash
# システム環境変数をDockerに渡す
docker run -e OPENAI_API_KEY="$OPENAI_API_KEY" transcript-cleaner
```

## 📝 まとめ

| 環境 | 推奨方法 | 理由 |
|------|----------|------|
| 開発 | システム環境変数 | セキュリティベストプラクティス |
| 本番 | システム環境変数 + シークレット管理 | 最高レベルのセキュリティ |
| Docker | 環境変数 + Secrets | コンテナ環境での標準的な方法 |

**重要**: `.env`ファイルは開発時の利便性のためのフォールバックとして残していますが、本番環境では必ずシステム環境変数を使用してください。