"""Session factory for Day 03."""

import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

APP_NAME = "day03-ecombot"


def get_session_service():
    return InMemorySessionService()


async def make_runner(agent) -> tuple[Runner, str, str]:
    session_service = get_session_service()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)

    user_id = f"user-{uuid.uuid4().hex[:6]}"
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    return runner, user_id, session_id
