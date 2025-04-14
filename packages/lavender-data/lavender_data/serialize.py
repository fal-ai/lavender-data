import io
import numpy as np
import ujson as json

try:
    import torch
except ImportError:
    torch = None


def attach_length(content: bytes):
    return len(content).to_bytes(4, "big") + content


def detach_length(content: bytes):
    return int.from_bytes(content[:4], "big"), content[4:]


def serialize_ndarray(ndarray: np.ndarray) -> bytes:
    memfile = io.BytesIO()
    np.save(memfile, ndarray)
    return memfile.getvalue()


def deserialize_ndarray(data: bytes) -> np.ndarray:
    memfile = io.BytesIO(data)
    return np.load(memfile)


def serialize_item(item):
    if isinstance(item, bytes):
        return b"by" + item
    elif torch is not None and isinstance(item, torch.Tensor):
        return b"ts" + serialize_ndarray(item.cpu().numpy())
    elif isinstance(item, np.ndarray):
        return b"np" + serialize_ndarray(item)
    else:
        try:
            return b"js" + json.dumps(item).encode("utf-8")
        except Exception:
            raise RuntimeError(
                "This sample contains an object that can not be serialized. "
                "Please ensure that the object one of the following types: "
                f"bytes, {'torch.Tensor, ' if torch is not None else ''}"
                "numpy.ndarray, or json serializable object. "
                + (
                    "If you want to serialize torch.Tensor, please install torch."
                    if torch is None
                    else ""
                )
            )


def deserialize_item(content: bytes):
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
    elif type_flag == b"js":
        return json.loads(value.decode("utf-8"))
    else:
        raise ValueError(f"Unknown type flag: {type_flag}")


def serialize_list(items: list):
    body = b"ls"
    for item in items:
        body += attach_length(serialize_item(item))
    return body


def deserialize_list(content: bytes):
    current = content[2:]
    items = []
    while current:
        length, item = detach_length(current)
        items.append(deserialize_item(item[:length]))
        current = item[length:]
    return items


def serialize_sample(sample: dict):
    keys = json.dumps(list(sample.keys())).encode("utf-8")
    header = len(keys).to_bytes(4, "big") + keys
    body = b"sa"
    for value in sample.values():
        if isinstance(value, list):
            body += attach_length(serialize_list(value))
        else:
            body += attach_length(serialize_item(value))
    return header + body


def deserialize_sample(content: bytes):
    header_length, current = detach_length(content)
    keys = json.loads(current[:header_length].decode("utf-8"))
    values = []
    current = current[header_length:]
    signature = current[:2]
    if signature != b"sa":
        raise ValueError(f"Unknown signature: {signature}")
    current = current[2:]
    while current:
        value_length, value = detach_length(current)
        current_value = value[:value_length]
        type_flag = current_value[:2]
        if type_flag == b"ls":
            values.append(deserialize_list(current_value))
        else:
            values.append(deserialize_item(current_value))
        current = value[value_length:]
    return dict(zip(keys, values))
