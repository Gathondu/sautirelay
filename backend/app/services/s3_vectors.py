from __future__ import annotations

from collections.abc import Mapping, Sequence

SUPPORTED_S3_VECTOR_REGIONS = {
    "af-south-1",
    "ap-east-1",
    "ap-east-2",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-northeast-3",
    "ap-south-1",
    "ap-south-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-southeast-3",
    "ap-southeast-4",
    "ap-southeast-5",
    "ap-southeast-6",
    "ap-southeast-7",
    "ca-central-1",
    "ca-west-1",
    "eu-central-1",
    "eu-central-2",
    "eu-north-1",
    "eu-south-1",
    "eu-south-2",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "mx-central-1",
    "sa-east-1",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
}


def validate_s3_vectors_region(region: str) -> None:
    if region not in SUPPORTED_S3_VECTOR_REGIONS:
        supported = ", ".join(sorted(SUPPORTED_S3_VECTOR_REGIONS))
        raise RuntimeError(f"S3 Vectors is not available in AWS_REGION={region!r}. Supported regions: {supported}")


class S3VectorStore:
    """Small S3 Vectors wrapper for report embeddings."""

    def __init__(
        self,
        *,
        vector_bucket_name: str,
        index_name: str,
        region_name: str,
        client: object | None = None,
    ) -> None:
        validate_s3_vectors_region(region_name)
        self._vector_bucket_name = vector_bucket_name
        self._index_name = index_name
        if client is None:
            import boto3

            client = boto3.client("s3vectors", region_name=region_name)
        self._client = client

    def put_report_embedding(
        self,
        *,
        report_id: str,
        embedding: Sequence[float],
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not embedding:
            return

        self._client.put_vectors(
            vectorBucketName=self._vector_bucket_name,
            indexName=self._index_name,
            vectors=[
                {
                    "key": report_id,
                    "data": {"float32": [float(value) for value in embedding]},
                    "metadata": dict(metadata or {}),
                }
            ],
        )

    def get_report_embedding(self, report_id: str) -> list[float] | None:
        response = self._client.get_vectors(
            vectorBucketName=self._vector_bucket_name,
            indexName=self._index_name,
            keys=[report_id],
            returnData=True,
            returnMetadata=False,
        )
        vectors = response.get("vectors", [])
        if not vectors:
            return None
        vector_data = vectors[0].get("data", {})
        values = vector_data.get("float32")
        if not isinstance(values, list):
            return None
        return [float(value) for value in values]

    def query_similar_reports(self, embedding: Sequence[float], *, top_k: int = 10) -> list[dict[str, object]]:
        response = self._client.query_vectors(
            vectorBucketName=self._vector_bucket_name,
            indexName=self._index_name,
            topK=top_k,
            queryVector={"float32": [float(value) for value in embedding]},
            returnDistance=True,
            returnMetadata=True,
        )
        return list(response.get("vectors", []))
