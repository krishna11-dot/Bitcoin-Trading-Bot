"""
Gmail Notifier - Daily Summary Email Notifications

PURPOSE:
    Send daily summary emails with portfolio performance, trades executed,
    and key metrics via Gmail API.

ARCHITECTURE FIT:
    Decision Box → Gmail Notifier (daily summary)
    Same pattern as Telegram, but for daily summaries instead of real-time alerts

FEATURES:
    - OAuth2 authentication with token refresh
    - Daily portfolio summary emails
    - Trade history summary
    - Performance metrics (return, Sharpe, drawdown)
    - Graceful degradation (trading continues if Gmail fails)

SETUP REQUIRED:
    1. Enable Gmail API in Google Cloud Console
    2. Create OAuth 2.0 Client ID (Desktop app)
    3. Download credentials.json
    4. Run authorization flow (first time only)
    5. Refresh token saved for future use

See: GMAIL_SETUP_GUIDE.md for complete setup instructions
"""

import os
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False


class GmailNotifier:
    """
    Sends daily summary emails via Gmail API.

    Uses OAuth2 for authentication with token refresh.
    Gracefully degrades if credentials missing or API unavailable.
    """

    # Gmail API scope (send emails only)
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    def __init__(self,
                 credentials_path: str = None,
                 token_path: str = None,
                 recipient_email: str = None,
                 enabled: bool = True):
        """
        Initialize Gmail notifier.

        Args:
            credentials_path: Path to OAuth2 credentials.json from Google Console
            token_path: Path to save/load refresh token (auto-generated)
            recipient_email: Email address to send summaries to
            enabled: Whether Gmail notifications are enabled
        """
        self.enabled = enabled and GMAIL_AVAILABLE

        if not GMAIL_AVAILABLE:
            print("[GMAIL] Warning: google-auth libraries not installed")
            print("        Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            self.enabled = False
            return

        # Default paths
        project_root = Path(__file__).parent.parent.parent

        if credentials_path is None:
            credentials_path = project_root / "config" / "gmail_credentials.json"
        else:
            credentials_path = Path(credentials_path)

        if token_path is None:
            token_path = project_root / "config" / "gmail_token.pickle"
        else:
            token_path = Path(token_path)

        self.credentials_path = credentials_path
        self.token_path = token_path

        # Get recipient email from env or parameter
        from dotenv import load_dotenv
        env_path = project_root / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        self.recipient_email = recipient_email or os.getenv('GMAIL_RECIPIENT_EMAIL')

        # Check if setup is complete
        if not self.credentials_path.exists():
            print(f"[GMAIL] Warning: Credentials not found at {self.credentials_path}")
            print("        See GMAIL_SETUP_GUIDE.md for setup instructions")
            self.enabled = False
            return

        if not self.recipient_email:
            print("[GMAIL] Warning: GMAIL_RECIPIENT_EMAIL not set in .env")
            self.enabled = False
            return

        # Initialize Gmail service
        self.service = None
        if self.enabled:
            self._authenticate()

    def _authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2.

        First run: Opens browser for authorization, saves refresh token
        Subsequent runs: Uses saved refresh token

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            creds = None

            # Load existing token if available
            if self.token_path.exists():
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)

            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # Refresh expired token
                    print("[GMAIL] Refreshing access token...")
                    creds.refresh(Request())
                else:
                    # Run OAuth flow (first time setup)
                    print("[GMAIL] Running OAuth authorization flow...")
                    print("        A browser window will open for authorization")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save token for future use
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
                print(f"[GMAIL] Token saved to {self.token_path}")

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            print("[GMAIL] Authentication successful")
            return True

        except Exception as e:
            print(f"[GMAIL] Authentication error: {str(e)}")
            self.enabled = False
            return False

    def send_email(self, subject: str, body_html: str) -> bool:
        """
        Send HTML email via Gmail API.

        Args:
            subject: Email subject line
            body_html: Email body in HTML format

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled or not self.service:
            return False

        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['To'] = self.recipient_email
            message['Subject'] = subject

            # Attach HTML body
            html_part = MIMEText(body_html, 'html')
            message.attach(html_part)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send via Gmail API
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            print(f"[GMAIL] Email sent to {self.recipient_email}")
            return True

        except HttpError as e:
            print(f"[GMAIL] API error: {e}")
            return False
        except Exception as e:
            print(f"[GMAIL] Error sending email: {str(e)}")
            return False

    def send_daily_summary(self,
                          portfolio: Dict,
                          trades_today: List[Dict],
                          metrics: Dict,
                          current_price: float,
                          date: datetime = None) -> bool:
        """
        Send daily portfolio summary email.

        Args:
            portfolio: Current portfolio state (cash, btc, total_value)
            trades_today: List of trades executed today
            metrics: Performance metrics (total_return, sharpe, drawdown, etc.)
            current_price: Current BTC price
            date: Date for summary (default: today)

        Returns:
            True if sent successfully, False otherwise
        """
        if date is None:
            date = datetime.now()

        # Format subject
        subject = f" BTC Trading Bot - Daily Summary {date.strftime('%Y-%m-%d')}"

        # Build HTML email
        html = self._build_summary_html(
            portfolio, trades_today, metrics, current_price, date
        )

        return self.send_email(subject, html)

    def _build_summary_html(self,
                           portfolio: Dict,
                           trades_today: List[Dict],
                           metrics: Dict,
                           current_price: float,
                           date: datetime) -> str:
        """
        Build HTML email body for daily summary.

        Returns clean, readable HTML with portfolio performance and trade details.
        """
        # Portfolio summary
        total_value = portfolio.get('cash', 0) + (portfolio.get('btc', 0) * current_price)
        cash = portfolio.get('cash', 0)
        btc = portfolio.get('btc', 0)
        btc_value = btc * current_price

        # Performance metrics
        total_return = metrics.get('total_return', 0)
        sharpe = metrics.get('sharpe_ratio', 0)
        max_drawdown = metrics.get('max_drawdown', 0)
        win_rate = metrics.get('win_rate', 0)
        total_trades = metrics.get('total_trades', 0)

        # Return color
        return_color = "#00C851" if total_return >= 0 else "#ff4444"
        return_symbol = "" if total_return >= 0 else ""

        # Trades summary
        trades_html = ""
        if trades_today:
            for trade in trades_today:
                action = trade.get('action', 'UNKNOWN')
                price = trade.get('price', 0)
                amount = trade.get('amount', 0)
                strategy = trade.get('strategy', 'Unknown')
                time = trade.get('timestamp', '')

                if action == 'BUY':
                    icon = ""
                    color = "#00C851"
                elif action == 'SELL':
                    icon = ""
                    color = "#ff4444"
                else:
                    icon = "⏸"
                    color = "#ffbb33"

                trades_html += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        <span style="color: {color}; font-weight: bold;">{icon} {action}</span>
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">${price:,.2f}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">${amount:,.2f}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{strategy}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{time}</td>
                </tr>
                """
        else:
            trades_html = """
            <tr>
                <td colspan="5" style="padding: 16px; text-align: center; color: #999;">
                    No trades executed today
                </td>
            </tr>
            """

        # Build complete HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">

    <h1 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">
         BTC Trading Bot - Daily Summary
    </h1>

    <p style="color: #7f8c8d; font-size: 14px;">
        {date.strftime('%A, %B %d, %Y')}
    </p>

    <!-- Portfolio Summary -->
    <div style="background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0;">
        <h2 style="margin-top: 0; color: #2c3e50;">Portfolio Value</h2>
        <p style="font-size: 32px; font-weight: bold; margin: 10px 0; color: #2c3e50;">
            ${total_value:,.2f}
        </p>
        <p style="font-size: 18px; color: {return_color}; font-weight: bold; margin: 5px 0;">
            {return_symbol} {total_return:+.2f}% Total Return
        </p>
    </div>

    <!-- Asset Breakdown -->
    <div style="margin: 20px 0;">
        <h3 style="color: #2c3e50;">Asset Breakdown</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px; background: #ecf0f1; font-weight: bold;">Cash (USD)</td>
                <td style="padding: 10px; text-align: right; background: #ecf0f1;">${cash:,.2f}</td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #f8f9fa; font-weight: bold;">Bitcoin Holdings</td>
                <td style="padding: 10px; text-align: right; background: #f8f9fa;">{btc:.6f} BTC</td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #ecf0f1; font-weight: bold;">BTC Value @ ${current_price:,.2f}</td>
                <td style="padding: 10px; text-align: right; background: #ecf0f1;">${btc_value:,.2f}</td>
            </tr>
        </table>
    </div>

    <!-- Performance Metrics -->
    <div style="margin: 20px 0;">
        <h3 style="color: #2c3e50;">Performance Metrics</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px; background: #f8f9fa;">Sharpe Ratio</td>
                <td style="padding: 10px; text-align: right; background: #f8f9fa; font-weight: bold;">{sharpe:.2f}</td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #ecf0f1;">Max Drawdown</td>
                <td style="padding: 10px; text-align: right; background: #ecf0f1; font-weight: bold; color: #ff4444;">{max_drawdown:.2f}%</td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #f8f9fa;">Win Rate</td>
                <td style="padding: 10px; text-align: right; background: #f8f9fa; font-weight: bold;">{win_rate:.1f}%</td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #ecf0f1;">Total Trades</td>
                <td style="padding: 10px; text-align: right; background: #ecf0f1; font-weight: bold;">{total_trades}</td>
            </tr>
        </table>
    </div>

    <!-- Trades Today -->
    <div style="margin: 20px 0;">
        <h3 style="color: #2c3e50;">Trades Executed Today</h3>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
            <thead>
                <tr style="background: #3498db; color: white;">
                    <th style="padding: 10px; text-align: left;">Action</th>
                    <th style="padding: 10px; text-align: left;">Price</th>
                    <th style="padding: 10px; text-align: left;">Amount</th>
                    <th style="padding: 10px; text-align: left;">Strategy</th>
                    <th style="padding: 10px; text-align: left;">Time</th>
                </tr>
            </thead>
            <tbody>
                {trades_html}
            </tbody>
        </table>
    </div>

    <!-- Footer -->
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 12px;">
        <p>
             Generated by BTC Intelligent Trader<br>
            Automated daily summary sent via Gmail API
        </p>
        <p style="color: #999; font-size: 11px;">
            This is an automated message. Performance data is for informational purposes only.
        </p>
    </div>

