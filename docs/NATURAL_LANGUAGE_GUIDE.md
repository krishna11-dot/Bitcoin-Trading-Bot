# Natural Language Interface Guide

## Overview

Your Bitcoin trading bot now has a **natural language chat interface** powered by Google Gemini AI!

Ask questions in plain English instead of running complex commands.

---

## Quick Start

### 1. Get Gemini API Key (Free)

1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### 2. Add to `.env` file

```bash
# Add this line to your .env file
GEMINI_API_KEY=your_key_here
```

### 3. Install Dependencies

```bash
pip install google-generativeai pydantic langgraph
# Or with uv:
uv pip install google-generativeai pydantic langgraph
```

### 4. Run Chat Mode

```bash
python main.py --mode chat
```

---

## Example Conversations

### Check Market Conditions
```
You: What's the market situation?
Bot: BTC is trading at $98,234. RSI is 45 (neutral).
     Fear & Greed Index is 32 (fear). MACD is -1,234 (bearish trend).
```

### Get Trading Recommendation
```
You: Should I buy now?
Bot: Based on current conditions, the DCA strategy recommends BUY.
     Reasons: Fear & Greed is 32 (below 40 threshold) and RSI is 45
     (below 60 threshold). Suggested amount: $500.
```

### Ask About Strategies
```
You: What is DCA?
Bot: DCA (Dollar-Cost Averaging) is a steady accumulation strategy.
     It triggers BUY signals when RSI < 60 OR Fear & Greed < 40.
     The system buys $500 worth of BTC each time conditions are met.
```

### Run Trade Cycle
```
You: Run a trade cycle
Bot: Trade cycle executed. Decision: BUY $500. Strategy: DCA.
     Reason: Fear & Greed 32 < 40.
     Note: This is a SIMULATED decision - no actual order placed.
```

---

## Architecture

### LangGraph State Machine

The natural language interface uses **LangGraph** to orchestrate the 4-step pipeline:

```
Your Question
    ↓
[START]
    ↓

   LANGGRAPH STATE MACHINE               
                                         
  Node 1: Understand (Gemini AI)        
      ↓                                  
  Node 2: Validate (Guardrails)         
      ↓                                  
  Node 3: Execute (Decision Box)        
      ↓                                  
  Node 4: Respond (Gemini AI)           

    ↓
[END]
    ↓
Natural Language Answer
```

**Why LangGraph?**
- **Learning Experience**: Industry-standard framework for AI agent workflows
- **Clean Architecture**: Each node has one clear responsibility
- **State Management**: Shared state flows through all nodes automatically
- **Resume Value**: Demonstrates knowledge of modern agentic frameworks
- **Follows Mentor's Guidance**: Uses professional tooling ("use LangGraph")

**Implementation:**
```python
# Build graph with 4 nodes
workflow = StateGraph(AgentState)
workflow.add_node("understand", self._understand_node)  # Gemini AI
workflow.add_node("validate", self._validate_node)      # Guardrails
workflow.add_node("execute", self._execute_node)        # Decision Box
workflow.add_node("respond", self._respond_node)        # Gemini AI

# Linear flow (no branching)
workflow.set_entry_point("understand")
workflow.add_edge("understand", "validate")
workflow.add_edge("validate", "execute")
workflow.add_edge("execute", "respond")
workflow.add_edge("respond", END)
```

### Key Features

**Safe by Design**
- Hard-coded guardrails (not just prompts!)
- Only 5 allowed intents: check_market, check_portfolio, run_trade, get_decision, help
- Cannot execute dangerous commands

**Rate Limited**
- Gemini Free Tier: 10 requests/minute, 250 requests/day
- Automatic rate limiting with exponential backoff
- Response caching for repeated questions

**No Code Modifications**
- Natural language layer sits ABOVE existing system
- All trading decisions still made by existing Decision Box
- Modules, strategies, and executor completely untouched

**Retry Logic**
- Automatic retry on errors (3 attempts)
- Exponential backoff for rate limits
- Graceful error handling

---

## File Structure

