"""Advisory analysis endpoint running the pure domain forecasting pipeline."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from purecast.api.schemas.analyze import (
    AnalyzeRequest,
    AnalyzeResponse,
    DiagnosisSchema,
    StageForecastSchema,
)
from purecast.core.deps import get_current_user, require_roles
from purecast.domain.enums import Role
from purecast.domain.reading import SensorReading
from purecast.domain.services.pipeline import DeviceState, analyze
from purecast.infrastructure.db.models import User

router = APIRouter(
    prefix="/analyze",
    tags=["analysis"],
    dependencies=[
        Depends(
            require_roles(
                Role.PLATFORM_ADMIN,
                Role.TENANT_ADMIN,
                Role.TENANT_ANALYST,
                Role.SERVICE_TECHNICIAN,
                Role.HOUSEHOLD_OWNER,
                Role.DEVICE,
            )
        )
    ],
)


@router.post("", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
async def run_analysis(
    req: AnalyzeRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> AnalyzeResponse:
    """Execute domain prognostics and diagnostics pipeline on telemetry readings."""
    # Convert API inputs to pure domain SensorReading dataclasses
    domain_readings = [
        SensorReading(
            timestamp=r.timestamp,
            pump_running=r.pump_running,
            pressure_p1=r.pressure_p1,
            pressure_p2=r.pressure_p2,
            pressure_p3=r.pressure_p3,
            flow_rate=r.flow_rate,
            tds_in=r.tds_in,
            tds_out=r.tds_out,
            temperature=r.temperature,
            turbidity=r.turbidity,
            uv_current=r.uv_current,
            operating_mode=r.operating_mode,
            device_tier=r.device_tier,
        )
        for r in req.readings
    ]

    # Reconstitute or initialize DeviceState
    dev_state = (
        DeviceState.from_dict(req.device_state)
        if req.device_state
        else DeviceState()
    )

    # Execute pure domain pipeline
    analysis_res, updated_state = analyze(
        device_state=dev_state,
        readings=domain_readings,
    )

    # Map domain result to Pydantic response
    stages_schema = {
        stg: StageForecastSchema(
            health_percent=fc.health_percent,
            remaining_days=fc.remaining_days,
            band_low=fc.band_low,
            band_high=fc.band_high,
            status_text=fc.status_text,
            estimated=fc.estimated,
            learning=fc.learning,
        )
        for stg, fc in analysis_res.stages.items()
    }

    diagnoses_schema = [
        DiagnosisSchema(
            fault_type=d.fault_type,
            reason_code=d.reason_code,
            confidence=d.confidence,
            evidence=d.evidence,
            human_text=d.human_text,
        )
        for d in analysis_res.active_diagnoses
    ]

    return AnalyzeResponse(
        stages=stages_schema,
        active_diagnoses=diagnoses_schema,
        event_tags=analysis_res.event_tags,
        is_lite_mode=analysis_res.is_lite_mode,
        device_tier=analysis_res.device_tier,
        sensor_faults_detected=analysis_res.sensor_faults_detected,
        updated_device_state=updated_state.to_dict(),
    )
