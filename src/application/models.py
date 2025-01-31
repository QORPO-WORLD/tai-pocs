import json
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Generator

import boto3


class ModelID(Enum):
    NOVA_PRO = "amazon.nova-pro-v1:0"
    CLAUDE_V2 = "anthropic.claude-v2"
    CLAUDE_SONNET = "anthropic.claude-3-5-sonnet-20240620-v1:0"


class Model(ABC):
    def __init__(self, model_id: ModelID, region: str) -> None:
        self.model_id = model_id
        self.arn = f"arn:aws:bedrock:{region}::foundation-model/{model_id.value}"
        self.bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)
        self.got_sentence_times: list[float] = []

    def generate_sentences_from_stream(
        self, stream_body, text_getter: Callable[[dict], str], start_time: float
    ) -> Generator[str, None, None]:
        sentence = []
        for chunk in stream_body:
            text = text_getter(chunk)
            sentence.append(text)
            if any(char in text for char in (".", "!", "?")):
                self.got_sentence_times.append(time.time() - start_time)
                yield "".join(sentence)
                sentence = []
        if sentence:
            yield "".join(sentence)

    @abstractmethod
    def get_text_from_chunk(self, chunk: dict) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_streamed_response(self, messages: list[dict], start_time: float, temperature: float = 0.9) -> Generator[str, None, None]:
        raise NotImplementedError

    @abstractmethod
    def get_content(self, prompt: str) -> dict | list:
        raise NotImplementedError


class Anthropic(Model):
    def get_streamed_response(self, messages: list[dict], start_time: float, temperature: float = 0.9) -> Generator[str, None, None]:
        request = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 128,
                "temperature": temperature,
                "messages": messages,
            }
        )

        stream = self.bedrock_runtime.invoke_model_with_response_stream(
            modelId=self.model_id.value,
            body=request,
        )
        yield from self.generate_sentences_from_stream(stream["body"], self.get_text_from_chunk, start_time)

    def get_text_from_chunk(self, chunk: dict) -> str:
        delta = json.loads(chunk["chunk"]["bytes"].decode("utf-8")).get("delta")
        return delta.get("text", "") if delta is not None else ""

    def get_content(self, prompt: str) -> dict:
        return {"type": "text", "text": prompt}


class ClaudeV2(Anthropic):
    def __init__(self, region="eu-central-1") -> None:
        super().__init__(ModelID.CLAUDE_V2, region)


class ClaudeSonnet(Anthropic):
    def __init__(self, region="eu-central-1") -> None:
        super().__init__(ModelID.CLAUDE_SONNET, region)


class NovaPro(Model):
    def __init__(self, region="us-east-1") -> None:
        super().__init__(ModelID.NOVA_PRO, region)

    def get_streamed_response(self, messages: list[dict], start_time: float, temperature: float = 0.9) -> Generator[str, None, None]:
        request = json.dumps(
            {
                "inferenceConfig": {
                    "max_new_tokens": 128,
                    "temperature": temperature,
                },
                "messages": messages,
            }
        )

        stream = self.bedrock_runtime.invoke_model_with_response_stream(
            modelId=self.model_id.value,
            body=request,
        )
        yield from self.generate_sentences_from_stream(stream["body"], self.get_text_from_chunk, start_time)

    def get_content(self, prompt: str) -> dict:
        return {"text": prompt}

    def get_text_from_chunk(self, chunk: dict) -> str:
        content_block_delta = json.loads(chunk["chunk"]["bytes"].decode("utf-8")).get("contentBlockDelta")
        delta = content_block_delta.get("delta") if content_block_delta is not None else None
        return delta.get("text", "") if delta is not None else ""
