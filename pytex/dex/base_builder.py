from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell


class Builder:
    def __init__(self):
        pass

    @staticmethod
    async def build_jetton_transfer_body(
        destination_address: str,
        amount: int,
        query_id: int = 0,
        response_address: str = None,
        custom_payload: TonSdkCell | None = None,
        forward_amount: int = 0,
        forward_payload: TonSdkCell | None = None,
    ) -> TonSdkCell:
        jetton_transfer_body: TonSdkCell = TonSdkCell()
        jetton_transfer_body.bits.write_uint(0xF8A7EA5, 32)  # request_transfer op
        jetton_transfer_body.bits.write_uint(query_id, 64)  # query_id
        jetton_transfer_body.bits.write_coins(amount)  # Swap amount
        jetton_transfer_body.bits.write_address(TonSdkAddress(destination_address))
        jetton_transfer_body.bits.write_address(
            TonSdkAddress(response_address or destination_address)
        )

        if custom_payload is None:
            jetton_transfer_body.bits.write_bit(0)  # null custom_payload
        else:
            jetton_transfer_body.bits.write_bit(1)
            jetton_transfer_body.refs.append(custom_payload)

        jetton_transfer_body.bits.write_grams(forward_amount)

        if forward_payload is None:
            jetton_transfer_body.bits.write_bit(0)  # null forward_payload
        else:
            jetton_transfer_body.bits.write_bit(1)
            jetton_transfer_body.refs.append(forward_payload)
        return jetton_transfer_body
