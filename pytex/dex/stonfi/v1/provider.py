from decimal import Decimal

from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_provider import Provider
from pytex.dex.stonfi.v1.builder import StonfiV1Builder
from pytex.dex.stonfi.v1.constants import (
    STONFI_ROUTER_V1,
    pTON_ADDRESS_V1,
    GAS_TON_TO_JETTON,
    GAS_JETTON_TO_JETTON,
    GAS_JETTON_TO_TON,
)
from pytex.dex.stonfi.v1.op import StonfiV1Operator
from pytex.units import Asset, AssetType


class StonfiV1Provider(Provider):
    def __init__(self, mnemonic: list[str], toncenter_api_key: str):
        super().__init__(mnemonic=mnemonic, toncenter_api_key=toncenter_api_key)
        self.operator = StonfiV1Operator(toncenter_api_key=toncenter_api_key)

    async def _create_swap_transfer_message(
        self,
        ask_asset: Asset,
        offer_asset: Asset,
        offer_amount: int,
        response_address: str,
        gas_amount: int,
        forward_amount: int,
        min_ask_amount: int,
        query_id: int,
        referral_address: str,
        offer_owner_address: str = None,
        custom_payload: TonSdkCell | None = None,
    ) -> dict[str, TonSdkCell | str | int]:
        sfv1_native_builder = StonfiV1Builder()
        if offer_owner_address is None:
            offer_owner_address = STONFI_ROUTER_V1

        ask_jetton_wallet_address = await self.operator.get_jetton_wallet_address(
            jetton_master_address=ask_asset.address.to_string(True, True, True),
            wallet_address=STONFI_ROUTER_V1,
        )

        offer_jetton_wallet_address = await self.operator.get_jetton_wallet_address(
            jetton_master_address=offer_asset.address.to_string(True, True, True),
            wallet_address=offer_owner_address,
        )

        swap_body = await sfv1_native_builder.build_swap_body(
            wallet_address=response_address,
            ask_jetton_wallet_address=ask_jetton_wallet_address,
            min_ask_amount=min_ask_amount,
            referral_address=referral_address,
        )

        transfer_body = await sfv1_native_builder.build_jetton_transfer_body(
            destination_address=STONFI_ROUTER_V1,
            amount=offer_amount,
            query_id=query_id,
            response_address=response_address,
            custom_payload=custom_payload,
            forward_amount=forward_amount,
            forward_payload=swap_body,
        )

        return {
            "to_address": offer_jetton_wallet_address,
            "amount": int(gas_amount),
            "payload": transfer_body,
        }

    async def create_swap_ton_to_jetton_transfer_message(
        self,
        ask_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        response_address: str = None,
        offer_asset: Asset = Asset(
            _type=AssetType.JETTON, address=pTON_ADDRESS_V1, decimals=9
        ),
        min_ask_amount: int = 0,
        gas_amount: Decimal = GAS_TON_TO_JETTON.FORWARD_GAS_AMOUNT,
        referral_address: str = None,
        custom_payload: TonSdkCell | None = None,
        **_
    ) -> dict[str, TonSdkCell | str | int]:
        if response_address is None:
            response_address = self.wallet_address
        return await self._create_swap_transfer_message(
            ask_asset=ask_asset,
            offer_asset=offer_asset,
            offer_amount=int(offer_amount),
            response_address=response_address,
            forward_amount=int(gas_amount),
            gas_amount=int(offer_amount + gas_amount),
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            referral_address=referral_address,
            custom_payload=custom_payload,
        )

    async def create_swap_jetton_to_jetton_transfer_message(
        self,
        ask_asset: Asset,
        offer_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        response_address: str = None,
        min_ask_amount: int = 0,
        gas_amount: Decimal = GAS_JETTON_TO_JETTON.GAS_AMOUNT,
        referral_address: str = None,
        custom_payload: TonSdkCell | None = None,
        **_
    ) -> dict[str, TonSdkCell | str | int]:
        if response_address is None:
            response_address = self.wallet_address
        return await self._create_swap_transfer_message(
            ask_asset=ask_asset,
            offer_asset=offer_asset,
            offer_amount=int(offer_amount),
            response_address=response_address,
            offer_owner_address=response_address,
            forward_amount=int(GAS_JETTON_TO_JETTON.FORWARD_GAS_AMOUNT),
            gas_amount=int(gas_amount),
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            referral_address=referral_address,
            custom_payload=custom_payload,
        )

    async def create_swap_jetton_to_ton_transfer_message(
        self,
        offer_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        response_address: str = None,
        ask_asset: Asset = Asset(
            _type=AssetType.JETTON, address=pTON_ADDRESS_V1, decimals=9
        ),
        min_ask_amount: int = 0,
        gas_amount: Decimal = GAS_JETTON_TO_TON.GAS_AMOUNT,
        referral_address: str = None,
        custom_payload: TonSdkCell | None = None,
        **_
    ) -> dict[str, TonSdkCell | str | int]:
        if response_address is None:
            response_address = self.wallet_address
        return await self._create_swap_transfer_message(
            ask_asset=ask_asset,
            offer_asset=offer_asset,
            offer_amount=int(offer_amount),
            response_address=response_address,
            offer_owner_address=response_address,
            forward_amount=int(GAS_JETTON_TO_TON.FORWARD_GAS_AMOUNT),
            gas_amount=int(gas_amount),
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            referral_address=referral_address,
            custom_payload=custom_payload,
        )
