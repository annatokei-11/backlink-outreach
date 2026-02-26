"""
Email finder service — waterfall enrichment adapted for Flask.

Uses LinkedIn search (Serper + OpenAI) then tries email providers in order:
Kendo -> SalesQL -> Apollo -> Snov -> RocketReach

All API keys come from app.config (set via environment variables).
"""
import re
import json
import time
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

import requests
from flask import current_app

logger = logging.getLogger(__name__)

SERVICE_ORDER = ['Kendo', 'SalesQL', 'Apollo', 'Snov', 'RocketReach']


@dataclass
class EmailResult:
    email: Optional[str] = None
    source: str = ''
    confidence: int = 0
    linkedin_url: Optional[str] = None
    title: str = ''
    organization: str = ''
    error: str = ''

    @property
    def found(self):
        return bool(self.email)


# ---------------------------------------------------------------------------
# LinkedIn search (Serper + OpenAI)
# ---------------------------------------------------------------------------

def _serper_search(query: str, api_key: str, num: int = 10) -> Optional[dict]:
    try:
        resp = requests.post(
            'https://google.serper.dev/search',
            json={'q': query, 'num': num},
            headers={'X-API-KEY': api_key, 'Content-Type': 'application/json'},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        logger.warning('Serper error: %s', exc)
    return None


def _openai_chat(prompt: str, system: str, api_key: str) -> Optional[str]:
    try:
        resp = requests.post(
            'https://api.openai.com/v1/chat/completions',
            json={
                'model': 'gpt-4o-mini',
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': 0.3,
                'max_tokens': 300,
            },
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            timeout=20,
        )
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'].strip()
    except Exception as exc:
        logger.warning('OpenAI error: %s', exc)
    return None


def _fetch_page_text(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if resp.status_code == 200:
            text = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:5000]
    except Exception:
        pass
    return ''


def _get_key(name: str) -> str:
    """Read an API key: try DB (AppSetting) first, fall back to app config."""
    from app.models import AppSetting
    val = AppSetting.get(name, '')
    if val:
        return val
    return current_app.config.get(name, '')


def find_linkedin(contact_name: str, platform_name: str) -> Tuple[Optional[str], str]:
    """Two-phase LinkedIn search: gather intelligence then targeted search."""
    serper_key = _get_key('SERPER_API_KEY')
    openai_key = _get_key('OPENAI_API_KEY')

    if not serper_key:
        return None, 'No Serper API key configured'
    if not openai_key:
        return None, 'No OpenAI API key configured'

    # Phase 1 — broad search + scrape for intel
    data = _serper_search(f'"{contact_name}" "{platform_name}"', serper_key, 10)
    if not data or 'organic' not in data:
        return None, 'No search results'

    combined = ''
    for result in data['organic'][:5]:
        link = result.get('link', '')
        if link:
            combined += '\n' + _fetch_page_text(link)[:1000]

    # Check if LinkedIn URL already in scraped content
    m = re.search(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', combined)
    if m:
        return f'https://www.linkedin.com/in/{m.group(1)}', 'Found in page content'

    # Extract intelligence via OpenAI
    intel = {}
    raw = _openai_chat(
        f'Extract info about {contact_name} from {platform_name}.\nContent:\n{combined[:2000]}\n'
        'Return JSON: {{"company":"...","title":"...","location":"..."}}',
        'Information extraction. Respond only with valid JSON.',
        openai_key,
    )
    if raw:
        try:
            cleaned = raw
            if cleaned.startswith('```'):
                cleaned = cleaned.split('```')[1]
                if cleaned.startswith('json'):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()
            intel = json.loads(cleaned)
        except Exception:
            pass

    # Phase 2 — targeted LinkedIn queries (up to 3 attempts)
    name_parts = contact_name.strip().split()
    queries = [
        f'"{contact_name}" site:linkedin.com/in/',
    ]
    company = intel.get('company', '')
    if company and company != 'Unknown':
        queries.insert(0, f'"{contact_name}" {company} site:linkedin.com/in/')
    if len(name_parts) >= 2:
        queries.append(f'{name_parts[0]} {name_parts[-1]} site:linkedin.com/in/')

    for query in queries[:3]:
        data = _serper_search(query, serper_key, 10)
        if not data or 'organic' not in data:
            time.sleep(0.3)
            continue

        linkedin_results = []
        for r in data['organic']:
            link = r.get('link', '')
            if 'linkedin.com/in/' in link:
                linkedin_results.append({
                    'url': link.split('?')[0],
                    'title': r.get('title', ''),
                    'snippet': r.get('snippet', ''),
                })

        if not linkedin_results:
            time.sleep(0.3)
            continue

        # Ask OpenAI to pick the right profile
        results_text = '\n'.join(
            f'{i+1}. {r["title"]} — {r["url"]}\n   {r["snippet"]}'
            for i, r in enumerate(linkedin_results)
        )
        analysis = _openai_chat(
            f'Find "{contact_name}" from "{platform_name}" (company: {company}).\n'
            f'LinkedIn results:\n{results_text}\n'
            'Return JSON: {{"match": true/false, "url": "...", "confidence": 0-100}}',
            'LinkedIn profile analyst. Respond only with valid JSON.',
            openai_key,
        )
        if analysis:
            try:
                cleaned = analysis
                if cleaned.startswith('```'):
                    cleaned = cleaned.split('```')[1]
                    if cleaned.startswith('json'):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
                result = json.loads(cleaned)
                if result.get('match') and result.get('url'):
                    url = result['url'].split('?')[0]
                    if 'linkedin.com/in/' in url:
                        return url, f'Found (confidence {result.get("confidence", "?")}%)'
            except Exception:
                pass
        time.sleep(0.3)

    return None, 'LinkedIn profile not found'


# ---------------------------------------------------------------------------
# Email provider waterfall
# ---------------------------------------------------------------------------

def _extract_linkedin_id(url: str) -> str:
    return url.split('?')[0].strip().rstrip('/').split('/')[-1]


def _try_kendo(linkedin_url: str, api_key: str) -> EmailResult:
    linkedin_id = _extract_linkedin_id(linkedin_url)
    try:
        resp = requests.get(
            'https://kendoemailapp.com/emailbylinkedin',
            params={'apikey': api_key, 'linkedin': linkedin_id},
            timeout=20,
        )
        if resp.status_code == 429:
            return EmailResult(error='Rate limited')
        if resp.status_code != 200:
            return EmailResult(error=f'HTTP {resp.status_code}')
        data = resp.json()
        email = data.get('work_email') or data.get('private_email')
        if email:
            return EmailResult(email=email, source='Kendo', confidence=90,
                               title=data.get('title', ''), organization=data.get('company', ''))
    except Exception as exc:
        return EmailResult(error=str(exc)[:80])
    return EmailResult(error='No email found')


def _try_salesql(linkedin_url: str, api_key: str) -> EmailResult:
    clean_url = linkedin_url.split('?')[0].strip().rstrip('/')
    try:
        resp = requests.get(
            'https://api-public.salesql.com/v1/persons/enrich/',
            params={'linkedin_url': clean_url},
            headers={'accept': 'application/json', 'Authorization': f'Bearer {api_key}'},
            timeout=20,
        )
        if resp.status_code == 429:
            return EmailResult(error='Rate limited')
        if resp.status_code != 200:
            return EmailResult(error=f'HTTP {resp.status_code}')
        data = resp.json()
        for entry in (data.get('emails') or []):
            email = entry.get('email', '') if isinstance(entry, dict) else ''
            if email and '@' in email:
                return EmailResult(email=email, source='SalesQL', confidence=85,
                                   title=data.get('title', ''), organization=data.get('company', ''))
    except Exception as exc:
        return EmailResult(error=str(exc)[:80])
    return EmailResult(error='No email found')


def _try_apollo(linkedin_url: str, api_key: str) -> EmailResult:
    try:
        resp = requests.post(
            'https://api.apollo.io/api/v1/people/match',
            json={'reveal_personal_emails': True, 'linkedin_url': linkedin_url},
            headers={'x-api-key': api_key, 'Content-Type': 'application/json'},
            timeout=30,
        )
        if resp.status_code == 429:
            return EmailResult(error='Rate limited')
        if resp.status_code != 200:
            return EmailResult(error=f'HTTP {resp.status_code}')
        data = resp.json()
        person = data.get('person') or {}
        email = person.get('email')
        if email:
            return EmailResult(email=email, source='Apollo', confidence=90,
                               title=person.get('title', ''), organization=person.get('organization_name', ''))
    except Exception as exc:
        return EmailResult(error=str(exc)[:80])
    return EmailResult(error='No email found')


def _try_snov(linkedin_url: str, client_id: str, client_secret: str) -> EmailResult:
    # Get access token
    try:
        token_resp = requests.post(
            'https://api.snov.io/v1/oauth/access_token',
            data={'grant_type': 'client_credentials', 'client_id': client_id, 'client_secret': client_secret},
            timeout=10,
        )
        if token_resp.status_code != 200:
            return EmailResult(error='Token request failed')
        token = token_resp.json().get('access_token')
        if not token:
            return EmailResult(error='No token returned')
    except Exception as exc:
        return EmailResult(error=str(exc)[:80])

    clean_url = linkedin_url.split('?')[0].strip().rstrip('/')
    try:
        requests.post('https://api.snov.io/v1/add-url-for-search',
                       data={'access_token': token, 'url': clean_url}, timeout=10)
        time.sleep(1)
        resp = requests.post('https://api.snov.io/v1/get-emails-from-url',
                              data={'access_token': token, 'url': clean_url}, timeout=10)
        if resp.status_code == 429:
            return EmailResult(error='Rate limited')
        if resp.status_code == 200:
            result = resp.json()
            data = result.get('data', {})
            if isinstance(data, list):
                data = data[0] if data else {}
            for entry in (data.get('emails') or []):
                email = entry.get('email', '').lower()
                if email and '@' in email and email.split('@')[0] not in ('info', 'contact', 'hello', 'support'):
                    return EmailResult(email=email, source='Snov', confidence=80,
                                       title=(data.get('currentJob') or {}).get('position', ''),
                                       organization=(data.get('currentJob') or {}).get('companyName', ''))
    except Exception as exc:
        return EmailResult(error=str(exc)[:80])
    return EmailResult(error='No email found')


def _try_rocketreach(linkedin_url: str, api_key: str) -> EmailResult:
    clean_url = linkedin_url.split('?')[0].strip().rstrip('/')
    # Normalize country-specific LinkedIn domains
    clean_url = re.sub(r'https://\w{2}\.linkedin\.com/', 'https://www.linkedin.com/', clean_url)
    try:
        resp = requests.get(
            'https://api.rocketreach.co/api/v2/person/lookup',
            params={'linkedin_url': clean_url},
            headers={'Api-Key': api_key, 'Accept': 'application/json'},
            timeout=20,
        )
        if resp.status_code == 429:
            return EmailResult(error='Rate limited')
        if resp.status_code not in (200, 202):
            return EmailResult(error=f'HTTP {resp.status_code}')
        data = resp.json()
        email = (data.get('current_work_email') or data.get('current_personal_email')
                 or data.get('recommended_email'))
        if email:
            return EmailResult(email=email, source='RocketReach', confidence=85,
                               title=data.get('current_title', ''),
                               organization=data.get('current_employer', ''))
    except Exception as exc:
        return EmailResult(error=str(exc)[:80])
    return EmailResult(error='No email found')


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_email_for_platform(platform) -> EmailResult:
    """
    Run the full enrichment pipeline for one Platform row:
    1. Find LinkedIn profile via Serper + OpenAI
    2. Waterfall through email providers using the LinkedIn URL

    Returns an EmailResult with the best email found (or .found == False).
    """
    contact = platform.contact_name
    if not contact:
        return EmailResult(error='No contact name on this platform')

    # Step 1 — LinkedIn
    linkedin_url, linkedin_status = find_linkedin(contact, platform.name)
    logger.info('LinkedIn search for %s: %s (%s)', contact, linkedin_url, linkedin_status)

    if not linkedin_url:
        return EmailResult(error=f'LinkedIn not found: {linkedin_status}')

    # Step 2 — email waterfall (keys read from DB or config)
    providers = [
        ('Kendo',       lambda: _try_kendo(linkedin_url, _get_key('KENDO_API_KEY'))),
        ('SalesQL',     lambda: _try_salesql(linkedin_url, _get_key('SALESQL_API_KEY'))),
        ('Apollo',      lambda: _try_apollo(linkedin_url, _get_key('APOLLO_API_KEY'))),
        ('Snov',        lambda: _try_snov(linkedin_url, _get_key('SNOV_CLIENT_ID'), _get_key('SNOV_CLIENT_SECRET'))),
        ('RocketReach', lambda: _try_rocketreach(linkedin_url, _get_key('ROCKETREACH_API_KEY'))),
    ]

    key_checks = {
        'Kendo':       _get_key('KENDO_API_KEY'),
        'SalesQL':     _get_key('SALESQL_API_KEY'),
        'Apollo':      _get_key('APOLLO_API_KEY'),
        'Snov':        _get_key('SNOV_CLIENT_ID') and _get_key('SNOV_CLIENT_SECRET'),
        'RocketReach': _get_key('ROCKETREACH_API_KEY'),
    }

    for name, provider_fn in providers:
        if not key_checks.get(name):
            continue

        result = provider_fn()
        result.linkedin_url = linkedin_url
        if result.found:
            logger.info('Email found for %s via %s: %s', contact, name, result.email)
            return result
        logger.debug('%s: %s', name, result.error)
        time.sleep(0.5)

    return EmailResult(linkedin_url=linkedin_url, error='Email not found by any provider')
