from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sqlalchemy import and_, func, or_, select, union_all

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import Base, SessionLocal, engine
from app.models import InteractionSource, InteractionType, SeverityLevel
from app.models.drug import Drug
from app.models.interaction import Condition, Food, Interaction, InteractionSourceAssertion, SourceCoverageCheck
from app.services.normalization import NormalizationResult, normalize_drug_name

CSV_PATH = PROJECT_ROOT / "scripts" / "ddinter_synthetic.csv"


def generate_synthetic_ddinter_data() -> Path:
    rows = [
        {"ddinter_id": "DDI001", "drug_a_name": "warfarin", "drug_b_name": "aspirin", "interaction_level": "Major", "mechanism": "Additive antiplatelet and anticoagulant effects increase bleeding risk.", "management": "Avoid combination or monitor closely for bleeding and INR changes.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI002", "drug_a_name": "warfarin", "drug_b_name": "ciprofloxacin", "interaction_level": "Major", "mechanism": "Ciprofloxacin may inhibit warfarin metabolism and potentiate anticoagulation.", "management": "Monitor INR closely and reduce warfarin dose if needed.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI003", "drug_a_name": "warfarin", "drug_b_name": "clarithromycin", "interaction_level": "Major", "mechanism": "Clarithromycin can increase warfarin exposure and bleeding risk.", "management": "Avoid if possible or intensify INR monitoring.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI004", "drug_a_name": "amiodarone", "drug_b_name": "warfarin", "interaction_level": "Major", "mechanism": "Amiodarone inhibits warfarin clearance and increases anticoagulant effect.", "management": "Lower warfarin dose and monitor INR frequently.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI005", "drug_a_name": "digoxin", "drug_b_name": "clarithromycin", "interaction_level": "Major", "mechanism": "Macrolides may raise digoxin concentrations through gut flora and P-gp effects.", "management": "Check digoxin levels and watch for toxicity.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI006", "drug_a_name": "simvastatin", "drug_b_name": "clarithromycin", "interaction_level": "Contraindicated", "mechanism": "Strong CYP3A4 inhibition can sharply increase simvastatin exposure.", "management": "Avoid combination because of rhabdomyolysis risk.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI007", "drug_a_name": "simvastatin", "drug_b_name": "amiodarone", "interaction_level": "Contraindicated", "mechanism": "Amiodarone increases simvastatin concentration and myopathy risk.", "management": "Avoid or switch to a safer statin.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI008", "drug_a_name": "clopidogrel", "drug_b_name": "omeprazole", "interaction_level": "Major", "mechanism": "Omeprazole may reduce CYP2C19-mediated activation of clopidogrel.", "management": "Use an alternative acid suppressant when possible.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI009", "drug_a_name": "fluoxetine", "drug_b_name": "tramadol", "interaction_level": "Major", "mechanism": "Serotonergic effects and CYP2D6 inhibition increase serotonin syndrome and seizure risk.", "management": "Avoid combination or monitor for neurologic toxicity.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI010", "drug_a_name": "sertraline", "drug_b_name": "tramadol", "interaction_level": "Major", "mechanism": "Combined serotonergic activity may precipitate serotonin toxicity.", "management": "Use another analgesic if possible.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI011", "drug_a_name": "lithium", "drug_b_name": "lisinopril", "interaction_level": "Major", "mechanism": "ACE inhibitors can reduce lithium clearance and increase serum lithium.", "management": "Check lithium levels and renal function closely.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI012", "drug_a_name": "clozapine", "drug_b_name": "ciprofloxacin", "interaction_level": "Contraindicated", "mechanism": "Ciprofloxacin inhibits CYP1A2 and may cause toxic clozapine levels.", "management": "Avoid combination or use a noninteracting antibiotic.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI013", "drug_a_name": "haloperidol", "drug_b_name": "clarithromycin", "interaction_level": "Contraindicated", "mechanism": "Both agents prolong QT interval and can trigger torsades de pointes.", "management": "Avoid combination because of high arrhythmia risk.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI014", "drug_a_name": "tacrolimus", "drug_b_name": "clarithromycin", "interaction_level": "Contraindicated", "mechanism": "CYP3A4 inhibition can cause markedly elevated tacrolimus concentrations.", "management": "Avoid and monitor tacrolimus very closely if unavoidable.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI015", "drug_a_name": "metformin", "drug_b_name": "ciprofloxacin", "interaction_level": "Moderate", "mechanism": "Fluoroquinolones may alter glucose control in patients taking metformin.", "management": "Monitor blood glucose during coadministration.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI016", "drug_a_name": "metoprolol", "drug_b_name": "fluoxetine", "interaction_level": "Moderate", "mechanism": "Fluoxetine inhibits CYP2D6 and may increase metoprolol exposure.", "management": "Monitor for bradycardia and lower metoprolol dose if needed.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI017", "drug_a_name": "metoprolol", "drug_b_name": "sertraline", "interaction_level": "Moderate", "mechanism": "Sertraline can modestly increase beta-blocker concentrations.", "management": "Monitor heart rate and blood pressure.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI018", "drug_a_name": "digoxin", "drug_b_name": "omeprazole", "interaction_level": "Moderate", "mechanism": "Changes in gastric pH and transport may increase digoxin exposure.", "management": "Watch for digoxin toxicity symptoms.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI019", "drug_a_name": "phenytoin", "drug_b_name": "omeprazole", "interaction_level": "Moderate", "mechanism": "Omeprazole may reduce phenytoin clearance and increase serum levels.", "management": "Monitor phenytoin levels and clinical response.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI020", "drug_a_name": "carbamazepine", "drug_b_name": "clarithromycin", "interaction_level": "Major", "mechanism": "Clarithromycin inhibits carbamazepine metabolism and can precipitate toxicity.", "management": "Avoid or check carbamazepine levels closely.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI021", "drug_a_name": "codeine", "drug_b_name": "fluoxetine", "interaction_level": "Moderate", "mechanism": "CYP2D6 inhibition may reduce conversion of codeine to morphine.", "management": "Consider an alternative analgesic if pain control is poor.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI022", "drug_a_name": "codeine", "drug_b_name": "sertraline", "interaction_level": "Moderate", "mechanism": "Sertraline may blunt codeine activation through CYP2D6 inhibition.", "management": "Monitor analgesic response.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI023", "drug_a_name": "clopidogrel", "drug_b_name": "fluoxetine", "interaction_level": "Moderate", "mechanism": "Fluoxetine may impair clopidogrel activation and augment bleeding risk.", "management": "Monitor bleeding and antiplatelet effect clinically.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI024", "drug_a_name": "aspirin", "drug_b_name": "sertraline", "interaction_level": "Moderate", "mechanism": "SSRIs impair platelet aggregation and increase aspirin-related bleeding risk.", "management": "Use gastroprotection and monitor for bleeding.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI025", "drug_a_name": "amiodarone", "drug_b_name": "metoprolol", "interaction_level": "Moderate", "mechanism": "Additive AV nodal suppression may cause symptomatic bradycardia.", "management": "Monitor heart rate, ECG, and blood pressure.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI026", "drug_a_name": "lisinopril", "drug_b_name": "tadalafil", "interaction_level": "Moderate", "mechanism": "Combined vasodilatory effects may produce hypotension.", "management": "Counsel patients on dizziness and monitor blood pressure.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI027", "drug_a_name": "lisinopril", "drug_b_name": "sildenafil", "interaction_level": "Moderate", "mechanism": "Additive blood pressure lowering can increase orthostasis risk.", "management": "Start with lower PDE5 inhibitor doses and monitor symptoms.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI028", "drug_a_name": "warfarin", "drug_b_name": "sertraline", "interaction_level": "Minor", "mechanism": "Sertraline may slightly increase bleeding tendency in anticoagulated patients.", "management": "Counsel on bruising and monitor if symptoms occur.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI029", "drug_a_name": "metformin", "drug_b_name": "lisinopril", "interaction_level": "Minor", "mechanism": "ACE inhibitor initiation may modestly improve insulin sensitivity and alter glucose readings.", "management": "Observe blood glucose after regimen changes.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI030", "drug_a_name": "atorvastatin", "drug_b_name": "aspirin", "interaction_level": "Minor", "mechanism": "No major pharmacokinetic interaction; additive dyspepsia may occur.", "management": "Use routine monitoring only.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI031", "drug_a_name": "omeprazole", "drug_b_name": "lisinopril", "interaction_level": "Minor", "mechanism": "Clinically significant interaction is unlikely, but mild dizziness may occur in some patients.", "management": "Continue usual care and reassess if symptoms develop.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI032", "drug_a_name": "metoprolol", "drug_b_name": "aspirin", "interaction_level": "Minor", "mechanism": "NSAID-like attenuation of antihypertensive effect is minimal with low-dose aspirin.", "management": "Monitor blood pressure with chronic use.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI033", "drug_a_name": "warfarin", "drug_b_name": "grapefruit", "interaction_level": "Moderate", "mechanism": "Grapefruit may alter metabolism and dietary consistency can destabilize anticoagulation.", "management": "Keep diet consistent and monitor INR if intake changes.", "interaction_type": "DFI"},
        {"ddinter_id": "DDI034", "drug_a_name": "simvastatin", "drug_b_name": "grapefruit", "interaction_level": "Contraindicated", "mechanism": "Grapefruit inhibits intestinal CYP3A4 and can markedly increase simvastatin levels.", "management": "Avoid grapefruit products during therapy.", "interaction_type": "DFI"},
        {"ddinter_id": "DDI035", "drug_a_name": "metformin", "drug_b_name": "alcohol", "interaction_level": "Major", "mechanism": "Alcohol can potentiate lactic acidosis risk with metformin.", "management": "Avoid heavy alcohol intake and counsel patients carefully.", "interaction_type": "DFI"},
        {"ddinter_id": "DDI036", "drug_a_name": "warfarin", "drug_b_name": "leafy greens", "interaction_level": "Moderate", "mechanism": "Vitamin K rich foods can reduce anticoagulant effect.", "management": "Maintain consistent vitamin K intake and monitor INR.", "interaction_type": "DFI"},
        {"ddinter_id": "DDI037", "drug_a_name": "tacrolimus", "drug_b_name": "grapefruit", "interaction_level": "Contraindicated", "mechanism": "Grapefruit may greatly increase tacrolimus exposure through CYP3A4 inhibition.", "management": "Avoid grapefruit and monitor tacrolimus levels.", "interaction_type": "DFI"},
        {"ddinter_id": "DDI038", "drug_a_name": "lisinopril", "drug_b_name": "renal impairment", "interaction_level": "Major", "mechanism": "Reduced renal reserve increases risk of ACE inhibitor-associated hyperkalemia and renal injury.", "management": "Use cautiously and monitor creatinine and potassium.", "interaction_type": "DDSI"},
        {"ddinter_id": "DDI039", "drug_a_name": "metformin", "drug_b_name": "renal impairment", "interaction_level": "Contraindicated", "mechanism": "Renal dysfunction increases metformin accumulation and lactic acidosis risk.", "management": "Avoid metformin in severe renal impairment.", "interaction_type": "DDSI"},
        {"ddinter_id": "DDI040", "drug_a_name": "warfarin", "drug_b_name": "pregnancy", "interaction_level": "Contraindicated", "mechanism": "Warfarin crosses the placenta and can cause fetal harm.", "management": "Avoid in pregnancy and switch to safer anticoagulation.", "interaction_type": "DDSI"},
        {"ddinter_id": "DDI041", "drug_a_name": "haloperidol", "drug_b_name": "QT prolongation", "interaction_level": "Contraindicated", "mechanism": "Baseline QT prolongation heightens torsades risk with haloperidol.", "management": "Avoid use or choose a non-QT-prolonging alternative.", "interaction_type": "DDSI"},
        {"ddinter_id": "DDI042", "drug_a_name": "sildenafil", "drug_b_name": "hypotension", "interaction_level": "Major", "mechanism": "Underlying hypotension increases risk of symptomatic blood pressure collapse.", "management": "Use only with careful blood pressure assessment.", "interaction_type": "DDSI"},
        {"ddinter_id": "DDI043", "drug_a_name": "fluoxetine", "drug_b_name": "clozapine", "interaction_level": "Major", "mechanism": "CYP inhibition can elevate clozapine concentrations and toxicity risk.", "management": "Monitor clozapine levels and adverse effects closely.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI044", "drug_a_name": "atorvastatin", "drug_b_name": "clarithromycin", "interaction_level": "Major", "mechanism": "Macrolide inhibition of CYP3A4 may increase atorvastatin exposure.", "management": "Hold atorvastatin temporarily or use another antibiotic.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI045", "drug_a_name": "tacrolimus", "drug_b_name": "fluoxetine", "interaction_level": "Moderate", "mechanism": "Combined CYP interactions may increase tacrolimus concentration variability.", "management": "Check tacrolimus troughs after antidepressant changes.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI046", "drug_a_name": "digoxin", "drug_b_name": "amiodarone", "interaction_level": "Major", "mechanism": "Amiodarone can inhibit P-gp and raise digoxin concentrations.", "management": "Reduce digoxin dose and monitor levels.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI047", "drug_a_name": "phenytoin", "drug_b_name": "warfarin", "interaction_level": "Moderate", "mechanism": "Protein binding displacement and enzyme effects can destabilize anticoagulation.", "management": "Monitor INR closely when starting or stopping either drug.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI048", "drug_a_name": "carbamazepine", "drug_b_name": "warfarin", "interaction_level": "Moderate", "mechanism": "Enzyme induction can reduce warfarin effect and lower INR.", "management": "Increase INR monitoring and adjust dose as needed.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI049", "drug_a_name": "tramadol", "drug_b_name": "haloperidol", "interaction_level": "Major", "mechanism": "Combined seizure threshold lowering and QT effects increase adverse event risk.", "management": "Avoid when possible or monitor neurologic and cardiac status.", "interaction_type": "DDI"},
        {"ddinter_id": "DDI050", "drug_a_name": "tadalafil", "drug_b_name": "metoprolol", "interaction_level": "Minor", "mechanism": "Mild additive blood pressure lowering may occur.", "management": "Counsel patients about dizziness on initiation.", "interaction_type": "DDI"},
    ]

    df = pd.DataFrame(rows)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    return CSV_PATH


