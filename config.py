import os
from dotenv import load_dotenv

load_dotenv()

ETH_NETWORK = 'https://mainnet.infura.io/v3/' + os.getenv('INFURA_PROJECT_ID')
PLUTOKEN_CONTRACT_ADDRESS = '-'  # Replace with your deployed contract address
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CASHAPP_APP_ID = os.getenv('CASHAPP_APP_ID')
CASHAPP_TOKEN = os.getenv('CASHAPP_TOKEN')

