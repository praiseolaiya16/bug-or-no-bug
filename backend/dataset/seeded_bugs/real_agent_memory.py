def add_memory(agent_name, content, agent_input: dict = {}):
    """Record a piece of content into an agent's shared memory input."""
    agent_input.setdefault("history", [])
    agent_input["history"].append({"agent": agent_name, "content": content})
    return agent_input


def summarize_memory(agent_input: dict = {}):
    """Return a short summary string of everything recorded so far."""
    history = agent_input.get("history", [])
    return f"{len(history)} entries recorded"
