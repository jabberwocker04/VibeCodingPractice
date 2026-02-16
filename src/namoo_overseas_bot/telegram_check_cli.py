from __future__ import annotations

import argparse
from datetime import datetime, timezone

from namoo_overseas_bot.config import BotConfig
from namoo_overseas_bot.notifiers.telegram import TelegramNotifier


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send a Telegram test alert using .env config")
    parser.add_argument(
        "--message",
        default="",
        help="optional custom message",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = BotConfig.from_env()

    if not config.telegram_bot_token or not config.telegram_chat_id:
        raise ValueError("telegram token/chat id is missing in environment")

    message = args.message.strip()
    if not message:
        now = datetime.now(timezone.utc).isoformat()
        message = f"[테스트] namoo-overseas-bot Telegram 알림 점검 | utc={now}"

    notifier = TelegramNotifier(
        bot_token=config.telegram_bot_token,
        chat_id=config.telegram_chat_id,
    )
    notifier.send(message)
    print("telegram test alert sent")


if __name__ == "__main__":
    main()
