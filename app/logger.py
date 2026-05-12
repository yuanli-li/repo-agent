import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4


class StepLogger:
    def __init__(self, log_dir: str = "logs") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        short_id = uuid4().hex[:8]
        self.file_path = self.log_dir / f"session_{timestamp}_{short_id}.jsonl"

    def log_step(self, record: Dict[str, Any]) -> None:
        enriched = {
            "logged_at": datetime.now().isoformat(),
            **record,
        }

        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(enriched, ensure_ascii=False) + "\n")

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        self.log_step({
            "event_type": event_type,
            **payload,
        })

    def get_log_path(self) -> str:
        return str(self.file_path)
