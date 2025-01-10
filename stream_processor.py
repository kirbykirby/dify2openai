import json
from config import OUTPUT_VARIABLE


class StreamProcessor:
    def __init__(self):
        self.result = ""
        self.usage_data = None
        self.has_error = False
        self.message_ended = False
        self.buffer = ""
        self.skip_workflow_finished = False

    def process_chunk(self, chunk: bytes) -> None:
        self.buffer += chunk.decode()
        lines = self.buffer.split("\n")

        for line in lines[:-1]:
            self._process_line(line)

        self.buffer = lines[-1]

    def _process_line(self, line: str) -> None:
        cleaned_line = line.replace("data: ", "").strip()
        if not cleaned_line:
            return

        try:
            chunk_obj = json.loads(cleaned_line)
        except json.JSONDecodeError:
            return

        self._handle_event(chunk_obj)

    def _handle_event(self, chunk_obj: dict) -> None:
        event = chunk_obj["event"]

        if event in ("message", "agent_message"):
            self.result += chunk_obj["answer"]
            self.skip_workflow_finished = True
        elif event == "message_end":
            self._handle_message_end(chunk_obj)
        elif event == "workflow_finished" and not self.skip_workflow_finished:
            self._handle_workflow_finished(chunk_obj)
        elif event == "error":
            self._handle_error(chunk_obj)

    def _handle_message_end(self, chunk_obj: dict) -> None:
        self.message_ended = True
        self.usage_data = self._extract_usage(chunk_obj["metadata"]["usage"])

    def _handle_workflow_finished(self, chunk_obj: dict) -> None:
        self.message_ended = True
        outputs = chunk_obj["data"]["outputs"]
        if OUTPUT_VARIABLE:
            self.result = outputs[OUTPUT_VARIABLE]
        else:
            self.result = outputs
        self.result = str(self.result)
        self.usage_data = self._extract_usage(
            chunk_obj["metadata"]["usage"], chunk_obj["data"].get("total_tokens")
        )

    def _handle_error(self, chunk_obj: dict) -> None:
        print(f"Error: {chunk_obj['code']}, {chunk_obj['message']}")
        self.has_error = True

    @staticmethod
    def _extract_usage(usage: dict, total_tokens: int = None) -> dict:
        return {
            "prompt_tokens": usage.get("prompt_tokens", 100),
            "completion_tokens": usage.get("completion_tokens", 10),
            "total_tokens": total_tokens or usage.get("total_tokens", 110),
        }
