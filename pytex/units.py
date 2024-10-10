from decimal import Decimal
from enum import IntEnum

from tonsdk.utils import Address as TonSdkAddress
from tonsdk.boc import Cell as TonSdkCell

TON_ZERO_ADDRESS = "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c"


class PoolType(IntEnum):
    VOLATILE = 0
    STABLE = 1


class AssetType(IntEnum):
    NATIVE = 0
    JETTON = 1


class Asset:
    def __init__(
        self,
        _type: AssetType | None = None,
        address: str | None = None,
        decimals: int | None = None,
        tag: str | None = None,
    ):
        if _type.value is not None and _type.value == AssetType.NATIVE:
            self.address = TonSdkAddress(TON_ZERO_ADDRESS)
            self.decimals = 9
            self.tag = "ton" if tag is None else tag
        elif address is not None:
            self.address = TonSdkAddress(address)
            if address == TON_ZERO_ADDRESS:
                self._type = AssetType.NATIVE
                self.decimals = 9
                self.tag = "ton" if tag is None else tag
            else:
                self._type = AssetType.JETTON
                if decimals is not None:
                    self.decimals = decimals
                else:
                    raise ValueError("Decimals is required for JETTON asset")
                if tag is not None:
                    self.tag = tag
        else:
            raise ValueError("Address is required for JETTON asset")

        self.address = (
            TonSdkAddress(address)
            if address is not None
            else TonSdkAddress(TON_ZERO_ADDRESS)
        )
        self.decimals = decimals
        self.tag = tag
        self.type = _type
        # self.cell: TonSdkCell | None = None
        self.cell = None
        self._get_cell()

    def _get_cell(self):
        if self.type == AssetType.NATIVE:
            asset_native_cell = TonSdkCell()
            asset_native_cell.bits.write_uint(0, 4)  # Asset type is native
            self.cell = asset_native_cell
        elif self.type == AssetType.JETTON:
            asset_jetton_cell = TonSdkCell()
            asset_jetton_cell.bits.write_uint(1, 4)  # Asset type is jetton
            asset_jetton_cell.bits.write_uint(self.address.wc, 8)
            asset_jetton_cell.bits.write_bytes(self.address.hash_part)
            self.cell = asset_jetton_cell


class Reserve:
    def __init__(self, asset: Asset, reserve: Decimal):
        self.asset = asset
        self.reserve = reserve

    def reserve_nano(self, decimals: int | None = None) -> Decimal:
        if decimals is not None:
            return self.reserve * 10 ** (9 - decimals)
        return self.reserve * 10 ** (9 - self.asset.decimals)
