from datetime import datetime, timezone
from app import db


class Platform(db.Model):
    __tablename__ = 'platforms'

    id = db.Column(db.Integer, primary_key=True)
    tier = db.Column(db.String(10))                       # T1, T2, T3
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    submission_type = db.Column(db.String(50))             # Full Article, Pitch First
    topic_to_submit = db.Column(db.String(300))
    difficulty = db.Column(db.String(20))                  # Easy, Medium, Hard
    contact_name = db.Column(db.String(200))               # Contact/Editor
    contact_email = db.Column(db.String(200))              # Email
    pitch_sent_date = db.Column(db.Date)
    article_sent_date = db.Column(db.Date)
    follow_up_1 = db.Column(db.Date)
    follow_up_2 = db.Column(db.Date)
    response_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Not Started')
    notes = db.Column(db.Text)
    publication_date = db.Column(db.Date)
    live_url = db.Column(db.String(500))
    backlink_confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    targets = db.relationship('Target', backref='platform', lazy='dynamic',
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Platform {self.name}>'


class Target(db.Model):
    __tablename__ = 'targets'

    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    target_url = db.Column(db.String(500), nullable=False)
    target_page_title = db.Column(db.String(300))
    our_url = db.Column(db.String(500))
    anchor_text = db.Column(db.String(300))
    status = db.Column(db.String(50), default='identified',
                       nullable=False)  # identified, contacted, negotiating, approved, live, rejected
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    emails = db.relationship('OutreachEmail', backref='target', lazy='dynamic',
                             cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Target {self.target_url}>'


class Campaign(db.Model):
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft')  # draft, active, paused, completed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    emails = db.relationship('OutreachEmail', backref='campaign', lazy='dynamic',
                             cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Campaign {self.name}>'


class OutreachEmail(db.Model):
    __tablename__ = 'outreach_emails'

    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('targets.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=True)
    recipient_email = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='draft')  # draft, sent, delivered, replied, bounced
    sent_at = db.Column(db.DateTime)
    gmail_message_id = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<OutreachEmail to={self.recipient_email} status={self.status}>'
