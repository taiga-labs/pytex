from datetime import datetime, timedelta
from decimal import Decimal

from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_provider import Provider
from pytex.dex.stonfi.v2.builder import StonfiV2Builder, SwapStep, SwapChain
from pytex.dex.stonfi.v2.constants import (
    pTON_ADDRESS_V2,
    GAS_TON_TO_JETTON,
    GAS_JETTON_TO_JETTON,
    GAS_JETTON_TO_TON,
)
from pytex.dex.stonfi.v2.op import StonfiV2Operator
from pytex.units import Asset, AssetType, TON_ZERO_ADDRESS


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

        additional_data = await sfv2_native_builder.build_additional_data(
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
            additional_data=additional_data,
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

        additional_data = await sfv2_native_builder.build_additional_data(
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
            additional_data=additional_data,
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

    async def _create_ton_multi_swap_transfer_message_ex(
        self,
        swap_chain: SwapChain,
        offer_asset: Asset,
        offer_amount: int,
        response_address: str,
        min_ask_amount: int,
        query_id: int,
        deadline: int,
        gas_amount: int | None = None,
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

        swap_body, full_forward_gas = await sfv2_native_builder.pack_swap_steps(
            swap_chain=swap_chain,
            response_address=response_address,
            min_ask_amount=min_ask_amount,
            deadline=deadline,
            refund_address=refund_address,
            excesses_address=excesses_address,
            referral_gas=referral_gas,
            referral_address=referral_address,
            fulfill_gas=fulfill_gas,
            custom_payload=fulfill_payload,
            reject_gas=reject_gas,
            reject_payload=reject_payload,
        )

        offer_router_pton_wallet_address = (
            await self.operator.get_jetton_wallet_address(
                jetton_master_address=offer_asset.address.to_string(True, True, True),
                wallet_address=swap_chain.tail.router_address,
            )
        )

        transfer_body = await sfv2_native_builder.build_pton_transfer_body(
            ton_amount=offer_amount,
            query_id=query_id,
            refund_address=response_address,
            forward_payload=swap_body,
        )

        return {
            "to_address": offer_router_pton_wallet_address,
            "amount": gas_amount or offer_amount + full_forward_gas,
            "payload": transfer_body,
        }

    async def _create_ton_multi_swap_transfer_message(
        self,
        pool_addresses: list[str],
        offer_asset: Asset,
        offer_amount: int,
        response_address: str,
        min_ask_amount: int,
        query_id: int,
        deadline: int,
        gas_amount: int | None = None,
        refund_address: str | None = None,
        excesses_address: str | None = None,
        referral_gas: int = 0,
        referral_address: str | None = None,
        fulfill_gas: int = 0,
        fulfill_payload: TonSdkCell | None = None,
        reject_gas: int = 0,
        reject_payload: TonSdkCell | None = None,
    ) -> dict[str, TonSdkCell | str | int]:
        swap_chain = SwapChain()
        for pool_address in pool_addresses:
            router_address = await self.operator.get_router_address(
                pool_address=pool_address
            )
            reserve0, reserve1 = await self.operator.get_pool_reserves(
                pool_address=pool_address
            )

            pool_asset0_address = (
                pTON_ADDRESS_V2
                if reserve0.asset.address.to_string(True, True, True)
                == TON_ZERO_ADDRESS
                else reserve0.asset.address.to_string(True, True, True)
            )
            pool_asset1_address = (
                pTON_ADDRESS_V2
                if reserve1.asset.address.to_string(True, True, True)
                == TON_ZERO_ADDRESS
                else reserve1.asset.address.to_string(True, True, True)
            )

            if swap_chain.head is None:
                prev_ask_asset_address = offer_asset.address.to_string(True, True, True)
            else:
                prev_ask_asset_address = swap_chain.head.ask_jetton_address

            if prev_ask_asset_address == pool_asset0_address:
                offer_jetton_address = pool_asset0_address
                ask_jetton_address = pool_asset1_address
            elif prev_ask_asset_address == pool_asset1_address:
                offer_jetton_address = pool_asset1_address
                ask_jetton_address = pool_asset0_address
            else:
                raise ValueError("Wrong assets")

            router_offer_jetton_wallet_address = None
            if offer_jetton_address == pTON_ADDRESS_V2:
                router_offer_jetton_wallet_address = (
                    await self.operator.get_jetton_wallet_address(
                        jetton_master_address=offer_jetton_address,
                        wallet_address=router_address.to_string(True, True, True),
                    )
                )

            router_ask_jetton_wallet_address = (
                await self.operator.get_jetton_wallet_address(
                    jetton_master_address=ask_jetton_address,
                    wallet_address=router_address.to_string(True, True, True),
                )
            )
            swap_step = SwapStep(
                pool_address=pool_address,
                router_address=router_address.to_string(True, True, True),
                offer_jetton_address=prev_ask_asset_address,
                ask_jetton_address=ask_jetton_address,
                router_offer_jetton_wallet_address=router_offer_jetton_wallet_address,
                router_ask_jetton_wallet_address=router_ask_jetton_wallet_address,
                min_ask_amount=min_ask_amount,
                deadline=deadline,
            )
            swap_chain.push(swap_step)

        return await self._create_ton_multi_swap_transfer_message_ex(
            swap_chain=swap_chain,
            offer_asset=offer_asset,
            offer_amount=offer_amount,
            response_address=response_address,
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            deadline=deadline,
            gas_amount=gas_amount,
            refund_address=refund_address,
            excesses_address=excesses_address,
            referral_gas=referral_gas,
            referral_address=referral_address,
            fulfill_gas=fulfill_gas,
            fulfill_payload=fulfill_payload,
            reject_gas=reject_gas,
            reject_payload=reject_payload,
        )

    async def _create_jetton_multi_swap_transfer_message_ex(
        self,
        swap_chain: SwapChain,
        offer_asset: Asset,
        offer_amount: int,
        response_address: str,
        min_ask_amount: int,
        query_id: int,
        deadline: int,
        forward_amount: int | None = None,
        gas_amount: int | None = None,
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

        swap_body, full_forward_gas = await sfv2_native_builder.pack_swap_steps(
            swap_chain=swap_chain,
            response_address=response_address,
            min_ask_amount=min_ask_amount,
            deadline=deadline,
            refund_address=refund_address,
            excesses_address=excesses_address,
            referral_gas=referral_gas,
            referral_address=referral_address,
            fulfill_gas=fulfill_gas,
            custom_payload=fulfill_payload,
            reject_gas=reject_gas,
            reject_payload=reject_payload,
        )

        transfer_body = await sfv2_native_builder.build_jetton_transfer_body(
            destination_address=swap_chain.tail.router_address,
            amount=offer_amount,
            query_id=query_id,
            response_address=response_address,
            forward_amount=forward_amount or full_forward_gas,
            forward_payload=swap_body,
        )

        offer_jetton_wallet_address = await self.operator.get_jetton_wallet_address(
            jetton_master_address=offer_asset.address.to_string(True, True, True),
            wallet_address=response_address,
        )

        if swap_chain.tail.ask_jetton_address == pTON_ADDRESS_V2:
            transfer_gas = int(GAS_JETTON_TO_TON.TRANSFER_FAS)
        else:
            transfer_gas = int(GAS_JETTON_TO_TON.TRANSFER_FAS)

        return {
            "to_address": offer_jetton_wallet_address,
            "amount": gas_amount or full_forward_gas + transfer_gas,
            "payload": transfer_body,
        }

    async def _create_jetton_multi_swap_transfer_message(
        self,
        pool_addresses: list[str],
        offer_asset: Asset,
        offer_amount: int,
        response_address: str,
        min_ask_amount: int,
        query_id: int,
        deadline: int,
        forward_amount: int | None = None,
        gas_amount: int | None = None,
        refund_address: str | None = None,
        excesses_address: str | None = None,
        referral_gas: int = 0,
        referral_address: str | None = None,
        fulfill_gas: int = 0,
        fulfill_payload: TonSdkCell | None = None,
        reject_gas: int = 0,
        reject_payload: TonSdkCell | None = None,
    ) -> dict[str, TonSdkCell | str | int]:
        swap_chain = SwapChain()
        for pool_address in pool_addresses:
            router_address = await self.operator.get_router_address(
                pool_address=pool_address
            )
            reserve0, reserve1 = await self.operator.get_pool_reserves(
                pool_address=pool_address
            )

            pool_asset0_address = (
                pTON_ADDRESS_V2
                if reserve0.asset.address.to_string(True, True, True)
                == TON_ZERO_ADDRESS
                else reserve0.asset.address.to_string(True, True, True)
            )
            pool_asset1_address = (
                pTON_ADDRESS_V2
                if reserve1.asset.address.to_string(True, True, True)
                == TON_ZERO_ADDRESS
                else reserve1.asset.address.to_string(True, True, True)
            )

            if swap_chain.head is None:
                prev_ask_asset_address = offer_asset.address.to_string(True, True, True)
            else:
                prev_ask_asset_address = swap_chain.head.ask_jetton_address

            if prev_ask_asset_address == pool_asset0_address:
                offer_jetton_address = pool_asset0_address
                ask_jetton_address = pool_asset1_address
            elif prev_ask_asset_address == pool_asset1_address:
                offer_jetton_address = pool_asset1_address
                ask_jetton_address = pool_asset0_address
            else:
                raise ValueError("Wrong assets")

            router_offer_jetton_wallet_address = None
            if offer_jetton_address == pTON_ADDRESS_V2:
                router_offer_jetton_wallet_address = (
                    await self.operator.get_jetton_wallet_address(
                        jetton_master_address=offer_jetton_address,
                        wallet_address=router_address.to_string(True, True, True),
                    )
                )

            router_ask_jetton_wallet_address = (
                await self.operator.get_jetton_wallet_address(
                    jetton_master_address=ask_jetton_address,
                    wallet_address=router_address.to_string(True, True, True),
                )
            )
            swap_step = SwapStep(
                pool_address=pool_address,
                router_address=router_address.to_string(True, True, True),
                offer_jetton_address=prev_ask_asset_address,
                ask_jetton_address=ask_jetton_address,
                router_offer_jetton_wallet_address=router_offer_jetton_wallet_address,
                router_ask_jetton_wallet_address=router_ask_jetton_wallet_address,
                min_ask_amount=min_ask_amount,
                deadline=deadline,
            )
            swap_chain.push(swap_step)

        return await self._create_jetton_multi_swap_transfer_message_ex(
            swap_chain=swap_chain,
            offer_asset=offer_asset,
            offer_amount=offer_amount,
            response_address=response_address,
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            deadline=deadline,
            forward_amount=forward_amount,
            gas_amount=gas_amount,
            refund_address=refund_address,
            excesses_address=excesses_address,
            referral_gas=referral_gas,
            referral_address=referral_address,
            fulfill_gas=fulfill_gas,
            fulfill_payload=fulfill_payload,
            reject_gas=reject_gas,
            reject_payload=reject_payload,
        )

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
        **_,
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
        pools: list[str],
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
        **_,
    ) -> dict[str, TonSdkCell | str | int]:
        if response_address is None:
            response_address = self.wallet_address

        return await self._create_jetton_swap_transfer_message(
            pool_address=pools[0],
            ask_asset=ask_asset,
            offer_asset=offer_asset,
            offer_amount=int(offer_amount),
            response_address=response_address,
            gas_amount=int(gas_amount),
            forward_amount=int(GAS_JETTON_TO_JETTON.FORWARD_GAS_AMOUNT),
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            refund_address=refund_address if refund_address else response_address,
            excesses_address=excesses_address if excesses_address else response_address,
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
        **_,
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

    async def create_ton_multi_swap_transfer_message(
        self,
        pools: list[str],
        offer_amount: Decimal,
        query_id: int,
        offer_asset: Asset = Asset(
            _type=AssetType.JETTON, address=pTON_ADDRESS_V2, decimals=9
        ),
        deadline: datetime | None = None,
        response_address: str = None,
        min_ask_amount: int = 0,
        forward_amount: Decimal | None = None,
        gas_amount: Decimal | None = None,
        refund_address: str | None = None,
        excesses_address: str | None = None,
        referral_gas: Decimal | None = None,
        referral_address: str = None,
        fulfill_gas: Decimal | None = None,
        fulfill_payload: TonSdkCell | None = None,
        reject_gas: Decimal | None = None,
        reject_payload: TonSdkCell | None = None,
        **_,
    ) -> dict[str, TonSdkCell | str | int]:
        if response_address is None:
            response_address = self.wallet_address

        return await self._create_ton_multi_swap_transfer_message(
            pool_addresses=pools,
            offer_asset=offer_asset,
            offer_amount=int(offer_amount),
            response_address=response_address,
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            deadline=(
                int((datetime.now() + timedelta(minutes=30)).timestamp())
                if deadline is None
                else int(datetime.timestamp(deadline))
            ),
            gas_amount=int(gas_amount) if gas_amount is not None else None,
            refund_address=refund_address if refund_address else response_address,
            excesses_address=(
                excesses_address if excesses_address else response_address
            ),
            referral_gas=0 if referral_gas is None else int(referral_gas),
            referral_address=referral_address,
            fulfill_gas=0 if fulfill_gas is None else int(fulfill_gas),
            fulfill_payload=fulfill_payload,
            reject_gas=0 if reject_gas is None else int(reject_gas),
            reject_payload=reject_payload,
        )

    async def create_jetton_multi_swap_transfer_message(
        self,
        pools: list[str],
        offer_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        deadline: datetime | None = None,
        response_address: str = None,
        min_ask_amount: int = 0,
        forward_amount: Decimal | None = None,
        gas_amount: Decimal | None = None,
        refund_address: str | None = None,
        excesses_address: str | None = None,
        referral_gas: Decimal | None = None,
        referral_address: str = None,
        fulfill_gas: Decimal | None = None,
        fulfill_payload: TonSdkCell | None = None,
        reject_gas: Decimal | None = None,
        reject_payload: TonSdkCell | None = None,
        **_,
    ) -> dict[str, TonSdkCell | str | int]:
        if response_address is None:
            response_address = self.wallet_address

        return await self._create_jetton_multi_swap_transfer_message(
            pool_addresses=pools,
            offer_asset=offer_asset,
            offer_amount=int(offer_amount),
            response_address=response_address,
            min_ask_amount=min_ask_amount,
            query_id=query_id,
            deadline=(
                int((datetime.now() + timedelta(minutes=30)).timestamp())
                if deadline is None
                else int(datetime.timestamp(deadline))
            ),
            forward_amount=int(forward_amount) if forward_amount is not None else None,
            gas_amount=int(gas_amount) if gas_amount is not None else None,
            refund_address=refund_address if refund_address else response_address,
            excesses_address=(
                excesses_address if excesses_address else response_address
            ),
            referral_gas=0 if referral_gas is None else int(referral_gas),
            referral_address=referral_address,
            fulfill_gas=0 if fulfill_gas is None else int(fulfill_gas),
            fulfill_payload=fulfill_payload,
            reject_gas=0 if reject_gas is None else int(reject_gas),
            reject_payload=reject_payload,
        )