```
src/natural_language/
 __init__.py
 rate_limiter.py         # 10 RPM, 250 RPD enforcement
 gemini_client.py         # API wrapper with retry
 guardrails.py            # CRITICAL: Hard-coded output validation
 agent.py                 # LangGraph orchestration (4-node state machine)
 interface.py             # CLI chat interface
```

---

## Available Commands

### Market Data
- "What's the Bitcoin price?"
- "Show me current market conditions"
- "What's the RSI?"
- "How's the Fear & Greed Index?"

### Trading Decisions
- "Should I buy?"
- "Should I sell?"
- "What's your recommendation?"
- "Give me a trading decision"

### Execute Trades (Simulated)
- "Run a trade cycle"
- "Execute a trade"
- "Make a decision and execute"

### Portfolio (Not Yet Implemented)
- "Show my portfolio"
- "What are my positions?"
- "How much BTC do I have?"

### Strategy Information
- "What is DCA?"
- "Explain ATR Stop-Loss"
- "How does Swing Trading work?"
- "What are all the strategies?"

### General
- "Help"
- "What can you do?"
- "Exit" (to quit)

---

## Technical Details

### Rate Limiting

**Gemini Free Tier Limits:**
- 10 requests per minute (RPM)
- 250 requests per day (RPD)

**Enforcement:**
- Sliding window rate limiter
- Automatic waiting when limits reached
- Clear error messages

**Example:**
```python
from src.natural_language.rate_limiter import RateLimiter

limiter = RateLimiter(rpm=10, rpd=250)
limiter.wait_if_needed()  # Blocks if rate limit hit
limiter.record_request()  # Track this request
```

### Guardrails (CRITICAL)

**Mentor's Guidance:**
> "You have to hard code to make sure the output is limited to what you want.
> You cannot rely on prompts to control output."

**Implementation:**
```python
from src.natural_language.guardrails import OutputGuardrails

# LLM might return anything - guardrails force it to be valid
raw_output = '{"intent": "hack_system"}'  # Invalid!
validated = OutputGuardrails.validate_and_parse(raw_output)

print(validated.intent)  # "help" (fuzzy matched to valid intent)
```

**Safety Features:**
1. **Only 5 valid intents** - Anything else gets corrected
2. **Parameter sanitization** - Strip dangerous characters
3. **Fuzzy matching** - Map invalid intents to closest valid one
4. **Ultimate fallback** - Always return valid structure (never crash)

### Response Caching

**Purpose:** Avoid repeated API calls for same question

**Example:**
```python
client = GeminiClient()

# First call - hits API
response1 = client.generate("What is Bitcoin?")

# Second call - uses cache (instant, no API call)
response2 = client.generate("What is Bitcoin?")

print(client.get_cache_size())  # 1
```

---

## Debugging

### Verbose Mode

Run with verbose output to see what's happening:

```bash
python -m src.natural_language.interface --verbose
```

**Output:**
```
[1/4] Understanding: 'What's the BTC price?'
Rate limits: 1/10 RPM, 1/250 RPD
API call successful (attempt 1)
[2/4] Validating intent...
[2/4] Intent: check_market (confidence: 0.90)
[3/4] Executing: check_market
[4/4] Formatting response...
```

### Test Individual Components

**Test Rate Limiter:**
```bash
python src/natural_language/rate_limiter.py
```

**Test Gemini Client:**
```bash
python src/natural_language/gemini_client.py
```

**Test Guardrails:**
```bash
python src/natural_language/guardrails.py
```

**Test Agent:**
```bash
python src/natural_language/agent.py
```

---

## Troubleshooting

### Error: "GEMINI_API_KEY not found"

**Fix:**
1. Get API key from: https://aistudio.google.com/app/apikey
2. Add to `.env` file: `GEMINI_API_KEY=your_key_here`
3. Restart the chat interface

### Error: "google-generativeai not installed" or "langgraph not installed"

**Fix:**
```bash
pip install google-generativeai pydantic langgraph
# Or with uv:
uv pip install google-generativeai pydantic langgraph
```

### Error: "Rate limit hit"

