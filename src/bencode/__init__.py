__version__ = "1.0.0"
__author__ = "Zrekryu"

from typing import Protocol

from .exceptions import BencodeEncodeError, BencodeDecodeError

from .types import BencodeDataTypes, BencodeSerializableTypes

from .encoder import BencodeEncoder
from .decoder import BencodeDecoder


class EncodeFunc(Protocol):
    def __call__(
        self, data: BencodeSerializableTypes, *, sort_keys: bool = False
    ) -> bytes: ...


class DecodeFunc(Protocol):
    def __call__(
        self, data: bytes, *, pos: int = 0, validate_sorted_keys: bool = False
    ) -> BencodeDataTypes: ...


encode: EncodeFunc = BencodeEncoder.encode
decode: DecodeFunc = BencodeDecoder.decode

__all__ = [
    "BencodeEncodeError",
    "BencodeDecodeError",
    "BencodeDataTypes",
    "BencodeSerializableTypes",
    "BencodeEncoder",
    "BencodeDecoder",
    "encode",
    "decode",
]
