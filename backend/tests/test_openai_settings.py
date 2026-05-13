from __future__ import annotations

from typing import Any

import pytest
from backend.app.core.config import get_settings
from backend.app.services.clustering import EmbeddingService
from backend.app.services.openai_intake import (
    OpenAIIntakeService,
    _create_openai_client,
)


def test_openai_settings_prefer_sautirelay_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openrouter-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("OPENAI_MODEL", "openrouter/model")
    monkeypatch.setenv("EMBEDDING_MODEL", "openrouter/embedding-model")
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "384")
    monkeypatch.setenv("EMBEDDING_INPUT_TYPE", "search_document")
    monkeypatch.setenv(
        "EMBEDDING_EXTRA_BODY",
        '{"provider":{"allow_fallbacks":true,"data_collection":"deny"}}',
    )
    monkeypatch.setenv(
        "EMBEDDING_EXTRA_HEADERS",
        '{"HTTP-Referer":"http://localhost:5173","X-Title":"SautiRelay"}',
    )
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.openai_api_key == "openrouter-key"
    assert settings.openai_base_url == "https://openrouter.ai/api/v1"
    assert settings.openai_model == "openrouter/model"
    assert settings.embedding_model == "openrouter/embedding-model"
    assert settings.embedding_dimensions == 384
    assert settings.embedding_input_type == "search_document"
    assert settings.embedding_extra_body == {
        "provider": {
            "allow_fallbacks": True,
            "data_collection": "deny",
        },
    }
    assert settings.embedding_extra_headers == {
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "SautiRelay",
    }


def test_intake_service_passes_configured_base_url_to_openai_client(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_kwargs: dict[str, Any] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured_kwargs.update(kwargs)

    monkeypatch.setattr("backend.app.services.openai_intake.OpenAI", FakeOpenAI)

    _create_openai_client(api_key="openrouter-key", base_url="https://openrouter.ai/api/v1")

    assert captured_kwargs == {
        "api_key": "openrouter-key",
        "base_url": "https://openrouter.ai/api/v1",
    }


def test_services_read_configured_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openrouter-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    get_settings.cache_clear()

    intake_service = OpenAIIntakeService()
    embedding_service = EmbeddingService()

    assert intake_service.api_key == "openrouter-key"
    assert intake_service.base_url == "https://openrouter.ai/api/v1"
    assert embedding_service.api_key == "openrouter-key"
    assert embedding_service.base_url == "https://openrouter.ai/api/v1"


def test_embedding_service_sends_provider_specific_kwargs(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_client_kwargs: dict[str, Any] = {}
    captured_embedding_kwargs: dict[str, Any] = {}

    class FakeEmbeddings:
        @staticmethod
        def create(**kwargs: Any) -> Any:
            captured_embedding_kwargs.update(kwargs)

            class Response:
                data = [type("Embedding", (), {"embedding": [0.5, 0.5]})()]

            return Response()

    class FakeOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured_client_kwargs.update(kwargs)
            self.embeddings = FakeEmbeddings()

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)

    service = EmbeddingService(
        api_key="openrouter-key",
        base_url="https://openrouter.ai/api/v1",
        model="provider/embedding-model",
        dimensions=384,
        input_type="search_document",
        extra_body={"provider": {"allow_fallbacks": True}},
        extra_headers={"HTTP-Referer": "http://localhost:5173"},
    )

    assert service.embed_text("Report text") == pytest.approx([0.70710678118, 0.70710678118])
    assert captured_client_kwargs == {
        "api_key": "openrouter-key",
        "base_url": "https://openrouter.ai/api/v1",
    }
    assert captured_embedding_kwargs == {
        "input": "Report text",
        "model": "provider/embedding-model",
        "dimensions": 384,
        "extra_body": {
            "provider": {"allow_fallbacks": True},
            "input_type": "search_document",
        },
        "extra_headers": {"HTTP-Referer": "http://localhost:5173"},
    }


def test_embedding_dimensions_are_omitted_unless_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_embedding_kwargs: dict[str, Any] = {}

    class FakeEmbeddings:
        @staticmethod
        def create(**kwargs: Any) -> Any:
            captured_embedding_kwargs.update(kwargs)

            class Response:
                data = [type("Embedding", (), {"embedding": [1.0, 0.0]})()]

            return Response()

    class FakeOpenAI:
        def __init__(self, **_: Any) -> None:
            self.embeddings = FakeEmbeddings()

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)

    service = EmbeddingService(api_key="openrouter-key", model="provider/fixed-dimension-model")
    service.embed_text("Report text")

    assert "dimensions" not in captured_embedding_kwargs
