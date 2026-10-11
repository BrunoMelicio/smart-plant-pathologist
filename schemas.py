from typing import List
from pydantic import BaseModel, Field


class PlantDiagnosisResult(BaseModel):
    plant_name: str = Field(
        default="Unknown Plant",
        description="Identified plant or crop species (common name and botanical name if recognizable).",
    )
    health_status: str = Field(
        default="Undetermined",
        description="Healthy, Mild Deficiency, Moderate Distress, or Critical Infection.",
    )
    severity: str = Field(
        default="Moderate",
        description="Severity level: Healthy, Low, Moderate, High, or Critical.",
    )
    primary_issue: str = Field(
        default="No acute distress identified",
        description="Primary diagnosed disease, deficiency, pest infestation, or environmental distress.",
    )
    visual_symptoms: List[str] = Field(
        default_factory=list,
        description="Specific leaf/stem symptoms spotted by the vision model.",
    )
    remediation_steps: List[str] = Field(
        default_factory=list,
        description="Immediate actionable steps to cure the plant or halt progression.",
    )
    prognosis: str = Field(
        default="Good recovery with timely treatment within 7-14 days.",
        description="Expected recovery timeframe and health outlook.",
    )
    raw_vision_analysis: str = Field(
        default="",
        description="Detailed spatial and color description extracted by Moondream.",
    )
