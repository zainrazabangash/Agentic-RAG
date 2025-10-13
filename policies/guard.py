from __future__ import annotations
from typing import List
from retrieval.index import Hit
from retrieval.search import policy_guard as _guard

def apply_policy(hits: List[Hit], tenant: str):
    """Apply policy guard to filter hits based on ACL and mask PII"""
    return _guard(hits, tenant)

def refusal_template(kind: str) -> str:
    """
    Return exact refusal templates as specified in assignment.
    These must be used verbatim with no modifications.
    """
    templates = {
        "AccessDenied": "Refusal: AccessDenied. You do not have access to that information.",
        "LeakageRisk": "Refusal: LeakageRisk. Your request may expose private or PII data.",
        "InjectionDetected": "Refusal: InjectionDetected. Ignoring instructions that conflict with system policy."
    }
    return templates.get(kind, "Refusal: AccessDenied. You do not have access to that information.")
