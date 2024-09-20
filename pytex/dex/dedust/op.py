import base64
from decimal import Decimal

from tonsdk.utils import bytes_to_b64str
from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_operator import Operator
from pytex.exceptions import OperatorError
from pytex.units import Asset, PoolType, Reserve


class DedustOperator(Operator):
    DEDUST_MAINNET_FACTORY_ADDR = "EQBfBWT7X2BHg9tXAxzhz2aKiNTU1tpt5NsiK0uSDW_YAJ67"

    def __init__(self, toncenter_api_key: str):
        super().__init__(toncenter_api_key)

    async def get_vault_address(self, asset: Asset) -> str:
        request_stack = [["tvm.Slice", bytes_to_b64str(asset.cell.to_boc())]]
        raw_get_vault_address = self.client.raw_run_method(
            method="get_vault_address",
            address=self.DEDUST_MAINNET_FACTORY_ADDR,
            stack_data=request_stack,
        )
        raw_data = await self.run(to_run=raw_get_vault_address)
        if raw_data is None:
            raise OperatorError(f"run get_vault_address")

        try:
            b64_bytes_str = raw_data[0].get("stack")[0][1].get("bytes")
            vault_address: TonSdkAddress = self._read_address(
                TonSdkCell.one_from_boc(base64.b64decode(b64_bytes_str))
            )
        except Exception as e:
            raise OperatorError(f"parse address | raw_data: {raw_data} -> {e}")

        return vault_address.to_string(True, True, True)

    async def get_pool_address(
        self, asset0: Asset, asset1: Asset, pool_type: int = PoolType.VOLATILE
    ) -> str:
        request_stack = [
            ["num", int(pool_type)],
            ["tvm.Slice", bytes_to_b64str(asset0.cell.to_boc())],
            ["tvm.Slice", bytes_to_b64str(asset1.cell.to_boc())],
        ]
        raw_get_pool_address = self.client.raw_run_method(
            method="get_pool_address",
            address=self.DEDUST_MAINNET_FACTORY_ADDR,
            stack_data=request_stack,
        )
        raw_data = await self.run(to_run=raw_get_pool_address)
        if raw_data is None:
            raise OperatorError(f"run get_pool_address")

        try:
            b64_bytes_str = raw_data[0].get("stack")[0][1].get("bytes")
            pool_address: TonSdkAddress = self._read_address(
                TonSdkCell.one_from_boc(base64.b64decode(b64_bytes_str))
            )
        except Exception as e:
            raise OperatorError(f"_read_address | raw_data: {raw_data} -> {e}")

        return pool_address.to_string(True, True, True)

    async def get_pool_assets(self, pool_address: str) -> (Asset, Asset):
        raw_get_assets = self.client.raw_run_method(
            method="get_assets", address=pool_address, stack_data=[]
        )
        raw_data = await self.run(to_run=raw_get_assets)
        if raw_data is None:
            raise OperatorError(f"run get_assets")

        asset0_b64 = raw_data[0].get("stack")[0][1].get("bytes")
        cell = TonSdkCell.one_from_boc(base64.b64decode(asset0_b64))
        try:
            asset0 = self._read_asset(cell)
        except Exception as e:
            raise OperatorError(f"_read_asset | raw_data: {raw_data} -> {e}")

        asset1_b64 = raw_data[0].get("stack")[1][1].get("bytes")
        cell = TonSdkCell.one_from_boc(base64.b64decode(asset1_b64))
        try:
            asset1 = self._read_asset(cell)
        except Exception as e:
            raise OperatorError(f"_read_asset | raw_data: {raw_data} -> {e}")

        return asset0, asset1

    async def get_pool_reserves(self, pool_address: str) -> (Reserve, Reserve):
        asset0, asset1 = await self.get_pool_assets(pool_address=pool_address)

        raw_get_reserves = self.client.raw_run_method(
            method="get_reserves", address=pool_address, stack_data=[]
        )
        raw_data = await self.run(to_run=raw_get_reserves)
        if raw_data is None:
            raise OperatorError(f"run get_reserves")
        try:
            reserve0 = int(raw_data[0].get("stack")[0][1], 16)
            reserve1 = int(raw_data[0].get("stack")[1][1], 16)
        except Exception as e:
            raise OperatorError(f"parse reserve | raw_data: {raw_data} -> {e}")

        return Reserve(asset=asset0, reserve=Decimal(reserve0)), Reserve(
            asset=asset1, reserve=Decimal(reserve1)
        )
