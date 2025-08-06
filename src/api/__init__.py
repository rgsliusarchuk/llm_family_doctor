from .router_clinic import router as clinic_router
from .router_doctors import router as doctors_router
from .router_diagnose import router as diagnose_router
from .router_doctor_answers import router as doctor_answers_router
from .router_intake import router as intake_router
from .router_doctor_review import router as doctor_review_router
from .router_assistant import router as assistant_router

__all__ = [
    "clinic_router", 
    "doctors_router", 
    "diagnose_router", 
    "doctor_answers_router",
    "intake_router",
    "doctor_review_router",
    "assistant_router"
] 