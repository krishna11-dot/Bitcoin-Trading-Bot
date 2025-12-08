# Quick Fix: Gmail Notifier

## Problem
Gmail notifier showing as "not enabled" with error:
```
[GMAIL] Authentication error: invalid_grant: Token has been expired or revoked
```

## Root Cause
OAuth tokens expire periodically. This is normal OAuth behavior.

## Solution (2 minutes)

### Step 1: Delete Expired Token
```bash
cd c:\Users\krish\btc-intelligent-trader
rm config\gmail_token.pickle
```

### Step 2: Re-Authorize
```bash
uv run python src\notifications\gmail_notifier.py
```

This will:
1. Open your browser
2. Ask you to sign in to Google
3. Request permission to send emails
4. Save a new token

### Step 3: Verify
Check that the new token file was created:
```bash
ls -la config\gmail_token.pickle
```

You should see a file dated today.

## Why This Happens

Google OAuth tokens can expire for several reasons:
- Time-based expiration (refresh tokens can expire)
- Security reasons (Google detected suspicious activity)
- Token revocation by user
- Changes to Google account security settings

This is **not a bug** - it's standard OAuth security.

## Prevention

Google OAuth refresh tokens can last a long time, but there's no way to prevent expiration entirely. When it happens, just re-authorize (takes 30 seconds).

## Files Confirmed Working

✅ `config/gmail_credentials.json` - OAuth client credentials (present)
✅ `.env` has `GMAIL_RECIPIENT_EMAIL=krishnanair041@gmail.com`

All you need is a fresh token!
