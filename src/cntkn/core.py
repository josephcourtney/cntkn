import tiktoken
from tiktoken.model import MODEL_PREFIX_TO_ENCODING, MODEL_TO_ENCODING

# pure data for tests and help text
SUPPORTED_MODELS = sorted(MODEL_TO_ENCODING.keys())
SUPPORTED_PREFIXES = sorted(MODEL_PREFIX_TO_ENCODING.keys())


def is_model_supported(name: str) -> bool:
    """Return True if `name` is one of the known models, or starts with one of the supported prefixes."""
    if name in MODEL_TO_ENCODING:
        return True
    return any(name.startswith(pref) for pref in MODEL_PREFIX_TO_ENCODING)


def count_tokens(text: str, model: str = "gpt-4o", *, return_tokens: bool = False) -> int | list[int]:
    """Return number of tokens or the tokens themselves."""
    enc = tiktoken.encoding_for_model(model)
    encoded = enc.encode(text)
    return encoded if return_tokens else len(encoded)


def get_supported_models() -> dict[str, list[str]]:
    return {
        "exact_models": SUPPORTED_MODELS,
        "prefixes": SUPPORTED_PREFIXES,
    }
