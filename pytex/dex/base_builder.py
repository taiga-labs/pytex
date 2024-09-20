from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell


class Builder:
    def __init__(self):
        pass

    @staticmethod
    async def build_transfer_body(
        offer_amount: int,
        to_address: str,
        response_address: str = None,
        forward_amount: int = 0,
        forward_payload: TonSdkCell = None,
        query_id: int = 0,
    ) -> TonSdkCell:
        jetton_transfer_body: TonSdkCell = TonSdkCell()
        jetton_transfer_body.bits.write_uint(0xF8A7EA5, 32)  # request_transfer op
        jetton_transfer_body.bits.write_uint(query_id, 64)  # query_id
        jetton_transfer_body.bits.write_coins(offer_amount)
        jetton_transfer_body.bits.write_address(TonSdkAddress(to_address))
        jetton_transfer_body.bits.write_address(
            TonSdkAddress(response_address or to_address)
        )
        jetton_transfer_body.bits.write_bit(0)  # null custom_payload
        jetton_transfer_body.bits.write_grams(forward_amount)
        if forward_payload is None:
            jetton_transfer_body.bits.write_bit(
                0
            )  # forward_payload in this slice, not separate cell
        else:
            jetton_transfer_body.bits.write_bit(1)
            jetton_transfer_body.refs.append(forward_payload)
        return jetton_transfer_body
