import os
import hashlib
import urllib.parse
from pathlib import Path
from typing import Optional

from lavender_data.storage.abc import Storage


MULTIPART_CHUNKSIZE = 1 << 23


class S3Storage(Storage):
    scheme = "s3"

    def __init__(self):
        try:
            import boto3
            import botocore.client
        except ImportError:
            raise ImportError(
                "Please install required dependencies for S3Storage. "
                "You can install them with `pip install lavender-data[s3]`"
            )

        endpoint_url = os.getenv("AWS_ENDPOINT_URL", None)
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", None)
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", None)

        config = botocore.client.Config(
            tcp_keepalive=os.getenv("AWS_TCP_KEEPALIVE", "").lower() == "true",
        )
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=config,
        )

    def download(self, remote_path: str, local_path: str) -> None:
        parsed = urllib.parse.urlparse(remote_path)
        bucket = parsed.netloc
        key = parsed.path[1:]

        if Path(local_path).exists():
            # md5 check
            try:
                etag = self.client.head_object(Bucket=bucket, Key=key)["ETag"]
            except Exception as e:
                if "404" in str(e):
                    raise FileNotFoundError(f"File not found: {remote_path}")
                raise

            etag = etag.strip('"')
            etag_parts = etag.split("-")
            if len(etag_parts) == 1:
                etag_hash = etag_parts[0]
                chunk_count = 0
            elif len(etag_parts) == 2:
                etag_hash = etag_parts[0]
                chunk_count = int(etag_parts[1])
            else:
                raise ValueError(f"Invalid etag: {etag}")

            read_chunk_count = 0
            chunks = b""
            with open(local_path, "rb") as f:
                for chunk in iter(lambda: f.read(MULTIPART_CHUNKSIZE), b""):
                    if chunk_count > 0:
                        chunks += hashlib.md5(chunk).digest()
                        read_chunk_count += 1
                    else:
                        chunks += chunk

            if read_chunk_count == chunk_count:
                md5_hash = hashlib.md5(chunks).hexdigest()

                if md5_hash == etag_hash:
                    return

        if not Path(local_path).parent.exists():
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            self.client.download_file(
                Bucket=bucket,
                Key=key,
                Filename=local_path,
            )
        except Exception as e:
            if "404" in str(e):
                raise FileNotFoundError(f"File not found: {remote_path}")
            raise

    def upload(self, local_path: str, remote_path: str) -> None:
        if not Path(local_path).exists():
            raise FileNotFoundError(f"File not found: {local_path}")

        if not Path(local_path).is_file():
            raise FileNotFoundError(f"Not a file: {local_path}")

        parsed = urllib.parse.urlparse(remote_path)
        bucket = parsed.netloc
        key = parsed.path[1:]

        self.client.upload_file(
            Bucket=bucket,
            Key=key,
            Filename=local_path,
        )

    def list(self, remote_path: str, limit: Optional[int] = None) -> list[str]:
        parsed = urllib.parse.urlparse(remote_path)
        bucket = parsed.netloc
        prefix = parsed.path[1:]

        keys = []

        offset = ""
        max_keys = 1000
        while True:
            r = self.client.list_objects_v2(
                Bucket=bucket, MaxKeys=max_keys, StartAfter=offset, Prefix=prefix
            )
            if r.get("Contents") is None:
                break

            for obj in r["Contents"]:
                filename = obj["Key"][len(prefix) :]
                if filename.startswith("/"):
                    filename = filename[1:]
                keys.append(filename)
            offset = r.get("NextContinuationToken")
            if offset is None:
                break
            if limit is not None and len(keys) >= limit:
                keys = keys[:limit]
                break

        return keys

    def get_url(self, remote_path: str):
        parsed = urllib.parse.urlparse(remote_path)
        bucket = parsed.netloc
        prefix = parsed.path[1:]
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": prefix},
            ExpiresIn=60 * 60,
        )
