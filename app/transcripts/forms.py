"""
Forms for transcript management.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Optional
from app.models import WordList


class TranscriptUploadForm(FlaskForm):
    """Form for uploading transcript files."""
    title = StringField('タイトル', validators=[DataRequired(), Length(max=255)])
    file = FileField('トランスクリプトファイル', validators=[
        FileRequired(),
        FileAllowed(['txt'], 'テキストファイル(.txt)のみアップロード可能です')
    ])
    submit = SubmitField('アップロード')


class TranscriptProcessForm(FlaskForm):
    """Form for processing transcripts."""
    transcript_id = SelectField('トランスクリプト', coerce=int, validators=[DataRequired()])
    processing_mode = SelectField('処理モード', choices=[
        ('proofreading', '誤字脱字修正'),
        ('grammar', '文法修正'),
        ('summary', '要約生成'),
        ('custom', 'カスタム処理')
    ], default='proofreading', validators=[DataRequired()])
    
    model_used = SelectField('AIモデル', choices=[
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4o-mini', 'GPT-4o Mini'),
        ('gpt-4-turbo', 'GPT-4 Turbo'),
        ('gpt-4', 'GPT-4'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo')
    ], default='gpt-4o', validators=[DataRequired()])
    
    wordlist_id = SelectField('ワードリスト（任意）', coerce=int, validators=[Optional()])
    custom_prompt = TextAreaField('カスタムプロンプト（任意）', validators=[Optional()])
    
    submit = SubmitField('処理実行')
    
    def __init__(self, user, *args, **kwargs):
        super(TranscriptProcessForm, self).__init__(*args, **kwargs)
        
        # Populate transcript choices
        self.transcript_id.choices = [(0, '選択してください...')] + [
            (t.id, f'{t.title} ({t.character_count}文字)')
            for t in user.transcripts.order_by('title')
        ]
        
        # Populate wordlist choices (DBが未整備でも落ちないようにフェイルセーフ)
        self.wordlist_id.choices = [(0, '使用しない')]
        try:
            self.wordlist_id.choices += [
                (w.id, f'{w.name} ({w.word_count}語)')
                for w in user.wordlists.filter_by(is_active=True).order_by('name')
            ]
        except Exception:
            # 例: 初回起動で wordlists テーブル未作成など
            pass


class TranscriptEditForm(FlaskForm):
    """Form for editing transcript metadata."""
    title = StringField('タイトル', validators=[DataRequired(), Length(max=255)])
    content = TextAreaField('内容', validators=[DataRequired()], render_kw={'rows': 20})
    submit = SubmitField('更新')