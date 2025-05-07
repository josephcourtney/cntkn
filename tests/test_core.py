import pytest
import tiktoken.model

from cntkn.core import SUPPORTED_MODELS, SUPPORTED_PREFIXES, is_model_supported


@pytest.mark.parametrize("model", SUPPORTED_MODELS[:5])
def test_exact_models_supported(model):
    assert is_model_supported(model)


@pytest.mark.parametrize("prefix", SUPPORTED_PREFIXES[:5])
def test_prefix_models_supported(prefix):
    # simulate a variant
    variant = prefix + "-custom-suffix"
    assert is_model_supported(variant)


@pytest.mark.parametrize("bad", ["", "foo-bar", "gpt-x-unknown"])
def test_invalid_models_not_supported(bad):
    assert not is_model_supported(bad)


def test_supported_lists_match_tiktoken():
    # spot-check that the core lists mirror tiktoken.model
    assert set(SUPPORTED_MODELS) == set(tiktoken.model.MODEL_TO_ENCODING.keys())
    assert set(SUPPORTED_PREFIXES) == set(tiktoken.model.MODEL_PREFIX_TO_ENCODING.keys())
