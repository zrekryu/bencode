type BencodeDataTypes = (
    int
    | bytes
    | list[BencodeDataTypes]
    | dict[bytes, BencodeDataTypes]
)

type BencodeSerializableTypes = (
    int
    | bool
    | bytes
    | str
    | list[BencodeSerializableTypes]
    | dict[bytes | str, BencodeSerializableTypes]
)