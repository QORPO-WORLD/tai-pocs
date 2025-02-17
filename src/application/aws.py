import os
from typing import Generator

import boto3

from application.models import ClaudeSonnet, ClaudeV2, Model, ModelID, NovaPro


class KnowledgeBase:
    def __init__(self, **kwargs) -> None:
        self.base_id = kwargs.get("base_id", os.getenv("KNOWLEDGE_BASE_ID"))
        self.bucket_name = kwargs.get("bucket_name", os.getenv("BUCKET_NAME"))
        self.data_source_id = kwargs.get("data_source_id", os.getenv("DATA_SOURCE_ID"))


class AwsAPI:

    def __init__(self, **kwargs) -> None:
        self.polly = boto3.client("polly")

        self.models_mapping: dict[ModelID, Model] = {
            ModelID.NOVA_PRO: NovaPro(),
            ModelID.CLAUDE_V2: ClaudeV2(),
            ModelID.CLAUDE_SONNET: ClaudeSonnet(),
        }
        self.s3 = boto3.client("s3")
        self.knowledge_base = KnowledgeBase(**kwargs)

        self.delays: list[float] = []

    def get_streamed_response(
        self,
        model_id: ModelID,
        messages: list[dict],
        temperature: float = 0.9,
    ) -> Generator[str, None, None]:
        yield from self.models_mapping[model_id].get_streamed_response(messages, temperature)

    def get_streamed_response_rag(self, model: Model, prompt: str) -> Generator[str, None, None]:
        """
        Note: looks like it's impossible to pass a list of prompts when using knowledge bases.
        """
        bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=model.region)
        knowledge_base_config = {
            "knowledgeBaseId": self.knowledge_base.base_id,
            "modelArn": model.arn,
            "generationConfiguration": {},
            "orchestrationConfiguration": {},
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {
                    "numberOfResults": 5,
                },
            },
        }

        stream = bedrock_agent_runtime.retrieve_and_generate_stream(
            input={"text": prompt},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": knowledge_base_config,
            },
        )
        model = self.models_mapping[model.model_id]
        yield from model.generate_sentences_from_stream(
            stream_body=stream["stream"], text_getter=lambda chunk: chunk.get("output", {}).get("text", "")
        )

    def get_bedrock_stats(self, model_id: ModelID) -> str:
        model = self.models_mapping[model_id]
        deltas = [model.delays[0]] + [model.delays[i] - model.delays[i - 1] for i in range(1, len(model.delays))]
        average_got_sentence_time = sum(deltas) / len(model.delays)
        min_got_sentence_time, max_got_sentence_time = min(deltas), max(deltas)
        model.delays.clear()
        return f"1 sentence generation latencies: avg={average_got_sentence_time:.2f}sec, min={min_got_sentence_time:.2f}sec, max={max_got_sentence_time:.2f}sec"

    def convert_to_voice(self, response_text: str, filename: str) -> None:
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
        with open(filename, "wb") as file:
            body = response["AudioStream"]
            for b in body:
                file.write(b)

    def get_polly_stats(self) -> str:
        average_saved_audio_time = sum(self.delays) / len(self.delays)
        min_saved_audio_time, max_saved_audio_time = min(self.delays), max(self.delays)
        # self.delays.clear()
        return (
            f"Polly latencies: avg={average_saved_audio_time:.2f}sec, min={min_saved_audio_time:.2f}sec, max={max_saved_audio_time:.2f}sec"
        )
