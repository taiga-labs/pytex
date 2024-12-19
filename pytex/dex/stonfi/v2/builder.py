from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell, Cell

from pytex.dex.stonfi.builder import StonfiBuilder
from pytex.dex.stonfi.v2.constants import (
    pTON_ADDRESS_V2,
    GAS_JETTON_TO_TON,
    GAS_TON_TO_JETTON,
    GAS_JETTON_TO_JETTON,
)
from pytex.units import TON_ZERO_ADDRESS


class SwapStep:
    def __init__(
        self,
        pool_address: str,
        router_address: str,
        offer_jetton_address: str,
        ask_jetton_address: str,
        router_ask_jetton_wallet_address: str,
        min_ask_amount: int,
        deadline: int,
        router_offer_jetton_wallet_address: str | None = None,
        refund_address: str | None = None,
        excesses_address: str | None = None,
        referral_gas: int = 0,
        referral_address: str | None = None,
        fulfill_gas: int = 0,
        fulfill_payload: TonSdkCell | None = None,
        reject_gas: int = 0,
        reject_payload: TonSdkCell | None = None,
    ):
        self.pool_address = pool_address
        self.router_address = router_address
        self.offer_jetton_address = offer_jetton_address
        self.ask_jetton_address = ask_jetton_address
        self.router_offer_jetton_wallet_address = router_offer_jetton_wallet_address
        self.router_ask_jetton_wallet_address = router_ask_jetton_wallet_address
        self.min_ask_amount = min_ask_amount
        self.deadline = deadline
        self.refund_address = refund_address
        self.excesses_address = excesses_address
        self.referral_gas = referral_gas
        self.referral_address = referral_address
        self.fulfill_gas = fulfill_gas
        self.fulfill_payload = fulfill_payload
        self.reject_gas = reject_gas
        self.reject_payload = reject_payload

        if (
            self.offer_jetton_address == TON_ZERO_ADDRESS
            or self.offer_jetton_address == pTON_ADDRESS_V2
        ):
            if self.router_offer_jetton_wallet_address is None:
                raise ValueError(
                    "Router offer jetton wallet must be specified if offer token is TON"
                )

        # doubly linked list
        self.next: SwapStep | None = None
        self.prev: SwapStep | None = None


class SwapChain:
    def __init__(self):
        self.head = None
        self.tail = None

    def push(self, swap_step: SwapStep):
        swap_step.prev = self.head
        if self.head is not None:
            self.head.next = swap_step
        else:
            self.tail = swap_step
        self.head = swap_step

    # TODO add extended methods


