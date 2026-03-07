"""Import all handlers so they register via @register_handler."""

from app.engine.handlers import (  # noqa: F401
    ask_user,
    calculate,
    critic_review,
    densify,
    format_export,
    generate_document,
    research,
)
