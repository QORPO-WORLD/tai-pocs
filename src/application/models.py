import json
import time
from abc import ABC, abstractmethod
from typing import Generator

import boto3


class Model(ABC):
    def __init__(self, model_id: str, region: str) -> None:
        self.model_id = model_id
        self.bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)
        self.got_sentence_times: list[float] = []

    def generate_sentences_from_stream(self, stream, start_time: float) -> Generator[str, None, None]:
        sentence = []
        for chunk in stream["body"]:
            text = self.get_text_from_chunk(chunk)
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


class ClaudeV2(Model):
    def __init__(self, region="eu-central-1") -> None:
        model_id = "anthropic.claude-v2"
        super().__init__(model_id, region)

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
            modelId=self.model_id,
            body=request,
        )
        yield from self.generate_sentences_from_stream(stream, start_time)

    def get_text_from_chunk(self, chunk: dict) -> str:
        delta = json.loads(chunk["chunk"]["bytes"].decode("utf-8")).get("delta")
        return delta.get("text", "") if delta is not None else ""

    def get_content(self, prompt: str) -> dict:
        return {"type": "text", "text": prompt}


class NovaPro(Model):
    def __init__(self, region="us-east-1") -> None:
        model_id = "amazon.nova-pro-v1:0"
        super().__init__(model_id, region)

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
            modelId=self.model_id,
            body=request,
        )
        yield from self.generate_sentences_from_stream(stream, start_time)

    def get_content(self, prompt: str) -> dict:
        return {"text": prompt}

    def get_text_from_chunk(self, chunk: dict) -> str:
        content_block_delta = json.loads(chunk["chunk"]["bytes"].decode("utf-8")).get("contentBlockDelta")
        delta = content_block_delta.get("delta") if content_block_delta is not None else None
        return delta.get("text", "") if delta is not None else ""
