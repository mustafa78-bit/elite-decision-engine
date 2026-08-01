from services.ollo.prompts.greeting.command_deck import command_deck_greeting

GREETING_TEMPLATES: dict[str, callable] = {
    "command_deck": command_deck_greeting,
}


def get_greeting(room_id: str, context: dict) -> str:
    template = GREETING_TEMPLATES.get(room_id, command_deck_greeting)
    return template(context)
