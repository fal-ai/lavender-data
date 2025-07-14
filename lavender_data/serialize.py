import io
import numpy as np
import ujson as json
import warnings
from typing import Union

try:
    import torch
except ImportError:
    torch = None


def _int_to_bytes(i: int):
    return i.to_bytes(4, "big")


def _bytes_to_int(b: bytes):
    return int.from_bytes(b, "big")


def _ensure_bytes(content: Union[bytes, memoryview]):
    if isinstance(content, memoryview):
        return content.tobytes()
    return content


def attach_length(content: bytes):
    return _int_to_bytes(len(content)) + content


def detach_length(content: Union[bytes, memoryview]):
    return _bytes_to_int(_ensure_bytes(content[:4])), content[4:]


def serialize_ndarray(ndarray: np.ndarray) -> bytes:
    shape = ndarray.shape
    dtype = str(ndarray.dtype)
    strides = ndarray.strides
    header = serialize_list([shape, dtype, strides])
    header_length = len(header)
    return _int_to_bytes(header_length) + header + ndarray.data.tobytes()


def deserialize_ndarray(data: Union[bytes, memoryview]) -> np.ndarray:
    header_length, data = detach_length(data)
    header = data[:header_length]
    data = data[header_length:]
    shape, dtype, strides = deserialize_list(header)
    ndarray = np.ndarray(shape, dtype, buffer=data, strides=strides)
    return ndarray


def serialize_item(item):
    if isinstance(item, bytes):
        return b"by" + item
    elif torch is not None and isinstance(item, torch.Tensor):
        return b"ts" + serialize_ndarray(item.cpu().numpy())
    elif isinstance(item, np.ndarray):
        return b"np" + serialize_ndarray(item)
    elif isinstance(item, dict):
        return b"di" + serialize_dict(item)
    elif isinstance(item, list):
        return b"ls" + serialize_list(item)
    else:
        try:
            return b"js" + json.dumps(item).encode("utf-8")
        except Exception:
            raise RuntimeError(
                f"This sample contains an object that can not be serialized (type: {type(item)}). "
                "Please ensure that the object one of the following types: "
                f"bytes, {'torch.Tensor, ' if torch is not None else ''}"
                "numpy.ndarray, or json serializable object. "
                + (
                    "If you want to serialize torch.Tensor, please install torch."
                    if torch is None
                    else ""
                )
            )


def deserialize_item(content: Union[bytes, memoryview]):
    type_flag = content[:2]
    value = content[2:]
    if type_flag == b"by":
        return value
    elif type_flag == b"ts":
        if torch is None:
            raise RuntimeError(
                "This sample contains a torch tensor, but torch is not installed and can not be deserialized. "
                "Please install torch to deserialize this sample."
            )
        return torch.from_numpy(deserialize_ndarray(value))
    elif type_flag == b"np":
        return deserialize_ndarray(value)
    elif type_flag == b"di":
        return deserialize_dict(value)
    elif type_flag == b"ls":
        return deserialize_list(value)
    elif type_flag == b"js":
        return json.loads(_ensure_bytes(value).decode("utf-8"))
    else:
        raise ValueError(f"Unknown type flag: {_ensure_bytes(type_flag)}")


def serialize_list(items: list):
    body = b""
    for item in items:
        body += attach_length(serialize_item(item))
    return body


def deserialize_list(content: Union[bytes, memoryview]):
    current = content[:]
    items = []
    while current:
        length, item = detach_length(current)
        items.append(deserialize_item(item[:length]))
        current = item[length:]
    return items


def serialize_dict(items: dict):
    body = b""
    for key, value in items.items():
        body += attach_length(key.encode("utf-8"))
        body += attach_length(serialize_item(value))
    return body


def deserialize_dict(content: Union[bytes, memoryview]):
    current = content[:]
    items = {}
    while current:
        length, key = detach_length(current)
        current = key[length:]
        key = _ensure_bytes(key[:length]).decode("utf-8")
        length, value = detach_length(current)
        items[key] = deserialize_item(value[:length])
        current = value[length:]
    return items


def serialize_sample(sample: dict):
    keys = json.dumps(list(sample.keys())).encode("utf-8")
    header = len(keys).to_bytes(4, "big") + keys
    body = b"sa"
    for value in sample.values():
        body += attach_length(serialize_item(value))

    return header + body


class DeserializeException(Exception):
    pass


def deserialize_sample(content: Union[bytes, memoryview], strict: bool = True):
    header_length, current = detach_length(content)
    keys = json.loads(_ensure_bytes(current[:header_length]).decode("utf-8"))
    current = current[header_length:]
    signature = _ensure_bytes(current[:2])
    if signature != b"sa":
        raise ValueError(f"Unknown signature: {signature}")
    current = current[2:]
    i = 0

    result = {}
    while current and i < len(keys):
        value_length, value = detach_length(current)
        current_value = value[:value_length]
        try:
            result[keys[i]] = deserialize_item(current_value)
        except Exception as e:
            msg = (
                f"Failed to deserialize item {keys[i]}: {e}\n"
                f"Remaining {len(value)} bytes, current item {len(current_value)} bytes, length {value_length}"
            )
            if not strict:
                warnings.warn(msg)
                result[keys[i]] = None
            else:
                raise DeserializeException(msg)
        current = value[value_length:]
        i += 1

    if len(current) > 0:
        warnings.warn(f"Remaining {len(current)} bytes")

    return result
