from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app

from app import db
from app.models import Platform, Target, Campaign, OutreachEmail
from app.forms import (PlatformForm, TargetForm, CampaignForm,
                       OutreachEmailForm, SendEmailForm)
from app.services.gmail_service import GmailService

main_bp = Blueprint('main', __name__)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@main_bp.route('/')
def dashboard():
    total_platforms = Platform.query.count()
    total_targets = Target.query.count()
    total_campaigns = Campaign.query.count()
    total_emails = OutreachEmail.query.count()

    targets_by_status = (
        db.session.query(Target.status, db.func.count(Target.id))
        .group_by(Target.status)
        .all()
    )
    emails_by_status = (
        db.session.query(OutreachEmail.status, db.func.count(OutreachEmail.id))
        .group_by(OutreachEmail.status)
        .all()
    )

    recent_emails = (
        OutreachEmail.query
        .order_by(OutreachEmail.created_at.desc())
        .limit(10)
        .all()
    )
    recent_targets = (
        Target.query
        .order_by(Target.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template('dashboard.html',
                           total_platforms=total_platforms,
                           total_targets=total_targets,
                           total_campaigns=total_campaigns,
                           total_emails=total_emails,
                           targets_by_status=dict(targets_by_status),
                           emails_by_status=dict(emails_by_status),
                           recent_emails=recent_emails,
                           recent_targets=recent_targets)


# ---------------------------------------------------------------------------
# Platforms CRUD
# ---------------------------------------------------------------------------

@main_bp.route('/platforms')
def platforms_list():
    platforms = Platform.query.order_by(Platform.created_at.desc()).all()
    return render_template('platforms/list.html', platforms=platforms)


@main_bp.route('/platforms/new', methods=['GET', 'POST'])
def platform_create():
    form = PlatformForm()
    if form.validate_on_submit():
        platform = Platform(
            name=form.name.data,
            url=form.url.data,
            domain_authority=form.domain_authority.data,
            contact_email=form.contact_email.data,
            contact_name=form.contact_name.data,
            notes=form.notes.data,
        )
        db.session.add(platform)
        db.session.commit()
        flash('Platform created.', 'success')
        return redirect(url_for('main.platforms_list'))
    return render_template('platforms/form.html', form=form, title='Add Platform')


@main_bp.route('/platforms/<int:id>/edit', methods=['GET', 'POST'])
def platform_edit(id):
    platform = Platform.query.get_or_404(id)
    form = PlatformForm(obj=platform)
    if form.validate_on_submit():
        form.populate_obj(platform)
        db.session.commit()
        flash('Platform updated.', 'success')
        return redirect(url_for('main.platforms_list'))
    return render_template('platforms/form.html', form=form, title='Edit Platform')


@main_bp.route('/platforms/<int:id>/delete', methods=['POST'])
def platform_delete(id):
    platform = Platform.query.get_or_404(id)
    db.session.delete(platform)
    db.session.commit()
    flash('Platform deleted.', 'success')
    return redirect(url_for('main.platforms_list'))


# ---------------------------------------------------------------------------
# Targets CRUD
# ---------------------------------------------------------------------------

@main_bp.route('/targets')
def targets_list():
    status_filter = request.args.get('status')
    query = Target.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    targets = query.order_by(Target.created_at.desc()).all()
    return render_template('targets/list.html', targets=targets,
                           current_status=status_filter)


@main_bp.route('/targets/new', methods=['GET', 'POST'])
def target_create():
    form = TargetForm()
    form.platform_id.choices = [
        (p.id, p.name) for p in Platform.query.order_by(Platform.name).all()
    ]
    if form.validate_on_submit():
        target = Target(
            platform_id=form.platform_id.data,
            target_url=form.target_url.data,
            target_page_title=form.target_page_title.data,
            our_url=form.our_url.data,
            anchor_text=form.anchor_text.data,
            status=form.status.data,
            priority=form.priority.data,
            notes=form.notes.data,
        )
        db.session.add(target)
        db.session.commit()
        flash('Target created.', 'success')
        return redirect(url_for('main.targets_list'))
    return render_template('targets/form.html', form=form, title='Add Target')


@main_bp.route('/targets/<int:id>/edit', methods=['GET', 'POST'])
def target_edit(id):
    target = Target.query.get_or_404(id)
    form = TargetForm(obj=target)
    form.platform_id.choices = [
        (p.id, p.name) for p in Platform.query.order_by(Platform.name).all()
    ]
    if form.validate_on_submit():
        form.populate_obj(target)
        db.session.commit()
        flash('Target updated.', 'success')
        return redirect(url_for('main.targets_list'))
    return render_template('targets/form.html', form=form, title='Edit Target')


@main_bp.route('/targets/<int:id>/delete', methods=['POST'])
def target_delete(id):
    target = Target.query.get_or_404(id)
    db.session.delete(target)
    db.session.commit()
    flash('Target deleted.', 'success')
    return redirect(url_for('main.targets_list'))


# ---------------------------------------------------------------------------
# Campaigns CRUD
# ---------------------------------------------------------------------------

@main_bp.route('/campaigns')
def campaigns_list():
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return render_template('campaigns/list.html', campaigns=campaigns)


@main_bp.route('/campaigns/new', methods=['GET', 'POST'])
def campaign_create():
    form = CampaignForm()
    if form.validate_on_submit():
        campaign = Campaign(
            name=form.name.data,
            description=form.description.data,
            status=form.status.data,
        )
        db.session.add(campaign)
        db.session.commit()
        flash('Campaign created.', 'success')
        return redirect(url_for('main.campaigns_list'))
    return render_template('campaigns/form.html', form=form, title='New Campaign')


@main_bp.route('/campaigns/<int:id>/edit', methods=['GET', 'POST'])
def campaign_edit(id):
    campaign = Campaign.query.get_or_404(id)
    form = CampaignForm(obj=campaign)
    if form.validate_on_submit():
        form.populate_obj(campaign)
        db.session.commit()
        flash('Campaign updated.', 'success')
        return redirect(url_for('main.campaigns_list'))
    return render_template('campaigns/form.html', form=form, title='Edit Campaign')


@main_bp.route('/campaigns/<int:id>/delete', methods=['POST'])
def campaign_delete(id):
    campaign = Campaign.query.get_or_404(id)
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted.', 'success')
    return redirect(url_for('main.campaigns_list'))


# ---------------------------------------------------------------------------
# Outreach Emails CRUD + Send
# ---------------------------------------------------------------------------

@main_bp.route('/emails')
def emails_list():
    status_filter = request.args.get('status')
    query = OutreachEmail.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    emails = query.order_by(OutreachEmail.created_at.desc()).all()
    return render_template('emails/list.html', emails=emails,
                           current_status=status_filter)


@main_bp.route('/emails/new', methods=['GET', 'POST'])
def email_create():
    form = OutreachEmailForm()
    form.target_id.choices = [
        (t.id, f'{t.target_page_title or t.target_url} ({t.platform.name})')
        for t in Target.query.order_by(Target.created_at.desc()).all()
    ]
    form.campaign_id.choices = [(0, '-- No Campaign --')] + [
        (c.id, c.name) for c in Campaign.query.order_by(Campaign.name).all()
    ]

    # Pre-fill recipient from target's platform contact
    if request.method == 'GET' and request.args.get('target_id'):
        target = Target.query.get(request.args.get('target_id'))
        if target and target.platform.contact_email:
            form.recipient_email.data = target.platform.contact_email
            form.target_id.data = target.id

    if form.validate_on_submit():
        email = OutreachEmail(
            target_id=form.target_id.data,
            campaign_id=form.campaign_id.data if form.campaign_id.data != 0 else None,
            recipient_email=form.recipient_email.data,
            subject=form.subject.data,
            body=form.body.data,
        )
        db.session.add(email)
        db.session.commit()
        flash('Email draft saved.', 'success')
        return redirect(url_for('main.emails_list'))
    return render_template('emails/form.html', form=form, title='Compose Email')


@main_bp.route('/emails/<int:id>/edit', methods=['GET', 'POST'])
def email_edit(id):
    email = OutreachEmail.query.get_or_404(id)
    if email.status == 'sent':
        flash('Cannot edit a sent email.', 'warning')
        return redirect(url_for('main.emails_list'))

    form = OutreachEmailForm(obj=email)
    form.target_id.choices = [
        (t.id, f'{t.target_page_title or t.target_url} ({t.platform.name})')
        for t in Target.query.order_by(Target.created_at.desc()).all()
    ]
    form.campaign_id.choices = [(0, '-- No Campaign --')] + [
        (c.id, c.name) for c in Campaign.query.order_by(Campaign.name).all()
    ]
    if not email.campaign_id:
        form.campaign_id.data = 0

    if form.validate_on_submit():
        email.target_id = form.target_id.data
        email.campaign_id = form.campaign_id.data if form.campaign_id.data != 0 else None
        email.recipient_email = form.recipient_email.data
        email.subject = form.subject.data
        email.body = form.body.data
        db.session.commit()
        flash('Email draft updated.', 'success')
        return redirect(url_for('main.emails_list'))
    return render_template('emails/form.html', form=form, title='Edit Email')


@main_bp.route('/emails/<int:id>/send', methods=['POST'])
def email_send(id):
    email = OutreachEmail.query.get_or_404(id)
    if email.status == 'sent':
        flash('Email already sent.', 'warning')
        return redirect(url_for('main.emails_list'))

    gmail = GmailService(
        credentials_file=current_app.config.get('GMAIL_CREDENTIALS_FILE'),
        token_file=current_app.config.get('GMAIL_TOKEN_FILE'),
        sender_email=current_app.config.get('GMAIL_SENDER_EMAIL'),
    )

    result = gmail.send_email(
        to=email.recipient_email,
        subject=email.subject,
        body_html=email.body,
    )

    if 'error' in result:
        flash(f'Failed to send: {result["error"]}', 'danger')
    else:
        email.status = 'sent'
        email.sent_at = datetime.now(timezone.utc)
        email.gmail_message_id = result.get('id')
        # Also update the target status to contacted if it was just identified
        if email.target.status == 'identified':
            email.target.status = 'contacted'
        db.session.commit()
        flash('Email sent successfully!', 'success')

    return redirect(url_for('main.emails_list'))


@main_bp.route('/emails/<int:id>/delete', methods=['POST'])
def email_delete(id):
    email = OutreachEmail.query.get_or_404(id)
    db.session.delete(email)
    db.session.commit()
    flash('Email deleted.', 'success')
    return redirect(url_for('main.emails_list'))
