import asyncio
import json
import logging
import signal
from typing import Dict, Any

from trading_bot.bot.trading_bot import TradingBot
from trading_bot.bot.telegram_handler import TelegramHandler
from trading_bot.brokers.flattrade import FlattradeBroker
from trading_bot.setup_config import setup_config, update_token_in_config

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Loads the configuration from config.json."""
    setup_config() # Ensure config file exists
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("config.json not found. Please run setup.py or ensure it's in the root directory.")
        exit(1)
    except json.JSONDecodeError:
        logger.error("Error decoding config.json. Please check its format.")
        exit(1)

# --- Main Application Logic ---
async def main():
    """The main entrypoint for the trading bot application."""
    config = load_config()

    # --- Initialization ---
    broker = FlattradeBroker()

    # Authenticate broker
    session_token = config['flattrade'].get('session_token')
    if not session_token:
        logger.warning("Session token not found in config. Attempting interactive login.")
        session_token = broker.generate_session_token_interactive()
        if session_token:
            update_token_in_config(session_token)

    if not session_token or not broker.authenticate(session_token):
        logger.error("Broker authentication failed. Exiting.")
        return

    telegram_handler = TelegramHandler(
        token=config['telegram'].get('token'),
        chat_id=config['telegram'].get('chat_id')
    )

    # --- Bot Creation ---
    bots = []
    for bot_config in config['bots']:
        instrument_token = broker.get_token(bot_config['exchange'], bot_config['symbol'])
        if instrument_token:
            bot = TradingBot(
                config={**bot_config, 'trading': config['trading']},
                broker=broker,
                telegram_handler=telegram_handler,
                instrument_token=instrument_token
            )
            bots.append(bot)
        else:
            logger.error(f"Could not retrieve token for {bot_config['symbol']}. Bot not started.")

    if not bots:
        logger.error("No bots were created. Exiting.")
        return

    # --- Running the Bots ---
    tasks = [asyncio.create_task(bot.run()) for bot in bots]

    loop = asyncio.get_running_loop()
    stop = lambda: [bot.stop() for bot in bots]
    loop.add_signal_handler(signal.SIGINT, stop)
    loop.add_signal_handler(signal.SIGTERM, stop)

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Bot tasks were cancelled.")
    finally:
        logger.info("All bots have been shut down.")
        await telegram_handler.send_message("All bots have been shut down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application shut down by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)