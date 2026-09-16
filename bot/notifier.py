import json
import logging
import requests
from datetime import datetime, timezone
from bot.config import config

logger = logging.getLogger("Notifier")

class BotNotifier:
    def __init__(self):
        self.discord_url = config.discord_webhook_url
        self.telegram_token = config.telegram_bot_token
        self.telegram_chat_id = config.telegram_chat_id

    def send(self, title: str, message: str, color: str = "info"):
        """
        Envia una notificació als canals configurats (Discord, Telegram i consola).
        Colors: 'info' (blau), 'success' (verd), 'danger' (vermell), 'warning' (taronja)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{title}] {message}"
        
        if color == "danger":
            logger.error(log_msg)
        elif color == "warning":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
            
        print(f"📣 {title}: {message}")

        # 1. Enviar a Discord
        if self.discord_url:
            self._send_discord(title, message, color)

        # 2. Enviar a Telegram
        if self.telegram_token and self.telegram_chat_id:
            self._send_telegram(title, message)

    def _send_discord(self, title: str, message: str, color_name: str):
        color_map = {
            "info": 3447003,      # Blau
            "success": 3066993,   # Verd
            "danger": 15158332,   # Vermell
            "warning": 15105570   # Taronja
        }
        color_code = color_map.get(color_name, 3447003)

        payload = {
            "embeds": [{
                "title": title,
                "description": message,
                "color": color_code,
                "footer": {"text": f"Tradovate MNQ Zones Bot • {config.tradovate_env.upper()}"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]
        }

        try:
            res = requests.post(self.discord_url, json=payload, timeout=5)
            if res.status_code not in (200, 204):
                logger.warning(f"Error enviant a Discord: HTTP {res.status_code}")
        except Exception as e:
            logger.error(f"Excepció enviant a Discord: {e}")

    def _send_telegram(self, title: str, message: str):
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        text = f"*{title}*\n\n{message}\n\n_Entorn: {config.tradovate_env.upper()}_"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code != 200:
                logger.warning(f"Error enviant a Telegram: HTTP {res.status_code}")
        except Exception as e:
            logger.error(f"Excepció enviant a Telegram: {e}")

notifier = BotNotifier()
