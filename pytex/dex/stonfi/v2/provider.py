from datetime import datetime, timedelta
from decimal import Decimal

from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_provider import Provider
from pytex.dex.stonfi.v2.builder import StonfiV2Builder
from pytex.dex.stonfi.v2.constants import (
    pTON_ADDRESS_V2,
    GAS_TON_TO_JETTON,
    GAS_JETTON_TO_JETTON,
    GAS_JETTON_TO_TON,
)
from pytex.dex.stonfi.v2.op import StonfiV2Operator
from pytex.units import Asset, AssetType


class StonfiV2Provider(Provider):
    def __init__(self, mnemonic: list[str], toncenter_api_key: str):
        super().__init__(mnemonic=mnemonic, toncenter_api_key=toncenter_api_key)
        self.operator = StonfiV2Operator(toncenter_api_key=toncenter_api_key)

    async def _create_ton_swap_transfer_message(
        self,
        pool_address: str,
        ask_asset: Asset,
        offer_asset: Asset,
        offer_amount: int,
        response_address: str,
        gas_amount: int,
        min_ask_amount: int,
        query_id: int,
        deadline: int,
        refund_address: str | None = None,
        excesses_address: str | None = None,
        referral_gas: int = 0,
        referral_address: str | None = None,
        fulfill_gas: int = 0,
        fulfill_payload: TonSdkCell | None = None,
        reject_gas: int = 0,
        reject_payload: TonSdkCell | None = None,
    ) -> dict[str, TonSdkCell | str | int]:
        sfv2_native_builder = StonfiV2Builder()

        router_address = await self.operator.get_router_address(
            pool_address=pool_address
        )

        ask_jetton_wallet_address = await self.operator.get_jetton_wallet_address(
            jetton_master_address=ask_asset.address.to_string(True, True, True),
            wallet_address=router_address.to_string(True, True, True),
        )

        offer_pton_wallet_address = await self.operator.get_jetton_wallet_address(
            jetton_master_address=offer_asset.address.to_string(True, True, True),
            wallet_address=router_address.to_string(True, True, True),
        )

        cross_swap_body = await sfv2_native_builder.build_cross_swap_body(
            min_out=min_ask_amount,
            receiver_address=response_address,
            fwd_gas=fulfill_gas,
            refund_fwd_gas=reject_gas,
            ref_fee=referral_gas,
            custom_payload=fulfill_payload,
            refund_payload=reject_payload,
            referral_address=referral_address,
        )

        swap_body = await sfv2_native_builder.build_swap_body(
            ask_jetton_wallet_address=ask_jetton_wallet_address,
            refund_address=refund_address or response_address,
            excesses_address=excesses_address or response_address,
            deadline=deadline,
            cross_swap_body=cross_swap_body,
        )

        transfer_body = await sfv2_native_builder.build_pton_transfer_body(
            ton_amount=offer_amount,
            query_id=query_id,
            refund_address=response_address,
            forward_payload=swap_body,
        )

        return {
            "to_address": offer_pton_wallet_address,
            "amount": int(gas_amount),
            "payload": transfer_body,
        }

    async def _create_jetton_swap_transfer_message(
        self,
        pool_address: str,
        ask_asset: Asset,
        offer_asset: Asset,
        offer_amount: int,
        response_address: str,
        gas_amount: int,
        forward_amount: int,
        min_ask_amount: int,
        query_id: int,
        deadline: int,
        refund_address: str | None = None,
        excesses_address: str | None = None,
        referral_gas: int = 0,
        referral_address: str | None = None,
        fulfill_gas: int = 0,
        fulfill_payload: TonSdkCell | None = None,
        reject_gas: int = 0,
        reject_payload: TonSdkCell | None = None,
    ) -> dict[str, TonSdkCell | str | int]:
        sfv2_native_builder = StonfiV2Builder()

        router_address = await self.operator.get_router_address(
            pool_address=pool_address
        )

        ask_jetton_wallet_address = await self.operator.get_jetton_wallet_address(
            jetton_master_address=ask_asset.address.to_string(True, True, True),
            wallet_address=router_address.to_string(True, True, True),
        )

        offer_jetton_wallet_address = await self.operator.get_jetton_wallet_address(
            jetton_master_address=offer_asset.address.to_string(True, True, True),
            wallet_address=response_address,
        )

        cross_swap_body = await sfv2_native_builder.build_cross_swap_body(
            min_out=min_ask_amount,
            receiver_address=response_address,
            fwd_gas=fulfill_gas,
            refund_fwd_gas=reject_gas,
            ref_fee=referral_gas,
            custom_payload=fulfill_payload,
            refund_payload=reject_payload,
            referral_address=referral_address,
        )

        swap_body = await sfv2_native_builder.build_swap_body(
            ask_jetton_wallet_address=ask_jetton_wallet_address,
            refund_address=refund_address or response_address,
            excesses_address=excesses_address or response_address,
            deadline=deadline,
            cross_swap_body=cross_swap_body,
        )

        transfer_body = await sfv2_native_builder.build_jetton_transfer_body(
            destination_address=router_address.to_string(True, True, True),
            amount=offer_amount,
            query_id=query_id,
            response_address=response_address,
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
        pool_address: str,
        ask_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        deadline: datetime | None = None,
        response_address: str = None,
        offer_asset: Asset = Asset(
            _type=AssetType.JETTON, address=pTON_ADDRESS_V2, decimals=9
        ),
        min_ask_amount: int = 0,
        gas_amount: Decimal = GAS_TON_TO_JETTON.FORWARD_GAS_AMOUNT,
        refund_address: str | None = None,
        excesses_address: str | None = None,
        referral_gas: Decimal | None = None,
        referral_address: str = None,
        fulfill_gas: Decimal | None = None,
        fulfill_payload: TonSdkCell | None = None,
        reject_gas: Decimal | None = None,
        reject_payload: TonSdkCell | None = None,
        *_
    ) -> dict[str, TonSdkCell | str | int]:
        if response_address is None:
            response_address = self.wallet_address
        return await self._create_ton_swap_transfer_message(
            pool_address=pool_address,
            ask_asset=ask_asset,
            offer_asset=offer_asset,
            offer_amount=int(offer_amount),
            response_address=response_address,
            gas_amount=int(offer_amount + gas_amount),
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            refund_address=refund_address,
            excesses_address=excesses_address,
            referral_gas=0 if referral_gas is None else int(referral_gas),
            referral_address=referral_address,
            fulfill_gas=0 if fulfill_gas is None else int(fulfill_gas),
            fulfill_payload=fulfill_payload,
            reject_gas=0 if reject_gas is None else int(reject_gas),
            reject_payload=reject_payload,
            deadline=(
                int((datetime.now() + timedelta(minutes=30)).timestamp())
                if deadline is None
                else int(datetime.timestamp(deadline))
            ),
        )

    async def create_swap_jetton_to_jetton_transfer_message(
        self,
        pool_address: str,
        ask_asset: Asset,
        offer_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        deadline: datetime | None = None,
        response_address: str = None,
        min_ask_amount: int = 0,
        gas_amount: Decimal = GAS_JETTON_TO_JETTON.GAS_AMOUNT,
        refund_address: str | None = None,
        excesses_address: str | None = None,
        referral_gas: Decimal | None = None,
        referral_address: str = None,
        fulfill_gas: Decimal | None = None,
        fulfill_payload: TonSdkCell | None = None,
        reject_gas: Decimal | None = None,
        reject_payload: TonSdkCell | None = None,
        *_
    ) -> dict[str, TonSdkCell | str | int]:
        if response_address is None:
            response_address = self.wallet_address
        return await self._create_jetton_swap_transfer_message(
            pool_address=pool_address,
            ask_asset=ask_asset,
            offer_asset=offer_asset,
            offer_amount=int(offer_amount),
            response_address=response_address,
            gas_amount=int(gas_amount),
            forward_amount=int(GAS_JETTON_TO_JETTON.FORWARD_GAS_AMOUNT),
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            refund_address=refund_address,
            excesses_address=excesses_address,
            referral_gas=0 if referral_gas is None else int(referral_gas),
            referral_address=referral_address,
            fulfill_gas=0 if fulfill_gas is None else int(fulfill_gas),
            fulfill_payload=fulfill_payload,
            reject_gas=0 if reject_gas is None else int(reject_gas),
            reject_payload=reject_payload,
            deadline=(
                int((datetime.now() + timedelta(minutes=30)).timestamp())
                if deadline is None
                else int(datetime.timestamp(deadline))
            ),
        )

    async def create_swap_jetton_to_ton_transfer_message(
        self,
        pool_address: str,
        offer_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        deadline: datetime | None = None,
        response_address: str | None = None,
        ask_asset: Asset = Asset(
            _type=AssetType.JETTON, address=pTON_ADDRESS_V2, decimals=9
        ),
        min_ask_amount: int = 0,
        gas_amount: Decimal = GAS_JETTON_TO_TON.GAS_AMOUNT,
        refund_address: str | None = None,
        excesses_address: str | None = None,
        referral_gas: Decimal | None = None,
        referral_address: str = None,
        fulfill_gas: Decimal | None = None,
        fulfill_payload: TonSdkCell | None = None,
        reject_gas: Decimal | None = None,
        reject_payload: TonSdkCell | None = None,
        *_
    ) -> dict[str, TonSdkCell | str | int]:
        if response_address is None:
            response_address = self.wallet_address
        return await self._create_jetton_swap_transfer_message(
            pool_address=pool_address,
            ask_asset=ask_asset,
            offer_asset=offer_asset,
            offer_amount=int(offer_amount),
            response_address=response_address,
            gas_amount=int(gas_amount),
            forward_amount=int(GAS_JETTON_TO_TON.FORWARD_GAS_AMOUNT),
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            refund_address=refund_address,
            excesses_address=excesses_address,
            referral_gas=0 if referral_gas is None else int(referral_gas),
            referral_address=referral_address,
            fulfill_gas=0 if fulfill_gas is None else int(fulfill_gas),
            fulfill_payload=fulfill_payload,
            reject_gas=0 if reject_gas is None else int(reject_gas),
            reject_payload=reject_payload,
            deadline=(
                int((datetime.now() + timedelta(minutes=30)).timestamp())
                if deadline is None
                else int(datetime.timestamp(deadline))
            ),
        )
