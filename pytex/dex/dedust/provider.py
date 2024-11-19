from datetime import datetime
from decimal import Decimal

from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_provider import Provider
from pytex.dex.dedust.builder import NativeDedustBuilder, JettonDedustBuilder, SwapStep
from pytex.dex.dedust.op import DedustOperator
from pytex.units import Asset, AssetType


class DedustProvider(Provider):
    DEDUST_NATIVE_VAULT = "EQDa4VOnTYlLvDJ0gZjNYm5PXfSmmtL6Vs6A_CZEtXCNICq_"

    class GAS:
        GAS_AMOUNT = Decimal("300000000")
        FORWARD_GAS_AMOUNT = Decimal("250000000")

    def __init__(self, mnemonic: list[str], toncenter_api_key: str):
        super().__init__(mnemonic=mnemonic, toncenter_api_key=toncenter_api_key)
        self.operator = DedustOperator(toncenter_api_key=toncenter_api_key)

    async def create_swap_ton_to_jetton_transfer_message(
        self,
        ask_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        response_address: str = None,
        offer_asset: Asset = Asset(_type=AssetType.NATIVE),
        min_ask_amount: int = 0,
        gas_amount: Decimal = GAS.GAS_AMOUNT,
        referral_address: str = None,
        fulfill_payload: TonSdkCell | None = None,
        reject_payload: TonSdkCell | None = None,
        deadline: datetime | None = None,
    ) -> dict[str, TonSdkCell | str | int]:
        if not response_address:
            response_address = self.wallet_address

        dd_native_builder = NativeDedustBuilder()
        swap_params = await dd_native_builder.build_swap_params(
            response_address=response_address,
            referral_address=referral_address,
            fulfill_payload=fulfill_payload,
            reject_payload=reject_payload,
            deadline=0 if deadline is None else int(datetime.timestamp(deadline)),
        )

        pool_address = await self.operator.get_pool_address(
            asset0=ask_asset, asset1=offer_asset
        )

        swap_steps = [SwapStep(pool_address=pool_address, limit=min_ask_amount)]

        swap_body = await dd_native_builder.build_swap_body(
            offer_amount=int(offer_amount),
            swap_steps=swap_steps,
            forward_payload=swap_params,
            query_id=query_id,
        )
        return {
            "to_address": self.DEDUST_NATIVE_VAULT,
            "amount": int(offer_amount + gas_amount),
            "payload": swap_body,
        }

    async def create_swap_jetton_to_jetton_transfer_message(
        self,
        ask_asset: Asset,
        offer_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        response_address: str = None,
        min_ask_amount: int = 0,
        gas_amount: Decimal = GAS.GAS_AMOUNT,
        referral_address: str = None,
        fulfill_payload: TonSdkCell | None = None,
        reject_payload: TonSdkCell | None = None,
        deadline: datetime | None = None,
    ) -> dict[str, TonSdkCell | str | int]:
        if not response_address:
            response_address = self.wallet_address

        dd_jetton_builder = JettonDedustBuilder()
        swap_params = await dd_jetton_builder.build_swap_params(
            response_address=response_address,
            referral_address=referral_address,
            fulfill_payload=fulfill_payload,
            reject_payload=reject_payload,
            deadline=0 if deadline is None else int(datetime.timestamp(deadline)),
        )

        pool_address = await self.operator.get_pool_address(
            asset0=ask_asset, asset1=offer_asset
        )

        swap_steps = [SwapStep(pool_address=pool_address, limit=min_ask_amount)]

        swap_body = await dd_jetton_builder.build_swap_body(
            swap_steps=swap_steps, forward_payload=swap_params
        )

        jetton_vault_address = await self.operator.get_vault_address(asset=offer_asset)
        # jetton_vault_address = await self.operator.get_vault_address(asset=ask_asset)
        transfer_body = await dd_jetton_builder.build_jetton_transfer_body(
            destination_address=jetton_vault_address,
            amount=int(offer_amount),
            query_id=query_id,
            response_address=response_address,
            forward_amount=int(self.GAS.FORWARD_GAS_AMOUNT),
            forward_payload=swap_body,
        )
        jetton_wallet_address = await self.operator.get_jetton_wallet_address(
            jetton_master_address=offer_asset.address.to_string(True, True, True),
            wallet_address=response_address,
        )
        return {
            "to_address": jetton_wallet_address,
            "amount": int(gas_amount),
            "payload": transfer_body,
        }

    async def create_swap_jetton_to_ton_transfer_message(
        self,
        offer_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        response_address: str = None,
        ask_asset: Asset = Asset(_type=AssetType.NATIVE),
        min_ask_amount: int = 0,
        gas_amount: Decimal = GAS.GAS_AMOUNT,
        referral_address: str = None,
        fulfill_payload: TonSdkCell | None = None,
        reject_payload: TonSdkCell | None = None,
        deadline: datetime | None = None,
    ) -> dict[str, TonSdkCell | str | int]:
        return await self.create_swap_jetton_to_jetton_transfer_message(
            ask_asset=ask_asset,
            offer_asset=offer_asset,
            offer_amount=offer_amount,
            response_address=response_address,
            query_id=query_id,
            min_ask_amount=min_ask_amount,
            gas_amount=gas_amount,
            referral_address=referral_address,
        )
