"""Phase 17: promote a configurator draft into a runtime GameGenome.

A draft carries name/function/verb/maturity_stage + selected_organs. To make it
runnable as a session we need to fill in the structural fields (rounds,
player_actions, llm_roles, verdicts/fates/etc.) that a Play page needs. We do
this by template per field_type. The researcher picks the field_type explicitly
at promote time, so the template is deterministic.
"""
from __future__ import annotations
from typing import Any
from sqlalchemy.orm import Session
from ..models import GenomeDraft, Organ


# Field_type → (player_actions, default llm_role, rounds template, verdicts list,
#               fates list, absence_types, mediums, phrase_actions, profile_dimensions)
_TEMPLATES: dict[str, dict[str, Any]] = {
    "clickable_text_units": {
        "player_actions": ["select_unit", "prove_operation", "assign_verdict"],
        "default_llm_role": "prosecutor",
        "rounds": [
            {"id": "read",   "title": "Read",    "instruction": "Прочти материал. Что выглядит как несущий узел?", "time_sec": 120},
            {"id": "select", "title": "Select",  "instruction": "Отметь до 3 фраз, которые ты заявляешь как несущие операцию.", "time_sec": 180},
            {"id": "prove",  "title": "Prove",   "instruction": "Для каждой назови операцию.", "time_sec": 240},
            {"id": "verdict","title": "Verdict", "instruction": "Под давлением прокурора — стоишь на выборе или признаёшь слабость.", "time_sec": 120},
        ],
        "verdicts": ["bearing_node", "false_click", "weak_sprout", "service_phrase"],
        "fates": [], "absence_types": [], "mediums": [], "phrase_actions": [],
        "trace_schema": ["unit_id", "claimed_operation", "verdict"],
        "profile_dimensions": ["bias", "verdict_distribution"],
    },
    "gap_click_text": {
        "player_actions": ["click_gap", "assign_absence_type", "respond_to_patch", "assign_fate"],
        "default_llm_role": "spackler",
        "rounds": [
            {"id": "read",   "title": "Read",  "instruction": "Прочти текст без редактирования.", "time_sec": 180},
            {"id": "gap",    "title": "Gap",   "instruction": "Отметь места, где текст перепрыгивает через операцию.", "time_sec": 240},
            {"id": "patch",  "title": "Patch", "instruction": "Шпаклёвщик предложит заплатку. Прими, исправь или отвергни.", "time_sec": 240},
            {"id": "fate",   "title": "Fate",  "instruction": "Назначь судьбу каждой дыре.", "time_sec": 240},
        ],
        "verdicts": [],
        "fates": ["restore", "keep_open", "bury", "archive", "turn_into_question", "return_to_author"],
        "absence_types": ["logical", "subject", "resource", "register", "archive", "promise", "ontology", "criterion"],
        "mediums": [], "phrase_actions": [],
        "trace_schema": ["gap_position", "absence_type", "patch_response", "fate"],
        "profile_dimensions": ["absence_blindness", "patch_susceptibility", "fate_distribution"],
    },
    "card_sorting": {
        "player_actions": ["sort_card", "defend_fate", "revise_fate", "set_incubation_test"],
        "default_llm_role": "sprout_advocate",
        "rounds": [
            {"id": "read",   "title": "Read",   "instruction": "Прочти карточки. Не оценивай красоту.", "time_sec": 180},
            {"id": "sort",   "title": "Sort",   "instruction": "Раскидай по зонам — зоны определяются автором игры.", "time_sec": 360},
            {"id": "defend", "title": "Defend", "instruction": "Адвокат-росток вмешается. Подтверди или измени.", "time_sec": 240},
        ],
        "verdicts": [],
        "fates": ["cut", "incubate", "require_proof", "no_name"],
        "absence_types": [], "mediums": [], "phrase_actions": [],
        "trace_schema": ["card_id", "fate", "revision"],
        "profile_dimensions": ["selection_bias", "fate_distribution", "revisions"],
    },
    "medium_shift_phrase": {
        "player_actions": ["assign_phrase_action", "compare_medium_shift", "repair_machine_reading", "transfer_phrase"],
        "default_llm_role": "literal_alien",
        "rounds": [
            {"id": "first_read", "title": "First Read", "instruction": "На каждой вкладке-медиуме назови действие фразы.", "time_sec": 180},
            {"id": "shift",      "title": "Shift",      "instruction": "Сравни смену медиума: что изменилось — адресат, риск, темп?", "time_sec": 240},
            {"id": "blindness",  "title": "Blindness",  "instruction": "Литералист даст плоское чтение. Почини.", "time_sec": 180},
            {"id": "transfer",   "title": "Transfer",   "instruction": "Перенеси фразу в новый медиум, сохранив действие.", "time_sec": 180},
        ],
        "verdicts": [],
        "fates": [],
        "absence_types": [],
        "mediums": ["telegram", "email", "protocol", "talk", "doc_comment"],
        "phrase_actions": ["hidden_request", "alibi", "dispute_closure", "in_group_check", "pathos_reset", "joke", "threat", "command", "refusal"],
        "trace_schema": ["medium", "phrase_action", "repair", "transfer_target"],
        "profile_dimensions": ["register_blindness", "transfer_accuracy", "phrase_action_distribution"],
    },
    "promise_court_text": {
        "player_actions": ["mark_promise", "fill_obligation_form", "send_to_court", "accept_promise"],
        "default_llm_role": "spackler",
        "rounds": [
            {"id": "read",    "title": "Read",    "instruction": "Прочти текст. Не редактируй формулировки.", "time_sec": 120},
            {"id": "mark",    "title": "Mark",    "instruction": "Кликни до 5 фраз, которые выглядят как обещания.", "time_sec": 180},
            {"id": "fill",    "title": "Fill",    "instruction": "Для каждого заполни форму: owner / deadline / criterion / fallback.", "time_sec": 360},
            {"id": "verdict", "title": "Court",   "instruction": "Любая пустая клетка — обещание идёт в суд.", "time_sec": 120},
        ],
        "verdicts": ["accepted", "sent_to_court"],
        "fates": [],
        "absence_types": [],
        "mediums": [],
        "phrase_actions": [],
        "trace_schema": ["promise_position", "owner", "deadline", "criterion", "fallback", "verdict"],
        "profile_dimensions": ["promise_blindness", "court_load", "completeness_demand"],
    },
}