**Fix:**
- Gemini free tier: 10 requests/minute, 250 requests/day
- Wait 1 minute, or get paid API key
- System automatically waits and retries

### Error: "Could not fetch market data"

**Fix:**
- Ensure historical data exists: `data/processed/bitcoin_clean.csv`
- Run: `python main.py --mode backtest --months 1` to generate it

---

## Limitations

### Current Limitations

**Portfolio Tracking:** Not yet implemented
- Shows placeholder message
- Suggests running backtesting instead

**Live Trading:** Only simulated
- Returns decisions but doesn't place real orders
- Use `--mode live` for actual paper trading

**Historical Data Only:** Chat uses cached CSV data
- Not real-time prices
- Last date depends on your CSV file

### Future Enhancements

- Real-time price integration
- Portfolio position tracking
- Trade history analysis
- Performance charts
- Multi-turn conversations with memory

---

## Security

### What's Safe

**Intent validation** - Only 5 allowed intents
**Parameter sanitization** - Dangerous characters stripped
**Read-only operations** - Cannot modify files or execute arbitrary code
**Simulated trading** - No real money at risk
**API key security** - Stored in .env (not committed to git)

### What's NOT Safe

**Sharing API keys** - Keep GEMINI_API_KEY private
**Trusting LLM blindly** - Always use guardrails
**Production trading** - This is for testing/learning only

---

## Cost

### Gemini Free Tier

**FREE:**
- 10 requests per minute
- 250 requests per day
- Perfect for chat interface usage

**Typical Usage:**
- ~5-10 requests per chat session
- ~20-50 requests per day
- Well within free tier limits

**If You Need More:**
- Gemini Pro pricing: https://ai.google.dev/pricing
- Or use caching more aggressively

---

## Examples

### Beginner Questions
```
You: I'm new here, what can you do?
Bot: I can help you with your Bitcoin trading bot! Here's what I can do:
     • Check current market conditions (BTC price, RSI, Fear & Greed)
     • Give trading recommendations (should you buy/sell?)
     • Explain trading strategies (DCA, Swing Trading, etc.)
     • Run simulated trade cycles

     Try asking: "What's the market situation?" or "Explain DCA strategy"
```

### Strategy Questions
```
You: How does the ATR Stop-Loss work?
Bot: ATR Stop-Loss is a dynamic risk management strategy. It calculates
     a stop-loss price using: Stop = Entry Price - (2.0 × ATR).

     Example: If you bought BTC at $100,000 and ATR is $1,500, your
     stop-loss would be at $97,000. If price drops below that, the
     system automatically sells to limit your loss.
```

### Market Analysis
```
You: Is now a good time to buy?
Bot: Based on current market analysis:
     • BTC Price: $98,234 (down from recent high)
     • RSI: 42 (slightly oversold - bullish signal)
     • Fear & Greed: 28 (extreme fear - contrarian buy signal)
     • MACD: -1,234 (bearish momentum)

     Recommendation: BUY. The DCA strategy triggers because Fear & Greed
     is below 40 (extreme fear = buying opportunity). Suggested amount: $500.

     Note: This is educational - not financial advice!
```

---

## Summary

**What You Get:**
- Natural language chat interface
- Google Gemini AI integration (free tier)
- Hard-coded safety guardrails
- Rate limiting and caching
- No modifications to existing trading code

**How to Use:**
```bash
# 1. Get API key
https://aistudio.google.com/app/apikey

# 2. Add to .env
GEMINI_API_KEY=your_key_here

# 3. Install deps
pip install google-generativeai pydantic langgraph
# Or: uv pip install google-generativeai pydantic langgraph

# 4. Run chat
python main.py --mode chat

# 5. Start asking questions!
You: What's the market like?
```

**Architecture:**
- LangGraph orchestrates 4-node state machine (understand → validate → execute → respond)
- LLM for understanding & formatting only (NOT for trading decisions)
- Guardrails enforce safety (hard-coded, not prompt-based)
- All trading logic in existing Decision Box (untouched)
- Natural language layer sits ABOVE system (no modifications)

**Now you can talk to your trading bot in plain English!** 