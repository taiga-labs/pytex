from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.stonfi.builder import StonfiBuilder


class StonfiV1Builder(StonfiBuilder):
    @staticmethod
    async def build_swap_body(
        wallet_address: str,
        ask_jetton_wallet_address: str,  # stonfi router jetton wallet address
        min_ask_amount: int,
        referral_address: str | None = None,
    ) -> TonSdkCell:
        swap_body: TonSdkCell = TonSdkCell()
        swap_body.bits.write_uint(0x25938561, 32)  # swap op code
        swap_body.bits.write_address(TonSdkAddress(ask_jetton_wallet_address))
        swap_body.bits.write_coins(min_ask_amount)  # limit
        swap_body.bits.write_address(TonSdkAddress(wallet_address))  # Recipient address

        if referral_address is None:
            swap_body.bits.write_bit(0)  # null referral address
        else:
            swap_body.bits.write_bit(1)
            swap_body.bits.write_address(TonSdkAddress(referral_address))

        return swap_body