</body>
</html>
        """

        return html.strip()


def test_gmail_connection():
    """
    Test Gmail API connection and authentication.

    Run this after completing OAuth setup to verify everything works.
    """
    print("=" * 70)
    print("GMAIL API CONNECTION TEST")
    print("=" * 70)

    if not GMAIL_AVAILABLE:
        print("\n Gmail libraries not installed")
        print("   Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False

    notifier = GmailNotifier()

    if not notifier.enabled:
        print("\n Gmail notifier not enabled")
        print("   Check:")
        print("   1. gmail_credentials.json exists in config/")
        print("   2. GMAIL_RECIPIENT_EMAIL set in .env")
        print("   3. See GMAIL_SETUP_GUIDE.md for setup")
        return False

    print("\nGmail notifier initialized")
    print(f"  Recipient: {notifier.recipient_email}")

    # Send test email
    print("\nSending test email...")

    test_html = """
    <html>
        <body>
            <h2> Gmail API Test Successful</h2>
            <p>Your BTC Trading Bot can now send daily summaries via Gmail!</p>
            <p><strong>Next steps:</strong></p>
            <ul>
                <li>Run backtest to generate performance data</li>
                <li>Daily summaries will be sent automatically</li>
                <li>Check spam folder if you don't see emails</li>
            </ul>
        </body>
    </html>
    """

    success = notifier.send_email(
        subject=" BTC Trading Bot - Gmail Test",
        body_html=test_html
    )

    if success:
        print("\n Test email sent successfully!")
        print(f"   Check {notifier.recipient_email}")
        return True
    else:
        print("\n Failed to send test email")
        print("   Check authentication and credentials")
        return False


if __name__ == "__main__":
    test_gmail_connection()
