# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Chatbot: State-machine of Step objects (Strategy for parsing, easy to add/remove questions)."""
from .rules import evaluate
from . import criteria as C

class Step:
    key, question, options = "", "", ()
    def parse(self, text): return text.strip()
    def applies(self, a): return True

class NumberStep(Step):
    def __init__(self, key, question, lo, hi, cast): self.key, self.question, self.lo, self.hi, self.cast = key, question, lo, hi, cast
    def parse(self, t):
        v = self.cast(t.strip().split()[0])
        if not self.lo <= v <= self.hi: raise ValueError
        return v

class ChoiceStep(Step):
    def __init__(self, key, question, options, when=lambda a: True):
        self.key, self.question, self.options, self.when = key, question, tuple(options), when
    def applies(self, a): return self.when(a)
    def parse(self, t):
        for o in self.options:
            if t.strip().lower() == o.lower(): return o
        raise ValueError

class DateStep(Step):
    """A day like 2026-09-14 (also 14/9/2026)."""
    def __init__(self, key, question, when=lambda a: True): self.key, self.question, self.when = key, question, when
    def applies(self, a): return self.when(a)
    def parse(self, t):
        from datetime import datetime
        t = t.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d %B %Y"):
            try: return datetime.strptime(t, fmt).date().isoformat()
            except ValueError: continue
        raise ValueError

YN = ("Yes", "No")
ADV = C.ADVISORY
STEPS = [
    NumberStep("age", "How old are you?", 10, 100, int),
    ChoiceStep("repeat", "Have you donated blood before?", YN, lambda a: a["age"] > C.AGE_MAX),
    NumberStep("weight", "What's your weight in kg?", 20, 250, float),
    ChoiceStep("sex", "What is your sex?", ("Male", "Female")),
    ChoiceStep("illness", f"Any sore throat, cough, runny nose or diarrhoea in the last {C.SYMPTOM_FREE_DAYS} days?", YN),
    ChoiceStep("fever", f"Have you had a fever in the last {C.FEVER_FREE_WEEKS} weeks?", YN),
    ChoiceStep("advisory", f"In the last {ADV.wait_months} months, did you stay overnight in {ADV.places_text}?", YN),
    DateStep("advisory_return", "When did you come back? (e.g. 2026-09-14)", lambda a: a.get("advisory") == "Yes"),
    ChoiceStep("abroad", "Any other trips outside Singapore in the last 3 months?", YN),
    ChoiceStep("risk", "Did you visit a malaria or Zika risk area (or are you unsure)?", ("Yes", "No", "Not sure"), lambda a: a.get("abroad") == "Yes"),
    ChoiceStep("tattoo", "Any tattoo or piercing in the last 6 months?", YN),
    ChoiceStep("pregnant", "Are you pregnant or breastfeeding?", YN, lambda a: a["sex"] == "Female"),
    ChoiceStep("medication", "Are you on antibiotics or blood thinners?", YN),
]

def to_answers(a):
    from datetime import date
    yes = lambda k: a.get(k, "No") != "No"
    back = a.get("advisory_return")
    return {"age": a["age"], "repeat": a.get("repeat") == "Yes", "sex": a.get("sex"), "weight": a["weight"], "hb": None, "last": None,
            "illness": yes("illness"), "fever": yes("fever"), "advisory_return": date.fromisoformat(back) if back else None,
            "abroad": yes("abroad"), "travel": a.get("abroad") == "Yes" and yes("risk"), "tattoo": yes("tattoo"),
            "pregnant": a.get("pregnant") == "Yes", "medication": yes("medication")}

class ChatFlow:
    def __init__(self, steps=STEPS): self.steps = steps

    def handle(self, state, text):
        if text == "__start__" or "i" not in state or state["i"] >= len(self.steps):
            state.clear(); state.update(i=0, a={})
            return self._ask(state, "Hi, I'm LifeBot 🩸 Let's check if you can donate. ")
        step = self.steps[state["i"]]
        try: state["a"][step.key] = step.parse(text)
        except (ValueError, IndexError):
            return {"reply": "Sorry, I didn't catch that. " + step.question, "options": list(step.options)}
        state["i"] += 1
        return self._ask(state)

    def _ask(self, state, prefix=""):
        while state["i"] < len(self.steps) and not self.steps[state["i"]].applies(state["a"]): state["i"] += 1
        if state["i"] >= len(self.steps): return self._result(state["a"])
        s = self.steps[state["i"]]
        return {"reply": prefix + s.question, "options": list(s.options), "progress": round(state["i"] / len(self.steps) * 100)}

    def _result(self, a):
        ok, reasons, notes = evaluate(to_answers(a))
        extra = ("\n\nAlso:\n• " + "\n• ".join(notes)) if notes else ""
        info = C.HSA_URL if a.get("abroad") == "Yes" or a.get("advisory") == "Yes" else None
        if ok: return {"reply": "✅ You look eligible! The nurse checks your haemoglobin and makes the final call on the day." + extra,
                       "link": "/register", "info": info, "options": ["Start over"], "progress": 100, "eligible": True}
        return {"reply": "Not right now:\n• " + "\n• ".join(reasons) + extra, "info": info, "options": ["Start over"], "progress": 100}
