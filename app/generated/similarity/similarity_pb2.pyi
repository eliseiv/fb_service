from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StringListMap(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, key: _Optional[str] = ..., value: _Optional[_Iterable[str]] = ...) -> None: ...

class StringList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, values: _Optional[_Iterable[str]] = ...) -> None: ...

class CountRatioSRequest(_message.Message):
    __slots__ = ("substring", "text")
    SUBSTRING_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    substring: str
    text: str
    def __init__(self, substring: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class CountRatioSResponse(_message.Message):
    __slots__ = ("ratio",)
    RATIO_FIELD_NUMBER: _ClassVar[int]
    ratio: float
    def __init__(self, ratio: _Optional[float] = ...) -> None: ...

class CountRatioRequest(_message.Message):
    __slots__ = ("substring", "text", "root")
    SUBSTRING_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    ROOT_FIELD_NUMBER: _ClassVar[int]
    substring: str
    text: str
    root: int
    def __init__(self, substring: _Optional[str] = ..., text: _Optional[str] = ..., root: _Optional[int] = ...) -> None: ...

class CountRatioResponse(_message.Message):
    __slots__ = ("ratio",)
    RATIO_FIELD_NUMBER: _ClassVar[int]
    ratio: float
    def __init__(self, ratio: _Optional[float] = ...) -> None: ...

class ExtractWordsFromTextRequest(_message.Message):
    __slots__ = ("text",)
    TEXT_FIELD_NUMBER: _ClassVar[int]
    text: str
    def __init__(self, text: _Optional[str] = ...) -> None: ...

class ExtractWordsFromTextResponse(_message.Message):
    __slots__ = ("result",)
    RESULT_FIELD_NUMBER: _ClassVar[int]
    result: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, result: _Optional[_Iterable[str]] = ...) -> None: ...

class SimpleRatioWithLogResponseMap(_message.Message):
    __slots__ = ("ratio", "ratio_log", "intersections")
    RATIO_FIELD_NUMBER: _ClassVar[int]
    RATIO_LOG_FIELD_NUMBER: _ClassVar[int]
    INTERSECTIONS_FIELD_NUMBER: _ClassVar[int]
    ratio: float
    ratio_log: str
    intersections: StringList
    def __init__(self, ratio: _Optional[float] = ..., ratio_log: _Optional[str] = ..., intersections: _Optional[_Union[StringList, _Mapping]] = ...) -> None: ...

class SimpleRatioWithLogRequest(_message.Message):
    __slots__ = ("substring", "text", "url", "synonyms")
    class SynonymsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: StringList
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[StringList, _Mapping]] = ...) -> None: ...
    SUBSTRING_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    SYNONYMS_FIELD_NUMBER: _ClassVar[int]
    substring: str
    text: str
    url: str
    synonyms: _containers.MessageMap[str, StringList]
    def __init__(self, substring: _Optional[str] = ..., text: _Optional[str] = ..., url: _Optional[str] = ..., synonyms: _Optional[_Mapping[str, StringList]] = ...) -> None: ...

class SimpleRatioWithLogResponse(_message.Message):
    __slots__ = ("result",)
    RESULT_FIELD_NUMBER: _ClassVar[int]
    result: SimpleRatioWithLogResponseMap
    def __init__(self, result: _Optional[_Union[SimpleRatioWithLogResponseMap, _Mapping]] = ...) -> None: ...

class GetNltkSynonymsRequest(_message.Message):
    __slots__ = ("remote_syns",)
    REMOTE_SYNS_FIELD_NUMBER: _ClassVar[int]
    remote_syns: str
    def __init__(self, remote_syns: _Optional[str] = ...) -> None: ...

class GetNltkSynonymsResponse(_message.Message):
    __slots__ = ("result",)
    RESULT_FIELD_NUMBER: _ClassVar[int]
    result: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, result: _Optional[_Iterable[str]] = ...) -> None: ...
