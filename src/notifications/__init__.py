"""
Notifications Module - Send trade alerts and daily summaries

Handles:
- Real-time trade notifications via Telegram
- Daily portfolio summaries via Gmail
"""

from .telegram_notifier import TelegramNotifier
from .gmail_notifier import GmailNotifier

__all__ = ['TelegramNotifier', 'GmailNotifier']
