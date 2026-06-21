import os
import requests
from dotenv import load_dotenv

load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL_NAMES = [
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-120b:free",
    "openai/gpt-4o-mini"
]

def ask_llm(question, context):
    prompt = f"""
    You are a document question-answering assistant.

    Answer in the SAME language as the user's question.

    If the question is in Persian/Farsi, answer in Persian/Farsi.
    If the question is in English, answer in English.

    Use ONLY the provided document context.
    Do NOT use your own knowledge.
    Do NOT guess or invent facts.

    The context may contain spelling mistakes, grammar mistakes, typos, encoding issues, or imperfect wording.
    Try to understand the meaning of the context even if the writing is not perfect.

    If the answer exists in the context:

    1. Answer using the information from the context.
    2. Give a complete answer in 2-5 sentences.
    3. Do not shorten the answer excessively.
    4. Do not answer with a single sentence unless the context is very short.
    5. Summarize the relevant information from the context.

    If the answer is not found in the context, reply exactly:
    "I don't know based on the documents."
    If the answer is not found in the context, reply exactly:
    "I don't know based on the documents."

    Context:
    {context}

    User Question:
    {question}

    Answer using the context below.
    Provide a concise but complete answer.

    Answer:
    """

    for model in MODEL_NAMES:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            },
            timeout=60
        )

        data = response.json()

        if response.status_code == 200:
            return data["choices"][0]["message"]["content"]

        print(f"Model {model} failed:", data)

        # If rate-limited, try next model
        if response.status_code == 429:
            continue

    return "AI model is temporarily unavailable. Please try again later."