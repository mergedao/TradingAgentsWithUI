import questionary
import typer
from typing import List, Optional, Tuple, Dict
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.table import Table
from rich import box

from cli.models import AnalystType
from tradingagents.default_config import DEFAULT_CONFIG

console = Console()

ANALYST_ORDER = [
    ("Market Analyst", AnalystType.MARKET),
    ("Social Media Analyst", AnalystType.SOCIAL),
    ("News Analyst", AnalystType.NEWS),
    ("Fundamentals Analyst", AnalystType.FUNDAMENTALS),
]


def get_ticker() -> str:
    """Prompt the user to enter a ticker symbol."""
    ticker = questionary.text(
        "Enter the ticker symbol to analyze:",
        validate=lambda x: len(x.strip()) > 0 or "Please enter a valid ticker symbol.",
        style=questionary.Style(
            [
                ("text", "fg:green"),
                ("highlighted", "noinherit"),
            ]
        ),
    ).ask()

    if not ticker:
        console.print("\n[red]No ticker symbol provided. Exiting...[/red]")
        exit(1)

    return ticker.strip().upper()


def get_analysis_date() -> str:
    """Prompt the user to enter a date in YYYY-MM-DD format."""
    import re
    from datetime import datetime

    def validate_date(date_str: str) -> bool:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    date = questionary.text(
        "Enter the analysis date (YYYY-MM-DD):",
        validate=lambda x: validate_date(x.strip())
        or "Please enter a valid date in YYYY-MM-DD format.",
        style=questionary.Style(
            [
                ("text", "fg:green"),
                ("highlighted", "noinherit"),
            ]
        ),
    ).ask()

    if not date:
        console.print("\n[red]No date provided. Exiting...[/red]")
        exit(1)

    return date.strip()


