"""Candidate pygame-ce event mapping; import and device setup belong to a later cut."""


def controller_action(event: object, pygame: object) -> str | None:
    """Map controller button-down events to synthetic menu actions."""
    if event.type != pygame.CONTROLLERBUTTONDOWN:
        return None
    return {
        pygame.CONTROLLER_BUTTON_DPAD_UP: "up",
        pygame.CONTROLLER_BUTTON_DPAD_DOWN: "down",
        pygame.CONTROLLER_BUTTON_A: "select",
        pygame.CONTROLLER_BUTTON_B: "back",
    }.get(event.button)
