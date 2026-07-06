There are 2 ways to check output :
1.on live website that has option to see using web terminal or ui
  https://aashsih-trading-bot.hf.space -> open this link to run directly on web which is hosted on Hugging face using public space via docker
  copy paste the above link directly

2.download this as zip and follow the below steps
  # 1. Install Python 3.11+ (from python.org — check "Add to PATH")
      After python is installed  run the below command to install libs
  #       pip install requests python-dotenv  <!-- this installs both request and python-dotenv -->
  #       requests
  #       python-dotenv

  # 2. Download the trading_bot folder to your desktop

  # 3. Create .env file with your Binance testnet keys
  #    (get them from https://testnet.binancefuture.com/)

  The current .env file have api keys inbuild and will be expired after 13-july-2026 after the key is expired u can create it from STEP 4
  #   BINANCE_TESTNET_API_KEY=your_api_key_here
  #   BINANCE_TESTNET_API_SECRET=your_api_secret_here

trading_bot/
## 📁 Project Structure

to run in terminal run python cli.py
to run in web(UI) run python dashboard.py

```
trading_bot/
├── dashboard.py          ← Web based UI
├── cli.py                ← Terminal based UI
├── requirements.txt      ← pip install this
├── .env                  ← your API keys ( shared ) can be expired after the time
├── bot/                  ← Actual code files
│   ├── client.py         
│   ├── portfolio.py      
│   |── logging_config.py
|   ├── orders.py         
│   └── validators.py 
└── ui/                   ← UI code for web
    ├── index.html        
    ├── style.css
    └── app.js
```
