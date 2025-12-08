#!/usr/bin/env python3
"""
Trading Interface - CLI Chat

Simple command-line interface for natural language trading assistant.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.natural_language.agent import TradingAssistant


class TradingInterface:
    """
    Command-line interface for natural language trading assistant.

    Usage:
        python -m src.natural_language.interface
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize interface.

        Args:
            verbose: Print debug information
        """
        print("[INFO] Initializing Bitcoin Trading Assistant...")

        try:
            self.assistant = TradingAssistant(verbose=verbose)
            print("[OK] Ready!\n")
            self.verbose = verbose

        except ValueError as e:
            print(f"\n[ERROR] Configuration error: {e}")
            print("\nTo fix:")
            print("1. Get API key from: https://aistudio.google.com/app/apikey")
            print("2. Add to .env file: GEMINI_API_KEY=your_key_here")
            sys.exit(1)

        except ImportError as e:
            print(f"\n[ERROR] Missing dependency: {e}")
            print("\nTo fix:")
            print("pip install google-generativeai pydantic")
            sys.exit(1)

        except Exception as e:
            print(f"\n[ERROR] Initialization error: {e}")
            sys.exit(1)

    def run(self):
        """Main chat loop."""
        self._print_welcome()

        while True:
            try:
                # Get user input
                user_input = input("\n You: ").strip()

                if not user_input:
                    continue

                # Check for exit
                if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
                    print("\nGoodbye! Happy trading!")
                    break

                # Process query
                print("\nBot: ", end="", flush=True)
                response = self._handle_query(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n\nGoodbye! Happy trading!")
                break

            except Exception as e:
                print(f"\n[ERROR] Error: {e}")

                if self.verbose:
                    import traceback
                    traceback.print_exc()

    def _print_welcome(self):
        """Print welcome message."""
        print("=" * 60)
        print("BITCOIN TRADING ASSISTANT")
        print("=" * 60)
        print("\nAsk me anything about your trading bot!")
        print("\nExample questions:")
        print("  • What's the market situation?")
        print("  • Should I buy now?")
        print("  • Show my portfolio")
        print("  • Run a trade cycle")
        print("  • What is DCA strategy?")
        print("\nCommands:")
        print("  • Type 'exit' or 'quit' to stop")
        print("  • Type 'help' for more information")

    def _handle_query(self, user_input: str) -> str:
        """
        Process user query through agent.

        Args:
            user_input: User's question/command

        Returns:
            Natural language response
        """
        try:
            response = self.assistant.chat(user_input)
            return response

        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()

            return f"Sorry, I encountered an error: {e}"


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Bitcoin Trading Assistant - Natural Language Interface"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print debug information'
    )

    args = parser.parse_args()

    # Run interface
    interface = TradingInterface(verbose=args.verbose)
    interface.run()


if __name__ == "__main__":
    main()
