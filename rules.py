from __future__ import annotations

from schemas import EvaluationResult, RuleResult, TriageExtraction


def evaluate_policy(
    extraction: TriageExtraction,
    policy: dict
) -> EvaluationResult:
    """
    Evaluate extracted application evidence against deterministic program rules.

    Claude interprets the evidence.
    This rules engine evaluates the policy.
    """

    results: list[RuleResult] = []

    for rule_id, rule in policy["criteria"].items():
        field_name = rule["field"]
        extracted_field = getattr(extraction, field_name)

        # If the application contains conflicting evidence, the rule should not be resolved automatically.
        if extracted_field.status == "CONFLICT":
            results.append(
                RuleResult(
                    rule_id=rule_id,
                    status="HUMAN_REVIEW",
                    explanation=f"Conflicting evidence found for {field_name}.",
                )
            )
            continue

        # Missing evidence stays unresolved.
        if (
            extracted_field.status == "UNKNOWN"
            or extracted_field.value is None
        ):
            results.append(
                RuleResult(
                    rule_id=rule_id,
                    status="UNKNOWN",
                    explanation=f"Required evidence for {field_name} is missing.",
                )
            )
            continue

        rule_type = rule["type"]
        passed = False

        if rule_type == "boolean_equals":
            passed = extracted_field.value == rule["value"]

        elif rule_type == "numeric_gte":
            try:
                passed = float(extracted_field.value) >= float(rule["value"])
            except (TypeError, ValueError):
                results.append(
                    RuleResult(
                        rule_id=rule_id,
                        status="HUMAN_REVIEW",
                        explanation=f"{field_name} could not be evaluated as a number.",
                    )
                )
                continue

        elif rule_type == "enum_in":
            passed = extracted_field.value in rule["values"]

        elif rule_type == "list_intersects":
            values = (
                extracted_field.value
                if isinstance(extracted_field.value, list)
                else [extracted_field.value]
            )

            passed = bool(
                set(values) & set(rule["values"])
            )

        else:
            results.append(
                RuleResult(
                    rule_id=rule_id,
                    status="HUMAN_REVIEW",
                    explanation=f"Unsupported rule type: {rule_type}",
                )
            )
            continue

        results.append(
            RuleResult(
                rule_id=rule_id,
                status="PASS" if passed else "FAIL",
                explanation=(
                    f"{field_name} passed the rule."
                    if passed
                    else f"{field_name} failed the rule."
                ),
            )
        )

    statuses = [result.status for result in results]

    # Sensitive or special-handling cases always require human review
    if extraction.special_handling_flags:
        return EvaluationResult(
            route="REVIEW_REQUIRED",
            rule_results=results,
            reason="Special-handling flag requires human review.",
        )

    # Missing or conflicting information should not become an automatic approval or rejection.
    if any(
        status in {"UNKNOWN", "HUMAN_REVIEW"}
        for status in statuses
    ):
        return EvaluationResult(
            route="REVIEW_REQUIRED",
            rule_results=results,
            reason="Application cannot be resolved from the current evidence.",
        )

    # A hard-rule failure creates an apparent negative outcome. A human should still confirm the rejection.
    if any(status == "FAIL" for status in statuses):
        return EvaluationResult(
            route="NOT_QUALIFIED",
            rule_results=results,
            reason="One or more explicit program rules failed.",
        )

    return EvaluationResult(
        route="QUALIFIED",
        rule_results=results,
        reason="All explicit program rules passed and no escalation flag was triggered.",
    )