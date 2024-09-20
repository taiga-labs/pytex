from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

from pytex.dex.base_builder import Builder


class DedustBuilder(Builder):
    @staticmethod
    async def build_swap_params(
        wallet_address: str,
        referral_address: str | None,
        fulfill_payload: TonSdkCell = None,
        reject_payload: TonSdkCell = None,
    ) -> TonSdkCell:
        dedust_swap_params = TonSdkCell()
        dedust_swap_params.bits.write_uint(0, 32)  # Deadline
        dedust_swap_params.bits.write_address(
            TonSdkAddress(wallet_address)
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
    def _insert_swap_step(pool_address: str, inner_swap_cell: TonSdkCell):
        swap_step_cell: TonSdkCell = TonSdkCell()
        swap_step_cell.bits.write_address(TonSdkAddress(pool_address))
        swap_step_cell.bits.write_uint(0, 1)  # Swap kind
        swap_step_cell.bits.write_grams(0)  # Swap limit
        swap_step_cell.bits.write_bit(1)  # Maybe refs (yes there are)
        swap_step_cell.refs.append(inner_swap_cell)
        return swap_step_cell

    def pack_swap_steps(self, pool_addresses_list: list[str]) -> TonSdkCell:
        # last swap step cell
        swap_step_cell: TonSdkCell = TonSdkCell()
        swap_step_cell.bits.write_address(TonSdkAddress(pool_addresses_list[-1]))
        swap_step_cell.bits.write_uint(0, 1)  # Swap kind
        swap_step_cell.bits.write_grams(0)  # Swap limit
        swap_step_cell.bits.write_bit(0)  # no more refs

        if len(pool_addresses_list) == 1:
            return swap_step_cell

        pool_addresses_list_r = reversed(pool_addresses_list[0:-1])

        for pool_addr in pool_addresses_list_r:
            swap_step_cell = self._insert_swap_step(
                pool_address=pool_addr, inner_swap_cell=swap_step_cell
            )
        return swap_step_cell


class NativeDedustBuilder(DedustBuilder):

    async def build_swap_body(
        self,
        offer_amount: int,
        pools: list[str],
        forward_payload: TonSdkCell,
        query_id: int = 0,
    ) -> TonSdkCell:
        dedust_swap_native_body: TonSdkCell = TonSdkCell()
        dedust_swap_native_body.bits.write_uint(0xEA06185D, 32)  # Swap op-code
        dedust_swap_native_body.bits.write_uint(query_id, 64)  # Query id
        dedust_swap_native_body.bits.write_coins(offer_amount)  # Swap amount
        dedust_swap_native_body.write_cell(
            self.pack_swap_steps(pool_addresses_list=pools)
        )
        dedust_swap_native_body.refs.append(forward_payload)  # store_ref
        return dedust_swap_native_body


class JettonDedustBuilder(DedustBuilder):
    async def build_swap_body(
        self, pools: list[str], forward_payload: TonSdkCell
    ) -> TonSdkCell:
        dedust_swap_jetton_body: TonSdkCell = TonSdkCell()
        dedust_swap_jetton_body.bits.write_uint(0xE3A0D482, 32)  # Swap op-code
        dedust_swap_jetton_body.write_cell(
            self.pack_swap_steps(pool_addresses_list=pools)
        )
        dedust_swap_jetton_body.refs.append(forward_payload)
        return dedust_swap_jetton_body
