from typing import Any

from tonsdk.boc import Cell
from tonsdk.contract import Contract
from tonsdk.contract.wallet import WalletV4ContractR2, SendModeEnum


class ContractMulti(Contract):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    @classmethod
    def create_out_msg(
        cls,
        address: str,
        amount: int,
        payload: str | bytes | Cell | None = None,
        state_init: Cell | None = None,
    ) -> Cell:
        payload_cell = Cell()
        if payload:
            if isinstance(payload, Cell):
                payload_cell = payload
            elif isinstance(payload, str):
                if len(payload) > 0:
                    payload_cell.bits.write_uint(0, 32)
                    payload_cell.bits.write_string(payload)
            else:
                payload_cell.bits.write_bytes(payload)

        order_header = cls.create_internal_message_header(address, amount)
        order = cls.create_common_msg_info(order_header, state_init, payload_cell)
        return order


class WalletContractMulti(WalletV4ContractR2, ContractMulti):
    DEFAULT_SEND_MODE = SendModeEnum.ignore_errors | SendModeEnum.pay_gas_separately

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    def create_transfer_message(
        self,
        to_addr: str,
        amount: int,
        seqno: int,
        payload: Cell | str | bytes | None = None,
        send_mode: int = DEFAULT_SEND_MODE,
        dummy_signature: bool = False,
        state_init: Cell | None = None,
    ):
        return self.create_transfer_messages(
            seqno,
            messages=[
                {
                    "to_address": to_addr,
                    "amount": amount,
                    "payload": payload,
                    "state_init": state_init,
                }
            ],
            send_mode=send_mode,
            dummy_signature=dummy_signature,
        )

    def create_transfer_messages(
        self,
        seqno: int,
        messages: list[dict[str, Any]],
        send_mode: int = DEFAULT_SEND_MODE,
        dummy_signature: bool = False,
    ):
        if seqno < 0:
            raise ValueError("seqno must be integer >= 0")
        if not (1 <= len(messages) <= 4):
            raise ValueError("expected 1-4 messages")
        signing_message = self.create_signing_message(seqno)
        for msg in messages:
            send_mode = msg.get("send_mode", send_mode)
            signing_message.bits.write_uint8(send_mode)
            signing_message.refs.append(
                self.create_out_msg(
                    msg["to_address"],
                    msg["amount"],
                    msg.get("payload"),
                    msg.get("state_init"),
                )
            )
        return self.create_external_message(signing_message, seqno, dummy_signature)
