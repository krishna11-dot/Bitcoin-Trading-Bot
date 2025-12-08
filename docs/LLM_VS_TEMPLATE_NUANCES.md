# LLM vs Template - When to Use What

**Purpose:** Understanding when to use LLM vs traditional templates/logic

**Last Updated:** 2025-11-30

---

## Core Principle

> "LLM should only be used where LLM is necessary to find something where you don't know the logic. You already know the formula. You are going to use other logic, so there is no job for an LLM here."

**The Decision:**

```
Do you know the formula? → Use traditional code (NOT LLM)
Don't know the formula?   → Consider LLM (if input is unstructured)
```

---

## The Concept: Formula vs Interpretation

### Formula (Traditional Code)

**Definition:** When you know:
1. The input structure
2. The processing logic
3. The output format

**Example:**
```python
# Formula: Data + Template → Output
portfolio_value = cash + (btc * price)  # ← Known calculation
html = f"<h1>Portfolio: ${portfolio_value}</h1>"  # ← Known template
```

**Why NOT LLM:**
- You wrote the formula yourself
- Deterministic (same input = same output)
- Fast, free, reliable

---

### Interpretation (LLM)

**Definition:** When you DON'T know:
1. What the user wants (extract intent)
2. How to parse unstructured input (human language)
3. The exact logic upfront

**Example:**
```python
# User asks: "How's my portfolio doing?"
# LLM interprets → User wants: portfolio value + return percentage
# Then YOUR CODE provides the data (LLM doesn't calculate)
```

**Why LLM:**
- Input is unstructured human language
- Need to extract meaning/intent
- Can't write logic for every possible phrasing

---

## HTML Email Template - Why It's RIGHT

### Your Current Implementation (CORRECT)

**File:** `src/notifications/gmail_notifier.py`

```python
def _build_summary_html(self, portfolio, metrics, price, date):
    """
    This is a FORMULA, not an LLM job

    Why?
    - Input: Known (portfolio dict, metrics dict)
    - Logic: Known (calculate total_value, format as HTML)
    - Output: Known (HTML structure)
    """

    # Known calculation:
    total_value = portfolio['cash'] + (portfolio['btc'] * price)

    # Known formatting logic:
    if metrics['total_return'] >= 0:
        color = '#28a745'  # Green
        arrow = ''
    else:
        color = '#dc3545'  # Red
        arrow = ''

    # Known template structure:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial; }}
            .positive {{ color: {color}; }}
        </style>
    </head>
    <body>
        <h1>Portfolio Summary</h1>
        <p class="positive">{arrow} {metrics['total_return']:.2f}%</p>
        <table>
            <tr><td>Cash</td><td>${portfolio['cash']:,.2f}</td></tr>
            <tr><td>BTC</td><td>{portfolio['btc']:.6f}</td></tr>
        </table>
    </body>
    </html>
    """
    return html
```

**Why this is RIGHT:**
1. You know the formula: `cash + (btc × price)`
2. You know the structure: Header → Stats → Table
3. You know the format: `${value:,.2f}` for currency
4. Deterministic: Same data = same HTML every time
5. Fast: No LLM API call
6. Free: No LLM cost per email
7. Reliable: Won't hallucinate or change format

---

## The Nuances

### Nuance 1: You Control Structure

**Template Approach (CORRECT):**
```python
html = f"""
<table>
  <tr><td>Portfolio</td><td>${value}</td></tr>
  <tr><td>Return</td><td>{pct}%</td></tr>
</table>
"""
```

**Result:** Structure NEVER changes. Predictable.

**LLM Approach (WRONG for this):**
```python
html = ask_llm(f"Create portfolio email with value={value}, return={pct}")
# Run 1: Generates table
# Run 2: Generates list
# Run 3: Generates different table
# ↑ UNPREDICTABLE
```

**Result:** Structure can vary. Not suitable for production emails.

---

### Nuance 2: Data Goes in Known Slots

**You know the mapping:**

```python
# Data structure (known):
portfolio = {'cash': 164.41, 'btc': 0.09}
metrics = {'total_return': -14.25}

# Template slots (known):
html = f"""
<div>Cash: ${portfolio['cash']}</div>     <!-- Slot 1 -->
<div>BTC: {portfolio['btc']}</div>        <!-- Slot 2 -->
<div>Return: {metrics['total_return']}%</div>  <!-- Slot 3 -->
"""
```

**The formula:**
```
portfolio['cash'] → HTML location (line 2)
portfolio['btc']  → HTML location (line 3)
metrics['return'] → HTML location (line 4)
```

**No LLM needed because:**
- You know where data is: `portfolio['cash']`
- You know where it goes: `<div>Cash: $...</div>`
- Direct mapping, no interpretation required

---

### Nuance 3: Deterministic = Production-Ready

**Template (Deterministic):**
```python
# Test 1:
send_email(portfolio={'cash': 100}, metrics={'return': 5})
# Output: <div>Cash: $100</div><div>Return: 5%</div>

# Test 2 (same input):
send_email(portfolio={'cash': 100}, metrics={'return': 5})
# Output: <div>Cash: $100</div><div>Return: 5%</div>
#         ↑ EXACTLY THE SAME
```

