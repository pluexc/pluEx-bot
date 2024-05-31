import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from web3 import Web3
import wallet
import kyc
import re
import sqlite3
import secrets
from datetime import datetime
import cryptocompare
import logging

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

MOD_ROLE_ID = 1243552926677340240
SUPPORT_CHANNEL_ID = 1242639972163653673
KYC_CHANNEL_ID = 1243553612005769288

# Ensure the environment variable is loaded
contract_address_str = os.getenv('PLUTOKEN_CONTRACT_ADDRESS')
if not contract_address_str or contract_address_str == '-':
    raise ValueError("PLUTOKEN_CONTRACT_ADDRESS environment variable not set")

# Web3 setup for Ethereum-based token transactions
w3 = Web3(Web3.HTTPProvider(os.getenv('ETH_NETWORK')))
contract_address = w3.to_checksum_address(contract_address_str)
with open('PluTokenABI.json', 'r') as abi_file:
    contract_abi = abi_file.read()
plutoken_contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Set CryptoCompare API Key
cryptocompare.cryptocompare._set_api_key_parameter(os.getenv('CRYPTOCOMPARE_API_KEY'))

# Define fees
XPLT_MAKER_FEE = 0.004  # 0.4%
XPLT_TAKER_FEE = 0.007  # 0.7%
OTHER_MAKER_FEE = 0.005  # 0.5%
OTHER_TAKER_FEE = 0.012  # 1.2%

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Messages dictionary for multi-language support
messages = {
    'en': {
        'missing_argument': "Error: Missing required argument: {}",
        'invalid_command': "Invalid command. Use !commands to see the list of available commands.",
        'already_registered': "You are already registered.",
        'not_registered': "You must be registered to perform this action.",
        'invalid_name': "Name must contain only letters and spaces.",
        'invalid_dob': "DOB must be in MM/DD/YYYY format.",
        'kyc_approved': "Your KYC is already approved. You can edit your KYC details once if needed.",
        'kyc_attempts_exceeded': "You have exceeded the maximum number of KYC attempts. Please contact support.",
        'kyc_attachment_required': "Please attach a .png or .jpg/.jpeg file with your KYC details.",
        'kyc_invalid_file_type': "Invalid file type. Please upload a .png or .jpg/.jpeg file.",
        'kyc_edited': "Your KYC details have been edited and submitted for approval.",
        'kyc_submitted': "Your KYC details have been submitted for approval.",
        'kyc_details': "Name: {}\nDOB: {}\nID Number: {} {}",
        'kyc_submission': "New KYC submission from {}.\n{}",
        'kyc_approved_msg': "Your KYC has been approved. You now have access to all privileges.",
        'kyc_rejected_msg': "Your KYC has been rejected. You have {} attempts left.",
        'kyc_resubmit': "You can now resubmit your KYC details using the !kyc command.",
        'contact_support': "Please contact support in {}.",
        'no_kyc_details': "You have not submitted any KYC details.",
        'kyc_details_info': "Name: {}\nDOB: {}\nID Number: {}\nStatus: {}\nAttempts Left: {}",
        'moderator_dashboard': "Moderator Dashboard",
        'all_kyc_submissions': "All KYC submissions:\n{}",
        'change_kyc_status': "Use !changekyc <user_id> <status> to change a user's KYC status.",
        'invalid_status': "Invalid status. Use 'Approved', 'Rejected', or 'Pending'.",
        'kyc_status_updated': "KYC status for user {} has been updated to {}.",
        'invalid_channel': "This command can only be used in the designated channel.",
        'payment_method_not_supported': "Payment method not supported.",
        'deposit_successful': "You have successfully deposited {} PluToken.",
        'sell_successful': "You have successfully sold {} PluToken. Transaction hash: {}",
        'buy_successful': "You have successfully bought {} PluToken. Transaction hash: {}",
        'request_tokens': "{} has requested {} PluToken from you. Account Number: {}",
        'request_sent': "Requested {} PluToken from {}. Account Number: {}",
        'send_tokens': "{} has sent you {} PluToken.",
        'send_successful': "Sent {} PluToken to {}.",
        'transfer_successful': "You have successfully transferred {} PluToken to address {}. Transaction hash: {}",
        'balance_info': "Your balance is {} PluToken.",
        'dashboard_info': "Dashboard:\nBalance: {} PluToken\nKYC Status: {}",
        'account_deleted': "Your account has been deleted. You will need to register and submit KYC again to use the dashboard and other services.",
        'token_price': "The current price of PluToken is {} ETH.",
        'cashapp_payment': "Please send {} USD to {} and provide the receipt here.",
        'unsupported_crypto': "Currently, only Ethereum-based tokens are supported.",
        'buy_crypto_successful': "You have successfully bought {} {}. Transaction hash: {}",
        'withdraw_successful_usd': "You have successfully withdrawn {} USD.",
        'withdraw_successful_rub': "You have successfully withdrawn {} RUB via Tinkoff Pay."
    },
    'ru': {
        'missing_argument': "Ошибка: отсутствует обязательный аргумент: {}",
        'invalid_command': "Недопустимая команда. Используйте !commands, чтобы увидеть список доступных команд.",
        'already_registered': "Вы уже зарегистрированы.",
        'not_registered': "Вы должны быть зарегистрированы, чтобы выполнить это действие.",
        'invalid_name': "Имя должно содержать только буквы и пробелы.",
        'invalid_dob': "Дата рождения должна быть в формате ММ/ДД/ГГГГ.",
        'kyc_approved': "Ваша KYC уже одобрена. Вы можете изменить свои данные KYC один раз при необходимости.",
        'kyc_attempts_exceeded': "Вы превысили максимальное количество попыток KYC. Пожалуйста, свяжитесь с поддержкой.",
        'kyc_attachment_required': "Пожалуйста, прикрепите файл .png или .jpg/.jpeg с вашими данными KYC.",
        'kyc_invalid_file_type': "Неправильный тип файла. Пожалуйста, загрузите файл .png или .jpg/.jpeg.",
        'kyc_edited': "Ваши данные KYC были изменены и отправлены на одобрение.",
        'kyc_submitted': "Ваши данные KYC были отправлены на одобрение.",
        'kyc_details': "Имя: {}\nДата рождения: {}\нНомер ID: {} {}",
        'kyc_submission': "Новая заявка KYC от {}.\н{}",
        'kyc_approved_msg': "Ваша KYC была одобрена. Теперь у вас есть доступ ко всем привилегиям.",
        'kyc_rejected_msg': "Ваша KYC была отклонена. У вас осталось {} попыток.",
        'kyc_resubmit': "Теперь вы можете повторно отправить свои данные KYC, используя команду !kyc.",
        'contact_support': "Пожалуйста, свяжитесь с поддержкой в {}.",
        'no_kyc_details': "Вы не отправили никаких данных KYC.",
        'kyc_details_info': "Имя: {}\nДата рождения: {}\нНомер ID: {}\нСтатус: {}\нОсталось попыток: {}",
        'moderator_dashboard': "Панель модератора",
        'all_kyc_submissions': "Все заявки KYC:\н{}",
        'change_kyc_status': "Используйте !changekyc <user_id> <status>, чтобы изменить статус KYC пользователя.",
        'invalid_status': "Недопустимый статус. Используйте 'Approved', 'Rejected' или 'Pending'.",
        'kyc_status_updated': "Статус KYC для пользователя {} был обновлен на {}.",
        'invalid_channel': "Эту команду можно использовать только в указанном канале.",
        'payment_method_not_supported': "Способ оплаты не поддерживается.",
        'deposit_successful': "Вы успешно внесли {} PluToken.",
        'sell_successful': "Вы успешно продали {} PluToken. Хэш транзакции: {}",
        'buy_successful': "Вы успешно купили {} PluToken. Хэш транзакции: {}",
        'request_tokens': "{} запрашивает у вас {} PluToken. Номер счета: {}",
        'request_sent': "Запрошено {} PluToken у {}. Номер счета: {}",
        'send_tokens': "{} отправил вам {} PluToken.",
        'send_successful': "Отправлено {} PluToken {}.",
        'transfer_successful': "Вы успешно перевели {} PluToken на адрес {}. Хэш транзакции: {}",
        'balance_info': "Ваш баланс составляет {} PluToken.",
        'dashboard_info': "Панель управления:\нБаланс: {} PluToken\nСтатус KYC: {}",
        'account_deleted': "Ваш аккаунт был удален. Вам нужно будет зарегистрироваться и отправить KYC снова, чтобы использовать панель управления и другие услуги.",
        'token_price': "Текущая цена PluToken составляет {} ETH.",
        'cashapp_payment': "Пожалуйста, отправьте {} USD на {} и предоставьте квитанцию здесь.",
        'unsupported_crypto': "В настоящее время поддерживаются только токены на основе Ethereum.",
        'buy_crypto_successful': "Вы успешно купили {} {}. Хэш транзакции: {}",
        'withdraw_successful_usd': "Вы успешно вывели {} USD.",
        'withdraw_successful_rub': "Вы успешно вывели {} RUB через Tinkoff Pay."
    }
}