def map_severity(raw: str) -> SeverityLevel:
    mapping = {
        "major": SeverityLevel.major,
        "moderate": SeverityLevel.moderate,
        "minor": SeverityLevel.minor,
        "contraindicated": SeverityLevel.contraindicated,
        "avoid": SeverityLevel.contraindicated,
    }
    return mapping.get(raw.lower().strip(), SeverityLevel.unknown)


def get_or_create_food(name: str, db) -> Food:
    food = db.scalar(select(Food).where(func.lower(Food.name) == name.strip().lower()))
    if food is None:
        food = Food(name=name.strip())
        db.add(food)
        db.flush()
    return food


def get_or_create_condition(name: str, db) -> Condition:
    condition = db.scalar(select(Condition).where(func.lower(Condition.name) == name.strip().lower()))
    if condition is None:
        condition = Condition(name=name.strip())
        db.add(condition)
        db.flush()
    return condition


def get_or_create_interaction(row: dict[str, Any], resolved_a: NormalizationResult, resolved_b: Optional[NormalizationResult], food: Optional[Food], condition: Optional[Condition], db) -> tuple[Interaction, bool]:
    interaction_type = InteractionType(row["interaction_type"])

    if interaction_type == InteractionType.DDI:
        drug_a_rxcui, drug_b_rxcui = sorted([resolved_a.rxcui, resolved_b.rxcui])
        statement = select(Interaction).where(
            Interaction.interaction_type == interaction_type,
            Interaction.drug_a_rxcui == drug_a_rxcui,
            Interaction.drug_b_rxcui == drug_b_rxcui,
        )
        interaction = db.scalar(statement)
        if interaction is None:
            interaction = Interaction(
                interaction_type=interaction_type,
                drug_a_rxcui=drug_a_rxcui,
                drug_b_rxcui=drug_b_rxcui,
            )
            db.add(interaction)
            db.flush()
            return interaction, True
        return interaction, False

    if interaction_type == InteractionType.DFI:
        statement = select(Interaction).where(
            Interaction.interaction_type == interaction_type,
            Interaction.drug_a_rxcui == resolved_a.rxcui,
            Interaction.food_id == food.id,
        )
        interaction = db.scalar(statement)
        if interaction is None:
            interaction = Interaction(
                interaction_type=interaction_type,
                drug_a_rxcui=resolved_a.rxcui,
                food_id=food.id,
            )
            db.add(interaction)
            db.flush()
            return interaction, True
        return interaction, False

    statement = select(Interaction).where(
        Interaction.interaction_type == interaction_type,
        Interaction.drug_a_rxcui == resolved_a.rxcui,
        Interaction.condition_id == condition.id,
    )
    interaction = db.scalar(statement)
    if interaction is None:
        interaction = Interaction(
            interaction_type=interaction_type,
            drug_a_rxcui=resolved_a.rxcui,
            condition_id=condition.id,
        )
        db.add(interaction)
        db.flush()
        return interaction, True
    return interaction, False


