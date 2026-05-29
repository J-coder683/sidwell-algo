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
        meta_dict = data.get("meta", {})
        assumptions_list = data.get("assumptions", [])
        
        meta = AJPMeta(**meta_dict)
        
        assumptions = []
        for a_dict in assumptions_list:
            a = a_dict.copy()
            if "scenario" in a:
                a["scenario"] = AJPScenario(**a["scenario"])
            if "options_outstanding" in a and a["options_outstanding"]:
                a["options_outstanding"] = [AJPOptionTranche(**opt) for opt in a["options_outstanding"]]
            if "segments" in a and a["segments"]:
                a["segments"] = [AJPSegment(**seg) for seg in a["segments"]]
            assumptions.append(AJPAssumption(**a))
            
        return cls(meta=meta, assumptions=assumptions)
