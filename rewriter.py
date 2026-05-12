"""
rag-query-rewriter
==================
A minimal, context-aware query rewriter for RAG systems.

Turns follow-up questions ("How much is it?", "Is it refundable?", "What
about a cheaper one?") into standalone queries by reading the conversation
history. Without this, your RAG retriever will keep saying "I don't know"
even when the answer is sitting right there in your knowledge base.

Compatible with:
  - OpenAI
  - DeepSeek
  - Groq
  - Together AI
  - Local Ollama / vLLM (any OpenAI-compatible endpoint)

Set OPENAI_BASE_URL to point at any compatible server.

License: MIT  |  by Chung Tair Ltd. (https://chungtair.com)
"""

import os
from typing import List, Dict
from openai import OpenAI


# ---------------------------------------------------------------------------
# Client setup
# ---------------------------------------------------------------------------
# OPENAI_BASE_URL examples:
#   OpenAI            (leave unset)
#   DeepSeek          https://api.deepseek.com/v1
#   Groq              https://api.groq.com/openai/v1
#   Together          https://api.together.xyz/v1
#   Local Ollama      http://localhost:11434/v1
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", ""),
    base_url=os.environ.get("OPENAI_BASE_URL") or None,
)

MODEL = os.environ.get("REWRITER_MODEL", "gpt-4o-mini")


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You rewrite follow-up questions into standalone queries.

Given a short conversation history, output a single self-contained query
that captures what the user is really asking about, with all pronouns
("it", "this", "that") and missing subjects filled in from earlier turns.

Rules:
- Output ONLY the rewritten query. No explanation, no quotes.
- If the latest question is already standalone, output it unchanged.
- Preserve the user's original language (Chinese, English, Japanese, etc.).
- Do not invent information that is not in the history.
- Keep it concise.
"""


def rewrite_query(history: List[Dict[str, str]]) -> str:
    """
    Rewrite the latest user message in `history` into a standalone query.

    Args:
        history: A list of {"role": "user"|"assistant", "content": str}.
                 The last item must have role="user".

    Returns:
        The rewritten standalone query (string).

    Raises:
        ValueError: if history is empty or does not end with a user message.
    """
    if not history:
        raise ValueError("history is empty")
    if history[-1].get("role") != "user":
        raise ValueError("history must end with a user message")

    conv_lines = []
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        conv_lines.append(f"{role.capitalize()}: {content}")
    conv_text = "\n".join(conv_lines)

    user_prompt = (
        "Conversation history:\n"
        f"{conv_text}\n\n"
        "Rewrite the LAST user message as a standalone query:"
    )

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=200,
    )
    return resp.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    examples = [
        # Chinese: e-learning follow-up
        [
            {"role": "user", "content": "你們的 30 天高效英文課內容是什麼？"},
            {"role": "assistant", "content": "包含每日 15 分鐘影片、AI 對話練習、結業考試..."},
            {"role": "user", "content": "這個多少錢？"},
        ],
        # English: SaaS plan comparison
        [
            {"role": "user", "content": "Tell me about your Pro plan."},
            {"role": "assistant", "content": "Pro includes unlimited seats, priority support..."},
            {"role": "user", "content": "What about the cheaper one?"},
        ],
        # Japanese: e-commerce size/color follow-up
        [
            {"role": "user", "content": "Polo シャツ M サイズはありますか？"},
            {"role": "assistant", "content": "はい、Polo シャツ M サイズの在庫があります。"},
            {"role": "user", "content": "色は何色がありますか？"},
        ],
    ]

    for i, history in enumerate(examples, 1):
        print(f"\n=== Example {i} ===")
        for msg in history:
            print(f"  {msg['role']:>9}: {msg['content']}")
        try:
            rewritten = rewrite_query(history)
            print(f"  {'rewritten':>9}: {rewritten}")
        except Exception as e:
            print(f"  ERROR: {e}")
