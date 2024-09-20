from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from tonsdk.crypto import mnemonic_to_wallet_key
from tonsdk.boc import Cell as TonSdkCell


from .base_builder import Builder
from .base_operator import Operator
from pytex.units import Asset
from pytex.wallet import WalletContractMulti


class BaseProvider(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def create_swap_ton_to_jetton_transfer_message(
        self, ask_asset: Asset, offer_amount: Decimal, offer_asset: Asset, query_id: int
    ):
        raise NotImplementedError

    @abstractmethod
    async def create_swap_jetton_to_jetton_transfer_message(
        self, ask_asset: Asset, offer_asset: Asset, offer_amount: Decimal, query_id: int
    ):
        raise NotImplementedError

    @abstractmethod
    async def create_swap_jetton_to_ton_transfer_message(
        self, offer_asset: Asset, offer_amount: Decimal, ask_asset: Asset, query_id: int
    ):
        raise NotImplementedError


class Provider(BaseProvider):
    TRANSFER_NATIVE_GAS = Decimal("3000000")  # Ton
    TRANSFER_JETTON_GAS = Decimal("37000000")  # Ton

    def __init__(self, mnemonic: list[str], toncenter_api_key: str):
        super().__init__()
        self.mnemonic = mnemonic
        pub_k, priv_k = mnemonic_to_wallet_key(self.mnemonic)
        self.wallet_multi = WalletContractMulti(
            public_key=pub_k, private_key=priv_k, wc=0
        )
        self.wallet_address = self.wallet_multi.address.to_string(True, True, True)
        self.operator = Operator(toncenter_api_key)

    async def transfer(self, msgs: list[dict]) -> str:
        cur_seqno = await self.operator.get_seqno(wallet_address=self.wallet_address)

        query = self.wallet_multi.create_transfer_messages(
            messages=msgs, seqno=cur_seqno
        )
        task = self.operator.client.raw_send_message(query["message"].to_boc(False))
        await self.operator.run(to_run=task)
        return query["message"].bytes_hash().hex()

    async def activate(self):
        query = self.wallet_multi.create_init_external_message()
        task = self.operator.client.raw_send_message(query["message"].to_boc(False))
        await self.operator.run(to_run=task)

    async def create_jetton_transfer_message(
        self,
        jetton_master_address: str,
        amount: Decimal,
        destination_address: str,
        query_id: int = 0,
    ) -> dict[str, str | Any]:
        jetton_wallet_address = await self.operator.get_jetton_wallet_address(
            jetton_master_address=jetton_master_address,
            wallet_address=self.wallet_address,
        )
        jetton_transfer_body = await Builder().build_transfer_body(
            offer_amount=int(amount), to_address=destination_address, query_id=query_id
        )
        return {
            "to_address": jetton_wallet_address,
            "amount": int(self.TRANSFER_JETTON_GAS),
            "payload": jetton_transfer_body,
        }

    @staticmethod
    async def create_ton_transfer_message(
        destination_address: str,
        amount: Decimal = Decimal("0"),
        return_all: bool = False,
        query_id: int = 0,
    ) -> dict[str, str | Any]:
        payload: TonSdkCell = TonSdkCell()
        payload.bits.write_uint(0, 32)  # comment exists
        payload.bits.write_string(f"query_id: {query_id}")

        if return_all:
            return {
                "to_address": destination_address,
                "amount": 0,
                "send_mode": 128,
                "payload": payload,
            }
        return {
            "to_address": destination_address,
            "amount": int(amount),
            "payload": payload,
        }

    async def create_swap_ton_to_jetton_transfer_message(
        self,
        ask_asset: Asset,
        offer_amount: Decimal,
        offer_asset: Asset,
        query_id: int,
        referral_address: str | None = None,
    ):
        pass

    async def create_swap_jetton_to_jetton_transfer_message(
        self,
        ask_asset: Asset,
        offer_asset: Asset,
        offer_amount: Decimal,
        query_id: int,
        referral_address: str | None = None,
    ):
        pass

    async def create_swap_jetton_to_ton_transfer_message(
        self,
        offer_asset: Asset,
        offer_amount: Decimal,
        ask_asset: Asset,
        query_id: int,
        referral_address: str | None = None,
    ):
        pass