VALID_FIELD_TYPES = list(_TEMPLATES.keys())


class PromoteError(RuntimeError):
    pass


def promote_draft(draft: GenomeDraft, field_type: str, db: Session) -> dict:
    """Build a full runtime GameGenome dict from a draft + the chosen field_type.

    The selected_organs are USED to derive the LLM-role and to tag the genome with
    its theoretical roots. They are NOT used to invent new actions or rounds — the
    template per field_type is canonical.
    """
    if field_type not in VALID_FIELD_TYPES:
        raise PromoteError(f"unknown field_type {field_type}; must be one of {VALID_FIELD_TYPES}")
    tpl = _TEMPLATES[field_type]

    # Use the first llm_role organ from the draft as the role; fall back to default.
    llm_role_ids = (draft.selected_organs or {}).get("llm_role") or []
    role_name = tpl["default_llm_role"]
    if llm_role_ids:
        organ = db.query(Organ).filter(Organ.id == llm_role_ids[0]).first()
        if organ:
            # Map canonical role names to the 4 runtime organ slugs.
            mapping = {
                "слопогенератор": "spackler",
                "адвокат слопа": "sprout_advocate",
                "молчальник": "literal_alien",
                "ошибочник": "literal_alien",
                "значимый другой": "prosecutor",
                "слабый другой": "prosecutor",
                "архивист": "spackler",
                "призраколов": "prosecutor",
                "зеркало смотрящего": "literal_alien",
                "латентный монтажёр": "spackler",
                "агентный хор": "sprout_advocate",
                "переводчик модальностей": "literal_alien",
                "пороговый настройщик": "prosecutor",
                "мутационный двигатель": "spackler",
                "анти-сервильный критик": "prosecutor",
                "свидетель": "prosecutor",
                "чужой разум": "literal_alien",
                "оракул с ошибкой": "literal_alien",
                "снимающий костыль": "sprout_advocate",
                "поле": tpl["default_llm_role"],
            }
            role_name = mapping.get(organ.name.lower(), tpl["default_llm_role"])

    triggered_on = tpl["player_actions"][0] if tpl["player_actions"] else "select_unit"

    # Theoretical roots from the action bank — use organ names as tags.
    action_ids = (draft.selected_organs or {}).get("action") or []
    action_organs = db.query(Organ).filter(Organ.id.in_(action_ids)).all() if action_ids else []
    roots = [f"R-promoted-{draft.id[:6]}"]

    genome = {
        "id": f"promoted_{draft.id}",
        "title": draft.name or f"Promoted draft {draft.id[:6]}",
        "short_title": (draft.name or draft.id[:6])[:24],
        "function": draft.function or "промотированный черновик",
        "roots": roots,
        "field_type": field_type,
        "player_actions": list(tpl["player_actions"]),
        "rounds": list(tpl["rounds"]),
        "llm_roles": [{"id": role_name, "triggered_on_action": triggered_on}],
        "verdicts": list(tpl["verdicts"]),
        "fates": list(tpl["fates"]),
        "absence_types": list(tpl["absence_types"]),
        "mediums": list(tpl["mediums"]),
        "phrase_actions": list(tpl["phrase_actions"]),
        "trace_schema": list(tpl["trace_schema"]),
        "replay_mutation": {"by_profile_bias": True, "mutation_axis": ["sharpen_axis_of_weakness"]},
        "toxins": ["промотированный черновик не прошёл playtest — следи за выходом из роли"],
        "profile_dimensions": list(tpl["profile_dimensions"]),
        "_promoted_from_action_organs": [o.name for o in action_organs],
    }
    return genome
