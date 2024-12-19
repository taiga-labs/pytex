import base64
from decimal import Decimal

from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_operator import Operator
from pytex.dex.stonfi.v1.constants import pTON_ADDRESS_V1
from pytex.dex.stonfi.v2.constants import pTON_ADDRESS_V2
from pytex.exceptions import OperatorError
from pytex.units import TON_ZERO_ADDRESS


class StonfiOperator(Operator):
    def __init__(self, toncenter_api_key: str):
        super().__init__(toncenter_api_key)

    async def get_wallet_jetton_master_address(self, address: str) -> TonSdkAddress:
        raw_get_pool_data = self.client.raw_run_method(
            method="get_wallet_data", address=address, stack_data=[]
        )

        raw_data = await self.run_ex(to_run=raw_get_pool_data)
        if raw_data is None:
            raise OperatorError(f"run get_wallet_data")

        jeton_address_b64 = raw_data[0].get("stack")[2][1].get("bytes")
        cell = TonSdkCell.one_from_boc(base64.b64decode(jeton_address_b64))
        try:
            jetton_address = self._read_address(cell)
        except Exception as e:
            raise OperatorError(f"_read_address | raw_data: {raw_data} -> {e}")

        if jetton_address.to_string(True, True, True) == pTON_ADDRESS_V1:
            return TonSdkAddress(TON_ZERO_ADDRESS)
        if jetton_address.to_string(True, True, True) == pTON_ADDRESS_V2:
            return TonSdkAddress(TON_ZERO_ADDRESS)
        return jetton_address
