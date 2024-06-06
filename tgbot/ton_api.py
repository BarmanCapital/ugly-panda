from base64 import urlsafe_b64encode
from pytoniq_core import begin_cell

from pytonapi import AsyncTonapi
from tonsdk import boc   # tonsdk.boc.begin_cell 和 pytoniq_core.begin_cell 不一样，得分开处理
from tonsdk.utils import bytes_to_b64str, to_nano
from tonsdk.contract.wallet import Wallets, WalletVersionEnum

from uglypanda.settings import TON_API_KEY, TON_DEFAULT_ADDRESS, TON_MNEMONICS


async def send_ton(amount, dest_address=TON_DEFAULT_ADDRESS, comment="Withdraw @ Ugly Panda"):
    if amount > 10:
        print("[send_ton] amount > 10")
        return
    
    print("[send_ton] %s -> %s" % (amount, dest_address))
    
    # Initialize AsyncTonapi with the provided API key and set it to use the testnet or mainnet
    tonapi = AsyncTonapi(api_key=TON_API_KEY)  # is_testnet=True

    # Create a wallet from the provided mnemonics
    mnemonics_list = TON_MNEMONICS.split(" ")
    _mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(
        mnemonics_list,
        WalletVersionEnum.v4r2,  # Set the version of the wallet
        0,
    )

    # Get the sequence number of the wallet's current state
    method_result = await tonapi.blockchain.execute_get_method(
        wallet.address.to_string(False), "seqno"
    )
    seqno = int(method_result.decoded.get("state", 0))

    # Prepare a transfer message to the destination address with the specified amount and sequence number
    transfer_amount = to_nano(amount, 'ton')

    # Create the comment payload
    payload = boc.begin_cell().store_uint(0, 32).store_string(comment).end_cell()

    query = wallet.create_transfer_message(
        to_addr=dest_address,
        amount=transfer_amount,
        payload=payload,
        seqno=seqno,
    )

    # Convert the message to Base64 and send it through the Tonapi blockchain
    message_boc = bytes_to_b64str(query["message"].to_boc(False))
    data = {'boc': message_boc}
    await tonapi.blockchain.send_message(data)


def get_comment_message(destination_address: str, amount: int, comment: str) -> dict:

    data = {
        'address': destination_address,
        'amount': str(amount),
        'payload': urlsafe_b64encode(
            begin_cell()
            .store_uint(0, 32)  # op code for comment message
            .store_string(comment)  # store comment
            .end_cell()  # end cell
            .to_boc()  # convert it to boc
        )
        .decode()  # encode it to urlsafe base64
    }

    return data
