from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_builder import Builder


class StonfiBuilder(Builder):
    @staticmethod
    async def build_pton_transfer_body(
        ton_amount: int,
        query_id: int = 0,
        refund_address: str | None = None,
        forward_payload: TonSdkCell | None = None,
    ) -> TonSdkCell:
        pton_transfer_body: TonSdkCell = TonSdkCell()
        pton_transfer_body.bits.write_uint(0x01F3835D, 32)  # request_transfer op
        pton_transfer_body.bits.write_uint(query_id, 64)  # query_id
        pton_transfer_body.bits.write_coins(ton_amount)  # Swap amount

        pton_transfer_body.bits.write_address(TonSdkAddress(refund_address))
        # if refund_address is None:
        #     pton_transfer_body.bits.write_bit(0)  # null referral address
        # else:
        #     pton_transfer_body.bits.write_bit(1)
        #     pton_transfer_body.bits.write_address(TonSdkAddress(refund_address))

        if forward_payload is None:
            pton_transfer_body.bits.write_bit(0)  # null ton
        else:
            pton_transfer_body.bits.write_bit(1)
            pton_transfer_body.refs.append(forward_payload)
        return pton_transfer_body