class StonfiV2Builder(StonfiBuilder):
    @staticmethod
    async def build_cross_swap_custom_payload(
        other_token_wallet: str,
        deadline: int,
        refund_address: str | None = None,
        excess_address: str | None = None,
        additional_data: TonSdkCell | None = None,
    ):
        custom_payload: TonSdkCell = TonSdkCell()
        custom_payload.bits.write_uint(0x69CF1A5B, 32)  # cross swap op code
        custom_payload.bits.write_address(TonSdkAddress(other_token_wallet))
        custom_payload.bits.write_address(TonSdkAddress(refund_address))
        custom_payload.bits.write_address(TonSdkAddress(excess_address))
        custom_payload.bits.write_uint(deadline, 64)
        custom_payload.refs.append(additional_data)
        return custom_payload

    @staticmethod
    async def build_additional_data(
        min_out: int,
        receiver_address: str,
        fwd_gas: int = 0,
        refund_fwd_gas: int = 0,
        ref_fee: int = 0,  # max 100 (%)
        custom_payload: TonSdkCell | None = None,
        refund_payload: TonSdkCell | None = None,
        referral_address: str | None = None,
    ):
        cross_swap_body = TonSdkCell()
        # cross_swap_body.bits.write_uint(min_out, 32)
        cross_swap_body.bits.write_coins(min_out)
        cross_swap_body.bits.write_address(TonSdkAddress(receiver_address))
        cross_swap_body.bits.write_coins(fwd_gas)

        if custom_payload is None:
            cross_swap_body.bits.write_bit(0)  # null custom_payload
        else:
            cross_swap_body.bits.write_bit(1)
            cross_swap_body.refs.append(custom_payload)

        cross_swap_body.bits.write_coins(refund_fwd_gas)

        if refund_payload is None:
            cross_swap_body.bits.write_bit(0)  # null custom_payload
        else:
            cross_swap_body.bits.write_bit(1)
            cross_swap_body.refs.append(refund_payload)

        cross_swap_body.bits.write_uint(min(100, max(ref_fee, 0)), 16)

        if referral_address is None:
            cross_swap_body.bits.write_address(None)  # null referral address
        else:
            cross_swap_body.bits.write_address(TonSdkAddress(referral_address))

        return cross_swap_body

    @staticmethod
    async def build_swap_body(
        ask_jetton_wallet_address: str,  # stonfi router jetton wallet address
        refund_address: str,
        excesses_address: str,
        additional_data: TonSdkCell,
        deadline: int,
    ) -> TonSdkCell:
        swap_body: TonSdkCell = TonSdkCell()
        swap_body.bits.write_uint(0x6664DE2A, 32)  # swap op code
        swap_body.bits.write_address(TonSdkAddress(ask_jetton_wallet_address))
        swap_body.bits.write_address(TonSdkAddress(refund_address))
        swap_body.bits.write_address(TonSdkAddress(excesses_address))
        swap_body.bits.write_uint(deadline, 64)
        swap_body.refs.append(additional_data)

        return swap_body

    async def insert_cross_swap_step(
        self,
        swap_step,
        receiver_address: str,
        min_ask_amount: int,
        fulfill_gas: int,
        reject_gas: int,
        referral_gas: int,
        reject_payload: TonSdkCell,
        custom_payload: TonSdkCell,
        referral_address: str,
        refund_address: str,
        excesses_address: str,
        deadline: int,
    ):
        swap_additional_data = await self.build_additional_data(
            min_out=swap_step.min_ask_amount or min_ask_amount,
            receiver_address=receiver_address,
            fwd_gas=swap_step.fulfill_gas or fulfill_gas,
            refund_fwd_gas=swap_step.reject_gas or reject_gas,
            ref_fee=swap_step.referral_gas or referral_gas,
            custom_payload=custom_payload,
            refund_payload=swap_step.reject_payload or reject_payload,
            referral_address=swap_step.referral_address or referral_address,
        )

        cross_swap_payload = await self.build_cross_swap_custom_payload(
            other_token_wallet=swap_step.router_ask_jetton_wallet_address,
            deadline=swap_step.deadline or deadline,
            refund_address=swap_step.refund_address or refund_address,
            excess_address=swap_step.excesses_address or excesses_address,
            additional_data=swap_additional_data,
        )

        return cross_swap_payload

    async def insert_swap_step(
        self,
        swap_step,
        receiver_address: str,
        min_ask_amount: int,
        fulfill_gas: int,
        reject_gas: int,
        referral_gas: int,
        reject_payload: TonSdkCell,
        custom_payload: TonSdkCell,
        referral_address: str,
        refund_address: str,
        excesses_address: str,
        deadline: int,
    ):
        swap_additional_data = await self.build_additional_data(
            min_out=swap_step.min_ask_amount or min_ask_amount,
            receiver_address=receiver_address,
            fwd_gas=swap_step.fulfill_gas or fulfill_gas,
            refund_fwd_gas=swap_step.reject_gas or reject_gas,
            ref_fee=swap_step.referral_gas or referral_gas,
            custom_payload=custom_payload,
            refund_payload=swap_step.reject_payload or reject_payload,
            referral_address=swap_step.referral_address or referral_address,
        )

        swap_body = await self.build_swap_body(
            ask_jetton_wallet_address=swap_step.router_ask_jetton_wallet_address,
            refund_address=swap_step.refund_address or refund_address,
            excesses_address=swap_step.excesses_address or excesses_address,
            deadline=swap_step.deadline or deadline,
            additional_data=swap_additional_data,
        )

        return swap_body

    async def pack_swap_steps(
        self,
        swap_chain: SwapChain,
        response_address: str,
        min_ask_amount: int,
        fulfill_gas: int,
        reject_gas: int,
        referral_gas: int,
        reject_payload: TonSdkCell,
        custom_payload: TonSdkCell,
        referral_address: str,
        refund_address: str,
        excesses_address: str,
        deadline: int,
    ) -> tuple[Cell, int]:
        full_forward_gas = fulfill_gas

        swap_body = custom_payload
        swap_step = swap_chain.head
        while swap_step is not None:
            if (
                swap_step.prev is not None
                and swap_step.router_address == swap_step.prev.router_address
            ):
                swap_body = await self.insert_cross_swap_step(
                    swap_step=swap_step,
                    receiver_address=response_address,
                    min_ask_amount=min_ask_amount,
                    reject_gas=reject_gas,
                    referral_gas=referral_gas,
                    reject_payload=reject_payload,
                    fulfill_gas=full_forward_gas,
                    custom_payload=swap_body,
                    referral_address=referral_address,
                    refund_address=refund_address,
                    excesses_address=excesses_address,
                    deadline=deadline,
                )
            else:
                if (
                    swap_step.ask_jetton_address == TON_ZERO_ADDRESS
                    or swap_step.ask_jetton_address == pTON_ADDRESS_V2
                ):
                    receiver_address = (
                        swap_step.next.router_offer_jetton_wallet_address
                        if swap_step.next is not None
                        else response_address
                    )
                    fg = swap_step.fulfill_gas or GAS_JETTON_TO_TON.FORWARD_GAS_AMOUNT
                else:
                    receiver_address = (
                        swap_step.next.router_address
                        if swap_step.next is not None
                        else response_address
                    )
                    if (
                        swap_step.offer_jetton_address == TON_ZERO_ADDRESS
                        or swap_step.offer_jetton_address == pTON_ADDRESS_V2
                    ):
                        fg = GAS_TON_TO_JETTON.FORWARD_GAS_AMOUNT
                    else:
                        fg = GAS_JETTON_TO_JETTON.FORWARD_GAS_AMOUNT
                swap_body = await self.insert_swap_step(
                    swap_step=swap_step,
                    receiver_address=receiver_address,
                    min_ask_amount=min_ask_amount,
                    fulfill_gas=full_forward_gas,
                    reject_gas=reject_gas,
                    referral_gas=referral_gas,
                    reject_payload=reject_payload,
                    custom_payload=swap_body,
                    referral_address=referral_address,
                    refund_address=refund_address,
                    excesses_address=excesses_address,
                    deadline=deadline,
                )
                full_forward_gas += fg
            if swap_step.prev is None:
                break
            swap_step = swap_step.prev
        return swap_body, full_forward_gas
