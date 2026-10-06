"""Teammate extension point: consume the documented selected-account payload."""


def recommended_action(account):
    # Add action cards, scripts, offers or visit planning in your own branch.
    # Synthetic records and insufficient-history accounts have explicit statuses.
    return {
        "title": "Ready for the Act layer",
        "message": "Connect this account's evidence to a proposed action, talking-point card or visit plan.",
    }