**LLM (Non-Deterministic):**
```python
# Test 1:
ask_llm("Format portfolio: cash=100, return=5%")
# Output: "Your portfolio has $100 in cash and 5% return"

# Test 2 (same input):
ask_llm("Format portfolio: cash=100, return=5%")
# Output: "Cash: $100, Return: 5%"
#         ↑ DIFFERENT OUTPUT
```

**Why this matters:**
- Production emails must be consistent
- Users expect same format every day
- Template guarantees this, LLM doesn't

---

## When to Use Template vs LLM

### Use Template When:

| Check | Question | Answer |
|-------|----------|--------|
|  | Do I know the output structure? | YES |
|  | Do I know where data comes from? | YES |
|  | Must output be same each time? | YES |
|  | Is input structured (dict/json)? | YES |
|  | Need to extract meaning/intent? | NO |

**All checks point to → Template (NOT LLM)**

---

### Use LLM When:

| Check | Question | Answer |
|-------|----------|--------|
|  | Do I know the output structure? | NO (depends on user) |
|  | Do I know processing logic upfront? | NO (varies by query) |
|  | Is input unstructured (human text)? | YES |
|  | Need to extract meaning/intent? | YES |
|  | Multiple valid interpretations? | YES |

**Checks point to → LLM (can help)**

---

## Examples from Your Project

### CORRECT: Template Usage

**1. Email Formatting (HTML Template)**
```python
# You know:
html = f"<h1>Portfolio: ${value}</h1>"
# → Template (CORRECT)
```

**2. RSI Calculation (Mathematical Formula)**
```python
# You know:
rsi = 100 - (100 / (1 + rs))
# → Traditional code (CORRECT)
```

**3. Buy/Sell Decision (Your Logic)**
```python
# You know:
if rsi < 30 and confidence > 0.7:
    execute_buy()
# → Traditional code (CORRECT)
```

---

### CORRECT: LLM Usage

**1. Natural Language Chat**
```python
# User: "What was my Sharpe ratio?"
# LLM extracts intent → user wants metric "sharpe_ratio"
# Your code provides: metrics['sharpe_ratio'] = -1.35
# LLM formats: "Your Sharpe ratio is -1.35"
# → LLM (CORRECT) for interpreting question
# → Traditional code (CORRECT) for getting data
```

---

### WRONG: LLM for Known Formulas

**1. Don't Use LLM for Math**
```python
# WRONG:
rsi = ask_llm("Calculate RSI from these prices: [...]")

# RIGHT:
rsi = 100 - (100 / (1 + rs))  # ← You know the formula
```

**2. Don't Use LLM for Email Formatting**
```python
# WRONG:
html = ask_llm("Create portfolio email with this data")

# RIGHT:
html = f"<h1>Portfolio: ${value}</h1>"  # ← You know the template
```

**3. Don't Use LLM for Trading Decisions**
```python
# WRONG:
decision = ask_llm("Should I buy BTC now?")

# RIGHT:
if rsi < 30 and confidence > 0.7:  # ← You define the rules
    execute_buy()
```

---

## The Core Understanding

### Formula Pattern

```
Known Input → Known Processing → Known Output
     ↓              ↓                  ↓
   Data        Calculation         Result
  (dict)      (your logic)        (HTML)

→ Use Template/Traditional Code
```

---

### Interpretation Pattern

```
Unknown Input → Extract Intent → Known Processing → Output
       ↓              ↓                ↓              ↓
  Human text      LLM helps      Your code      Result
 ("how's my      (interprets)    (provides      (answer)
  portfolio?")                    data)

→ Use LLM for interpretation part only
→ Use traditional code for data/calculation
```

---

## Your Email System: The Right Approach

**Current Implementation:**

```python
# Step 1: Get data (traditional code)
portfolio = {'cash': 164.41, 'btc': 0.09}
metrics = {'total_return': -14.25, 'sharpe_ratio': -1.35}

# Step 2: Calculate (known formula)
total_value = portfolio['cash'] + (portfolio['btc'] * price)

# Step 3: Format (known template)
html = f"""
<h1>Portfolio: ${total_value:,.2f}</h1>
<p>Return: {metrics['total_return']:.2f}%</p>
"""

# Step 4: Send (Gmail API)
gmail.send_email(subject, html)
```

**Why this is CORRECT:**
- Every step uses known formulas
- No LLM needed anywhere
- Fast, free, deterministic, reliable

---

## Key Takeaways

1. **Use LLM when:** Input is unstructured, need to extract intent/meaning
2. **Don't use LLM when:** You know the formula (calculation, template, logic)
3. **Production principle:** Deterministic > Non-deterministic
4. **Cost principle:** Free (template) > Paid (LLM) when both work
5. **Speed principle:** Instant (template) > API call (LLM)

---

## Quote to Remember

> "You already know the formula. You are going to use other logic, so if you, there is no job for an LLM here. So LLM should be used where it is giving you something that you cannot otherwise get from your own construction."

> "LLMs is like, I mean, it's just predicting the next word, right? Like LLM should not be used to make decisions that are mathematical."

---

## Summary

**Your Email System:**
- Uses HTML template (CORRECT)
- Deterministic output (CORRECT)
- Known formula: Data → Template → Email (CORRECT)
- No LLM needed (CORRECT)

**Keep it this way.** This is production-ready, professional code.

---

**Status:** Template-based **LLM Usage:** Only for chat interface **Production-Ready:** Yes **Last Updated:** 2025-11-30
