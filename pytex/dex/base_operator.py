import asyncio
import base64
from decimal import Decimal

import aiohttp
from tonsdk.provider import ToncenterClient, prepare_address
from tonsdk.boc import Cell as TonSdkCell
from tonsdk.utils import Address as TonSdkAddress, bytes_to_b64str

from pytex.exceptions import OperatorError
from pytex.units import Asset, AssetType


class Operator:
    def __init__(self, toncenter_api_key: str):
        self.client = ToncenterClient(
            base_url="https://toncenter.com/api/v2/",
            api_key=toncenter_api_key,
        )

    async def run(self, to_run: dict, *, single_query=True):
        attempt = 1
        while True:
            try:
                return await self._execute(to_run, single_query)
            except BaseException as e:
                pass
            if attempt >= 10:
                raise OperatorError("failed run task | %s: %s", (e.__class__.__name__, e))
            attempt += 1
            await asyncio.sleep(3)

    @staticmethod
    async def _execute(to_run: dict, single_query):
        timeout = aiohttp.ClientTimeout(total=5)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            if single_query:
                to_run = [to_run]

            tasks = []
            for task in to_run:
                tasks.append(task["func"](session, *task["args"], **task["kwargs"]))

            return await asyncio.gather(*tasks)

    @staticmethod
    def _read_address(cell: TonSdkCell) -> TonSdkAddress | None:
        data = "".join([str(cell.bits.get(x)) for x in range(cell.bits.length)])
        if len(data) < 267:
            return None
        wc = int(data[3:11], 2)
        hashpart = int(data[11 : 11 + 256], 2).to_bytes(32, "big").hex()
        return TonSdkAddress(f"{wc if wc != 255 else -1}:{hashpart}")

    @staticmethod
    def _read_asset(cell: TonSdkCell) -> Asset:
        data = "".join([str(cell.bits.get(x)) for x in range(cell.bits.length)])
        _type = int(int(data[:4], 2).to_bytes(1, "big").hex())
        if _type == 0:
            return Asset(_type=AssetType.NATIVE)
        elif _type == 1:
            preaddr = int(int(data[4:12], 2).to_bytes(1, "big").hex())
            address = int(data[12 : 12 + 256], 2).to_bytes(32, "big").hex()
            return Asset(_type=AssetType.JETTON, address=f"{str(preaddr)}:{address}")
        else:
            raise Exception("Failed to read asset")

    async def get_jetton_wallet_address(
        self, jetton_master_address: str, wallet_address: str
    ) -> str | None:
        cell = TonSdkCell()
        cell.bits.write_address(TonSdkAddress(wallet_address))
        request_stack = [["tvm.Slice", bytes_to_b64str(cell.to_boc(False))]]
        raw_get_wallet_address = self.client.raw_run_method(
            method="get_wallet_address",
            address=jetton_master_address,
            stack_data=request_stack,
        )
        raw_data = await self.run(to_run=raw_get_wallet_address)
        try:
            b64_bytes_str = raw_data[0].get("stack")[0][1].get("bytes")
            jetton_wallet_address: TonSdkAddress = self._read_address(
                TonSdkCell.one_from_boc(base64.b64decode(b64_bytes_str))
            )
        except BaseException:
            raise OperatorError(f"parse address | raw_data: {raw_data}")

        return jetton_wallet_address.to_string(True, True, True)

    async def get_status(self, wallet_address: str) -> str | None:
        account_state_task = self.client.raw_get_account_state(
            prepared_address=prepare_address(wallet_address)
        )
        result = await self.run(to_run=account_state_task)
        if "state" in result[0]:
            return str(result[0].get("state"))
        return None

    async def get_seqno(self, wallet_address: str) -> int | None:
        cur_adr_seq_no_task = self.client.raw_run_method(
            method="seqno", address=wallet_address, stack_data=[]
        )
        cur_adr_seq_result = await self.run(to_run=cur_adr_seq_no_task)
        try:
            cur_seq_no = int(cur_adr_seq_result[0].get("stack")[0][1], 16)
        except BaseException:
            raise OperatorError(f"parse seqno | raw_data: {cur_adr_seq_result}")

        return cur_seq_no

    async def get_native_balance(self, wallet_address: str) -> Decimal | None:
        raw_get_account_state_task = self.client.raw_get_account_state(
            prepared_address=wallet_address
        )

        raw_state = await self.run(to_run=raw_get_account_state_task)
        try:
            raw_balance = raw_state[0].get("balance")
        except BaseException:
            raise OperatorError(f"parse balance | raw_data: {raw_state}")

        balance = Decimal(raw_balance)
        return balance

    async def get_jetton_balance(
        self, wallet_address: str, jetton_master_address: str
    ) -> Decimal:
        jetton_wallet_address = await self.get_jetton_wallet_address(
            jetton_master_address=jetton_master_address,
            wallet_address=wallet_address,
        )
        raw_get_wallet_data = self.client.raw_run_method(
            method="get_wallet_data", address=jetton_wallet_address, stack_data=[]
        )

        raw_data = await self.run(to_run=raw_get_wallet_data)
        try:
            hex_balance = raw_data[0].get("stack")[0][1]
        except BaseException:
            raise OperatorError(f"parse balance | raw_data: {raw_data}")

        balance = Decimal(str(int(hex_balance, 0)))
        return balance
