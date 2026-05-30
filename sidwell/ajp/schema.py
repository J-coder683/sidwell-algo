import dataclasses
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class AJPScenario:
    BEAR: Optional[float]
    BASE: Optional[float]
    BULL: Optional[float]

@dataclass
class AJPOptionTranche:
    shares: float
    strike_price: float

@dataclass
class AJPSegment:
    name: str
    valuation_method: str
    stake_pct: float
    value_mm: float

@dataclass
class AJPAssumption:
    driver_id: str
    value: Any
    unit: str
    source_type: str
    confidence: str
    rationale: str
    interrogation_refs: List[str] = field(default_factory=list)
    scenario: Optional[AJPScenario] = None
    split: Optional[Dict[str, float]] = None
    verify_flag: Optional[str] = None
    options_outstanding: Optional[List[AJPOptionTranche]] = None
    segments: Optional[List[AJPSegment]] = None

@dataclass
class AJPMeta:
    ticker: str
    as_of: str
    currency: str
    sources_ingested: List[str]
    fiscal_year_end_month: int
    last_actual_fy: str
    is_holdco: bool
    scenario_active: str
    gemini_run_id: Optional[str] = None

@dataclass
class AJP:
    meta: AJPMeta
    assumptions: List[AJPAssumption]

    @classmethod
    def from_dict(cls, data: dict) -> "AJP":
        """Tolerant parser: fills missing meta fields and ignores unknown keys so
        imperfect Gemini output still parses into a usable AJP."""
        meta_dict = dict(data.get("meta", {}) or {})
        meta_defaults = {
            "ticker": "", "as_of": "", "currency": "INR_MM",
            "sources_ingested": [], "fiscal_year_end_month": 3,
            "last_actual_fy": "", "is_holdco": False, "scenario_active": "BASE",
        }
        meta_fields = {f.name for f in dataclasses.fields(AJPMeta)}
        merged = {**meta_defaults, **{k: v for k, v in meta_dict.items() if k in meta_fields}}
        meta = AJPMeta(**merged)

        a_fields = {f.name for f in dataclasses.fields(AJPAssumption)}
        assumptions = []
        for a_dict in (data.get("assumptions", []) or []):
            a = {k: v for k, v in dict(a_dict).items() if k in a_fields}
            if not a.get("driver_id"):
                continue
            a.setdefault("unit", "ratio")
            a.setdefault("source_type", "ASSUMED")
            a.setdefault("confidence", "MEDIUM")
            a.setdefault("rationale", "")
            sc = a.get("scenario")
            if isinstance(sc, dict):
                a["scenario"] = AJPScenario(BEAR=sc.get("BEAR"), BASE=sc.get("BASE"), BULL=sc.get("BULL"))
            elif sc is not None and not isinstance(sc, AJPScenario):
                a["scenario"] = None
            if a.get("options_outstanding"):
                a["options_outstanding"] = [
                    AJPOptionTranche(shares=o.get("shares", 0.0), strike_price=o.get("strike_price", 0.0))
                    for o in a["options_outstanding"] if isinstance(o, dict)
                ]
            if a.get("segments"):
                a["segments"] = [
                    AJPSegment(name=s.get("name", ""), valuation_method=s.get("valuation_method", ""),
                               stake_pct=s.get("stake_pct", 1.0), value_mm=s.get("value_mm", 0.0))
                    for s in a["segments"] if isinstance(s, dict)
                ]
            try:
                assumptions.append(AJPAssumption(**a))
            except TypeError:
                continue

        return cls(meta=meta, assumptions=assumptions)