def upsert_interaction_source_assertion(interaction: Interaction, row: dict[str, Any], db) -> str:
    existing = db.scalar(
        select(InteractionSourceAssertion).where(
            InteractionSourceAssertion.interaction_id == interaction.id,
            InteractionSourceAssertion.source == InteractionSource.DDInter,
            InteractionSourceAssertion.source_record_id == row["ddinter_id"],
        )
    )

    payload = dict(row)
    payload["source"] = InteractionSource.DDInter.value
    severity = map_severity(row["interaction_level"])
    if existing is None:
        db.add(
            InteractionSourceAssertion(
                interaction_id=interaction.id,
                source=InteractionSource.DDInter,
                source_severity_raw=row["interaction_level"],
                severity=severity,
                mechanism=row["mechanism"],
                management=row["management"],
                source_record_id=row["ddinter_id"],
                raw_payload=payload,
            )
        )
        db.flush()
        return "inserted"

    existing.source_severity_raw = row["interaction_level"]
    existing.severity = severity
    existing.mechanism = row["mechanism"]
    existing.management = row["management"]
    existing.raw_payload = payload
    db.flush()
    return "updated"


def add_source_coverage(row: dict[str, Any], resolved_a: NormalizationResult, resolved_b: Optional[NormalizationResult], food: Optional[Food], condition: Optional[Condition], found_interaction: bool, note: Optional[str], db) -> None:
    coverage = SourceCoverageCheck(
        drug_a_rxcui=resolved_a.rxcui,
        drug_b_rxcui=resolved_b.rxcui if resolved_b else None,
        food_id=food.id if food else None,
        condition_id=condition.id if condition else None,
        source=InteractionSource.DDInter,
        found_interaction=found_interaction,
        notes=note,
    )
    db.add(coverage)
    db.flush()


