import openai
import os
import numpy as np


OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL")

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"),
                       base_url=os.getenv("OPENAI_API_BASE_URL"))


def normalize_embedding(embedding: list[float]) -> list[float]:
    return embedding / np.linalg.norm(embedding)


def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        input=text, model=OPENAI_EMBEDDING_MODEL)
    embedding = response.data[0].embedding
    return normalize_embedding(embedding)


def get_chat_completion(messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL, messages=messages)
    return response.choices[0].message.content


def get_summary(text: str) -> str:
    return get_chat_completion([
        {"role": "system", "content": """You are a helpful assistant that summarizes text.
         Summarize the text in a way that is easy to understand and relevant to the user in 2-3 sentences.
         The summary should be a single paragraph with no newlines or other formatting.
         Only output the summary, no other text.
         """},
        {"role": "user", "content": text}
    ])
