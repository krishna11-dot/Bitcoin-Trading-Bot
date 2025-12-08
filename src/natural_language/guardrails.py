#!/usr/bin/env python3
"""
Output Guardrails for LLM Responses

CRITICAL: Hard-coded validation to ensure LLM outputs are safe and valid.

Mentor's Guidance:
"You have to hard code to make sure the output is limited to what you want.
You cannot rely on prompts to control output."

This module enforces strict output validation - no matter what the LLM returns,
we force it into a safe, valid structure.
"""

import json
import re
from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field, validator


class TradingIntent(BaseModel):
    """
    Validated intent structure.

    This is the ONLY structure allowed to pass through guardrails.
    Any LLM output is forced into this format.
    """

    intent: Literal[
        "check_market",
        "check_portfolio",
        "run_trade",
        "get_decision",
        "analyze_backtest",
        "help"
    ] = Field(
        description="Validated intent - MUST be one of 6 allowed values"
    )

    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional parameters for the intent"
    )

    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)"
    )

    @validator('confidence')
    def clamp_confidence(cls, v):
        """Ensure confidence is between 0 and 1."""
        return max(0.0, min(1.0, float(v)))


class OutputGuardrails:
    """
    Hard-coded output validation.

    Cannot trust LLM to always follow instructions!
    This class enforces strict validation on ALL LLM outputs.
    """

    # GUARDRAIL 1: Only these intents are allowed
    VALID_INTENTS = {
        "check_market",
        "check_portfolio",
        "run_trade",
        "get_decision",
        "analyze_backtest",
        "help"
    }

    # GUARDRAIL 2: Intent keyword mapping
    INTENT_KEYWORDS = {
        "check_market": [
            "market", "price", "btc", "bitcoin", "current",
            "worth", "value", "cost", "rate", "ticker",
            "rsi", "atr", "macd", "indicator", "technical",
            "fear", "greed", "sentiment"
        ],
        "check_portfolio": [
            "portfolio", "position", "holding", "balance",
            "my", "mine", "own", "have", "holdings",
            "what do i", "how much", "show me"
        ],
        "run_trade": [
            "trade", "execute", "run", "start", "cycle",
            "do it", "go", "perform", "make", "place order"
        ],
        "get_decision": [
            "decision", "recommend", "should", "advice",
            "suggest", "opinion", "think", "would you",
            "buy", "sell", "hold"
        ],
        "analyze_backtest": [
            "backtest", "result", "results", "performance", "metrics",
            "accuracy", "trades", "return", "returns", "win rate",
            "sharpe", "drawdown", "conclusion", "how many", "ml",
            "business metric", "technical metric"
        ],
        "help": [
            "help", "what", "how", "explain", "tell me",
            "command", "option", "feature", "can you",
            "available", "?"
        ]
    }

    @staticmethod
    def validate_and_parse(llm_output: str) -> TradingIntent:
        """
        Parse LLM output with strict guardrails.

        Steps:
        1. Try to parse as JSON
        2. If fails, use fuzzy matching on raw text
        3. Force intent to be valid (no matter what LLM said)
        4. Validate parameters (strip dangerous content)
        5. Clamp confidence to [0, 1]

        Args:
            llm_output: Raw output from LLM (could be anything!)

        Returns:
            TradingIntent: Validated, safe intent object

        Example:
            >>> guardrails = OutputGuardrails()
            >>> intent = guardrails.validate_and_parse('{"intent": "check_market"}')
            >>> print(intent.intent)  # "check_market"
        """
        if not llm_output or not llm_output.strip():
            return TradingIntent(
                intent="help",
                parameters={},
                confidence=0.0
            )

        try:
            # Step 1: Try JSON parse
            # Clean markdown code blocks if present
            cleaned = OutputGuardrails._clean_markdown(llm_output)

            data = json.loads(cleaned)

            # Extract fields with fallbacks
            intent = data.get("intent", "help")
            parameters = data.get("parameters", {})
            confidence = data.get("confidence", 0.5)

            # GUARDRAIL: Force valid intent
            if not isinstance(intent, str) or intent.lower() not in OutputGuardrails.VALID_INTENTS:
                intent = OutputGuardrails._fuzzy_match_intent(str(intent))

            # GUARDRAIL: Validate parameters
            if not isinstance(parameters, dict):
                parameters = {}

            # GUARDRAIL: Strip dangerous parameters
            parameters = OutputGuardrails._sanitize_parameters(parameters)

            # GUARDRAIL: Clamp confidence
            try:
                confidence = float(confidence)
                confidence = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                confidence = 0.5

            return TradingIntent(
                intent=intent,
                parameters=parameters,
                confidence=confidence
            )

        except json.JSONDecodeError:
            # Step 2: JSON parse failed - use fuzzy matching
            return OutputGuardrails._fallback_parse(llm_output)

        except Exception as e:
            # Step 3: Ultimate fallback (something went very wrong)
            print(f"  Parsing error: {e}")
            return TradingIntent(
                intent="help",
                parameters={},
                confidence=0.0
            )

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Remove markdown code blocks from LLM output."""
        # Remove ```json ... ```
        if "```json" in text:
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Remove ``` ... ```
        if "```" in text:
            match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return match.group(1).strip()

        return text.strip()

    @staticmethod
    def _fuzzy_match_intent(text: str) -> str:
        """
        Find closest valid intent using keyword matching.

        GUARDRAIL: Never allow invalid intents to pass through.
        """
        if not isinstance(text, str):
            return "help"

        text = text.lower()

        # Score each intent based on keyword matches
        scores = {intent: 0 for intent in OutputGuardrails.VALID_INTENTS}

        for intent, keywords in OutputGuardrails.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[intent] += 1

        # Return highest scoring intent
        best_intent = max(scores, key=scores.get)

        # If no keywords matched, default to help
        if scores[best_intent] == 0:
            return "help"

        return best_intent

    @staticmethod
    def _sanitize_parameters(params: dict) -> dict:
        """
        Sanitize parameters to prevent injection attacks.

        GUARDRAIL: Strip any dangerous content.
        """
        safe_params = {}

        for key, value in params.items():
            # Only allow string and numeric parameters
            if isinstance(value, (str, int, float, bool)):
                # Convert to string and limit length
                safe_value = str(value)[:200]

                # Remove dangerous characters
                safe_value = re.sub(r'[;<>&|`$()]', '', safe_value)

                safe_params[key] = safe_value

        return safe_params

    @staticmethod
    def _fallback_parse(text: str) -> TradingIntent:
        """
        Parse plain text response when JSON fails.

        GUARDRAIL: Always return a valid TradingIntent.
        """
        intent = OutputGuardrails._fuzzy_match_intent(text)

        return TradingIntent(
            intent=intent,
            parameters={},
            confidence=0.3  # Lower confidence for fuzzy matches
        )


if __name__ == "__main__":
    # Test guardrails
    print("=" * 60)
    print("TESTING OUTPUT GUARDRAILS")
    print("=" * 60)

    test_cases = [
        # Valid JSON
        ('{"intent": "check_market", "confidence": 0.9}', "check_market"),

        # JSON with markdown
        ('```json\n{"intent": "check_portfolio"}\n```', "check_portfolio"),

        # Invalid intent (should be corrected)
        ('{"intent": "hack_system"}', "help"),

        # Plain text (fuzzy match)
        ("What's the Bitcoin price?", "check_market"),
        ("Show my portfolio", "check_portfolio"),
        ("Should I buy now?", "get_decision"),
        ("Execute a trade", "run_trade"),
        ("How do I use this?", "help"),

        # Edge cases
        ("", "help"),
        ("random gibberish xyz123", "help"),
        ('{"intent": "check_market", "confidence": 999}', "check_market"),  # Confidence clamped to 1.0

        # Injection attempts (should be sanitized)
        ('{"intent": "check_market", "parameters": {"cmd": "rm -rf /"}}', "check_market"),
    ]

    print("\nRunning test cases:\n")

    for i, (input_text, expected_intent) in enumerate(test_cases, 1):
        result = OutputGuardrails.validate_and_parse(input_text)

        status = "[OK]" if result.intent == expected_intent else "[FAIL]"
        print(f"{status} Test {i}: '{input_text[:50]}...'")
        print(f"   Expected: {expected_intent}")
        print(f"   Got: {result.intent} (confidence: {result.confidence:.2f})")

        if result.parameters:
            print(f"   Parameters: {result.parameters}")

        print()

    print("=" * 60)
    print("GUARDRAILS TEST COMPLETE")
    print("=" * 60)