def print_summary(summary: dict[str, Any]) -> None:
    print("\nImport summary")
    print("-" * 60)
    print(f"Total rows processed: {summary['processed']}")
    print(f"Rows imported successfully: {summary['imported']}")
    print(f"Rows updated: {summary['updated']}")
    print(f"Rows quarantined: {summary['quarantined']}")
    print("Severity distribution:")
    for severity, count in summary["severity_distribution"].items():
        print(f"  {severity}: {count}")
    print(f"Unique drug pairs: {summary['unique_pairs']}")
    print(f"DFI rows: {summary['dfi_rows']}")
    print(f"DDSI rows: {summary['ddsi_rows']}")


def print_hub_table(db) -> None:
    involvement = union_all(
        select(Interaction.drug_a_rxcui.label("rxcui")),
        select(Interaction.drug_b_rxcui.label("rxcui")).where(Interaction.drug_b_rxcui.is_not(None)),
    ).subquery()

    statement = (
        select(Drug.preferred_name, func.count().label("interaction_count"))
        .select_from(involvement)
        .join(Drug, Drug.rxcui == involvement.c.rxcui)
        .where(Drug.is_placeholder.is_(False))
        .group_by(Drug.preferred_name)
        .order_by(func.count().desc(), Drug.preferred_name.asc())
        .limit(10)
    )
    rows = db.execute(statement).all()

    print("\nHub drug ranking")
    print("-" * 60)
    print(f"{'Drug':30} {'Interactions':>12}")
    print("-" * 60)
    for preferred_name, interaction_count in rows:
        print(f"{preferred_name[:30]:30} {interaction_count:12d}")


