from __future__ import annotations

from typing import Protocol

import tiktoken
from tiktoken.model import MODEL_PREFIX_TO_ENCODING, MODEL_TO_ENCODING

# pure data for tests and help text
SUPPORTED_MODELS = sorted(MODEL_TO_ENCODING.keys())
SUPPORTED_PREFIXES = sorted(MODEL_PREFIX_TO_ENCODING.keys())


class TokenCounter(Protocol):
    """Protocol describing something that can count or return tokens for a model."""

    def encode(self, text: str, model: str, *, return_tokens: bool = False) -> int | list[int]: ...


class TiktokenCounter:
    """Production encoder backed by tiktoken."""

    @staticmethod
    def encode(text: str, model: str, *, return_tokens: bool = False) -> int | list[int]:
        if not isinstance(model, str):
            msg = f"model must be a string, got {type(model).__name__}"
            raise TypeError(msg)
        enc = tiktoken.encoding_for_model(model)
        encoded = enc.encode(text)
        return encoded if return_tokens else len(encoded)


def is_model_supported(name: str) -> bool:
    """Return True if `name` is one of the known models, or starts with one of the supported prefixes."""
    if name in MODEL_TO_ENCODING:
        return True
    return any(name.startswith(pref) for pref in MODEL_PREFIX_TO_ENCODING)


def count_tokens(
    text: str,
    model: str = "gpt-4o",
    *,
    return_tokens: bool = False,
    counter: TokenCounter | None = None,
) -> int | list[int]:
    """Return number of tokens or the tokens themselves."""
    impl = counter or TiktokenCounter()
    return impl.encode(text, model, return_tokens=return_tokens)


def get_supported_models() -> dict[str, list[str]]:
    return {
        "exact_models": SUPPORTED_MODELS,
        "prefixes": SUPPORTED_PREFIXES,
    }
