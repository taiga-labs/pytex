from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_builder import Builder


class SwapStep:
    def __init__(self, pool_address: str, limit: int = 0):
        self.pool_address = pool_address
        self.limit = limit


class DedustBuilder(Builder):
    @staticmethod
    async def build_swap_params(
        response_address: str,
        fulfill_payload: TonSdkCell = None,
        reject_payload: TonSdkCell = None,
        referral_address: str | None = None,
    ) -> TonSdkCell:
        dedust_swap_params = TonSdkCell()
        dedust_swap_params.bits.write_uint(0, 32)  # Deadline
        dedust_swap_params.bits.write_address(
            TonSdkAddress(response_address)
        )  # Recipient address

        if referral_address is None:
            dedust_swap_params.bits.write_address(None)  # null referral address
        else:
            dedust_swap_params.bits.write_address(TonSdkAddress(referral_address))

        if fulfill_payload is None:
            dedust_swap_params.bits.write_bit(0)
        else:
            dedust_swap_params.bits.write_bit(1)
            dedust_swap_params.bits.write_bit(fulfill_payload)  # Fulfill payload

        if reject_payload is None:
            dedust_swap_params.bits.write_bit(0)
        else:
            dedust_swap_params.bits.write_bit(1)
            dedust_swap_params.bits.write_bit(reject_payload)  # Reject payload

        return dedust_swap_params

    @staticmethod
    def _insert_swap_step(swap_step: SwapStep, inner_swap_cell: TonSdkCell):
        swap_step_cell: TonSdkCell = TonSdkCell()
        swap_step_cell.bits.write_address(TonSdkAddress(swap_step.pool_address))
        swap_step_cell.bits.write_uint(0, 1)  # Swap kind
        swap_step_cell.bits.write_grams(swap_step.limit)  # Swap limit
        swap_step_cell.bits.write_bit(1)  # Maybe refs (yes there are)
        swap_step_cell.refs.append(inner_swap_cell)
        return swap_step_cell

    def pack_swap_steps(self, swap_steps: list[SwapStep]) -> TonSdkCell:
        last_swap_step = swap_steps[-1]
        # last swap step cell
        swap_step_cell: TonSdkCell = TonSdkCell()
        swap_step_cell.bits.write_address(TonSdkAddress(last_swap_step.pool_address))
        swap_step_cell.bits.write_uint(0, 1)  # Swap kind
        swap_step_cell.bits.write_grams(last_swap_step.limit)  # Swap limit
        swap_step_cell.bits.write_bit(0)  # no more refs

        if len(swap_steps) == 1:
            return swap_step_cell

        swap_steps_r = reversed(swap_steps[0:-1])

        for swap_step in swap_steps_r:
            swap_step_cell = self._insert_swap_step(
                swap_step=swap_step, inner_swap_cell=swap_step_cell
            )
        return swap_step_cell


class NativeDedustBuilder(DedustBuilder):

    async def build_swap_body(
        self,
        offer_amount: int,
        swap_steps: list[SwapStep],
        forward_payload: TonSdkCell,
        query_id: int = 0,
    ) -> TonSdkCell:
        dedust_swap_native_body: TonSdkCell = TonSdkCell()
        dedust_swap_native_body.bits.write_uint(0xEA06185D, 32)  # Swap op-code
        dedust_swap_native_body.bits.write_uint(query_id, 64)  # Query id
        dedust_swap_native_body.bits.write_coins(offer_amount)  # Swap amount
        dedust_swap_native_body.write_cell(self.pack_swap_steps(swap_steps=swap_steps))
        dedust_swap_native_body.refs.append(forward_payload)  # store_ref
        return dedust_swap_native_body


class JettonDedustBuilder(DedustBuilder):
    async def build_swap_body(
        self, swap_steps: list[SwapStep], forward_payload: TonSdkCell
    ) -> TonSdkCell:
        dedust_swap_jetton_body: TonSdkCell = TonSdkCell()
        dedust_swap_jetton_body.bits.write_uint(0xE3A0D482, 32)  # Swap op-code
        dedust_swap_jetton_body.write_cell(self.pack_swap_steps(swap_steps=swap_steps))
        dedust_swap_jetton_body.refs.append(forward_payload)
        return dedust_swap_jetton_body
