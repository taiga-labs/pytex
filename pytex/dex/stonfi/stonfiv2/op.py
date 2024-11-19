import base64

from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.stonfi.op import StonfiOperator
from pytex.exceptions import OperatorError


class StonfiV2Operator(StonfiOperator):
    def __init__(self, toncenter_api_key: str):
        super().__init__(toncenter_api_key)

    async def get_router_address(self, pool_address: str) -> TonSdkAddress:
        raw_get_pool_data = self.client.raw_run_method(
            method="get_pool_data", address=pool_address, stack_data=[]
        )

        raw_data = await self.run(to_run=raw_get_pool_data)
        if raw_data is None:
            raise OperatorError(f"run get_wallet_data")

        jeton_address_b64 = raw_data[0].get("stack")[1][1].get("bytes")
        cell = TonSdkCell.one_from_boc(base64.b64decode(jeton_address_b64))
        try:
            jetton_address = self._read_address(cell)
        except Exception as e:
            raise OperatorError(
                f"_read_address | raw_data: {raw_data} -> {e}"
            )  # TODO stonfiv2 errors
        return jetton_address
