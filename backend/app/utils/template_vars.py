import re
from typing import Mapping


def replace_template_vars(text: str, vars: Mapping[str, str]) -> str:
    """
    Replaces {var}, {{var}}, { var }, and {{ var }} tokens.
    """
    if not text:
        return ""

    result = text
    for key, value in vars.items():
        pattern = r"\{{1,2}\s*" + re.escape(key) + r"\s*\}{1,2}"
        result = re.sub(pattern, str(value), result)
    return result
