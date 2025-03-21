import openai
import os


OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL")

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_API_BASE_URL"))

def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(input=text, model=OPENAI_EMBEDDING_MODEL)
    return response.data[0].embedding

def get_chat_completion(messages: list[dict]) -> str:
    response = client.chat.completions.create(model=OPENAI_CHAT_MODEL, messages=messages)
    return response.choices[0].message.content

def get_summary(text: str) -> str:
    return get_chat_completion([
        {"role": "system", "content": "You are a helpful assistant that summarizes text. Only output the summary, no other text."},
        {"role": "user", "content": text}
    ])
