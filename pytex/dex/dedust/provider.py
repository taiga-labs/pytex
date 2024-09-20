from decimal import Decimal

from tonsdk.boc import Cell

from pytex.dex.base_provider import Provider
from pytex.dex.dedust.builder import NativeDedustBuilder, JettonDedustBuilder
from pytex.dex.dedust.op import DedustOperator
from pytex.units import Asset, AssetType


class DedustProvider(Provider):
    DEDUST_NATIVE_VAULT = "EQDa4VOnTYlLvDJ0gZjNYm5PXfSmmtL6Vs6A_CZEtXCNICq_"

    class GAS:
        GAS_AMOUNT = 250000000
        FORWARD_GAS_AMOUNT = 50000000

    def __init__(self, mnemonic: list[str], toncenter_api_key: str):
        super().__init__(mnemonic=mnemonic, toncenter_api_key=toncenter_api_key)
        self.operator = DedustOperator(toncenter_api_key=toncenter_api_key)

    async def create_swap_ton_to_jetton_transfer_message(
        self,
        ask_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        offer_asset: Asset = Asset(_type=AssetType.NATIVE),
        referral_address: str | None = None,
    ) -> dict[str, Cell | str | int]:
        dd_native_builder = NativeDedustBuilder()
        swap_params = await dd_native_builder.build_swap_params(
            wallet_address=self.wallet_address,
            referral_address=referral_address,
        )

        pool_address = await self.operator.get_pool_address(
            asset0=ask_asset, asset1=offer_asset
        )

        swap_body = await dd_native_builder.build_swap_body(
            offer_amount=int(offer_amount),
            pools=[pool_address],
            forward_payload=swap_params,
            query_id=query_id,
        )
        return {
            "to_address": self.DEDUST_NATIVE_VAULT,
            "amount": int(offer_amount + self.GAS.GAS_AMOUNT),
            "payload": swap_body,
        }

    async def create_swap_jetton_to_jetton_transfer_message(
        self,
        ask_asset: Asset,
        offer_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        referral_address: str | None = None,
    ) -> dict[str, Cell | str | int]:
        dd_jetton_builder = JettonDedustBuilder()
        swap_params = await dd_jetton_builder.build_swap_params(
            wallet_address=self.wallet_address,
            referral_address=referral_address,
        )

        pool_address = await self.operator.get_pool_address(
            asset0=ask_asset, asset1=offer_asset
        )

        swap_body = await dd_jetton_builder.build_swap_body(
            pools=[pool_address], forward_payload=swap_params
        )

        jetton_vault_address = await self.operator.get_vault_address(asset=offer_asset)
        transfer_body = await dd_jetton_builder.build_transfer_body(
            offer_amount=int(offer_amount),
            to_address=jetton_vault_address,
            response_address=self.wallet_address,
            forward_amount=self.GAS.GAS_AMOUNT,
            forward_payload=swap_body,
            query_id=query_id,
        )
        jetton_wallet_address = await self.operator.get_jetton_wallet_address(
            jetton_master_address=offer_asset.address.to_string(True, True, True),
            wallet_address=self.wallet_address,
        )
        return {
            "to_address": jetton_wallet_address,
            "amount": self.GAS.FORWARD_GAS_AMOUNT + self.GAS.GAS_AMOUNT,
            "payload": transfer_body,
        }

    async def create_swap_jetton_to_ton_transfer_message(
        self,
        offer_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        ask_asset: Asset = Asset(_type=AssetType.NATIVE),
    ) -> dict[str, Cell | str | int]:
        return await self.create_swap_jetton_to_jetton_transfer_message(
            ask_asset=ask_asset,
            offer_asset=offer_asset,
            offer_amount=offer_amount,
            query_id=query_id,
        )
