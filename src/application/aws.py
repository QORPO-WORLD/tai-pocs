import json
import os
import time
from typing import Generator

import boto3

from application.models import ClaudeSonnet, ClaudeV2, Model, ModelID, NovaPro


class KnowledgeBase:
    def __init__(self, **kwargs) -> None:
        self.base_id = kwargs.get("base_id", os.getenv("KNOWLEDGE_BASE_ID"))
        self.bucket_name = kwargs.get("bucket_name", os.getenv("BUCKET_NAME"))
        self.data_source_id = kwargs.get("data_source_id", os.getenv("DATA_SOURCE_ID"))


class AwsAPI:

    def __init__(self, region: str = "eu-central-1", **kwargs) -> None:
        self.region = region
        self.polly = boto3.client("polly")

        self.models_mapping: dict[ModelID, Model] = {
            ModelID.NOVA_PRO: NovaPro(region),
            ModelID.CLAUDE_V2: ClaudeV2(region),
            ModelID.CLAUDE_SONNET: ClaudeSonnet(region),
        }
        self.s3 = boto3.client("s3")
        self.bedrock_agent = boto3.client("bedrock-agent", region_name=self.region)
        self.knowledge_base = KnowledgeBase(**kwargs)

        self.saved_audio_times: list[float] = []

    def get_streamed_response(
        self,
        model_id: ModelID,
        messages: list[dict],
        start_time: float,
        temperature: float = 0.9,
    ) -> Generator[str, None, None]:
        yield from self.models_mapping[model_id].get_streamed_response(messages, start_time, temperature)

    def update_knowledge_base(self, data: list[dict]) -> None:
        json_content = json.dumps(data, indent=4)
        self.s3.put_object(Bucket=self.knowledge_base.bucket_name, Key="game.json", Body=json_content)
        self.bedrock_agent.start_ingestion_job(
            clientToken=os.getenv("CLIENT_TOKEN"),
            dataSourceId=self.knowledge_base.data_source_id,
            knowledgeBaseId=self.knowledge_base.base_id,
        )

    def get_streamed_response_rag(self, model: Model, prompt: str, start_time: float) -> Generator[str, None, None]:
        """
        Note: looks like it's impossible to pass a list of prompts when using knowledge bases.
        """
        bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=self.region)
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
            stream_body=stream["stream"],
            text_getter=lambda chunk: chunk.get("output", {}).get("text", ""),
            start_time=start_time,
        )

    def get_bedrock_stats(self, model_id: ModelID) -> str:
        model = self.models_mapping[model_id]
        deltas = [model.got_sentence_times[0]] + [
            model.got_sentence_times[i] - model.got_sentence_times[i - 1] for i in range(1, len(model.got_sentence_times))
        ]
        average_got_sentence_time = sum(deltas) / len(model.got_sentence_times)
        min_got_sentence_time, max_got_sentence_time = min(deltas), max(deltas)
        model.got_sentence_times.clear()
        return f"1 sentence generation latencies: avg={average_got_sentence_time:.2f}sec, min={min_got_sentence_time:.2f}sec, max={max_got_sentence_time:.2f}sec"

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

    def get_polly_stats(self) -> str:
        deltas = self.saved_audio_times
        average_saved_audio_time = sum(deltas) / len(self.saved_audio_times)
        min_saved_audio_time, max_saved_audio_time = min(deltas), max(deltas)
        self.saved_audio_times.clear()
        return (
            f"Polly latencies: avg={average_saved_audio_time:.2f}sec, min={min_saved_audio_time:.2f}sec, max={max_saved_audio_time:.2f}sec"
        )
