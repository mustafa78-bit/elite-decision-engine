def room_query(room_id: str, context: dict, query: str) -> str:
    return f"""You are in the {room_id} mission area.

Context data:
{_format_context(context)}

Founder query: {query}

Respond professionally based on the available context data. Reference specific data points when relevant. Do not speculate beyond the provided information."""


def _format_context(context: dict) -> str:
    lines = []
    for key, value in context.items():
        if value is not None:
            lines.append(f"[{key}]: {value}")
    return "\n".join(lines) if lines else "No context data available."
