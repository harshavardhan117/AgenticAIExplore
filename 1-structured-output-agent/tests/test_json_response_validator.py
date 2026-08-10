"""Unit tests for JSON model-output validation."""

from providers.models import ModelResponse
from validation.json_response_validator import JsonResponseValidator


def make_response(text: str) -> ModelResponse:
    """Create a provider-neutral response used by validator tests."""
    return ModelResponse(text=text, provider_name="fake")


def test_accepts_json_that_matches_the_expected_structure() -> None:
    # Arrange
    validator = JsonResponseValidator()
    expected_format = {"summary": "", "priority": {"name": ""}}

    # Act
    result = validator.validate(
        make_response('{"summary": "Login fails", "priority": {"name": "High"}}'),
        expected_format,
    )

    # Assert
    assert result.is_valid is True
    assert result.parsed_output == {
        "summary": "Login fails",
        "priority": {"name": "High"},
    }


def test_rejects_an_empty_model_response() -> None:
    result = JsonResponseValidator().validate(make_response("   "), {"summary": ""})

    assert result.is_valid is False
    assert result.errors == ["Model response is empty"]


def test_rejects_malformed_json() -> None:
    result = JsonResponseValidator().validate(
        make_response('{"summary": "missing closing brace"'),
        {"summary": ""},
    )

    assert result.is_valid is False
    assert result.errors == ["Model response is not valid JSON"]


def test_rejects_a_missing_required_key() -> None:
    result = JsonResponseValidator().validate(
        make_response('{"summary": "Login fails"}'),
        {"summary": "", "description": ""},
    )

    assert result.is_valid is False
    assert result.errors == ["$.description is required"]


def test_rejects_an_incorrect_value_type() -> None:
    result = JsonResponseValidator().validate(
        make_response('{"priority": "High"}'),
        {"priority": {"name": ""}},
    )

    assert result.is_valid is False
    assert result.errors == ["$.priority must be an object"]


def test_rejects_an_unexpected_key() -> None:
    result = JsonResponseValidator().validate(
        make_response('{"summary": "Login fails", "extra": "not allowed"}'),
        {"summary": ""},
    )

    assert result.is_valid is False
    assert result.errors == ["$.extra is not allowed"]


def test_validates_each_item_in_a_non_empty_list_template() -> None:
    result = JsonResponseValidator().validate(
        make_response('{"labels": ["api", 10]}'),
        {"labels": [""]},
    )

    assert result.is_valid is False
    assert result.errors == ["$.labels[1] must be text"]


def test_validates_null_boolean_and_number_values() -> None:
    result = JsonResponseValidator().validate(
        make_response('{"owner": "not null", "approved": "yes", "score": true}'),
        {"owner": None, "approved": False, "score": 0},
    )

    assert result.is_valid is False
    assert result.errors == [
        "$.owner must be null",
        "$.approved must be a boolean",
        "$.score must be a number",
    ]
