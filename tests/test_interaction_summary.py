from types import SimpleNamespace

from app.models.enums import InteractionType, SeverityLevel
from app.schemas.interaction import build_summary


def test_build_summary_uses_max_severity_and_marks_source_conflict():
    interaction = SimpleNamespace(
        drug_a_rxcui="111",
        drug_b_rxcui="222",
        interaction_type=InteractionType.DDI,
        drug_a=SimpleNamespace(preferred_name="Evaluation Drug A"),
        drug_b=SimpleNamespace(preferred_name="Evaluation Drug B"),
        food=None,
        condition=None,
        llm_explanations=[],
    )
    assertions = [
        SimpleNamespace(
            severity=SeverityLevel.minor,
            mechanism="Minor mechanism text",
            management="Monitor therapy",
            raw_payload={"effect": "Minor effect"},
        ),
        SimpleNamespace(
            severity=SeverityLevel.major,
            mechanism="Major mechanism text",
            management="Avoid combination when possible",
            raw_payload={"effect": "Major effect"},
        ),
    ]

    summary = build_summary(interaction, assertions, {"111": 7, "222": 2})

    assert summary.severity == SeverityLevel.major
    assert summary.max_severity == SeverityLevel.major
    assert summary.sources_conflict is True
    assert summary.drug_a_name == "Evaluation Drug A"
    assert summary.drug_b_name == "Evaluation Drug B"
    assert summary.hub_score_a == 7
    assert summary.hub_score_b == 2


def test_build_summary_uses_condition_name_for_ddsi():
    interaction = SimpleNamespace(
        drug_a_rxcui="111",
        drug_b_rxcui=None,
        interaction_type=InteractionType.DDSI,
        drug_a=SimpleNamespace(preferred_name="Evaluation Drug A"),
        drug_b=None,
        food=None,
        condition=SimpleNamespace(name="renal impairment"),
        llm_explanations=[],
    )
    assertions = [
        SimpleNamespace(
            severity=SeverityLevel.moderate,
            mechanism="Condition-specific mechanism",
            management="Use caution",
            raw_payload={},
        )
    ]

    summary = build_summary(interaction, assertions, {"111": 3})

    assert summary.interaction_type == InteractionType.DDSI
    assert summary.drug_b_name == "renal impairment"
    assert summary.severity == SeverityLevel.moderate
