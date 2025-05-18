from .exceptions import BencodeDecodeError

from .delimiters import (
    NEGATIVE_SIGN_ORD,
    INT_START_ORD,
    INT_START_BYTE,
    INT_END_ORD,
    INT_END_BYTE,
    ZERO_ORD,
    NINE_ORD,
    STRING_SEPARATOR_ORD,
    STRING_SEPARATOR_BYTE,
    LIST_START_ORD,
    LIST_START_BYTE,
    LIST_END_ORD,
    LIST_END_BYTE,
    DICT_START_ORD,
    DICT_START_BYTE,
    DICT_END_ORD,
    DICT_END_BYTE,
)

from .types import BencodeDataTypes


class BencodeDecoder:
    @staticmethod
    def decode_int(data: memoryview | bytes, *, pos: int = 0) -> tuple[int, int]:
        data = memoryview(data).cast("B") if not isinstance(data, memoryview) else data

        if data[pos] != INT_START_ORD:
            raise BencodeDecodeError(
                f"Malformed integer: expected integer start: {INT_START_BYTE!r} (got {chr(data[pos])!r} instead)"
            )
        if data[pos + 1] == INT_END_ORD:
            raise BencodeDecodeError("Malformed integer: no integer was present")

        end_pos: int | None = None
        for i in range(pos + 1, len(data)):
            if data[i] == INT_END_ORD:
                end_pos = i
                break
        else:
            raise BencodeDecodeError(
                f"Malformed integer: missing integer end: {INT_END_BYTE!r}"
            )

        is_negative: bool = False
        if data[pos + 1] == NEGATIVE_SIGN_ORD:
            is_negative = True

            if data[pos + 2] == INT_END_ORD:
                raise BencodeDecodeError(
                    "Malformed integer: negative sign without integer value"
                )
            if data[pos + 2] == ZERO_ORD:
                raise BencodeDecodeError(
                    "Invalid integer: negative zero is not permitted"
                )

        if data[pos + 1] == ZERO_ORD and data[pos + 2] != INT_END_ORD:
            raise BencodeDecodeError(
                f"Malformed integer: leading zeros are not permitted"
            )

        num: int = 0
        start_pos: int = pos + 2 if is_negative else pos + 1
        for i in range(start_pos, end_pos):
            if not ZERO_ORD <= data[i] <= NINE_ORD:
                raise BencodeDecodeError(
                    f"Invalid integer: unexpected byte {chr(data[i])} at index: {i}"
                )

            num = num * 10 + (data[i] - ZERO_ORD)

        num = -num if is_negative else num

        return (num, end_pos + 1)

    @staticmethod
    def decode_byte_string(
        data: memoryview | bytes, *, pos: int = 0
    ) -> tuple[bytes, int]:
        data = memoryview(data).cast("B") if not isinstance(data, memoryview) else data

        if data[pos] == NEGATIVE_SIGN_ORD:
            raise BencodeDecodeError(
                "Malformed byte string: length prefix must not be negative"
            )

        if not ZERO_ORD <= data[pos] <= NINE_ORD:
            raise BencodeDecodeError(
                f"Malformed byte string: expected length prefix (got {chr(data[pos])!r} instead)"
            )

        sep_pos: int | None = None
        for i in range(pos, len(data)):
            if data[i] == STRING_SEPARATOR_ORD:
                sep_pos = i
                break
        else:
            raise BencodeDecodeError(
                f"Malformed byte string: missing length seperator: {STRING_SEPARATOR_BYTE!r}"
            )

        length_prefix: int = 0
        for i in range(pos, sep_pos):
            if not ZERO_ORD <= data[i] <= NINE_ORD:
                raise BencodeDecodeError(
                    f"Invalid byte string: length prefix is not a valid integer: {chr(data[i])} (index: {i})"
                )

            length_prefix = length_prefix * 10 + (data[i] - ZERO_ORD)

        end_pos: int = sep_pos + 1 + length_prefix
        byte_string: bytes = data[sep_pos + 1 : end_pos].tobytes()

        length: int = len(byte_string)
        if length < length_prefix:
            raise BencodeDecodeError(
                f"Invalid byte string: byte string length does not match length prefix (expected: {length_prefix}, got: {length})"
            )

        return (byte_string, end_pos)

    @classmethod
    def decode_list(
        cls,
        data: memoryview | bytes,
        *,
        pos: int = 0,
        validate_sorted_keys: bool = False,
    ) -> tuple[list[BencodeDataTypes], int]:
        data = memoryview(data).cast("B") if not isinstance(data, memoryview) else data

        if data[pos] != LIST_START_ORD:
            raise BencodeDecodeError(
                f"Malformed list: expected list start: {INT_START_BYTE!r} (got {chr(data[pos])!r} instead)"
            )

        item: BencodeDataTypes
        items: list[BencodeDataTypes] = []

        curr_pos = pos + 1
        while curr_pos < len(data):
            if data[curr_pos] == LIST_END_ORD:
                break

            try:
                item, curr_pos = cls.decode_data(
                    data, pos=curr_pos, validate_sorted_keys=validate_sorted_keys
                )
            except BencodeDecodeError:
                raise BencodeDecodeError(
                    f"Invalid list: unsupported list item: {chr(data[curr_pos])!r}"
                ) from None

            items.append(item)
        else:
            raise BencodeDecodeError(
                f"Malformed list: missing list end: {LIST_END_BYTE!r}"
            )

        return (items, curr_pos + 1)

    @classmethod
    def decode_dict(
        cls,
        data: memoryview | bytes,
        *,
        pos: int = 0,
        validate_sorted_keys: bool = False,
    ) -> tuple[dict[bytes, BencodeDataTypes], int]:
        data = memoryview(data).cast("B") if not isinstance(data, memoryview) else data

        if data[pos] != DICT_START_ORD:
            raise BencodeDecodeError(
                f"Malformed dictionary: expected dictionary start: {DICT_START_BYTE!r} (got {chr(data[pos])!r} instead)"
            )

        decoded_dict: dict[bytes, BencodeDataTypes] = {}

        key: bytes
        value: BencodeDataTypes
        previous_key: bytes | None = None

        curr_pos = pos + 1
        while curr_pos < len(data):
            if data[curr_pos] == DICT_END_ORD:
                break

            if not ZERO_ORD <= data[curr_pos] <= NINE_ORD:
                raise BencodeDecodeError(
                    f"Malformed dictionary: key must be a byte string (got {chr(data[curr_pos])!r} instead)"
                )

            key, curr_pos = cls.decode_byte_string(data, pos=curr_pos)

            if validate_sorted_keys and previous_key is not None and key < previous_key:
                raise BencodeDecodeError(
                    f"Invalid dictionary: keys are not sorted in lexicographical order (current key: {key!r}, previous key: {previous_key!r})"
                )

            previous_key = key

            try:
                value, curr_pos = cls.decode_data(
                    data, pos=curr_pos, validate_sorted_keys=validate_sorted_keys
                )
            except BencodeDecodeError:
                raise BencodeDecodeError(
                    f"Invalid dictionary: unsupported key value: {chr(data[curr_pos])!r}"
                ) from None

            decoded_dict[key] = value
        else:
            raise BencodeDecodeError(
                f"Malformed dictionary: missing dictionary end: {DICT_END_BYTE!r}"
            )

        return (decoded_dict, curr_pos + 1)

    @classmethod
    def decode_data(
        cls, data: bytes, *, pos: int = 0, validate_sorted_keys: bool = False
    ) -> tuple[BencodeDataTypes, int]:
        char: int = data[pos]
        if char == INT_START_ORD:
            return cls.decode_int(data, pos=pos)
        elif ZERO_ORD <= char <= NINE_ORD:
            return cls.decode_byte_string(data, pos=pos)
        elif char == LIST_START_ORD:
            return cls.decode_list(
                data, pos=pos, validate_sorted_keys=validate_sorted_keys
            )
        elif char == DICT_START_ORD:
            return cls.decode_dict(
                data, pos=pos, validate_sorted_keys=validate_sorted_keys
            )
        else:
            raise BencodeDecodeError(f"Malformed data: {chr(char)!r}")

    @classmethod
    def decode(
        cls, data: bytes, *, pos: int = 0, validate_sorted_keys: bool = False
    ) -> BencodeDataTypes:
        return cls.decode_data(
            data, pos=pos, validate_sorted_keys=validate_sorted_keys
        )[0]
