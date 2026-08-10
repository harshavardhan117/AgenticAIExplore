"""Validate JSON returned by a generation provider."""

import json
from typing import Any

from pydantic import BaseModel, Field

from providers.models import ModelResponse


class JsonValidationResult(BaseModel):
    """The result of checking a model response for a JSON object."""

    is_valid: bool
    parsed_output: dict[str, Any] | None = None
    error_message: str | None = None
    errors: list[str] = Field(default_factory=list)


class JsonResponseValidator:
    """Validate that a model response contains one JSON object."""

    def validate(
        self,
        model_response: ModelResponse,
        expected_output_format: dict[str, Any],
    ) -> JsonValidationResult:
        """Parse model text and validate it against the expected JSON structure."""
        response_text = model_response.text.strip()

        if not response_text:
            return self._invalid_result(["Model response is empty"])

        try:
            parsed_output = json.loads(response_text)
        except json.JSONDecodeError:
            return self._invalid_result(["Model response is not valid JSON"])

        if not isinstance(parsed_output, dict):
            return self._invalid_result(["Model response must contain a JSON object"])

        errors = self._find_structure_errors(
            expected=expected_output_format,
            actual=parsed_output,
            path="$",
        )

        if errors:
            return self._invalid_result(errors)

        return JsonValidationResult(is_valid=True, parsed_output=parsed_output)

    @staticmethod
    def _invalid_result(errors: list[str]) -> JsonValidationResult:
        """Create an invalid result with a summary and detailed errors."""
        return JsonValidationResult(
            is_valid=False,
            error_message=errors[0],
            errors=errors,
        )

    def _find_structure_errors(
        self,
        expected: Any,
        actual: Any,
        path: str,
    ) -> list[str]:
        """Return all structure and value-type mismatches at a JSON path."""
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                return [f"{path} must be an object"]

            errors = []
            for key, expected_value in expected.items():
                child_path = f"{path}.{key}"
                if key not in actual:
                    errors.append(f"{child_path} is required")
                    continue

                errors.extend(
                    self._find_structure_errors(
                        expected=expected_value,
                        actual=actual[key],
                        path=child_path,
                    )
                )

            for key in actual:
                if key not in expected:
                    errors.append(f"{path}.{key} is not allowed")

            return errors

        if isinstance(expected, list):
            if not isinstance(actual, list):
                return [f"{path} must be a list"]

            if not expected:
                return []

            errors = []
            for index, actual_item in enumerate(actual):
                errors.extend(
                    self._find_structure_errors(
                        expected=expected[0],
                        actual=actual_item,
                        path=f"{path}[{index}]",
                    )
                )

            return errors

        if expected is None:
            if actual is not None:
                return [f"{path} must be null"]
            return []

        if isinstance(expected, bool):
            if not isinstance(actual, bool):
                return [f"{path} must be a boolean"]
            return []

        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            if not isinstance(actual, (int, float)) or isinstance(actual, bool):
                return [f"{path} must be a number"]
            return []

        if not isinstance(actual, str):
            return [f"{path} must be text"]

        return []
