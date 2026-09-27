from __future__ import annotations

from ott_brain.preferences import ONBOARDING_COMPLETE, get_preference, set_preference
from ott_brain.subscriptions import get_subscribed_slugs, set_subscribed_slugs


def onboarding_complete() -> bool:
    return get_preference(ONBOARDING_COMPLETE, "false") == "true"


def complete_onboarding() -> None:
    set_preference(ONBOARDING_COMPLETE, "true")


def skip_onboarding() -> None:
    set_preference(ONBOARDING_COMPLETE, "true")


def subscriptions_configured() -> bool:
    return bool(get_subscribed_slugs())
