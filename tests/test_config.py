import os
import unittest

from namoo_overseas_bot.config import BotConfig


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._backup = dict(os.environ)
        os.environ["BOT_DISABLE_DOTENV"] = "true"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._backup)

    def test_reads_telegram_alias_env_names(self) -> None:
        os.environ["TELEGRAM_BOT_TOKE"] = "token-alias"
        os.environ["TELEGERAM_CHAT_ID"] = "chat-alias"
        cfg = BotConfig.from_env()
        self.assertEqual(cfg.telegram_bot_token, "token-alias")
        self.assertEqual(cfg.telegram_chat_id, "chat-alias")

    def test_prefers_canonical_env_names(self) -> None:
        os.environ["TELEGRAM_BOT_TOKEN"] = "token-main"
        os.environ["TELEGRAM_BOT_TOKE"] = "token-alias"
        os.environ["TELEGRAM_CHAT_ID"] = "chat-main"
        os.environ["TELEGERAM_CHAT_ID"] = "chat-alias"
        cfg = BotConfig.from_env()
        self.assertEqual(cfg.telegram_bot_token, "token-main")
        self.assertEqual(cfg.telegram_chat_id, "chat-main")


if __name__ == "__main__":
    unittest.main()
