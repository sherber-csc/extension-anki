from __future__ import annotations


def render_forms_hint(forms: str | None) -> str:
    """
    Template helper only.

    This module must not render full HTML cards. Anki templates remain the
    primary rendering layer, while the backend only normalizes a few field
    strings so the template can display them consistently.
    """
    if forms is None:
        return ""
    return forms.strip()
