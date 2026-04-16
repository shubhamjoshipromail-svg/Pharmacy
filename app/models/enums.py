import enum

from sqlalchemy import Enum


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


def sql_enum(enum_cls: type[enum.Enum], name: str) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        values_callable=enum_values,
        native_enum=False,
        validate_strings=True,
    )


class SeverityLevel(enum.Enum):
    unknown = "unknown"
    minor = "minor"
    moderate = "moderate"
    major = "major"
    contraindicated = "contraindicated"


class InteractionType(enum.Enum):
    DDI = "DDI"
    DFI = "DFI"
    DDSI = "DDSI"
    therapeutic_duplication = "therapeutic_duplication"


class InteractionSource(enum.Enum):
    DDInter = "DDInter"
    OpenFDA = "OpenFDA"
    RxNorm = "RxNorm"
    manual = "manual"


class NormalizationStatus(enum.Enum):
    matched_exact = "matched_exact"
    matched_brand = "matched_brand"
    matched_fuzzy = "matched_fuzzy"
    matched_ndc = "matched_ndc"
    unmatched = "unmatched"
    manual_override = "manual_override"


class OverrideAction(enum.Enum):
    acknowledged = "acknowledged"
    suppressed_for_patient = "suppressed_for_patient"
    overridden = "overridden"
    escalated = "escalated"
