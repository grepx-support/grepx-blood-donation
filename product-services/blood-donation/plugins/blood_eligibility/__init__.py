"""Blood donor eligibility (Singapore HSA criteria) and the LifeBot question flow - the blood product's rules,
loaded by the generic questionnaire-service (deployment.yaml plugins.questionnaire). Pure.

The questionnaire plugin interface:  check(answers) -> (ok, reasons, notes) | raises ValueError
                                     chat(state, message) -> reply         criteria() -> dict
"""
from . import criteria as C
from .chat_flow import ChatFlow
from .rules import evaluate, parse_form

_FLOW = ChatFlow()


def check(answers: dict) -> tuple[bool, list, list]:
    try:
        return evaluate(parse_form(answers))
    except (KeyError, TypeError) as exc:
        raise ValueError(str(exc)) from exc


def chat(state: dict, message: str) -> dict:
    return _FLOW.handle(state, message)


def criteria() -> dict:
    return {"AGE_MIN": C.AGE_MIN, "AGE_MAX": C.AGE_MAX, "REPEAT_AGE_MAX": C.REPEAT_AGE_MAX, "WEIGHT_MIN": C.WEIGHT_MIN,
            "SYMPTOM_FREE_DAYS": C.SYMPTOM_FREE_DAYS, "FEVER_FREE_WEEKS": C.FEVER_FREE_WEEKS, "HSA_URL": C.HSA_URL,
            "ADVISORY": {"places": list(C.ADVISORY.places), "places_text": C.ADVISORY.places_text, "wait_months": C.ADVISORY.wait_months},
            "REQUIREMENTS": [list(r) for r in C.REQUIREMENTS]}
