from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (StringField, TextAreaField, SelectField, IntegerField,
                     SubmitField, HiddenField)
from wtforms.validators import DataRequired, Email, Optional, URL, NumberRange


class PlatformForm(FlaskForm):
    name = StringField('Platform Name', validators=[DataRequired()])
    url = StringField('URL', validators=[DataRequired(), URL()])
    domain_authority = IntegerField('Domain Authority',
                                   validators=[Optional(), NumberRange(0, 100)])
    contact_email = StringField('Contact Email', validators=[Optional(), Email()])
    contact_name = StringField('Contact Name', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Platform')


class TargetForm(FlaskForm):
    platform_id = SelectField('Platform', coerce=int, validators=[DataRequired()])
    target_url = StringField('Target URL', validators=[DataRequired(), URL()])
    target_page_title = StringField('Page Title', validators=[Optional()])
    our_url = StringField('Our URL to Link', validators=[Optional()])
    anchor_text = StringField('Desired Anchor Text', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('identified', 'Identified'),
        ('contacted', 'Contacted'),
        ('negotiating', 'Negotiating'),
        ('approved', 'Approved'),
        ('live', 'Live'),
        ('rejected', 'Rejected'),
    ], validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Target')


class CampaignForm(FlaskForm):
    name = StringField('Campaign Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ], validators=[DataRequired()])
    submit = SubmitField('Save Campaign')


class OutreachEmailForm(FlaskForm):
    target_id = SelectField('Target', coerce=int, validators=[DataRequired()])
    campaign_id = SelectField('Campaign', coerce=int, validators=[Optional()])
    recipient_email = StringField('Recipient Email',
                                  validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired()])
    body = TextAreaField('Email Body (HTML)', validators=[DataRequired()])
    submit = SubmitField('Save Draft')


class SendEmailForm(FlaskForm):
    email_id = HiddenField('Email ID', validators=[DataRequired()])
    submit = SubmitField('Send Email')


class UploadPlatformsForm(FlaskForm):
    file = FileField('Upload File', validators=[
        FileRequired(),
        FileAllowed(['csv', 'xlsx', 'xls'], 'Only CSV and Excel files allowed.')
    ])
    submit = SubmitField('Upload & Import')
