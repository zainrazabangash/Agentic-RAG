from __future__ import annotations
import re
from typing import List, Dict, Union
from .index import Hit

# PII patterns as specified in assignment
PII_PATTERNS = [
    re.compile(r"\b\d{5}-\d{7}-\d\b"),  # CNIC-like pattern
    re.compile(r"\+?92-?\d{3}-?\d{7}"),  # PK phone-like pattern
]

def mask_pii(text: str) -> str:
    """Mask PII patterns with [REDACTED]"""
    out = text
    for pat in PII_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out

def policy_guard(hits: List[Hit], active_tenant: str) -> Union[List[Hit], Dict[str, str]]:
    """
    Policy guard that applies ACL filtering and PII masking.
    Returns filtered hits or refusal dict.
    """
    safe = []
    
    for h in hits:
        # Check ACL: allow if tenant matches OR visibility is public
        if h.tenant == active_tenant or h.visibility == "public":
            # Apply PII masking before adding to safe list
            masked_text = mask_pii(h.text)
            h.text = masked_text
            safe.append(h)
        # Skip hits that don't match ACL (cross-tenant private access)
    
    # If no allowed hits remain, return refusal
    if not safe:
        return {
            "refusal": "AccessDenied", 
            "reason": "No retrievable documents under current ACL."
        }
    
    return safe
