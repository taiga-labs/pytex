from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_builder import Builder


class StonfiBuilder(Builder):
    @staticmethod
    async def build_swap_body(
        wallet_address: str,
        min_ask_amount: int,
        ask_jetton_wallet_address: str,  # stonfi router jetton wallet address
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

    @staticmethod
    def build_transfer_body(
        destination: str,  # STONFI_ROUTER_ADDRESS
        amount: int,  # swap ton amount
        query_id: int = 0,
        response_address: str | None = None,
        custom_payload: TonSdkCell | None = None,
        forward_amount: int = 0,  # msg ton amount(with fee(ex: 0.2 - 0.1 = 0.1)) - 0.1
        forward_payload: TonSdkCell | None = None,
    ) -> TonSdkCell:
        transfer_payload_cell: TonSdkCell = TonSdkCell()
        transfer_payload_cell.bits.write_uint(0xF8A7EA5, 32)
        transfer_payload_cell.bits.write_uint(query_id, 64)
        transfer_payload_cell.bits.write_coins(amount)  # Swap amount
        transfer_payload_cell.bits.write_address(TonSdkAddress(destination))
        if response_address is None:
            transfer_payload_cell.bits.write_address(None)
        else:
            transfer_payload_cell.bits.write_address(TonSdkAddress(response_address))

        if custom_payload is None:
            transfer_payload_cell.bits.write_bit(0)  # null custom_payload
        else:
            transfer_payload_cell.bits.write_bit(1)
            transfer_payload_cell.refs.append(custom_payload)

        transfer_payload_cell.bits.write_grams(forward_amount)

        if forward_payload is None:
            transfer_payload_cell.bits.write_bit(0)  # null forward_payload
        else:
            transfer_payload_cell.bits.write_bit(1)
            transfer_payload_cell.refs.append(forward_payload)

        return transfer_payload_cell
