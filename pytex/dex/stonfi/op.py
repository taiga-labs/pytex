import base64
from decimal import Decimal

from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_operator import Operator
from pytex.exceptions import OperatorError
from pytex.units import Asset, AssetType, Reserve


class StonfiOperator(Operator):
    def __init__(self, toncenter_api_key: str):
        super().__init__(toncenter_api_key)

    async def get_wallet_jetton_master_address(self, address: str) -> TonSdkAddress:
        raw_get_pool_data = self.client.raw_run_method(
            method="get_wallet_data", address=address, stack_data=[]
        )

        raw_data = await self.run(to_run=raw_get_pool_data)
        if raw_data is None:
            raise OperatorError(f"run get_wallet_data")

        jeton_address_b64 = raw_data[0].get("stack")[2][1].get("bytes")
        cell = TonSdkCell.one_from_boc(base64.b64decode(jeton_address_b64))
        try:
            jetton_address = self._read_address(cell)
        except Exception as e:
            raise OperatorError(f"_read_address | raw_data: {raw_data} -> {e}")

        if (
            jetton_address.to_string(True, True, True)
            != "EQCM3B12QK1e4yZSf8GtBRT0aLMNyEsBc_DhVfRRtOEffLez"  # pTON stonfi jetton master:
        ):
            return jetton_address
        else:
            return TonSdkAddress(
                "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c"  # TON zero address
            )

    async def get_pool_reserves(self, pool_address: str) -> (Decimal, Decimal):
        asset0 = Asset(_type=AssetType.NATIVE)
        asset1 = Asset(_type=AssetType.NATIVE)

        raw_get_pool_data = self.client.raw_run_method(
            method="get_pool_data", address=pool_address, stack_data=[]
        )
        raw_data = await self.run(to_run=raw_get_pool_data)
        if raw_data is None:
            raise OperatorError(f"run get_wallet_data")
        try:
            reserve0 = int(raw_data[0].get("stack")[0][1], 16)
            reserve1 = int(raw_data[0].get("stack")[1][1], 16)
        except Exception as e:
            raise OperatorError(f"parse reserve | raw_data: {raw_data} -> {e}")

        try:
            b64_bytes_str = raw_data[0].get("stack")[2][1].get("bytes")
            token0_governed_address: TonSdkAddress = self._read_address(
                TonSdkCell.one_from_boc(base64.b64decode(b64_bytes_str))
            )

            b64_bytes_str = raw_data[0].get("stack")[3][1].get("bytes")
            token1_governed_address: TonSdkAddress = self._read_address(
                TonSdkCell.one_from_boc(base64.b64decode(b64_bytes_str))
            )
        except Exception as e:
            raise OperatorError(f"_read_address | raw_data: {raw_data} -> {e}")

        token0_address = await self.get_wallet_jetton_master_address(
            address=token0_governed_address.to_string(True, True, True)
        )
        token1_address = await self.get_wallet_jetton_master_address(
            address=token1_governed_address.to_string(True, True, True)
        )
        if asset0.address.to_string(True, True, True) != token0_address.to_string(
            True, True, True
        ):
            asset0 = Asset(
                _type=AssetType.JETTON,
                address=token0_address.to_string(True, True, True),
            )

        if asset1.address.to_string(True, True, True) != token1_address.to_string(
            True, True, True
        ):
            asset1 = Asset(
                _type=AssetType.JETTON,
                address=token1_address.to_string(True, True, True),
            )

        return Reserve(asset=asset0, reserve=Decimal(reserve0)), Reserve(
            asset=asset1, reserve=Decimal(reserve1)
        )
