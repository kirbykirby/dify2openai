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
        self.conversation_id = None
        self.dialogue_count = 0

    def process_chunk(self, chunk: bytes) -> None:
        if not chunk:
            # 如果收到空chunk，认为是流结束
            self._finalize_stream()
            return

        self.buffer += chunk.decode()
        lines = self.buffer.split("\n")

        # 处理完整的行
        for line in lines[:-1]:
            self._process_line(line)

        # 保存最后一个可能不完整的行
        self.buffer = lines[-1]

        # 如果buffer中有完整的JSON数据，也进行处理
        if self.buffer.strip() and self.buffer.strip().startswith("{"):
            try:
                json.loads(self.buffer)
                self._process_line(self.buffer)
                self.buffer = ""
            except json.JSONDecodeError:
                pass

    def _process_line(self, line: str) -> None:
        cleaned_line = line.replace("data: ", "").strip()
        if not cleaned_line:
            return

        try:
            chunk_obj = json.loads(cleaned_line)
            self._handle_event(chunk_obj)
        except json.JSONDecodeError:
            return

    def _handle_event(self, chunk_obj: dict) -> None:
        if "conversation_id" in chunk_obj:
            self.conversation_id = chunk_obj["conversation_id"]
        if "dialogue_count" in chunk_obj:
            self.dialogue_count = chunk_obj["dialogue_count"]
        # print(f"chunk_obj: {chunk_obj}")

        event = chunk_obj.get("event")

        if not event:
            # 处理没有event字段的消息
            if "answer" in chunk_obj:
                self.result += chunk_obj["answer"]
            elif "content" in chunk_obj:
                self.result += chunk_obj["content"]

            # 检查是否包含最终的usage信息
            if "usage" in chunk_obj or "conversation_id" in chunk_obj:
                self._finalize_stream(chunk_obj.get("usage", {}))
            return

        if event in ("message", "agent_message"):
            self.result += chunk_obj.get("answer", "")
            self.skip_workflow_finished = True
        elif event == "message_end":
            self._handle_message_end(chunk_obj)
        elif event == "workflow_finished" and not self.skip_workflow_finished:
            self._handle_workflow_finished(chunk_obj)
        elif event == "error":
            self._handle_error(chunk_obj)

    def _finalize_stream(self, usage: dict = None) -> None:
        """手动结束流处理"""
        self.message_ended = True
        if not self.usage_data:
            self.usage_data = self._extract_usage(usage or {})

    def _handle_message_end(self, chunk_obj: dict) -> None:
        self.message_ended = True
        usage = chunk_obj.get("metadata", {}).get("usage", {})
        self.usage_data = self._extract_usage(usage)

    def _handle_workflow_finished(self, chunk_obj: dict) -> None:
        self.message_ended = True
        outputs = chunk_obj.get("data", {}).get("outputs", {})
        if OUTPUT_VARIABLE and OUTPUT_VARIABLE in outputs:
            self.result = outputs[OUTPUT_VARIABLE]
        else:
            self.result = str(outputs)

        metadata_usage = chunk_obj.get("metadata", {}).get("usage", {})
        total_tokens = chunk_obj.get("data", {}).get("total_tokens")
        self.usage_data = self._extract_usage(metadata_usage, total_tokens)

    def _handle_error(self, chunk_obj: dict) -> None:
        error_code = chunk_obj.get("code", "unknown")
        error_message = chunk_obj.get("message", "Unknown error")
        print(f"Error: {error_code}, {error_message}")
        self.has_error = True
        self.message_ended = True  # 发生错误时也标记为结束

    @staticmethod
    def _extract_usage(usage: dict, total_tokens: int = None) -> dict:
        return {
            "prompt_tokens": usage.get("prompt_tokens", 100),
            "completion_tokens": usage.get("completion_tokens", 10),
            "total_tokens": total_tokens or usage.get("total_tokens", 110),
        }
