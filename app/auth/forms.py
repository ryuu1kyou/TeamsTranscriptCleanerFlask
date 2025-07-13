"""
Authentication forms using Flask-WTF.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Optional
from app.models import User


class LoginForm(FlaskForm):
    """User login form."""
    username = StringField('ユーザー名またはメールアドレス', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン状態を保持')
    submit = SubmitField('ログイン')


class RegistrationForm(FlaskForm):
    """User registration form."""
    username = StringField('ユーザー名', validators=[
        DataRequired(),
        Length(min=4, max=64, message='ユーザー名は4-64文字で入力してください')
    ])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    first_name = StringField('名前', validators=[Optional(), Length(max=64)])
    last_name = StringField('姓', validators=[Optional(), Length(max=64)])
    organization = StringField('組織名', validators=[Optional(), Length(max=100)])
    password = PasswordField('パスワード', validators=[
        DataRequired(),
        Length(min=8, message='パスワードは8文字以上で入力してください')
    ])
    password2 = PasswordField('パスワード（確認）', validators=[
        DataRequired(),
        EqualTo('password', message='パスワードが一致しません')
    ])
    submit = SubmitField('登録')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('このユーザー名は既に使用されています。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('このメールアドレスは既に登録されています。')


class ChangePasswordForm(FlaskForm):
    """Change password form."""
    current_password = PasswordField('現在のパスワード', validators=[DataRequired()])
    new_password = PasswordField('新しいパスワード', validators=[
        DataRequired(),
        Length(min=8, message='パスワードは8文字以上で入力してください')
    ])
    new_password2 = PasswordField('新しいパスワード（確認）', validators=[
        DataRequired(),
        EqualTo('new_password', message='パスワードが一致しません')
    ])
    submit = SubmitField('パスワード変更')


class EditProfileForm(FlaskForm):
    """Edit user profile form."""
    username = StringField('ユーザー名', validators=[
        DataRequired(),
        Length(min=4, max=64, message='ユーザー名は4-64文字で入力してください')
    ])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    first_name = StringField('名前', validators=[Optional(), Length(max=64)])
    last_name = StringField('姓', validators=[Optional(), Length(max=64)])
    organization = StringField('組織名', validators=[Optional(), Length(max=100)])
    submit = SubmitField('プロフィール更新')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('このユーザー名は既に使用されています。')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('このメールアドレスは既に登録されています。')


class RequestPasswordResetForm(FlaskForm):
    """Request password reset form."""
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    submit = SubmitField('パスワードリセット要求')


class ResetPasswordForm(FlaskForm):
    """Reset password form."""
    password = PasswordField('新しいパスワード', validators=[
        DataRequired(),
        Length(min=8, message='パスワードは8文字以上で入力してください')
    ])
    password2 = PasswordField('新しいパスワード（確認）', validators=[
        DataRequired(),
        EqualTo('password', message='パスワードが一致しません')
    ])
    submit = SubmitField('パスワードリセット')