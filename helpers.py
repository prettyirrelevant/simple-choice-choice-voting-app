from algosdk import account, mnemonic
from algosdk.encoding import is_valid_address
from algosdk.future.transaction import AssetTransferTxn, PaymentTxn

CHOICE_ASSET_ID = 21364625


def validate_escrow_wallet(address: str, _mnemonic: str, client) -> bool:
    """Validate an escrow wallet and check it has sufficient funds and is opted in to Choice Coin."""
    if not is_valid_address(address):
        return False

    # compare the address to the address gotten from the mnemonic
    if account.address_from_private_key(mnemonic.to_private_key(_mnemonic)) != address:
        return False

    if not contains_choice_coin(address, client):
        return False

    if get_balance(address, client) < 1000:
        return False

    return True


def get_balance(address: str, client):
    """Get the balance of a wallet."""
    account = client.account_info(address)
    return account["amount"]


def contains_choice_coin(address: str, client) -> bool:
    """Checks if the address is opted into Choice Coin."""
    account = client.account_info(address)
    contains_choice = False

    for asset in account["assets"]:
        if asset["asset-id"] == asset:
            contains_choice = True
            break

    return contains_choice


def create_option_account(escrow_private_key: str, escrow_address: str, client) -> str:
    """Creates an account for option."""

    # This is the amount of Algo to fund the account with. The unit is microAlgos.
    AMOUNT = 1000000
    private_key, address = account.generate_account()

    is_successful = fund_address(AMOUNT, address, escrow_address, escrow_private_key, client)
    if not is_successful:
        raise Exception("Funding Failed!")

    is_optin_successful = opt_in_to_choice(private_key, address, client)
    if not is_optin_successful:
        raise Exception("Choice Coin Opt In Failed!")

    return address


def fund_address(
    amount: int, recipient_address: str, escrow_address: str, escrow_private_key: str, client
) -> bool:
    """Fund an account with Algo."""
    suggested_params = client.suggested_params()
    unsigned_transaction = PaymentTxn(
        escrow_address,
        suggested_params,
        recipient_address,
        amount,
        note="Initial Funding for Decision Creation",
    )
    signed_transaction = unsigned_transaction.sign(escrow_private_key)
    transaction_id = client.send_transaction(signed_transaction)

    return True


def opt_in_to_choice(private_key: str, address: str, client) -> bool:
    """Opt in a wallet to Choice Coin."""

    suggested_params = client.suggested_params()
    if not contains_choice_coin(address):
        unsigned_transaction = AssetTransferTxn(
            address, suggested_params, address, 0, CHOICE_ASSET_ID
        )
        signed_transaction = unsigned_transaction.sign(private_key)
        transaction_id = client.send_transaction(signed_transaction)

    return True


def vote(escrow_private_key, escrow_address, option_zero_address, option_one_address, client):
    """Places a vote based on the input of the user."""
    voter = int(input("Vote 0 for zero and vote 1 for one:"))
    if voter == 1:
        make_vote(
            escrow_address,
            escrow_private_key,
            option_one_address,
            100,
            "Voting Powered by Choice Coin.",
            client,
        )
        print("Thanks for voting for one.")
    else:
        make_vote(
            escrow_address,
            escrow_private_key,
            option_zero_address,
            100,
            "Voting Powered by Choice Coin.",
            client,
        )
        print("Thanks for voting for zero.")


def make_vote(sender, key, receiver, amount, comment, client):
    """Sends the transaction"""
    parameters = client.suggested_params()
    transaction = AssetTransferTxn(
        sender, parameters, receiver, amount, CHOICE_ASSET_ID, note=comment
    )

    signature = transaction.sign(key)
    client.send_transaction(signature)

    txn_id = transaction.get_txid()
    return txn_id


def calculate_votes(addresses: list, client):
    """Calculate the result of a voting process."""
    results = []
    for addr in addresses:
        account_info = client.account_info(addr)
        assets = account_info.get("assets")

        for _asset in assets:
            if _asset["asset-id"] == CHOICE_ASSET_ID:
                amount = _asset.get("amount")
                results.append(amount)

    return results


def winner(option_zero_count, option_one_count):
    """Selects a winner based on the result."""
    if option_zero_count > option_one_count:
        print("Option zero wins.")
    else:
        print("Option one wins.")