def transfer_tokens(sender_private_key, recipient_address, amount):
    try:
        # Fetch the current gas price from the network
        gas_price = w3.eth.gasPrice  # Gets the current gas price in Wei
        # Estimate gas limit for the transaction
        gas_estimate = w3.eth.estimateGas({
            'to': recipient_address,
            'value': amount,
            'from': w3.eth.account.privateKeyToAccount(sender_private_key).address
        })

        # Create a transaction
        tx = {
            'to': recipient_address,
            'value': amount,
            'gas': gas_estimate,
            'gasPrice': gas_price,
            'nonce': w3.eth.getTransactionCount(w3.eth.account.privateKeyToAccount(sender_private_key).address),
            'chainId': 1
        }
        signed_tx = w3.eth.account.signTransaction(tx, sender_private_key)
        tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return tx_hash.hex()
    except Exception as e:
        logger.error(f"Error in transfer_tokens: {str(e)}")
        return str(e)


def generate_wallet():
    account = w3.eth.account.create()
    return account.address, account.privateKey.hex()


def store_user_info(user_id, email, password, address, private_key, recovery_code, language):
    conn = sqlite3.connect('migrations/users.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        email TEXT,
        password TEXT,
        address TEXT,
        private_key TEXT,
        recovery_code TEXT,
        language TEXT
    )
    ''')
    c.execute('''
    INSERT INTO users (user_id, email, password, address, private_key, recovery_code, language)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, email, password, address, private_key, recovery_code, language))
    conn.commit()
    conn.close()


