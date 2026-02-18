from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app

from app import db
from app.models import Platform, Target, Campaign, OutreachEmail
from app.forms import (PlatformForm, TargetForm, CampaignForm,
                       OutreachEmailForm, SendEmailForm, UploadPlatformsForm)
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
        platform = Platform()
        form.populate_obj(platform)
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


@main_bp.route('/platforms/delete-all', methods=['POST'])
def platform_delete_all():
    count = Platform.query.count()
    Platform.query.delete()
    db.session.commit()
    flash(f'Deleted all {count} platforms.', 'success')
    return redirect(url_for('main.platforms_list'))


@main_bp.route('/platforms/upload', methods=['GET', 'POST'])
def platform_upload():
    form = UploadPlatformsForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = file.filename.lower()

        try:
            rows = _parse_upload_file(file, filename)
        except Exception as e:
            flash(f'Could not read file: {e}', 'danger')
            return render_template('platforms/upload.html', form=form)

        if not rows:
            flash('File is empty or has no data rows.', 'warning')
            return render_template('platforms/upload.html', form=form)

        headers = [h.strip().lower() for h in rows[0]]
        col_map = _auto_map_columns(headers)

        if 'name' not in col_map and 'url' not in col_map:
            flash(
                f'Could not detect a Name or URL column. '
                f'Found columns: {", ".join(rows[0])}. '
                f'Please rename at least one column to "Name" or "URL".',
                'danger',
            )
            return render_template('platforms/upload.html', form=form)

        imported = 0
        skipped = []
        for row_num, row in enumerate(rows[1:], start=2):
            if len(row) < len(headers):
                row += [''] * (len(headers) - len(row))

            name = _get_mapped(row, headers, col_map, 'name')
            url = _get_mapped(row, headers, col_map, 'url')

            if not name and not url:
                continue  # skip blank rows

            if not name:
                name = url
            if not url:
                skipped.append(f'Row {row_num}: missing URL')
                continue

            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            platform = Platform(
                tier=(_get_mapped(row, headers, col_map, 'tier') or '').strip() or None,
                name=name.strip(),
                url=url.strip(),
                submission_type=(_get_mapped(row, headers, col_map, 'submission_type') or '').strip() or None,
                topic_to_submit=(_get_mapped(row, headers, col_map, 'topic_to_submit') or '').strip() or None,
                difficulty=(_get_mapped(row, headers, col_map, 'difficulty') or '').strip() or None,
                contact_name=(_get_mapped(row, headers, col_map, 'contact_name') or '').strip() or None,
                contact_email=(_get_mapped(row, headers, col_map, 'contact_email') or '').strip() or None,
                pitch_sent_date=_parse_date(_get_mapped(row, headers, col_map, 'pitch_sent_date')),
                article_sent_date=_parse_date(_get_mapped(row, headers, col_map, 'article_sent_date')),
                follow_up_1=_parse_date(_get_mapped(row, headers, col_map, 'follow_up_1')),
                follow_up_2=_parse_date(_get_mapped(row, headers, col_map, 'follow_up_2')),
                response_date=_parse_date(_get_mapped(row, headers, col_map, 'response_date')),
                status=(_get_mapped(row, headers, col_map, 'status') or '').strip() or 'Not Started',
                notes=(_get_mapped(row, headers, col_map, 'notes') or '').strip() or None,
                publication_date=_parse_date(_get_mapped(row, headers, col_map, 'publication_date')),
                live_url=(_get_mapped(row, headers, col_map, 'live_url') or '').strip() or None,
                backlink_confirmed=_parse_bool(_get_mapped(row, headers, col_map, 'backlink_confirmed')),
            )
            db.session.add(platform)
            imported += 1

        db.session.commit()

        msg = f'Imported {imported} platform{"s" if imported != 1 else ""}.'
        if skipped:
            msg += f' Skipped {len(skipped)}: {"; ".join(skipped[:5])}'
        flash(msg, 'success')
        return redirect(url_for('main.platforms_list'))

    return render_template('platforms/upload.html', form=form)


def _parse_upload_file(file, filename):
    """Parse CSV or Excel file and return list of rows (each row is a list of strings)."""
    import csv
    import io

    if filename.endswith('.csv'):
        content = file.read().decode('utf-8-sig')
        reader = csv.reader(io.StringIO(content))
        return [row for row in reader if any(cell.strip() for cell in row)]
    else:
        import openpyxl
        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
        ws = wb.active
        rows = []
        for row in ws.iter_rows(values_only=True):
            str_row = [str(cell) if cell is not None else '' for cell in row]
            if any(cell.strip() for cell in str_row):
                rows.append(str_row)
        wb.close()
        return rows


def _auto_map_columns(headers):
    """Map Platform fields to column indices based on common header names."""
    mapping = {}

    patterns = {
        'tier': ['tier'],
        'name': ['name', 'platform', 'website', 'site', 'site name', 'platform name', 'website name', 'blog'],
        'url': ['url', 'website url', 'link', 'domain', 'site url', 'platform url', 'web address'],
        'submission_type': ['submission type', 'submission_type', 'type', 'submit type'],
        'topic_to_submit': ['topic to submit', 'topic_to_submit', 'topic', 'article topic'],
        'difficulty': ['difficulty', 'level'],
        'contact_name': ['contact', 'contact name', 'contact_name', 'person', 'editor', 'author', 'contact/editor'],
        'contact_email': ['email', 'contact email', 'contact_email', 'e-mail', 'email address'],
        'pitch_sent_date': ['pitch sent date', 'pitch_sent_date', 'pitch sent', 'pitch date'],
        'article_sent_date': ['article sent date', 'article_sent_date', 'article sent', 'article date'],
        'follow_up_1': ['follow-up 1', 'follow_up_1', 'followup 1', 'follow up 1'],
        'follow_up_2': ['follow-up 2', 'follow_up_2', 'followup 2', 'follow up 2'],
        'response_date': ['response date', 'response_date', 'response'],
        'status': ['status'],
        'notes': ['notes', 'comments', 'note', 'comment', 'remarks'],
        'publication_date': ['publication date', 'publication_date', 'published date', 'pub date'],
        'live_url': ['live url', 'live_url', 'published url', 'article url', 'live link'],
        'backlink_confirmed': ['backlink confirmed', 'backlink_confirmed', 'backlink', 'confirmed'],
    }

    for field, keywords in patterns.items():
        for idx, header in enumerate(headers):
            if header in keywords:
                mapping[field] = idx
                break

    return mapping


def _get_mapped(row, headers, col_map, field):
    """Get a value from a row using the column mapping."""
    idx = col_map.get(field)
    if idx is not None and idx < len(row):
        return row[idx]
    return None


def _parse_date(value):
    """Try to parse a date string from various formats."""
    if not value or not value.strip():
        return None
    from dateutil import parser as dateutil_parser
    try:
        return dateutil_parser.parse(value.strip()).date()
    except (ValueError, TypeError):
        return None


def _parse_bool(value):
    """Parse a boolean from common truthy strings."""
    if not value:
        return False
    return value.strip().lower() in ('yes', 'true', '1', 'y', 'confirmed')


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
