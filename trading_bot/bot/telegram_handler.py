import telegram
import logging

logger = logging.getLogger(__name__)

class TelegramHandler:
    """Handles sending notifications via Telegram."""

    def __init__(self, token: str, chat_id: str):
        """
        Initializes the TelegramHandler.

        Args:
            token (str): The Telegram bot token.
            chat_id (str): The ID of the chat to send messages to.
        """
        if not token or not chat_id:
            logger.warning("Telegram token or chat_id not provided. Notifications will be disabled.")
            self.bot = None
            self.chat_id = None
        else:
            self.bot = telegram.Bot(token=token)
            self.chat_id = chat_id
            logger.info("TelegramHandler initialized.")

    async def send_message(self, message: str):
        """
        Sends a message to the configured Telegram chat.

        Args:
            message (str): The message to send.
        """
        if not self.bot:
            return

        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            logger.debug(f"Sent Telegram message: {message}")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")