from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.stonfi.builder import StonfiBuilder


class StonfiV2Builder(StonfiBuilder):
    @staticmethod
    async def build_cross_swap_body(
        min_out: int,
        receiver_address: str,  # TODO can be None
        fwd_gas: int = 0,
        refund_fwd_gas: int = 0,
        ref_fee: int = 0,  # max 100 (%)
        custom_payload: TonSdkCell | None = None,
        refund_payload: TonSdkCell | None = None,
        referral_address: str | None = None,
    ):
        cross_swap_body = TonSdkCell()
        # cross_swap_body.bits.write_uint(min_out, 32)
        cross_swap_body.bits.write_coins(min_out)
        cross_swap_body.bits.write_address(TonSdkAddress(receiver_address))
        cross_swap_body.bits.write_coins(fwd_gas)

        if custom_payload is None:
            cross_swap_body.bits.write_bit(0)  # null custom_payload
        else:
            cross_swap_body.bits.write_bit(1)
            cross_swap_body.refs.append(custom_payload)

        cross_swap_body.bits.write_coins(refund_fwd_gas)

        if refund_payload is None:
            cross_swap_body.bits.write_bit(0)  # null custom_payload
        else:
            cross_swap_body.bits.write_bit(1)
            cross_swap_body.refs.append(refund_payload)

        cross_swap_body.bits.write_uint(min(100, max(ref_fee, 0)), 16)

        if referral_address is None:
            cross_swap_body.bits.write_address(None)  # null referral address
        else:
            cross_swap_body.bits.write_address(TonSdkAddress(referral_address))

        return cross_swap_body

    @staticmethod
    async def build_swap_body(
        ask_jetton_wallet_address: str,  # stonfi router jetton wallet address
        refund_address: str,
        excesses_address: str,
        cross_swap_body: TonSdkCell,
        deadline: int,
    ) -> TonSdkCell:
        swap_body: TonSdkCell = TonSdkCell()
        swap_body.bits.write_uint(0x6664DE2A, 32)  # swap op code
        swap_body.bits.write_address(TonSdkAddress(ask_jetton_wallet_address))
        swap_body.bits.write_address(TonSdkAddress(refund_address))
        swap_body.bits.write_address(TonSdkAddress(excesses_address))
        swap_body.bits.write_uint(deadline, 64)
        swap_body.refs.append(cross_swap_body)

        # if additional_data is None:
        #     swap_body.bits.write_bit(0)
        # else:
        #     swap_body.bits.write_bit(1)
        #     swap_body.bits.write_bit(additional_data)  # Reject payload

        return swap_body
