from pytex.dex.stonfi.op import StonfiOperator


class StonfiV1Operator(StonfiOperator):
    def __init__(self, toncenter_api_key: str):
        super().__init__(toncenter_api_key)
