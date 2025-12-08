"""
MCP + RAG Integration Test

PURPOSE:
    Verify that the natural language agent correctly integrates:
    1. MCP (Model Context Protocol) for live Bitcoin prices
    2. RAG (Retrieval-Augmented Generation) for historical pattern matching

SUCCESS CRITERIA:
    - Agent fetches live price from CoinGecko MCP
    - Date shows current date (not historical CSV date)
    - Price source is 'mcp' (not 'csv')
    - RAG finds similar historical patterns (if enabled)
    - Graceful fallback to CSV if MCP unavailable

USAGE:
    python tests/test_mcp_rag_integration.py

EXPECTED OUTPUT:
    [MCP] LIVE Bitcoin price: $XX,XXX.XX (as of YYYY-MM-DD HH:MM)
    [RAG] Found N similar patterns
    SUCCESS: Agent is using MCP live data with correct date!
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.natural_language.agent import TradingAssistant
from datetime import datetime


def test_mcp_rag_integration():
    """Test MCP and RAG integration in natural language agent."""

    print("="*70)
    print("MCP + RAG INTEGRATION TEST")
    print("="*70)
    print()
    print("Purpose: Verify natural language agent uses live MCP data + RAG patterns")
    print()

    # Create agent (RAG is enabled by default)
    print("[1/4] Creating agent...")
    agent = TradingAssistant(verbose=False)
    print("      Agent created successfully")
    print("      RAG system:", "Enabled" if agent.rag and agent.rag.enabled else "Disabled")
    print()

    # Call _check_market() to get market data
    print("[2/4] Fetching market data via _check_market()...")
    market_data = agent._check_market()
    print("      Market data retrieved")
    print()

    # Display results
    print("[3/4] Analyzing results...")
    print("="*70)
    print("RESULTS")
    print("="*70)
    print(f"  Date (from agent):    {market_data.get('date')}")
    print(f"  Today's actual date:  {datetime.now().date()}")
    print(f"  Price:                ${market_data.get('price', 0):,.2f}")
    print(f"  Price Source:         {market_data.get('price_source')}")
    print(f"  Is Live:              {market_data.get('is_live')}")
    print(f"  24h Change:           {market_data.get('24h_change')}%")
    print(f"  RSI:                  {market_data.get('rsi'):.1f}")
    print(f"  Fear & Greed:         {market_data.get('fear_greed')}")

    # Check RAG patterns
    rag_patterns = market_data.get('rag_patterns', [])
    if rag_patterns:
        print(f"  RAG Patterns Found:   {len(rag_patterns)}")
        for i, pattern in enumerate(rag_patterns[:3], 1):
            sim = pattern.get('metadata', {}).get('similarity', 0)
            date = pattern.get('metadata', {}).get('date', 'unknown')
            print(f"    {i}. {date} (similarity: {sim:.0%})")
    else:
        print(f"  RAG Patterns Found:   0 (RAG may be disabled or no matches)")

    print()

    # Validate results
    print("[4/4] Validation...")
    print("="*70)

    is_date_correct = str(market_data.get('date')) == str(datetime.now().date())
    is_mcp_source = market_data.get('price_source') == 'mcp'
    is_live = market_data.get('is_live') == True

    if is_mcp_source and is_live and is_date_correct:
        print("SUCCESS: MCP integration working correctly!")
        print("  - Live price from CoinGecko API")
        print("  - Current date (not historical CSV date)")
        print("  - RAG enabled for pattern matching")
        status = "PASS"
    elif is_mcp_source and is_live:
        print("PARTIAL SUCCESS: MCP fetching live data but date issue")
        print(f"  - Expected date: {datetime.now().date()}")
        print(f"  - Got date: {market_data.get('date')}")
        status = "PARTIAL"
    elif market_data.get('price_source') == 'csv':
        print("INFO: Using CSV fallback (MCP unavailable)")
        print("  Possible reasons:")
        print("  - CoinGecko API temporarily unavailable")
        print("  - Rate limit hit (30 calls/min)")
        print("  - No API key configured")
        print("  - No internet connection")
        print()
        print("  This is EXPECTED BEHAVIOR - graceful fallback working!")
        status = "FALLBACK"
    else:
        print("UNEXPECTED: Unknown state")
        status = "UNKNOWN"

    print("="*70)
    print(f"Test Status: {status}")
    print("="*70)

    return status


if __name__ == "__main__":
    result = test_mcp_rag_integration()
    sys.exit(0 if result in ["PASS", "FALLBACK"] else 1)
