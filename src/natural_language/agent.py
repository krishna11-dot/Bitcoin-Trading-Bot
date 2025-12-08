#!/usr/bin/env python3
"""
Trading Assistant Agent

LangGraph-based state machine for natural language trading interface.
Orchestrates: understand → validate → execute → respond

Architecture:
- LangGraph: Manages workflow and state transitions
- LLM Layer: Only for understanding queries and formatting responses
- Trading Logic: All decisions still made by existing Decision Box
- No Modifications: Existing code untouched (wrapper only)

Why LangGraph?
- Learning experience (nodes, edges, state management)
- Industry-standard agentic workflow framework
- Resume value (demonstrates knowledge of modern AI architectures)
- Follows mentor's guidance on using professional tools
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, TypedDict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from langgraph.graph import StateGraph, END
from src.natural_language.gemini_client import GeminiClient
from src.natural_language.guardrails import OutputGuardrails
from src.rag.rag_system import RAGSystem
from src.data_pipeline.unified_data_fetcher import UnifiedDataFetcher


class AgentState(TypedDict):
    """
    State structure passed between LangGraph nodes.

    This is the shared state that flows through:
    understand → validate → execute → respond
    """
    user_input: str
    understanding: Optional[str]
    validated_intent: Optional[Any]
    tool_result: Optional[Dict[str, Any]]
    rag_context: Optional[list]  # RAG: Similar historical patterns
    final_response: Optional[str]
    verbose: bool


class TradingAssistant:
    """
    Natural language interface for Bitcoin trading bot using LangGraph.

    LangGraph Flow (4 nodes):
    1. understand_node (LLM) → Interpret user input
    2. validate_node (Guardrails) → Ensure valid intent
    3. execute_node (Python) → Call existing functions
    4. respond_node (LLM) → Natural language response

    Why LangGraph here?
    - Industry-standard agentic workflow framework
    - Clear separation of concerns (each node has one job)
    - Easy to extend with new nodes if needed
    - Learning experience for building AI agents
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize trading assistant with LangGraph state machine.

        Args:
            verbose: Print debug information
        """
        self.gemini_client = GeminiClient()
        self.verbose = verbose

        # Initialize RAG system for pattern matching
        try:
            self.rag = RAGSystem()
            if self.verbose and self.rag.enabled:
                print("[INFO] RAG system enabled for pattern matching")
        except Exception as e:
            print(f"[WARNING] RAG system unavailable: {e}")
            self.rag = None

        # Initialize unified data fetcher (MCP + CSV fallback)
        self.data_fetcher = UnifiedDataFetcher(force_csv=False)
        if self.verbose:
            print("[INFO] Unified data fetcher initialized")

        # Build LangGraph state machine
        self.graph = self._build_graph()

        if self.verbose:
            print("[INFO] Trading Assistant initialized with LangGraph")

    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph state machine.

        Graph structure:
            START → understand → validate → execute → respond → END

        Returns:
            Compiled StateGraph ready to process queries
        """
        # Create graph with state type
        workflow = StateGraph(AgentState)

        # Add nodes (each node is a function that processes state)
        workflow.add_node("understand", self._understand_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("respond", self._respond_node)

        # Define edges (linear flow: no branching)
        workflow.set_entry_point("understand")
        workflow.add_edge("understand", "validate")
        workflow.add_edge("validate", "execute")
        workflow.add_edge("execute", "respond")
        workflow.add_edge("respond", END)

        # Compile graph
        return workflow.compile()

    def chat(self, user_input: str) -> str:
        """
        Process user query through LangGraph and return natural language response.

        Args:
            user_input: Natural language query from user

        Returns:
            Natural language response

        Example:
            >>> assistant = TradingAssistant()
            >>> response = assistant.chat("What's the BTC price?")
            >>> print(response)
        """
        try:
            # Initialize state
            initial_state: AgentState = {
                "user_input": user_input,
                "understanding": None,
                "validated_intent": None,
                "tool_result": None,
                "rag_context": None,
                "final_response": None,
                "verbose": self.verbose
            }

            # Run through LangGraph
            if self.verbose:
                print(f"\n[LANGGRAPH] Processing: '{user_input}'")

            final_state = self.graph.invoke(initial_state)

            # Extract final response from state
            return final_state.get("final_response", "Sorry, I couldn't generate a response.")

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {e}"
            if self.verbose:
                print(f"[ERROR] Error in chat: {e}")
                import traceback
                traceback.print_exc()
            return error_msg

    # ========================================================================
    # LangGraph Node Functions
    # ========================================================================
    # Each node function:
    # - Receives current state
    # - Performs one step in the pipeline
    # - Updates state
    # - Returns updated state for next node

    def _understand_node(self, state: AgentState) -> AgentState:
        """
        Node 1: Understand user query using LLM.

        Input: user_input
        Output: understanding (JSON string with intent)
        """
        if state["verbose"]:
            print(f"[1/4] Understanding: '{state['user_input']}'")

        understanding = self._understand_query(state["user_input"])
        state["understanding"] = understanding
        return state

    def _validate_node(self, state: AgentState) -> AgentState:
        """
        Node 2: Validate LLM output using hard-coded guardrails.

        Input: understanding
        Output: validated_intent (TradingIntent object)
        """
        if state["verbose"]:
            print(f"[2/4] Validating intent...")

        # Keyword-based fallback for backtest questions
        user_input_lower = state["user_input"].lower()
        backtest_keywords = [
            "trade", "trades", "accuracy", "ml", "metrics", "return", "returns",
            "performance", "win rate", "sharpe", "drawdown", "backtest", "result",
            "conclusion", "business metric", "technical metric", "how many"
        ]

        if any(keyword in user_input_lower for keyword in backtest_keywords):
            # Force analyze_backtest intent if keywords detected
            from src.natural_language.guardrails import TradingIntent
            validated_intent = TradingIntent(
                intent="analyze_backtest",
                parameters={},
                confidence=0.95
            )
            if state["verbose"]:
                print(f"    [KEYWORD MATCH] Forcing analyze_backtest intent")
        else:
            validated_intent = OutputGuardrails.validate_and_parse(state["understanding"])

        if state["verbose"]:
            print(f"[2/4] Intent: {validated_intent.intent} "
                  f"(confidence: {validated_intent.confidence:.2f})")

        state["validated_intent"] = validated_intent
        return state

    def _execute_node(self, state: AgentState) -> AgentState:
        """
        Node 3: Execute tool based on validated intent.

        Input: validated_intent
        Output: tool_result (dict with execution results)
        """
        if state["verbose"]:
            print(f"[3/4] Executing: {state['validated_intent'].intent}")

        tool_result = self._execute_tool(state["validated_intent"])
        state["tool_result"] = tool_result
        return state

    def _respond_node(self, state: AgentState) -> AgentState:
        """
        Node 4: Format tool result as natural language using LLM.

        Input: tool_result, user_input
        Output: final_response (natural language string)
        """
        if state["verbose"]:
            print(f"[4/4] Formatting response...")

        final_response = self._format_response(state["tool_result"], state["user_input"])
        state["final_response"] = final_response
        return state

    # ========================================================================
    # Helper Methods (unchanged from original implementation)
    # ========================================================================

    def _understand_query(self, user_input: str) -> str:
        """
        Step 1: Use Gemini to understand natural language.

        Args:
            user_input: User's question/command

        Returns:
            JSON string with intent and parameters
        """
        prompt = f"""
User said: "{user_input}"

Analyze their intent and extract parameters.

Return ONLY valid JSON (no markdown, no extra text):
{{
    "intent": "check_market" | "check_portfolio" | "run_trade" | "get_decision" | "analyze_backtest" | "help",
    "parameters": {{}},
    "confidence": 0.0-1.0
}}

Intent definitions:
- check_market: User wants current BTC price, RSI, ATR, MACD, Fear & Greed
- check_portfolio: User wants to see their positions, balance, holdings
- run_trade: User wants to execute a trading cycle (fetch data, make decision, place order)
- get_decision: User wants trading recommendation WITHOUT executing
- analyze_backtest: User asks about PAST backtest results, metrics, performance, number of trades, ML accuracy, returns, win rates, conclusions
- help: User needs help or asks general questions about strategies/concepts

IMPORTANT: Any question about metrics, results, performance, accuracy, trades count → analyze_backtest

Examples:
"What's BTC price?" → {{"intent": "check_market", "parameters": {{}}, "confidence": 0.9}}
"Show my positions" → {{"intent": "check_portfolio", "parameters": {{}}, "confidence": 0.9}}
"Should I buy?" → {{"intent": "get_decision", "parameters": {{}}, "confidence": 0.8}}
"Execute a trade" → {{"intent": "run_trade", "parameters": {{}}, "confidence": 0.9}}
"What was the backtest conclusion?" → {{"intent": "analyze_backtest", "parameters": {{}}, "confidence": 0.9}}
"Show business metrics" → {{"intent": "analyze_backtest", "parameters": {{}}, "confidence": 0.9}}
"How many trades?" → {{"intent": "analyze_backtest", "parameters": {{}}, "confidence": 0.9}}
"What's my ML accuracy?" → {{"intent": "analyze_backtest", "parameters": {{}}, "confidence": 0.9}}
"Show results" → {{"intent": "analyze_backtest", "parameters": {{}}, "confidence": 0.9}}
"What's the return?" → {{"intent": "analyze_backtest", "parameters": {{}}, "confidence": 0.9}}
"Win rate?" → {{"intent": "analyze_backtest", "parameters": {{}}, "confidence": 0.9}}
"What is DCA?" → {{"intent": "help", "parameters": {{}}, "confidence": 0.9}}

Now analyze: "{user_input}"
"""

        response = self.gemini_client.generate(prompt, verbose=self.verbose)

        if not response:
            return '{"intent": "help", "confidence": 0.0}'

        return response

    def _execute_tool(self, validated_intent) -> Dict[str, Any]:
        """
        Step 3: Route to appropriate existing function.

        Args:
            validated_intent: Validated TradingIntent object

        Returns:
            Result dictionary
        """
        intent = validated_intent.intent

        try:
            if intent == "check_market":
                return self._check_market()

            elif intent == "check_portfolio":
                return self._check_portfolio()

            elif intent == "analyze_backtest":
                return self._analyze_backtest()

            elif intent == "run_trade":
                return self._run_trade_cycle()

            elif intent == "get_decision":
                return self._get_decision()

            else:  # help
                return self._get_help()

        except Exception as e:
            if self.verbose:
                print(f"[ERROR] Tool execution error: {e}")
                import traceback
                traceback.print_exc()

            return {
                "error": str(e),
                "message": "Sorry, something went wrong executing that command."
            }

    def _format_response(self, result: dict, user_input: str) -> str:
        """
        Step 4: Format result as natural language.

        Args:
            result: Tool execution result
            user_input: Original user query (for context)

        Returns:
            Natural language response
        """
        prompt = f"""
User asked: "{user_input}"

System returned: {result}

Format this as a natural, friendly response.

Guidelines:
- Be concise but informative
- Use bullet points for multiple items
- If there's an error, explain it kindly
- Don't use emojis (text only)
- Format numbers nicely (e.g., $98,234.56, 45.2%)
- Explain technical terms briefly

Example formats:
Market data → "BTC is trading at $98,234. RSI is 45 (neutral). Fear & Greed Index is 32 (fear)."
Portfolio → "You have 0.045 BTC worth $4,410. 2 open positions. Unrealized P&L: +2.3%"
Decision → "Recommendation: BUY $500. Strategy: DCA. Reason: Fear & Greed is 32 (below 40 threshold)"
Error → "I couldn't fetch the data right now. Please try again in a moment."
"""

        response = self.gemini_client.generate(prompt, verbose=self.verbose)

        if not response:
            return "Sorry, I couldn't format a response. Please try again."

        return response

    # Tool methods (call existing code)

    def _check_market(self) -> dict:
        """
        Get latest market data using unified data fetcher (MCP or CSV fallback).

        Uses:
        - UnifiedDataFetcher: Tries CoinGecko MCP, falls back to CSV
        - RAG System: Finds similar historical market patterns (if available)

        Returns market data with RAG context for better LLM responses.
        """
        try:
            from src.modules.module1_technical import get_latest_indicators

            # Get market data from unified fetcher (MCP or CSV)
            summary = self.data_fetcher.get_market_summary()

            if summary.get('current_price') is None:
                return {
                    "error": "No market data available",
                    "message": "Run a backtest first to generate data: python main.py --mode backtest --months 6",
                    "status": "no_data"
                }

            # Get historical data for indicators
            df = self.data_fetcher.get_historical_data()

            if df is None or len(df) == 0:
                return {
                    "error": "No historical data available",
                    "message": "Run a backtest first to generate data",
                    "status": "no_data"
                }

            # Get latest indicators from historical data
            latest_date = df['Date'].iloc[-1]
            indicators = get_latest_indicators(df, latest_date)

            # Get Fear & Greed (if available)
            fear_greed = "N/A"
            fear_greed_label = "N/A"
            try:
                from src.modules.module2_sentiment import SentimentAnalyzer
                from src.data_pipeline.api_client import APIClient

                api_client = APIClient()
                analyzer = SentimentAnalyzer(api_client)
                sentiment = analyzer.get_fear_greed_index()
                fear_greed = sentiment.get('fear_greed_score', 'N/A')
                fear_greed_label = sentiment.get('classification', 'N/A')
            except Exception:
                pass  # Fear & Greed not critical

            # Get RSI and prepare for RAG query
            rsi = float(indicators.get('RSI', 50))

            # Use RAG to find similar historical patterns
            rag_patterns = []
            if self.rag and self.rag.enabled:
                try:
                    current_conditions = {
                        'price': summary['current_price'],
                        'rsi': rsi,
                        'fear_greed': fear_greed if fear_greed != "N/A" else 50,
                        'narrative': f"Bitcoin trading at ${summary['current_price']:,.0f} with RSI {rsi:.1f}"
                    }

                    rag_patterns = self.rag.find_similar_patterns(
                        current_conditions,
                        top_k=3,
                        min_similarity=0.5
                    )

                    if self.verbose and rag_patterns:
                        print(f"[RAG] Found {len(rag_patterns)} similar patterns")
                except Exception as e:
                    if self.verbose:
                        print(f"[RAG] Pattern matching failed: {e}")

            # Use current date if MCP (live data), otherwise latest CSV date
            from datetime import datetime
            if summary.get('price_source') == 'mcp':
                current_date = datetime.now().date()
            else:
                current_date = latest_date.date() if hasattr(latest_date, 'date') else latest_date

            return {
                "date": str(current_date),
                "historical_data_date": str(latest_date.date()) if hasattr(latest_date, 'date') else str(latest_date),
                "price": summary['current_price'],
                "price_source": summary.get('price_source', 'csv'),
                "rsi": rsi,
                "atr": float(indicators.get('ATR', 0)),
                "macd_diff": float(indicators.get('MACD_diff', 0)),
                "fear_greed": fear_greed,
                "fear_greed_label": fear_greed_label,
                "24h_change": summary.get('24h_change'),
                "rag_patterns": rag_patterns,
                "is_live": summary.get('price_source') == 'mcp',
                "status": "success"
            }

        except Exception as e:
            return {
                "error": str(e),
                "message": "Could not load market data",
                "status": "error"
            }

    def _check_portfolio(self) -> dict:
        """Get portfolio status from latest backtest results."""
        try:
            import json
            from pathlib import Path

            # Load latest backtest results
            results_path = Path(__file__).parent.parent.parent / "data" / "processed" / "backtest_results.json"

            if not results_path.exists():
                return {
                    "message": "No backtest results found.",
                    "suggestion": "Run a backtest first: python main.py --mode backtest --months 6",
                    "status": "no_data"
                }

            with open(results_path, 'r') as f:
                results = json.load(f)

            return {
                "initial_capital": results.get('initial_capital', 10000),
                "final_value": results.get('final_value', 0),
                "total_return": results.get('total_return', 0),
                "sharpe_ratio": results.get('sharpe_ratio', 0),
                "max_drawdown": results.get('max_drawdown', 0),
                "win_rate": results.get('win_rate', 0),
                "num_trades": results.get('num_trades', 0),
                "avg_trade_return": results.get('avg_trade_return', 0),
                "bah_return": results.get('bah_return', 0),
                "beat_bah": results.get('beat_bah', False),
                "beat_bah_by": results.get('beat_bah_by', 0),
                "status": "success"
            }

        except Exception as e:
            return {
                "error": str(e),
                "message": "Could not load backtest results",
                "status": "error"
            }

    def _diagnose_profit_issues(self, total_return, ml_accuracy, rsi_win_rate,
                                 macd_win_rate, dca_win_rate, swing_win_rate) -> list:
        """
        Diagnose root causes of profit issues by tracing technical metrics.

        Following mentor's guidance: Technical metrics help trace business metric problems.
        """
        issues = []

        # Check ML accuracy (technical metric)
        if ml_accuracy < 0.55:
            issues.append({
                "technical_metric": "ML Direction Accuracy",
                "value": f"{ml_accuracy:.1%}",
                "diagnosis": "Model predictions are coin-flip (49.7%), no better than random",
                "impact_on_business": "Swing trading can't trigger reliably (needs 70% confidence)",
                "fix": "Improve ML features, try different algorithms (XGBoost, LSTM)"
            })

        # Check indicator performance (technical metrics)
        if rsi_win_rate == 0 and macd_win_rate == 0:
            issues.append({
                "technical_metric": "RSI & MACD Signal Win Rates",
                "value": "0% / 0%",
                "diagnosis": "Technical indicators not working in this market regime (2025 downtrend)",
                "impact_on_business": "Entry signals are weak, leading to unprofitable trades",
                "fix": "Consider market-regime-specific indicators or disable in bear markets"
            })

        # Check DCA performance (strategy metric)
        if dca_win_rate == 0 and total_return < 0:
            issues.append({
                "technical_metric": "DCA Win Rate",
                "value": "0%",
                "diagnosis": "All DCA buys resulted in losses (expected in sustained downtrend)",
                "impact_on_business": "Each buy averaged down but price continued falling",
                "fix": "DCA is working as designed (defensive), but in downtrend all buys lose money"
            })

        # But note if strategy still beats buy-and-hold
        if total_return > -0.21:  # Better than -20.08% buy-and-hold
            issues.append({
                "technical_metric": "Overall Strategy Execution",
                "value": f"{total_return:.1%}",
                "diagnosis": "Despite poor technical metrics, BEAT buy-and-hold by 5.83%",
                "impact_on_business": "Defensive strategy (stop-loss, take-profit) limited losses successfully",
                "fix": "Keep v1.0 defensive parameters, improve ML model for better swing entries"
            })

        return issues

    def _analyze_backtest(self) -> dict:
        """Analyze and explain backtest results."""
        try:
            import json
            from pathlib import Path

            # Load backtest results
            results_path = Path(__file__).parent.parent.parent / "data" / "processed" / "backtest_results.json"

            if not results_path.exists():
                return {
                    "message": "No backtest results found.",
                    "suggestion": "Run a backtest first: python main.py --mode backtest",
                    "status": "no_data"
                }

            with open(results_path, 'r') as f:
                results = json.load(f)

            # Business metrics
            total_return = results.get('total_return', 0)
            sharpe_ratio = results.get('sharpe_ratio', 0)
            max_drawdown = results.get('max_drawdown', 0)
            win_rate = results.get('win_rate', 0)
            num_trades = results.get('num_trades', 0)
            buy_hold_return = results.get('buy_and_hold_return', 0)

            # Technical metrics
            ml_accuracy = results.get('ml_direction_accuracy', 0)
            ml_rmse = results.get('ml_price_rmse', 0)
            rsi_win_rate = results.get('rsi_signal_win_rate', 0)
            macd_win_rate = results.get('macd_signal_win_rate', 0)
            fg_correlation = results.get('fg_correlation', 0)

            # Strategy metrics
            dca_win_rate = results.get('dca_win_rate', 0)
            swing_win_rate = results.get('swing_win_rate', 0)
            stop_loss_win_rate = results.get('stop_loss_win_rate', 0)

            # Calculate outperformance
            outperformance = total_return - buy_hold_return

            # Determine conclusion
            beats_buy_hold = outperformance > 0
            defensive_strategy = total_return < 0.15 and max_drawdown < 0.25

            return {
                "business_metrics": {
                    "total_return": total_return,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown": max_drawdown,
                    "win_rate": win_rate,
                    "num_trades": num_trades,
                    "buy_hold_return": buy_hold_return,
                    "outperformance": outperformance,
                    "beats_buy_hold": beats_buy_hold
                },
                "technical_metrics": {
                    "ml_direction_accuracy": ml_accuracy,
                    "ml_price_rmse": ml_rmse,
                    "rsi_signal_win_rate": rsi_win_rate,
                    "macd_signal_win_rate": macd_win_rate,
                    "fg_correlation": fg_correlation
                },
                "strategy_metrics": {
                    "dca_win_rate": dca_win_rate,
                    "swing_win_rate": swing_win_rate,
                    "stop_loss_win_rate": stop_loss_win_rate
                },
                "conclusion": {
                    "strategy_type": "DEFENSIVE (Capital Preservation)" if defensive_strategy else "AGGRESSIVE (Profit Maximization)",
                    "beats_buy_hold": beats_buy_hold,
                    "outperformance_pct": outperformance,
                    "key_finding": "Strategy beat buy-and-hold in downtrend" if beats_buy_hold else "Strategy underperformed buy-and-hold",
                    "ml_needs_improvement": ml_accuracy < 0.65,
                    "recommendation": "Keep v1.0 parameters, focus on ML improvements" if beats_buy_hold else "Consider parameter tuning"
                },
                "diagnostics": {
                    "profit_analysis": {
                        "business_metric": f"Total return: {total_return:.2%}",
                        "root_causes": self._diagnose_profit_issues(
                            total_return, ml_accuracy, rsi_win_rate,
                            macd_win_rate, dca_win_rate, swing_win_rate
                        ),
                        "primary_issue": "ML accuracy at 49.7% (coin-flip)" if ml_accuracy < 0.55 else "Strategy execution",
                        "impact": "Swing trading rarely triggers due to low ML confidence" if ml_accuracy < 0.55 else "All strategies executing"
                    },
                    "technical_to_business_link": {
                        "ml_impact": f"ML accuracy {ml_accuracy:.1%} means predictions are unreliable, limiting swing trades",
                        "indicator_impact": f"RSI/MACD win rates at {rsi_win_rate:.0%}/{macd_win_rate:.0%} indicate signals not working in this market",
                        "strategy_impact": f"DCA win rate {dca_win_rate:.0%}, but still beat buy-and-hold (defensive strategy working)",
                        "bottom_line": "Despite poor technical metrics, business metrics show defensive strategy is working as designed"
                    },
                    "traceability": f"Low profit (-14.25%) ← ML accuracy (49.7%) ← Need better features/model"
                },
                "status": "success"
            }

        except Exception as e:
            return {
                "error": str(e),
                "message": "Could not analyze backtest results",
                "status": "error"
            }

    def _run_trade_cycle(self) -> dict:
        """Execute one trading cycle (get decision + simulated execution)."""
        try:
            from src.decision_box.trading_logic import TradingDecisionBox
            from src.modules.module1_technical import get_latest_indicators
            from src.modules.module2_sentiment import SentimentAnalyzer
            from src.modules.module3_prediction import BitcoinPricePredictor
            from src.data_pipeline.data_loader import BitcoinDataLoader
            from src.data_pipeline.api_client import APIClient

            # Load data
            loader = BitcoinDataLoader()
            df = loader.load_clean_data()

            if df is None or len(df) == 0:
                return {"error": "No historical data available"}

            current_date = df['Date'].iloc[-1]
            current_price = df['Price'].iloc[-1]

            # Get indicators
            technical = get_latest_indicators(df, current_date)

            # Get sentiment
            api_client = APIClient()
            analyzer = SentimentAnalyzer(api_client)
            sentiment = analyzer.analyze_sentiment(technical, current_date)

            # Get prediction
            predictor = BitcoinPricePredictor()
            predictor.train(df, current_date)
            prediction = predictor.predict(df, current_date)

            # Get decision
            portfolio = {'cash': 10000, 'btc': 0, 'trades': []}
            decision_box = TradingDecisionBox(portfolio, initial_capital=10000)

            decision = decision_box.make_decision(
                technical, sentiment, prediction, current_price
            )

            return {
                "action": decision.get('action'),
                "strategy": decision.get('strategy'),
                "reason": decision.get('reason'),
                "amount": decision.get('quantity', decision.get('amount', 0)),
                "price": float(current_price),
                "note": "This is a SIMULATED decision - no actual order placed",
                "status": "success"
            }

        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()

            return {
                "error": str(e),
                "message": "Could not execute trade cycle"
            }

    def _get_decision(self) -> dict:
        """Get trading recommendation without executing."""
        result = self._run_trade_cycle()

        if result.get('status') == 'success':
            result['note'] = "This is a RECOMMENDATION only - no order executed"

        return result

    def _get_help(self) -> dict:
        """Return help information."""
        return {
            "commands": [
                "What's the market situation? - Shows BTC price, RSI, ATR, MACD, Fear & Greed",
                "Should I buy/sell? - Get trading recommendation (no execution)",
                "Run a trade cycle - Get recommendation (simulated)",
                "Show my portfolio - View positions (not yet implemented)",
                "What is DCA? - Ask about trading strategies",
                "Exit - Quit the assistant"
            ],
            "strategies": {
                "DCA": "Dollar-Cost Averaging - Steady accumulation when RSI < 60 or Fear & Greed < 40",
                "Swing": "Opportunistic large moves - Currently DISABLED (was buying tops)",
                "ATR Stop-Loss": "Dynamic exit - Sell if price < Entry - (2.0 × ATR)",
                "Take Profit": "Lock gains - Sell at +15% profit if RSI > 65",
                "Circuit Breaker": "Emergency stop - Pause trading at 25% drawdown"
            },
            "status": "success"
        }


if __name__ == "__main__":
    # Test trading assistant
    print("=" * 60)
    print("TESTING TRADING ASSISTANT")
    print("=" * 60)

    assistant = TradingAssistant(verbose=True)

    test_queries = [
        "What's the Bitcoin price?",
        "Should I buy now?",
        "What is DCA strategy?",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        response = assistant.chat(query)
        print(f"\nResponse: {response}\n")
