import logging
import sys
import time

from assistant_core.config import load_settings
from assistant_core.errors import AssistantError
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.logging_setup import setup_logging
from assistant_core.models import Message
from assistant_core.responder import StubLLMResponder
from assistant_core.service import AssistantService


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m assistant_core <question>")
        sys.exit(1)

    question = sys.argv[1]
    try:
        settings = load_settings()
        setup_logging(settings.log_level)
        logger = logging.getLogger("assistant_core")

        offices = OfficeDirectory.from_csv(settings.data_dir / "offices.csv")
        handbook = Handbook.from_json(settings.data_dir / "handbook.json")
        responder = StubLLMResponder()
        service = AssistantService(settings, offices, handbook, responder)

        start_time = time.perf_counter()
        msg = Message(text=question)
        response = service.handle(msg)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 1)

        extra = {
            "intent": response.intent.value,
            "latency_ms": latency_ms,
            "session": msg.session_id,
            "degraded": response.degraded,
        }
        logger.info("handled", extra=extra)
        print(response.answer)
    except AssistantError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
