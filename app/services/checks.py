from sqlalchemy import func, select, union_all
from sqlalchemy.orm import Session

from app.models.interaction import Interaction
from app.models.drug import Drug
from app.models.patient import PatientMedication


def medications_for_interaction_checks(db: Session, patient_id: str) -> list[PatientMedication]:
    """Exclude placeholder drugs at the query boundary for check orchestration."""

    statement = (
        select(PatientMedication)
        .join(Drug, PatientMedication.rxcui == Drug.rxcui)
        .where(PatientMedication.patient_id == patient_id)
        .where(PatientMedication.is_active.is_(True))
        .where(Drug.is_placeholder.is_(False))
    )
    return list(db.scalars(statement).all())


def get_hub_scores(patient_rxcuis: list[str], db: Session) -> dict[str, int]:
    """
    Given a list of RxCUIs for a patient's medications,
    return a dict of {rxcui: interaction_count} showing
    how many interactions each drug is involved in.
    Excludes placeholder drugs.
    Used by the frontend to rank drugs by interaction burden.
    """

    if not patient_rxcuis:
        return {}

    involvement = union_all(
        select(Interaction.drug_a_rxcui.label("rxcui")),
        select(Interaction.drug_b_rxcui.label("rxcui")).where(Interaction.drug_b_rxcui.is_not(None)),
    ).subquery()

    statement = (
        select(involvement.c.rxcui, func.count().label("interaction_count"))
        .join(Drug, Drug.rxcui == involvement.c.rxcui)
        .where(Drug.is_placeholder.is_(False))
        .where(involvement.c.rxcui.in_(patient_rxcuis))
        .group_by(involvement.c.rxcui)
    )

    return {rxcui: count for rxcui, count in db.execute(statement).all()}
