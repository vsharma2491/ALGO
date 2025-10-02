import os
import hashlib
import requests
import asyncio
import logging
from threading import Thread
from flask import Flask, request
from typing import Dict, Any, Optional, List
from werkzeug.serving import make_server
import threading
from datetime import datetime

from .base import BrokerBase
from NorenRestApiPy.NorenApi import NorenApi

logger = logging.getLogger(__name__)

class FlattradeBroker(BrokerBase):
    """
    A broker class for the Flattrade API.
    Handles authentication, order placement, and data retrieval.
    """
    def __init__(self):
        super().__init__()
        logger.info("Initializing FlattradeBroker...")
        self.api = NorenApi(host="https://auth.flattrade.in/?app_key=APIKEY",
            websocket="wss://piconnect.flattrade.in/PiConnectWSTp/")
        self.session_token = None
        self.tick_callback = None
        self.loop = None

    def _get_credentials(self) -> Optional[Dict[str, str]]:
        """Retrieves API credentials from environment variables."""
        api_key = os.getenv("FLATTRADE_API_KEY")
        api_secret = os.getenv("FLATTRADE_API_SECRET")
        broker_id = os.getenv("FLATTRADE_BROKER_ID")

        if not all([api_key, api_secret, broker_id]):
            logger.error("Flattrade API key, secret, or user ID are not set in environment variables.")
            return None

        return {"api_key": api_key, "api_secret": api_secret, "broker_id": broker_id}

    def authenticate(self, session_token: str) -> bool:
        """Authenticates with the Flattrade API using a session token."""
        credentials = self._get_credentials()
        if not credentials:
            return False

        ret = self.api.set_session(userid=credentials['broker_id'], password="", usertoken=session_token)
        if ret and ret.get('stat') == 'Ok':
            logger.info("Flattrade authentication successful.")
            self.session_token = session_token
            self.access_token = self.session_token
            self.authenticated = True
            return True
        else:
            emsg = ret.get('emsg') if ret else "Unknown error"
            logger.error(f"Flattrade authentication failed: {emsg}")
            return False

    def generate_session_token_interactive(self) -> Optional[str]:
        """
        Generates a session token by running a temporary web server and guiding the user
        through the Flattrade login process.
        """
        credentials = self._get_credentials()
        if not credentials:
            logger.error("Cannot generate session token without API credentials.")
            return None

        api_key = credentials['api_key']
        api_secret = credentials['api_secret']

        token_generated = threading.Event()

        app = Flask(__name__)

        @app.route('/', methods=['GET'])
        def token_handler():
            request_token = request.args.get('code')
            if not request_token:
                logger.error("Failed to retrieve request token from Flattrade.")
                return "Error: Could not retrieve request token.", 400

            sha256_hash = hashlib.sha256(f"{api_key}{request_token}{api_secret}".encode()).hexdigest()
            payload = { "api_key": api_key, "request_code": request_token, "api_secret": sha256_hash }

            try:
                response = requests.post("https://authapi.flattrade.in/trade/apitoken", json=payload)
                response.raise_for_status()
                token_data = response.json()

                if token_data.get('stat') == 'Ok' and token_data.get('token'):
                    self.session_token = token_data['token']
                    logger.info("Successfully obtained session token.")
                    token_generated.set()
                    return "Authentication successful! You can close this window."
                else:
                    logger.error(f"Failed to get session token: {token_data.get('emsg', 'Unknown error')}")
                    return f"Error: {token_data.get('emsg', 'Unknown error')}", 400
            except requests.exceptions.RequestException as e:
                logger.error(f"Request to get session token failed: {e}")
                return f"Error: {e}", 500

        server = make_server('127.0.0.1', 8080, app)
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        login_url = f"https://auth.flattrade.in/?app_key={api_key}"
        print(f"\n--- Flattrade Authentication Required ---\nPlease log in using this URL: {login_url}\nThe bot will continue once authentication is complete.")

        token_generated.wait(timeout=120)
        server.shutdown()

        return self.session_token

    def get_token(self, exchange: str, symbol: str) -> Optional[str]:
        """Retrieves the instrument token for a given symbol."""
        search_text = symbol
        is_index = ' ' in symbol
        if exchange == 'NSE' and '-EQ' not in symbol and not is_index:
            search_text = f"{symbol}-EQ"

        ret = self.api.searchscrip(exchange=exchange, searchtext=search_text)
        if ret and ret.get('stat') == 'Ok' and ret.get('values'):
            for value in ret['values']:
                if value.get('tsym') == search_text:
                    return value.get('token')
        logger.error(f"Could not find token for {symbol} on {exchange}")
        return None

    def get_historical_data(self, symbol: str, exchange: str, start_date: str, end_date: str, interval: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieves historical data for a given symbol."""
        from datetime import datetime
        token = self.get_token(exchange, symbol)
        if not token: return None

        try:
            start_ts = datetime.strptime(start_date, "%Y-%m-%d").timestamp()
            end_ts = datetime.strptime(end_date, "%Y-%m-%d").timestamp()
        except ValueError:
            logger.error("Invalid date format for historical data. Please use YYYY-MM-DD.")
            return None

        return self.api.get_time_price_series(exchange=exchange, token=token, starttime=start_ts, endtime=end_ts, interval=interval)

    async def place_order(self, symbol: str, quantity: int, price: float, transaction_type: str, order_type: str, product: str, exchange: str = 'NSE', tag: str = "strategy") -> Optional[str]:
        """Places a trading order asynchronously."""
        loop = asyncio.get_event_loop()
        ret = await loop.run_in_executor(None, lambda: self.api.place_order(
            buy_or_sell='B' if transaction_type == 'BUY' else 'S',
            product_type='M' if product == 'MIS' else 'C',
            exchange=exchange, tradingsymbol=symbol, quantity=quantity, discloseqty=0,
            price_type='MKT' if order_type == 'MARKET' else 'LMT',
            price=price, trigger_price=0.0, retention='DAY', remarks=tag
        ))
        if ret and ret.get('stat') == 'Ok' and ret.get('norenordno'):
            logger.info(f"Order placed successfully. Order ID: {ret['norenordno']}")
            return ret['norenordno']
        else:
            logger.error(f"Order placement failed: {ret.get('emsg', 'Unknown error')}")
            return None

    async def log_trade(self, symbol: str, side: str, entry_price: float, exit_price: float, entry_time: datetime, exit_time: datetime, pnl: float, reason: str):
        """Logs a completed trade to a CSV file."""
        filename = f"trades_live_{symbol.replace(' ', '_')}.csv"
        file_exists = os.path.exists(filename)
        try:
            with open(filename, "a") as f:
                if not file_exists:
                    f.write("symbol,side,entry_price,exit_price,entry_time,exit_time,pnl,exit_reason\n")
                f.write(f"{symbol},{side},{entry_price},{exit_price},{entry_time.strftime('%Y-%m-%d %H:%M:%S')},{exit_time.strftime('%Y-%m-%d %H:%M:%S')},{pnl:.2f},{reason}\n")
        except Exception as e:
            logger.error(f"Failed to log live trade: {e}")

    # --- WebSocket Methods ---
    def connect_websocket(self, tick_callback):
        self.tick_callback = tick_callback
        self.loop = asyncio.get_event_loop()
        self.api.start_websocket(
            order_update_callback=self.on_order_update,
            subscribe_callback=self.on_ticks,
            socket_open_callback=self.on_connect,
            socket_close_callback=self.on_close,
            socket_error_callback=self.on_error,
        )

    def subscribe(self, symbols: List[str], exchange: str = 'NSE'):
        instrument_list = [f"{exchange}|{self.get_token(exchange, s)}" for s in symbols if self.get_token(exchange, s)]
        if instrument_list:
            logger.info(f"Subscribing to: {instrument_list}")
            self.api.subscribe(instrument_list)

    def on_ticks(self, ticks):
        if self.tick_callback and self.loop:
            asyncio.run_coroutine_threadsafe(self.tick_callback(ticks), self.loop)

    def on_connect(self): logger.info("WebSocket connected.")
    def on_close(self): logger.info("WebSocket closed.")
    def on_error(self, err): logger.error(f"WebSocket error: {err}")
    def on_order_update(self, order_data): logger.info(f"Order Update: {order_data}")