def select_analysts() -> List[AnalystType]:
    """Select analysts using an interactive checkbox."""
    choices = questionary.checkbox(
        "Select Your [Analysts Team]:",
        choices=[
            questionary.Choice(display, value=value) for display, value in ANALYST_ORDER
        ],
        instruction="\n- Press Space to select/unselect analysts\n- Press 'a' to select/unselect all\n- Press Enter when done",
        validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not choices:
        console.print("\n[red]No analysts selected. Exiting...[/red]")
        exit(1)

    return choices


def select_research_depth() -> int:
    """Select research depth using an interactive selection."""

    # Define research depth options with their corresponding values
    DEPTH_OPTIONS = [
        ("Shallow - Quick research, few debate and strategy discussion rounds", 1),
        ("Medium - Middle ground, moderate debate rounds and strategy discussion", 3),
        ("Deep - Comprehensive research, in depth debate and strategy discussion", 5),
    ]

    choice = questionary.select(
        "Select Your [Research Depth]:",
        choices=[
            questionary.Choice(display, value=value) for display, value in DEPTH_OPTIONS
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:yellow noinherit"),
                ("highlighted", "fg:yellow noinherit"),
                ("pointer", "fg:yellow noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No research depth selected. Exiting...[/red]")
        exit(1)

    return choice


def select_llm_provider() -> tuple[str, str, dict]:
    """Select the LLM provider with support for default config and custom options."""
    # Check if we should offer saved configs first
    from cli.config_manager import select_saved_config, list_configs
    
    if list_configs():
        use_saved = questionary.confirm(
            "Would you like to use a saved configuration?",
            default=False
        ).ask()
        
        if use_saved:
            saved_config = select_saved_config()
            if saved_config:
                return "saved_config", "saved_config", {"type": "saved_config", "config": saved_config}
    
    # Define LLM provider options
    BASE_URLS = [
        ("Default Config", "default", {"type": "default"}),
        ("OpenAI", "https://api.openai.com/v1", {"type": "preset"}),
        ("Custom OpenAI Compatible", "custom_openai", {"type": "custom_openai"}),
        ("Anthropic", "https://api.anthropic.com/", {"type": "preset"}),
        ("Google", "https://generativelanguage.googleapis.com/v1", {"type": "preset"}),
        ("Openrouter", "https://openrouter.ai/api/v1", {"type": "preset"}),
        ("Ollama", "http://localhost:11434/v1", {"type": "preset"}),        
    ]
    
    choice = questionary.select(
        "Select your LLM Provider:",
        choices=[
            questionary.Choice(display, value=(display, value, metadata))
            for display, value, metadata in BASE_URLS
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()
    
    if choice is None:
        console.print("\n[red]No LLM provider selected. Exiting...[/red]")
        exit(1)
    
    display_name, url, metadata = choice
    
    if metadata["type"] == "default":
        # Use default config
        console.print(f"[green]Using default configuration from DEFAULT_CONFIG[/green]")
        return "default", "default", {"type": "default"}
    elif metadata["type"] == "custom_openai":
        # Get custom OpenAI compatible settings
        return get_custom_openai_config()
    else:
        # Preset provider
        console.print(f"You selected: {display_name}\tURL: {url}")
        return display_name, url, {"type": "preset"}


def get_custom_openai_config() -> tuple[str, str, dict]:
    """Get custom OpenAI compatible API configuration."""
    console.print("\n[bold cyan]Custom OpenAI Compatible API Configuration[/bold cyan]")
    
    # Get custom API URL
    custom_url = questionary.text(
        "Enter custom API base URL:",
        default="https://api.your-provider.com/v1",
        instruction="Enter the base URL for your OpenAI-compatible API"
    ).ask()
    
    if not custom_url:
        console.print("\n[red]No URL provided. Exiting...[/red]")
        exit(1)
    
    # Get custom models
    custom_quick_model = questionary.text(
        "Enter quick-thinking model name:",
        default="gpt-4o-mini",
        instruction="Enter the model name for quick thinking tasks"
    ).ask()
    
    custom_deep_model = questionary.text(
        "Enter deep-thinking model name:",
        default="gpt-4o",
        instruction="Enter the model name for deep thinking tasks"
    ).ask()
    
    if not custom_quick_model or not custom_deep_model:
        console.print("\n[red]Model names are required. Exiting...[/red]")
        exit(1)
    
    console.print(f"[green]Custom OpenAI Config:[/green]")
    console.print(f"  URL: {custom_url}")
    console.print(f"  Quick Model: {custom_quick_model}")
    console.print(f"  Deep Model: {custom_deep_model}")
    
    return "custom_openai", custom_url, {
        "type": "custom_openai",
        "quick_model": custom_quick_model,
        "deep_model": custom_deep_model
    }


def select_shallow_thinking_agent(provider_info) -> str:
    """Select shallow thinking llm engine using an interactive selection."""
    provider, url, metadata = provider_info
    
    # Handle different provider types
    if metadata["type"] == "default":
        console.print(f"[green]Using default quick-thinking model: {DEFAULT_CONFIG['quick_think_llm']}[/green]")
        return DEFAULT_CONFIG["quick_think_llm"]
    elif metadata["type"] == "custom_openai":
        console.print(f"[green]Using custom quick-thinking model: {metadata['quick_model']}[/green]")
        return metadata["quick_model"]
    elif metadata["type"] == "saved_config":
        saved_config = metadata["config"]
        model = saved_config.get("quick_think_llm", DEFAULT_CONFIG["quick_think_llm"])
        console.print(f"[green]Using saved quick-thinking model: {model}[/green]")
        return model
    
    # For preset providers, use the existing selection logic
    provider_key = provider.lower()
    
    # Define shallow thinking llm engine options with their corresponding model names
    SHALLOW_AGENT_OPTIONS = {
        "openai": [
            ("GPT-4o-mini - Fast and efficient for quick tasks", "gpt-4o-mini"),
            ("GPT-4.1-nano - Ultra-lightweight model for basic operations", "gpt-4.1-nano"),
            ("GPT-4.1-mini - Compact model with good performance", "gpt-4.1-mini"),
            ("GPT-4o - Standard model with solid capabilities", "gpt-4o"),
        ],
        "anthropic": [
            ("Claude Haiku 3.5 - Fast inference and standard capabilities", "claude-3-5-haiku-latest"),
            ("Claude Sonnet 3.5 - Highly capable standard model", "claude-3-5-sonnet-latest"),
            ("Claude Sonnet 3.7 - Exceptional hybrid reasoning and agentic capabilities", "claude-3-7-sonnet-latest"),
            ("Claude Sonnet 4 - High performance and excellent reasoning", "claude-sonnet-4-0"),
        ],
        "google": [
            ("Gemini 2.0 Flash-Lite - Cost efficiency and low latency", "gemini-2.0-flash-lite"),
            ("Gemini 2.0 Flash - Next generation features, speed, and thinking", "gemini-2.0-flash"),
            ("Gemini 2.5 Flash - Adaptive thinking, cost efficiency", "gemini-2.5-flash-preview-05-20"),
        ],
        "openrouter": [
            ("Meta: Llama 4 Scout", "meta-llama/llama-4-scout:free"),
            ("Meta: Llama 3.3 8B Instruct - A lightweight and ultra-fast variant of Llama 3.3 70B", "meta-llama/llama-3.3-8b-instruct:free"),
            ("google/gemini-2.0-flash-exp:free - Gemini Flash 2.0 offers a significantly faster time to first token", "google/gemini-2.0-flash-exp:free"),
        ],
        "ollama": [
            ("llama3.1 local", "llama3.1"),
            ("llama3.2 local", "llama3.2"),
        ]
    }

    if provider_key not in SHALLOW_AGENT_OPTIONS:
        console.print(f"[red]Unknown provider: {provider}. Exiting...[/red]")
        exit(1)

    choice = questionary.select(
        "Select Your [Quick-Thinking LLM Engine]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in SHALLOW_AGENT_OPTIONS[provider_key]
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print(
            "\n[red]No shallow thinking llm engine selected. Exiting...[/red]"
        )
        exit(1)

    return choice


def select_deep_thinking_agent(provider_info) -> str:
    """Select deep thinking llm engine using an interactive selection."""
    provider, url, metadata = provider_info
    
    # Handle different provider types
    if metadata["type"] == "default":
        console.print(f"[green]Using default deep-thinking model: {DEFAULT_CONFIG['deep_think_llm']}[/green]")
        return DEFAULT_CONFIG["deep_think_llm"]
    elif metadata["type"] == "custom_openai":
        console.print(f"[green]Using custom deep-thinking model: {metadata['deep_model']}[/green]")
        return metadata["deep_model"]
    elif metadata["type"] == "saved_config":
        saved_config = metadata["config"]
        model = saved_config.get("deep_think_llm", DEFAULT_CONFIG["deep_think_llm"])
        console.print(f"[green]Using saved deep-thinking model: {model}[/green]")
        return model
    
    # For preset providers, use the existing selection logic
    provider_key = provider.lower()

    # Define deep thinking llm engine options with their corresponding model names
    DEEP_AGENT_OPTIONS = {
        "openai": [
            ("GPT-4.1-nano - Ultra-lightweight model for basic operations", "gpt-4.1-nano"),
            ("GPT-4.1-mini - Compact model with good performance", "gpt-4.1-mini"),
            ("GPT-4o - Standard model with solid capabilities", "gpt-4o"),
            ("o4-mini - Specialized reasoning model (compact)", "o4-mini"),
            ("o3-mini - Advanced reasoning model (lightweight)", "o3-mini"),
            ("o3 - Full advanced reasoning model", "o3"),
            ("o1 - Premier reasoning and problem-solving model", "o1"),
        ],
        "anthropic": [
            ("Claude Haiku 3.5 - Fast inference and standard capabilities", "claude-3-5-haiku-latest"),
            ("Claude Sonnet 3.5 - Highly capable standard model", "claude-3-5-sonnet-latest"),
            ("Claude Sonnet 3.7 - Exceptional hybrid reasoning and agentic capabilities", "claude-3-7-sonnet-latest"),
            ("Claude Sonnet 4 - High performance and excellent reasoning", "claude-sonnet-4-0"),
            ("Claude Opus 4 - Most powerful Anthropic model", "	claude-opus-4-0"),
        ],
        "google": [
            ("Gemini 2.0 Flash-Lite - Cost efficiency and low latency", "gemini-2.0-flash-lite"),
            ("Gemini 2.0 Flash - Next generation features, speed, and thinking", "gemini-2.0-flash"),
            ("Gemini 2.5 Flash - Adaptive thinking, cost efficiency", "gemini-2.5-flash-preview-05-20"),
            ("Gemini 2.5 Pro", "gemini-2.5-pro-preview-06-05"),
        ],
        "openrouter": [
            ("DeepSeek V3 - a 685B-parameter, mixture-of-experts model", "deepseek/deepseek-chat-v3-0324:free"),
            ("Deepseek - latest iteration of the flagship chat model family from the DeepSeek team.", "deepseek/deepseek-chat-v3-0324:free"),
        ],
        "ollama": [
            ("llama3.1 local", "llama3.1"),
            ("qwen3", "qwen3"),
        ]
    }
    
    if provider_key not in DEEP_AGENT_OPTIONS:
        console.print(f"[red]Unknown provider: {provider}. Exiting...[/red]")
        exit(1)
    
    choice = questionary.select(
        "Select Your [Deep-Thinking LLM Engine]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in DEEP_AGENT_OPTIONS[provider_key]
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No deep thinking llm engine selected. Exiting...[/red]")
        exit(1)

    return choice
