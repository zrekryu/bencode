from collections.abc import Mapping, Sequence
from operator import itemgetter

from .exceptions import BencodeEncodeError

from .delimiters import (
    INT_START_BYTE,
    INT_END_BYTE,
    STRING_SEPARATOR_BYTE,
    LIST_START_BYTE,
    LIST_END_BYTE,
    DICT_START_BYTE,
    DICT_END_BYTE,
)

from .types import BencodeSerializableTypes


class BencodeEncoder:
    @staticmethod
    def encode_int(data: int) -> bytes:
        return INT_START_BYTE + str(data).encode("ascii") + INT_END_BYTE

    @classmethod
    def encode_bool(cls, data: bool) -> bytes:
        return cls.encode_int(int(data))

    @staticmethod
    def encode_byte_string(data: bytes) -> bytes:
        return str(len(data)).encode("ascii") + STRING_SEPARATOR_BYTE + data

    @staticmethod
    def encode_str(data: str) -> bytes:
        encoded_data: bytes = data.encode("utf-8")
        return (
            str(len(encoded_data)).encode("ascii")
            + STRING_SEPARATOR_BYTE
            + encoded_data
        )

    @classmethod
    def encode_list(
        cls, data: Sequence[BencodeSerializableTypes], *, sort_keys: bool = False
    ) -> bytes:
        encoded_list: bytearray = bytearray(LIST_START_BYTE)

        for i, item in enumerate(data):
            try:
                encoded_list += cls.encode(item, sort_keys=sort_keys)
            except BencodeEncodeError:
                raise BencodeEncodeError(
                    f"Unsupported list item: {type(item).__name__} (index: {i})"
                ) from None

        encoded_list += LIST_END_BYTE

        return bytes(encoded_list)

    @staticmethod
    def encode_dict_keys(
        data: Mapping[bytes | str, BencodeSerializableTypes],
    ) -> list[tuple[bytes, BencodeSerializableTypes]]:
        dict_items: list[tuple[bytes, BencodeSerializableTypes]] = []
        for key, value in data.items():
            if not isinstance(key, bytes):
                if isinstance(key, str):
                    encoded_key = key.encode("utf-8")
                else:
                    raise BencodeEncodeError(
                        f"Unsupported dictionary key type: {type(key).__name__}"
                    )

            dict_items.append((encoded_key, value))

        return dict_items

    @classmethod
    def encode_dict(
        cls,
        data: Mapping[bytes | str, BencodeSerializableTypes],
        *,
        sort_keys: bool = False
    ) -> bytes:
        encoded_dict: bytearray = bytearray(DICT_START_BYTE)

        dict_items: list[tuple[bytes, BencodeSerializableTypes]] = cls.encode_dict_keys(
            data
        )

        if sort_keys:
            dict_items.sort(key=itemgetter(0))

        for key, value in dict_items:
            encoded_dict += cls.encode_byte_string(key)

            try:
                encoded_dict += cls.encode(value, sort_keys=sort_keys)
            except BencodeEncodeError:
                raise BencodeEncodeError(
                    f"Unsupported dictionary key value type: {type(value).__name__} (key: {key!r})"
                ) from None

        encoded_dict += DICT_END_BYTE

        return bytes(encoded_dict)

    @classmethod
    def encode(
        cls, data: BencodeSerializableTypes, *, sort_keys: bool = False
    ) -> bytes:
        if isinstance(data, bool):
            return cls.encode_bool(data)
        elif isinstance(data, int):
            return cls.encode_int(data)
        elif isinstance(data, bytes):
            return cls.encode_byte_string(data)
        elif isinstance(data, str):
            return cls.encode_str(data)
        elif isinstance(data, list):
            return cls.encode_list(data, sort_keys=sort_keys)
        elif isinstance(data, dict):
            return cls.encode_dict(data, sort_keys=sort_keys)
        else:
            raise BencodeEncodeError(f"Unsupported data type: {type(data).__name__}")
