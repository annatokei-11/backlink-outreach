from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (StringField, TextAreaField, SelectField, IntegerField,
                     SubmitField, HiddenField, DateField, BooleanField)
from wtforms.validators import DataRequired, Email, Optional, URL, NumberRange


class PlatformForm(FlaskForm):
    tier = SelectField('Tier', choices=[
        ('', '-- Select --'),
        ('T1', 'T1'),
        ('T2', 'T2'),
        ('T3', 'T3'),
    ], validators=[Optional()])
    name = StringField('Platform Name', validators=[DataRequired()])
    url = StringField('URL', validators=[DataRequired(), URL()])
    submission_type = SelectField('Submission Type', choices=[
        ('', '-- Select --'),
        ('Full Article', 'Full Article'),
        ('Pitch First', 'Pitch First'),
    ], validators=[Optional()])
    topic_to_submit = StringField('Topic to Submit', validators=[Optional()])
    difficulty = SelectField('Difficulty', choices=[
        ('', '-- Select --'),
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ], validators=[Optional()])
    contact_name = StringField('Contact/Editor', validators=[Optional()])
    contact_email = StringField('Email', validators=[Optional(), Email()])
    pitch_sent_date = DateField('Pitch Sent Date', validators=[Optional()])
    article_sent_date = DateField('Article Sent Date', validators=[Optional()])
    follow_up_1 = DateField('Follow-up 1', validators=[Optional()])
    follow_up_2 = DateField('Follow-up 2', validators=[Optional()])
    response_date = DateField('Response Date', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Not Started', 'Not Started'),
        ('Pitch Sent', 'Pitch Sent'),
        ('Article Sent', 'Article Sent'),
        ('Follow-up', 'Follow-up'),
        ('Published', 'Published'),
        ('Rejected', 'Rejected'),
    ], validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    publication_date = DateField('Publication Date', validators=[Optional()])
    live_url = StringField('Live URL', validators=[Optional()])
    backlink_confirmed = BooleanField('Backlink Confirmed')
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
