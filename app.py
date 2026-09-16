from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import yaml

from rules import evaluate_policy
from triage import extract_application


ROOT = Path(__file__).parent


@st.cache_data
def load_policy():
    with open(ROOT / "policy.yaml", "r") as f:
        return yaml.safe_load(f)


@st.cache_data
def load_samples():
    with open(ROOT / "samples.json", "r") as f:
        return json.load(f)


def status_icon(value: str) -> str:
    return {
        "PASS": "✅",
        "FAIL": "❌",
        "UNKNOWN": "❓",
        "HUMAN_REVIEW": "🟡",
    }.get(value, "•")


st.set_page_config(
    page_title="CPN Triage Prototype",
    layout="wide",
)

st.title("Claude Partner Network — AI Triage Prototype")


policy = load_policy()
samples = load_samples()

with st.sidebar:
    st.subheader("Policy")
    st.code(
        yaml.safe_dump(policy, sort_keys=False),
        language="yaml",
    )

    st.caption(
        "Demo policy only — intentionally external to the model prompt."
    )

    st.divider()

    st.subheader("Sample application")

    sample_names = [sample["name"] for sample in samples]

    selected_name = st.selectbox(
        "Load a case",
        sample_names,
    )

    selected = next(
        sample
        for sample in samples
        if sample["name"] == selected_name
    )


default_text = json.dumps(
    selected["application"],
    indent=2,
)

raw_application = st.text_area(
    "Raw partner application",
    value=default_text,
    height=320,
    help="Edit the application to test missing information, contradictions, or adversarial content.",
)

run = st.button(
    "Run triage",
    type="primary",
    use_container_width=True,
)


if run:
    try:
        application = json.loads(raw_application)

    except json.JSONDecodeError as error:
        st.error(
            f"Application JSON is invalid: {error}"
        )
        st.stop()

    with st.spinner(
        "Claude is extracting evidence..."
    ):
        try:
            extraction = extract_application(
                application
            )

        except Exception as error:
            st.error(
                "Claude API call failed. "
                "Check that ANTHROPIC_API_KEY is configured."
            )
            st.exception(error)
            st.stop()

    evaluation = evaluate_policy(
        extraction,
        policy,
    )

    st.divider()

    extraction_col, rules_col, routing_col = st.columns(
        [1.4, 1.1, 1.1]
    )

    with extraction_col:
        st.subheader("1. Evidence Extraction")

        st.json(
            extraction.model_dump()
        )

    with rules_col:
        st.subheader("2. Policy Evaluation")

        for result in evaluation.rule_results:
            st.markdown(
                f"**{status_icon(result.status)} "
                f"{result.rule_id}: {result.status}**"
            )

            st.caption(
                result.explanation
            )

    with routing_col:
        st.subheader("3. Routing")

        if evaluation.route == "QUALIFIED":
            st.success("QUALIFIED")

            st.write(
                "Candidate for human-confirmed approval "
                "or future straight-through processing."
            )

        elif evaluation.route == "NOT_QUALIFIED":
            st.error("APPARENTLY NOT QUALIFIED")

            st.write(
                "Human confirmation required before "
                "an external rejection."
            )

        else:
            st.warning("REVIEW REQUIRED")

        st.write(
            evaluation.reason
        )

        if extraction.recommended_clarification:
            st.markdown(
                "**Suggested applicant follow-up**"
            )

            st.info(
                extraction.recommended_clarification
            )

        if extraction.conflicts:
            st.markdown(
                "**Conflicts**"
            )

            for conflict in extraction.conflicts:
                st.write(
                    f"- {conflict}"
                )

        if extraction.special_handling_flags:
            st.markdown(
                "**Special-handling flags**"
            )

            for flag in extraction.special_handling_flags:
                st.write(
                    f"- {flag}"
                )

    st.divider()

    st.subheader("Reviewer Packet")

    reviewer_packet = {
        "route": evaluation.route,
        "reason": evaluation.reason,
        "policy_version": policy["policy_version"],
        "rules": [
            result.model_dump()
            for result in evaluation.rule_results
        ],
        "missing_information": extraction.missing_information,
        "conflicts": extraction.conflicts,
        "special_handling_flags": extraction.special_handling_flags,
        "recommended_clarification": extraction.recommended_clarification,
    }

    st.json(
        reviewer_packet
    )