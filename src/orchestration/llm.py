from __future__ import annotations

import os

from crewai import LLM


def build_llm(*, temperature: float | None = None, max_tokens: int = 8192) -> LLM:
    """Builds the LLM used by every agent, from config — never hardcoded.

    LLM_PROVIDER=bedrock is the production path (Claude via AWS Bedrock, EU region).
    LLM_PROVIDER=anthropic is a direct-API fallback for local dev (spec section 7).
    """
    provider = os.environ.get("LLM_PROVIDER", "bedrock")

    if provider == "anthropic":
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
        return LLM(
            model=f"anthropic/{model}",
            api_key=os.environ["ANTHROPIC_API_KEY"],
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "bedrock":
        # TODO(mvp): Bedrock path is wired per litellm's documented "bedrock/<model_id>"
        # convention but UNVERIFIED in this session — no AWS Bedrock access was
        # available to test a live call. Verify against the installed litellm/crewai
        # version before relying on this in production, per spec section 7.
        region = os.environ.get("AWS_REGION", "eu-central-1")
        model_id = os.environ["BEDROCK_MODEL_ID"]
        return LLM(
            model=f"bedrock/{model_id}",
            aws_region_name=region,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}")