async def import_ddinter(csv_path: Path) -> None:
    Base.metadata.create_all(bind=engine)
    df = pd.read_csv(csv_path)

    print(f"Loaded synthetic DDInter data from {csv_path}")
    print(f"Rows in dataset: {len(df)}")

    with SessionLocal() as db:
        ddi_rows = df[df["interaction_type"] == "DDI"]
        unique_drug_names = sorted(set(ddi_rows["drug_a_name"]).union(set(ddi_rows["drug_b_name"])).union(set(df[df["interaction_type"] != "DDI"]["drug_a_name"])))

        normalization_cache: dict[str, NormalizationResult] = {}
        for index, drug_name in enumerate(unique_drug_names, start=1):
            print(f"[normalize {index}/{len(unique_drug_names)}] {drug_name}")
            normalization_cache[drug_name] = await normalize_drug_name(drug_name, db)

        processed = 0
        imported = 0
        updated = 0
        quarantined = 0
        unique_pairs: set[tuple[Any, ...]] = set()
        severity_distribution: Counter[str] = Counter()
        dfi_rows = 0
        ddsi_rows = 0
        quarantine_log: list[dict[str, Any]] = []

        for _, pandas_row in df.iterrows():
            row = pandas_row.to_dict()
            processed += 1
            severity_distribution[map_severity(row["interaction_level"]).value] += 1

            interaction_type = InteractionType(row["interaction_type"])
            resolved_a = normalization_cache[row["drug_a_name"]]
            resolved_b = normalization_cache[row["drug_b_name"]] if interaction_type == InteractionType.DDI else None
            food = None
            condition = None

            if interaction_type == InteractionType.DFI:
                dfi_rows += 1
                food = get_or_create_food(row["drug_b_name"], db)
            elif interaction_type == InteractionType.DDSI:
                ddsi_rows += 1
                condition = get_or_create_condition(row["drug_b_name"], db)

            unresolved = resolved_a.is_placeholder or not resolved_a.rxcui
            if interaction_type == InteractionType.DDI:
                unresolved = unresolved or resolved_b.is_placeholder or not resolved_b.rxcui

            if unresolved:
                quarantined += 1
                quarantine_reason = {
                    "ddinter_id": row["ddinter_id"],
                    "drug_a_name": row["drug_a_name"],
                    "drug_b_name": row["drug_b_name"],
                    "reason": "Unresolved normalization result",
                }
                quarantine_log.append(quarantine_reason)
                print(f"[quarantine] {row['ddinter_id']} -> {quarantine_reason['reason']}")
                add_source_coverage(row, resolved_a, resolved_b, food, condition, False, quarantine_reason["reason"], db)
                db.commit()
                continue

            interaction, created = get_or_create_interaction(row, resolved_a, resolved_b, food, condition, db)
            if interaction_type == InteractionType.DDI:
                unique_pairs.add((interaction.interaction_type.value, interaction.drug_a_rxcui, interaction.drug_b_rxcui))
            elif interaction_type == InteractionType.DFI:
                unique_pairs.add((interaction.interaction_type.value, interaction.drug_a_rxcui, interaction.food_id))
            else:
                unique_pairs.add((interaction.interaction_type.value, interaction.drug_a_rxcui, interaction.condition_id))

            result = upsert_interaction_source_assertion(interaction, row, db)
            if result == "inserted":
                imported += 1
            else:
                updated += 1

            add_source_coverage(row, resolved_a, resolved_b, food, condition, True, "Imported from synthetic DDInter dataset", db)
            db.commit()

            if created:
                print(f"[interaction] created {interaction.id} for {row['ddinter_id']}")
            else:
                print(f"[interaction] reused {interaction.id} for {row['ddinter_id']}")

        summary = {
            "processed": processed,
            "imported": imported,
            "updated": updated,
            "quarantined": quarantined,
            "severity_distribution": dict(severity_distribution),
            "unique_pairs": len(unique_pairs),
            "dfi_rows": dfi_rows,
            "ddsi_rows": ddsi_rows,
        }

        print_summary(summary)

        if quarantine_log:
            print("\nQuarantine list")
            print("-" * 60)
            for item in quarantine_log:
                print(json.dumps(item))

        print_hub_table(db)


def main() -> None:
    csv_path = generate_synthetic_ddinter_data()
    asyncio.run(import_ddinter(csv_path))


if __name__ == "__main__":
    main()
