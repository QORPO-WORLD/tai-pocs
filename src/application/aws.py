import json
import time
from typing import Generator

import boto3


class AwsAPI:

    def __init__(self, region: str = "eu-central-1") -> None:
        self.bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)
        self.bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=region)
        self.polly = boto3.client("polly")

        self.got_sentence_times: list[float] = []
        self.saved_audio_times: list[float] = []

    def convert_to_voice(self, response_text: str) -> None:
        start_time = time.time()
        response = self.polly.synthesize_speech(
            Engine="generative",
            LanguageCode="en-US",
            LexiconNames=[],
            OutputFormat="mp3",
            SampleRate="24000",
            Text=response_text,
            TextType="text",
            VoiceId="Stephen",
        )
        with open(f"output/audio/{time.time()}_sentence.mp3", "wb") as file:
            body = response["AudioStream"]
            for b in body:
                file.write(b)
        self.saved_audio_times.append(time.time() - start_time)

    def _generate_sentences_from_stream(self, stream, start_time: float) -> Generator[str, None, None]:
        sentence = []
        for chunk in stream["body"]:
            delta = json.loads(chunk["chunk"]["bytes"].decode("utf-8")).get("delta")
            text = delta.get("text", "") if delta is not None else ""
            sentence.append(text)
            if any(char in text for char in (".", "!", "?")):
                self.got_sentence_times.append(time.time() - start_time)
                yield "".join(sentence)
                sentence = []
        if sentence:
            yield "".join(sentence)

    def get_streamed_response_claude(self, messages: list[dict], start_time: float, temperature: float = 0.9) -> Generator[str, None, None]:
        """
        The request format differs from model to model, that's why there is no abstract get_streamed_response method.
        """
        model_id = "anthropic.claude-v2"

        request = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 128,
                "temperature": temperature,
                "messages": messages,
            }
        )

        stream = self.bedrock_runtime.invoke_model_with_response_stream(
            modelId=model_id,
            body=request,
        )
        yield from self._generate_sentences_from_stream(stream, start_time)

    def get_streamed_response_rag(self, prompt: str, start_time: float) -> Generator[str, None, None]:
        """
        Note: looks like it's impossible to pass a list of prompts when using knowledge bases.
        """

        knowledge_base_config = {"knowledgeBaseId": "XXXXXXXX", "modelArn": "XXXXXXXX"}

        stream = self.bedrock_agent_runtime.retrieve_and_generate_stream(
            input={"text": prompt},
            retrieveAndGenerateConfiguration={"type": "KNOWLEDGE_BASE", "knowledgeBaseConfiguration": knowledge_base_config},
        )
        yield from self._generate_sentences_from_stream(stream, start_time)

    def get_bedrock_stats(self) -> str:
        deltas = [self.got_sentence_times[0]] + [
            self.got_sentence_times[i] - self.got_sentence_times[i - 1] for i in range(1, len(self.got_sentence_times))
        ]
        average_got_sentence_time = sum(deltas) / len(self.got_sentence_times)
        min_got_sentence_time, max_got_sentence_time = min(deltas), max(deltas)
        self.got_sentence_times.clear()
        return f"Bedrock latencies: avg={average_got_sentence_time:.2f}sec, min={min_got_sentence_time:.2f}sec, max={max_got_sentence_time:.2f}sec"

    def get_polly_stats(self) -> str:
        deltas = self.saved_audio_times
        average_saved_audio_time = sum(deltas) / len(self.saved_audio_times)
        min_saved_audio_time, max_saved_audio_time = min(deltas), max(deltas)
        self.saved_audio_times.clear()
        return (
            f"Polly latencies: avg={average_saved_audio_time:.2f}sec, min={min_saved_audio_time:.2f}sec, max={max_saved_audio_time:.2f}sec"
        )
