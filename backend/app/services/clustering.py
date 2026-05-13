from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.core.config import get_settings

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_VECTOR_DIMENSIONS = 96
DEFAULT_SIMILARITY_THRESHOLD = 0.72

_TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


@dataclass(frozen=True)
class SimilarReport:
    report_id: str
    similarity: float
    category: str | None = None
    area: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SignalCluster:
    cluster_id: str
    title: str
    report_ids: list[str]
    summary: str
    category: str
    risk_level: str
    average_similarity: float
    status: str = "PENDING_REVIEW"

    @property
    def report_count(self) -> int:
        return len(self.report_ids)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class EmbeddingService:
    """OpenAI-backed embeddings with deterministic local fallback."""

    def __init__(
        self,
        *,
        model: str | None = None,
        dimensions: int | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        input_type: str | None = None,
        extra_body: dict[str, object] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.embedding_model or DEFAULT_EMBEDDING_MODEL
        self.dimensions = dimensions if dimensions is not None else settings.embedding_dimensions
        self.local_dimensions = self.dimensions or DEFAULT_VECTOR_DIMENSIONS
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.base_url = base_url if base_url is not None else settings.openai_base_url
        self.input_type = input_type if input_type is not None else settings.embedding_input_type
        self.extra_body = extra_body if extra_body is not None else settings.embedding_extra_body
        self.extra_headers = extra_headers if extra_headers is not None else settings.embedding_extra_headers

    def embed_text(self, text: str | None) -> list[float]:
        body = (text or "").strip()
        if self.api_key and body:
            try:
                from openai import OpenAI

                if self.base_url:
                    client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                else:
                    client = OpenAI(api_key=self.api_key)
                request_kwargs: Mapping[str, Any] = {
                    "input": body.replace("\n", " "),
                    "model": self.model,
                }
                open_ai_model = self.model.startswith("text-embedding") or self.model.startswith("openai/")
                if self.dimensions is not None:
                    request_kwargs["dimensions"] = self.dimensions

                extra_body = dict(self.extra_body)
                if self.input_type:
                    extra_body["input_type"] = self.input_type
                if extra_body:
                    request_kwargs["extra_body"] = extra_body
                if self.extra_headers:
                    request_kwargs["extra_headers"] = self.extra_headers
                if not open_ai_model:
                    request_kwargs["encoding_format"] = "float"
                    request_kwargs["check_embedding_ctx_length"] = False

                response = client.embeddings.create(**request_kwargs)
                return _normalize(response.data[0].embedding)
            except Exception:
                return deterministic_embedding(body, dimensions=self.local_dimensions)
        return deterministic_embedding(body, dimensions=self.local_dimensions)

    def embed_many(self, texts: Iterable[str | None]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


def deterministic_embedding(text: str | None, *, dimensions: int = DEFAULT_VECTOR_DIMENSIONS) -> list[float]:
    """Stable bag-of-words hash embedding for tests and local no-key runs."""

    vector = [0.0 for _ in range(dimensions)]
    tokens = _tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    for left, right in zip(tokens, tokens[1:], strict=False):
        pair = f"{left}_{right}"
        digest = hashlib.sha256(pair.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        vector[index] += 0.5

    return _normalize(vector)


def cosine_similarity(left: Sequence[float] | None, right: Sequence[float] | None) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)


def find_similar_reports(
    target: object,
    candidates: Iterable[object],
    *,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    embedding_service: EmbeddingService | None = None,
) -> list[SimilarReport]:
    service = embedding_service or EmbeddingService()
    target_embedding = _embedding_for(target, service)
    results: list[SimilarReport] = []

    for candidate in candidates:
        candidate_id = str(_get(candidate, "id", _get(candidate, "report_id", "")))
        target_id = str(_get(target, "id", _get(target, "report_id", "")))
        if candidate_id and candidate_id == target_id:
            continue
        score = cosine_similarity(target_embedding, _embedding_for(candidate, service))
        if score >= threshold:
            results.append(
                SimilarReport(
                    report_id=candidate_id,
                    similarity=round(score, 4),
                    category=_optional_str(_get(candidate, "category")),
                    area=_area_for(candidate),
                )
            )

    return sorted(results, key=lambda item: item.similarity, reverse=True)


def generate_clusters(
    reports: Iterable[object],
    *,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    embedding_service: EmbeddingService | None = None,
) -> list[SignalCluster]:
    service = embedding_service or EmbeddingService()
    report_list = list(reports)
    if not report_list:
        return []

    embeddings = [_embedding_for(report, service) for report in report_list]
    visited: set[int] = set()
    clusters: list[SignalCluster] = []

    for index, _report in enumerate(report_list):
        if index in visited:
            continue

        member_indexes = [index]
        visited.add(index)
        for other_index in range(index + 1, len(report_list)):
            if other_index in visited:
                continue
            similarity = cosine_similarity(embeddings[index], embeddings[other_index])
            if similarity >= threshold:
                member_indexes.append(other_index)
                visited.add(other_index)

        if len(member_indexes) < 2:
            continue

        members = [report_list[member_index] for member_index in member_indexes]
        similarities = [
            cosine_similarity(embeddings[member_indexes[0]], embeddings[member_index])
            for member_index in member_indexes[1:]
        ]
        category = _majority(_optional_str(_get(member, "category")) for member in members) or "NOT_SURE"
        risk_level = _highest_risk(_optional_str(_get(member, "risk_level")) for member in members)
        report_ids = [str(_get(member, "id", _get(member, "report_id", ""))) for member in members]
        title = f"Potential {category.lower().replace('_', ' ')} signal"
        summary = generate_cluster_summary(members, category=category)
        cluster_id = stable_cluster_id(report_ids)
        clusters.append(
            SignalCluster(
                cluster_id=cluster_id,
                title=title,
                report_ids=report_ids,
                summary=summary,
                category=category,
                risk_level=risk_level,
                average_similarity=round(sum(similarities) / len(similarities), 4),
            )
        )

    return clusters


def cluster_reports(
    reports: Iterable[object],
    *,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    embedding_service: EmbeddingService | None = None,
) -> list[SignalCluster]:
    return generate_clusters(
        reports,
        threshold=similarity_threshold,
        embedding_service=embedding_service,
    )


def generate_cluster_summary(reports: Iterable[object], *, category: str | None = None) -> str:
    report_list = list(reports)
    count = len(report_list)
    category_text = (category or "community").lower().replace("_", " ")
    areas = [_area_for(report) for report in report_list if _area_for(report)]
    area_text = f" around {areas[0]}" if areas else ""
    return (
        f"{count} related anonymous reports describe a possible {category_text} pattern"
        f"{area_text}. Human verification is recommended before mediator escalation."
    )


def stable_cluster_id(report_ids: Iterable[str]) -> str:
    normalized = "|".join(sorted(report_id for report_id in report_ids if report_id))
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
    return f"cluster_{digest}"


def _embedding_for(value: object, service: EmbeddingService) -> list[float]:
    existing = _get(value, "embedding")
    if isinstance(existing, list) and existing and all(isinstance(item, (int, float)) for item in existing):
        return [float(item) for item in existing]
    return service.embed_text(_text_for(value))


def _text_for(value: object) -> str:
    parts = [
        _get(value, "redacted_text"),
        _get(value, "translated_text"),
        _get(value, "summary"),
        _get(value, "raw_text"),
        _get(value, "description"),
        _get(value, "text"),
        _get(value, "category"),
    ]
    return " ".join(str(part) for part in parts if part)


def _area_for(value: object) -> str | None:
    location = _get(value, "approximate_location", _get(value, "location"))
    if isinstance(location, dict):
        area = (
            location.get("mediator_area")
            or location.get("analytics_area")
            or location.get("internal_area")
            or location.get("admin_level_2")
            or location.get("admin_level_1")
            or location.get("country")
            or location.get("manualDescription")
        )
        return str(area) if area else None
    return _optional_str(location)


def _tokenize(text: str | None) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return [0.0 for _ in vector]
    return [float(value) / norm for value in vector]


def _get(value: object, key: str, default: object = None) -> object:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _majority(values: Iterable[str | None]) -> str | None:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda item: item[1])[0]


def _highest_risk(values: Iterable[str | None]) -> str:
    rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    highest = "LOW"
    for value in values:
        normalized = (value or "LOW").upper()
        if rank.get(normalized, 0) > rank[highest]:
            highest = normalized
    return highest
