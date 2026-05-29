import json
import os
import jsonschema
from typing import Dict, Any, Tuple
from sidwell.ajp.schema import AJP, AJPAssumption

class AJPLoader:
    def __init__(self, schema_path: str = None):
        if not schema_path:
            schema_path = os.path.join(os.path.dirname(__file__), "ajp.schema.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)
            
    def load(self, filepath: str) -> Tuple[AJP, Dict[str, Any]]:
        """Loads and validates an AJP file, returning the AJP object and a validation report."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        try:
            jsonschema.validate(instance=data, schema=self.schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(f"AJP Validation Error: {e.message}") from e
            
        ajp = AJP.from_dict(data)
        
        # Build coverage score
        coverage = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNVERIFIED": 0, "FLAGGED": 0}
        for a in ajp.assumptions:
            coverage[a.confidence] += 1
            if a.confidence in ["LOW", "UNVERIFIED"] or a.verify_flag:
                coverage["FLAGGED"] += 1
                
        validation_report = {
            "is_valid": True,
            "coverage": coverage
        }
        return ajp, validation_report

    @staticmethod
    def get_assumption_or_fallback(
        ajp: AJP, 
        driver_id: str, 
        fallback_value: Any, 
        fallback_rationale: str
    ) -> AJPAssumption:
        """
        Retrieves an assumption from the AJP by driver_id.
        If missing, generates a fallback [ENGINE-EST] assumption to prevent crashes.
        """
        for a in ajp.assumptions:
            if a.driver_id == driver_id:
                return a
                
        # Generate fallback
        return AJPAssumption(
            driver_id=driver_id,
            value=fallback_value,
            unit="auto",
            source_type="ENGINE_COMPUTED",
            confidence="LOW",
            verify_flag="ENGINE-EST",
            rationale=fallback_rationale,
            interrogation_refs=[]
        )