def get_user_info(user_id):
    conn = sqlite3.connect('migrations/users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user_info = c.fetchone()
    conn.close()
    return user_info


def store_pending_purchase(user_id, amount, crypto, total_price, method, payment_link):
    conn = sqlite3.connect('migrations/users.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS pending_purchases (
        user_id TEXT,
        amount REAL,
        crypto TEXT,
        total_price REAL,
        method TEXT,
        payment_link TEXT,
        status TEXT DEFAULT 'pending'
    )
    ''')
    c.execute('''
    INSERT INTO pending_purchases (user_id, amount, crypto, total_price, method, payment_link)
    VALUES (?, ?, ?, ?, ?, ?, 'pending')
    ''', (user_id, amount, crypto, total_price, method, payment_link))
    conn.commit()
    conn.close()


# Payment link creation functions
def create_cashapp_payment_link(amount_usd):
    return f"https://cash.app/{os.getenv('CASHAPP_APP_ID')}/pay/{amount_usd}"


def create_stripe_payment_link(amount_usd):
    return f"https://checkout.stripe.com/pay/{amount_usd}"


def create_paypal_payment_link(amount_usd):
    return f"https://paypal.me/{os.getenv('PAYPAL_ID')}/{amount_usd}"


# Verify payment function
def verify_payment(payment_method, payment_link):
    # Implement the actual verification logic with respective payment provider APIs
    # For example, use webhook data to verify the payment status
    return True  # Placeholder, should return actual verification status


# Calculate total price function
def calculate_total_price(amount, crypto, is_xplt):
    crypto_price = get_crypto_price(crypto)
    if is_xplt:
        fee = amount * XPLT_TAKER_FEE
    else:
        fee = amount * OTHER_TAKER_FEE
    total_price = (amount / crypto_price) + fee
    return total_price


# Example get_crypto_price function
def get_crypto_price(crypto):
    price = cryptocompare.get_price(crypto, currency='USD')
    if price and crypto in price:
        return price[crypto]['USD']
    raise ValueError(f"Unable to fetch price for {crypto}")


@bot.command(name='register')
async def register(ctx, email: str, password: str):
    user_id = str(ctx.author.id)
    if get_user_info(user_id):
        await ctx.author.send(messages['en']['already_registered'])
        return

    address, private_key = generate_wallet()
    recovery_code = secrets.token_hex(16)
    language = 'en'  # Default to English; later ask user for preferred language
    store_user_info(user_id, email, password, address, private_key, recovery_code, language)
    await ctx.author.send(f"You have successfully registered. Your wallet address is {address}.")


@bot.command(name='kyc')
async def kyc_command(ctx, name: str, dob: str, id_number: str):
    user_id = str(ctx.author.id)
    if not get_user_info(user_id):
        await ctx.author.send(messages['en']['not_registered'])
        return

    if not re.match("^[A-Za-z ]+$", name):
        await ctx.author.send(messages['en']['invalid_name'])
        return

    try:
        datetime.strptime(dob, '%m/%d/%Y')
    except ValueError:
        await ctx.author.send(messages['en']['invalid_dob'])
        return

    if kyc.get_kyc_status(user_id) == 'Approved':
        await ctx.author.send(messages['en']['kyc_approved'])
        return

    if kyc.get_attempts(user_id) >= 3:
        await ctx.author.send(messages['en']['kyc_attempts_exceeded'])
        return

    if not ctx.message.attachments:
        await ctx.author.send(messages['en']['kyc_attachment_required'])
        return

    attachment = ctx.message.attachments[0]
    if not any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
        await ctx.author.send(messages['en']['kyc_invalid_file_type'])
        return

    os.makedirs('kyc_files', exist_ok=True)
    file_path = f'kyc_files/{ctx.author.id}_{attachment.filename}'
    await attachment.save(file_path)

    store_result = kyc.store_kyc_info(user_id, name, dob, id_number, file_path)
    if store_result == 'exceeded_attempts':
        await ctx.author.send(messages['en']['kyc_attempts_exceeded'])
    elif store_result == 'edit_limit_exceeded':
        await ctx.author.send(messages['en']['kyc_approved'])
    elif store_result == 'edited':
        await ctx.author.send(messages['en']['kyc_edited'])
        channel = bot.get_channel(KYC_CHANNEL_ID)
        kyc_details = messages['en']['kyc_details'].format(name, dob, id_number, "(Edited)")
        await channel.send(messages['en']['kyc_submission'].format(ctx.author.mention, kyc_details),
                           file=discord.File(file_path), view=KYCReviewView(user_id, kyc_details, file_path))
    else:
        await ctx.author.send(messages['en']['kyc_submitted'])
        channel = bot.get_channel(KYC_CHANNEL_ID)
        kyc_details = messages['en']['kyc_details'].format(name, dob, id_number, "")
        await channel.send(messages['en']['kyc_submission'].format(ctx.author.mention, kyc_details),
                           file=discord.File(file_path), view=KYCReviewView(user_id, kyc_details, file_path))


class KYCReviewView(discord.ui.View):
    def __init__(self, user_id, kyc_details, file_path):
        super().__init__(timeout=None)  # Ensure the view does not timeout
        self.user_id = user_id
        self.kyc_details = kyc_details
        self.file_path = file_path

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        kyc.approve_kyc(self.user_id)
        user = await bot.fetch_user(self.user_id)
        user_info = get_user_info(self.user_id)
        await user.send(messages[user_info[-1]]['kyc_approved_msg'])
        await interaction.message.edit(
            content=messages[user_info[-1]]['kyc_submission'].format(user.mention, self.kyc_details), view=None)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        kyc.reject_kyc(self.user_id)
        user = await bot.fetch_user(self.user_id)
        attempts_left = 3 - kyc.get_attempts(self.user_id)
        user_info = get_user_info(self.user_id)
        await user.send(messages[user_info[-1]]['kyc_rejected_msg'].format(attempts_left))
        await interaction.message.edit(
            content=messages[user_info[-1]]['kyc_submission'].format(user.mention, self.kyc_details), view=None)


class KYCEditView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)  # Ensure the view does not timeout
        self.user_id = user_id

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_info = get_user_info(self.user_id)
        await interaction.user.send(messages[user_info[-1]]['kyc_resubmit'])


class ContactSupportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Contact Support", style=discord.ButtonStyle.link)
    async def contact_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        support_channel = bot.get_channel(SUPPORT_CHANNEL_ID)
        user_info = get_user_info(interaction.user.id)
        await interaction.user.send(messages[user_info[-1]]['contact_support'].format(support_channel.mention))


@bot.command(name='mykyc')
async def mykyc(ctx):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    kyc_info = kyc.get_kyc_info(user_id)
    if not kyc_info:
        await ctx.author.send(messages[user_info[-1]]['no_kyc_details'])
        return

    kyc_status = kyc_info[5]
    attempts_left = 3 - kyc.get_attempts(user_id)
    kyc_details = messages[user_info[-1]]['kyc_details_info'].format(kyc_info[1], kyc_info[2], kyc_info[3], kyc_status,
                                                                     attempts_left)
    if kyc_status == 'Approved' and kyc_info[6] < 1:
        await ctx.author.send(kyc_details, view=KYCEditView(user_id))
    elif attempts_left <= 0:
        await ctx.author.send(kyc_details, view=ContactSupportView())
    else:
        await ctx.author.send(kyc_details)


@bot.command(name='moddashboard')
@commands.has_role(MOD_ROLE_ID)
async def moddashboard(ctx):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    await ctx.author.send(messages[user_info[-1]]['moderator_dashboard'], view=ModeratorDashboardView())


class ModeratorDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="View All KYCs", style=discord.ButtonStyle.secondary)
    async def view_all_kycs(self, interaction: discord.Interaction, button: discord.ui.Button):
        kycs = kyc.get_all_kycs()
        kyc_list = "\n".join([f"{kyc[0]}: {kyc[1]} ({kyc[5]})" for kyc in kycs])
        user_info = get_user_info(interaction.user.id)
        await interaction.user.send(messages[user_info[-1]]['all_kyc_submissions'].format(kyc_list))

    @discord.ui.button(label="Change User KYC Status", style=discord.ButtonStyle.secondary)
    async def change_user_kyc_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_info = get_user_info(interaction.user.id)
        await interaction.user.send(messages[user_info[-1]]['change_kyc_status'])


@bot.command(name='changekyc')
@commands.has_role(MOD_ROLE_ID)
async def changekyc(ctx, user_id: str, status: str):
    user_info = get_user_info(user_id)
    if status not in ['Approved', 'Rejected', 'Pending']:
        await ctx.author.send(messages[user_info[-1]]['invalid_status'])
        return

    kyc.update_kyc_status(user_id, status)
    await ctx.author.send(messages[user_info[-1]]['kyc_status_updated'].format(user_id, status))


@bot.command(name='deposit')
async def deposit(ctx, amount: float, payment_method: str):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    if payment_method not in ["cashapp", "tinkoff"]:
        await ctx.author.send(messages[user_info[-1]]['payment_method_not_supported'])
        return

    total_price = calculate_total_price(amount, 'xplt', True)
    if payment_method == 'cashapp':
        payment_link = create_cashapp_payment_link(total_price)
    elif payment_method == 'tinkoff':
        payment_link = "Tinkoff Pay link"  # Replace with actual Tinkoff Pay link generation

    await ctx.author.send(f"Please complete the payment using the following link: {payment_link}")

    store_pending_purchase(user_id, amount, 'xplt', total_price, payment_method, payment_link)


@bot.command(name='sell')
async def sell(ctx, amount: float, currency: str):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    if not user_info:
        await ctx.author.send(messages[user_info[-1]]['not_registered'])
        return

    if currency.lower() not in ["usd", "rub"]:
        await ctx.author.send(messages[user_info[-1]]['invalid_currency'])
        return

    if currency.lower() == 'usd':
        fee = amount * XPLT_TAKER_FEE
        net_amount = amount - fee
        await ctx.author.send(f"Withdrawing {amount} USD with a fee of {fee} USD. You will receive {net_amount} USD.")
        await ctx.author.send(messages[user_info[-1]]['withdraw_successful_usd'].format(net_amount))
    elif currency.lower() == 'rub':
        fee = amount * OTHER_TAKER_FEE
        net_amount = amount - fee
        await ctx.author.send(f"Withdrawing {amount} RUB with a fee of {fee} RUB. You will receive {net_amount} RUB.")
        await ctx.author.send(messages[user_info[-1]]['withdraw_successful_rub'].format(net_amount))

    wallet.update_user_balance(user_id, -amount, 'Successful')
    await ctx.message.delete()


@bot.command(name='request')
async def request(ctx, amount: float, user: discord.User):
    user_id = str(ctx.author.id)
    recipient_id = str(user.id)
    user_info = get_user_info(user_id)
    recipient_info = get_user_info(recipient_id)
    if not user_info or not recipient_info:
        await ctx.author.send(messages[user_info[-1]]['not_registered'])
        return

    sender_account = user_info[3]
    recipient_account = recipient_info[3]
    await user.send(messages[recipient_info[-1]]['request_tokens'].format(ctx.author.mention, amount, sender_account))
    await ctx.author.send(messages[user_info[-1]]['request_sent'].format(amount, user.mention, recipient_account))


@bot.command(name='send')
async def send(ctx, amount: float, user: discord.User):
    user_id = str(ctx.author.id)
    recipient_id = str(user.id)
    user_info = get_user_info(user_id)
    recipient_info = get_user_info(recipient_id)
    if not user_info or not recipient_info:
        await ctx.author.send(messages[user_info[-1]]['not_registered'])
        return

    sender_account = user_info[3]
    recipient_account = recipient_info[3]
    wallet.update_user_balance(user_id, -amount, 'Successful')
    wallet.update_user_balance(recipient_id, amount, 'Successful')
    await user.send(messages[recipient_info[-1]]['send_tokens'].format(ctx.author.mention, amount))
    await ctx.author.send(messages[user_info[-1]]['send_successful'].format(amount, user.mention))


@bot.command(name='transfer')
async def transfer(ctx, amount: float, address: str):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    amount_in_wei = Web3.toWei(amount, 'ether')
    tx_hash = transfer_tokens(user_info[4], address, amount_in_wei)
    await ctx.author.send(messages[user_info[-1]]['transfer_successful'].format(amount, address, tx_hash))


@bot.command(name='balance')
async def balance(ctx):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    balance = wallet.get_balance(user_id)
    await ctx.author.send(messages[user_info[-1]]['balance_info'].format(balance))


@bot.command(name='dashboard')
async def dashboard(ctx):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    if not user_info:
        await ctx.author.send(messages['en']['not_registered'])
        return
    if kyc.get_kyc_status(user_id) != 'Approved':
        await ctx.author.send(messages[user_info[-1]]['kyc_submitted'])
        return
    balance = wallet.get_balance(user_id)
    await ctx.author.send(messages[user_info[-1]]['dashboard_info'].format(balance, kyc.get_kyc_status(user_id)))


@bot.command(name='accdelete')
async def accdelete(ctx):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    kyc.reset_kyc(user_id)
    conn = sqlite3.connect('migrations/users.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    await ctx.author.send(messages[user_info[-1]]['account_deleted'])


def get_token_price():
    total_supply = plutoken_contract.functions.totalSupply().call()
    price = w3.fromWei(plutoken_contract.functions.balanceOf(contract_address).call(), 'ether') / total_supply
    return price


@bot.command(name='price')
async def price(ctx):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    token_price = get_token_price()
    await ctx.author.send(messages[user_info[-1]]['token_price'].format(token_price))


@bot.command(name='buy')
async def buy(ctx, amount: float, crypto: str):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    if not user_info:
        await ctx.author.send(messages['en']['not_registered'])
        return

    is_xplt = crypto.lower() == 'xplt'
    total_price = calculate_total_price(amount, crypto, is_xplt)

    cashapp_link = create_cashapp_payment_link(total_price)
    stripe_link = create_stripe_payment_link(total_price)
    paypal_link = create_paypal_payment_link(total_price)

    await ctx.author.send(f"Quotes for buying {amount} {crypto.upper()}:\n"
                          f"CashApp: {cashapp_link}\n"
                          f"Stripe: {stripe_link}\n"
                          f"PayPal: {paypal_link}")

    store_pending_purchase(user_id, amount, crypto, total_price, 'cashapp', cashapp_link)
    store_pending_purchase(user_id, amount, crypto, total_price, 'stripe', stripe_link)
    store_pending_purchase(user_id, amount, crypto, total_price, 'paypal', paypal_link)


@bot.command(name='confirm_payment')
async def confirm_payment(ctx, payment_method: str):
    user_id = str(ctx.author.id)
    user_info = get_user_info(user_id)
    if not user_info:
        await ctx.author.send(messages['en']['not_registered'])
        return

    conn = sqlite3.connect('migrations/users.db')
    c = conn.cursor()
    c.execute('''
    SELECT * FROM pending_purchases WHERE user_id = ? AND method = ? AND status = 'pending'
    ''', (user_id, payment_method))
    pending_purchase = c.fetchone()
    conn.close()

    if not pending_purchase:
        await ctx.author.send("No pending purchases found or already confirmed.")
        return

    amount, crypto, total_price = pending_purchase[1], pending_purchase[2], pending_purchase[3]

    payment_verified = verify_payment(payment_method, pending_purchase[5])  # Verify payment

    @bot.command(name='confirm_payment')
    async def confirm_payment(ctx, payment_method: str):
        user_id = str(ctx.author.id)
        user_info = get_user_info(user_id)
        if not user_info:
            await ctx.author.send(messages['en']['not_registered'])
            return

        conn = sqlite3.connect('migrations/users.db')
        c = conn.cursor()
        c.execute('''
        SELECT * FROM pending_purchases WHERE user_id = ? AND method = ? AND status = 'pending'
        ''', (user_id, payment_method))
        pending_purchase = c.fetchone()
        conn.close()

        if not pending_purchase:
            await ctx.author.send("No pending purchases found or already confirmed.")
            return

        amount, crypto, total_price = pending_purchase[1], pending_purchase[2], pending_purchase[3]

        payment_verified = verify_payment(payment_method, pending_purchase[5])  # Verify payment

        if payment_verified:
            wallet.update_user_balance(user_id, amount, 'Successful')
            conn = sqlite3.connect('migrations/users.db')
            c = conn.cursor()
            c.execute("UPDATE pending_purchases SET status = 'confirmed' WHERE user_id = ? AND method = ?",
                      (user_id, payment_method))
            conn.commit()
            conn.close()
            await ctx.author.send(f"Payment confirmed. Your balance has been updated with {amount} {crypto}.")
        else:
            await ctx.author.send("Payment verification failed. Please try again or contact support.")

    @bot.command(name='withdraw')
    async def withdraw(ctx, amount: float, currency: str):
        user_id = str(ctx.author.id)
        user_info = get_user_info(user_id)
        if not user_info:
            await ctx.author.send(messages['en']['not_registered'])
            return

        if currency.lower() not in ["usd", "rub"]:
            await ctx.author.send("Invalid currency. Only 'usd' and 'rub' are supported.")
            return

        balance = wallet.get_balance(user_id)
        if balance < amount:
            await ctx.author.send("Insufficient balance.")
            return

        if currency.lower() == 'usd':
            fee = amount * OTHER_TAKER_FEE
            net_amount = amount - fee
            await ctx.author.send(
                f"Withdrawing {amount} USD with a fee of {fee} USD. You will receive {net_amount} USD.")
            await ctx.author.send(messages[user_info[-1]]['withdraw_successful_usd'].format(net_amount))
        elif currency.lower() == 'rub':
            fee = amount * OTHER_TAKER_FEE
            net_amount = amount - fee
            await ctx.author.send(
                f"Withdrawing {amount} RUB with a fee of {fee} RUB. You will receive {net_amount} RUB.")
            await ctx.author.send(messages[user_info[-1]]['withdraw_successful_rub'].format(net_amount))

        wallet.update_user_balance(user_id, -amount, 'Successful')

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user.name}')
        print(f'Bot is ready.')

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(messages['en']['missing_argument'].format(error.param.name))
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(messages['en']['invalid_command'])
        else:
            raise error

    @bot.command(name='commands')
    async def commands_list(ctx):
        user_id = str(ctx.author.id)
        user_info = get_user_info(user_id)
        if user_info:
            lang = user_info[-1]
        else:
            lang = 'en'
        commands = """
        !commands - Show this message
        !register <email> <password> - Register an account
        !kyc <name> <dob> <id_number> - Submit KYC
        !deposit <amount> <payment_method> - Deposit money
        !sell <amount> <currency> - Sell PluToken
        !request <amount> <user> - Request PluToken from another user
        !send <amount> <user> - Send PluToken to another user
        !transfer <amount> <address> - Transfer PluToken to MetaMask
        !balance - Check your PluToken balance
        !dashboard - View your dashboard
        !price - Check PluToken price
        !mykyc - View your KYC status
        !moddashboard - Moderator dashboard
        !accdelete - Delete your account
        !confirm_payment <payment_method> - Confirm payment
        !withdraw <amount> <currency> - Withdraw funds
        """
        await ctx.send(commands)

    bot.run(os.getenv('DISCORD_TOKEN'))


