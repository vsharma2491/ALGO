import asyncio
import json
import logging
from datetime import datetime, timedelta

from trading_bot.brokers.flattrade import FlattradeBroker
from trading_bot.backtest.engine import BacktestEngine
from trading_bot.backtest.simulated_broker import SimulatedBroker
from trading_bot.setup_config import setup_config, update_token_in_config

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
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
async def run():
    """The main entrypoint for running a backtest."""
    config = load_config()

    # --- Initialize Live Broker for Historical Data ---
    live_broker = FlattradeBroker()

    session_token = config['flattrade'].get('session_token')
    if not session_token:
        logger.warning("Session token not found in config. Attempting interactive login.")
        session_token = live_broker.generate_session_token_interactive()
        if session_token:
            update_token_in_config(session_token)

    if not session_token or not live_broker.authenticate(session_token):
        logger.error("Live broker authentication failed. Cannot fetch historical data.")
        return

    # --- Select Bot to Backtest ---
    print("\nSelect a bot to backtest:")
    for i, bot_conf in enumerate(config['bots']):
        print(f"{i + 1}. {bot_conf['name']}")

    try:
        choice = int(input("Enter the number of the bot: ")) - 1
        if not 0 <= choice < len(config['bots']):
            raise ValueError
        selected_bot_config = config['bots'][choice]
    except (ValueError, IndexError):
        logger.error("Invalid selection.")
        return

    # --- Set up Backtest ---
    simulated_broker = SimulatedBroker()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    backtest_engine = BacktestEngine(
        bot_config={**selected_bot_config, 'trading': config['trading']},
        live_broker=live_broker,
        simulated_broker=simulated_broker,
        start_date=start_date_str,
        end_date=end_date_str
    )

    # --- Run Backtest ---
    await backtest_engine.run()

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Backtest interrupted by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during the backtest: {e}", exc_info=True)