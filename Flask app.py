from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Flask server is running. Use /flattrade for login callback."



if __name__ == '__main__':
    app.run(port=21000)
import requests

@app.route('/flattrade')
def flattrade_callback():
    code = request.args.get('code')
    client = request.args.get('client')
    if not code or not client:
        return "Missing code or client parameter", 400

    # Replace these with your actual Flattrade credentials
    client_id = 'FZ03316'
    client_secret = '2024.4183871a75394a9ca4393c1e65e4193bb2dd2c8bdb121df3'
    redirect_uri = 'http://localhost:21000/flattrade?'

    token_url = 'https://authapi.flattrade.in/trade/apitoken'  # Example token endpoint

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get('access_token')
        # Store the access token securely for later use in API calls
        return "Login successful! You can close this window."
    else:
        return f"Failed to get access token: {response.text}", 400
