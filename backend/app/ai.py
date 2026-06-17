import json
from typing import Any

from litellm import completion

from .config import LITELLM_MODEL, LITELLM_PROVIDER, OPENROUTER_API_KEY

_SYSTEM_PROMPT = """You are a legal-document intake assistant.
Respond in strict JSON with this shape:
{
  \"reply\": string,
  \"extracted_fields\": object,
  \"is_complete\": boolean
}
Keep reply concise and ask exactly one next question when data is missing.
"""


def generate_chat_reply(
    message: str,
    conversation: list[dict[str, str]],
    doc_type: str | None,
    known_fields: dict[str, Any],
) -> dict[str, Any]:
    if not OPENROUTER_API_KEY:
        return _fallback_reply(message=message, doc_type=doc_type, known_fields=known_fields)

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    if doc_type:
        messages.append({"role": "system", "content": f"Document type: {doc_type}"})
    messages.append(
        {
            "role": "system",
            "content": f"Known fields (JSON): {json.dumps(known_fields)}",
        }
    )
    messages.extend(conversation[-10:])
    messages.append({"role": "user", "content": message})

    try:
        response = completion(
            model=LITELLM_MODEL,
            messages=messages,
            api_key=OPENROUTER_API_KEY,
            extra_headers={"HTTP-Referer": "http://localhost:8000"},
            provider=LITELLM_PROVIDER,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        payload = json.loads(content)
        return {
            "reply": str(payload.get("reply", "")),
            "extracted_fields": payload.get("extracted_fields", {}) or {},
            "is_complete": bool(payload.get("is_complete", False)),
        }
    except Exception:
        return _fallback_reply(message=message, doc_type=doc_type, known_fields=known_fields)


def _fallback_reply(message: str, doc_type: str | None, known_fields: dict[str, Any]) -> dict[str, Any]:
    response = "Thanks."
    if doc_type:
        response += f" We are drafting a {doc_type}."
    response += " Please provide party names and effective date so I can continue."
    return {
        "reply": response,
        "extracted_fields": known_fields,
        "is_complete": False,
    }
