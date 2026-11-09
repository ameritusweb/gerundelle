"""A gerund node's skeleton. Only `skeleton` is here: it's all the domains use from the training code this file was taken
from, and keeping it alone means running them doesn't need torch."""
import re


def skeleton(node):
    """Strip slot types: 'agent:person' -> 'agent'. Gerunds, roles and nesting stay."""
    return re.sub(r"(\w+):\w*", r"\1", node)
