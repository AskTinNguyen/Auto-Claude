"""
Ralph CLI Output Utilities
=========================

Rich console output helpers for formatted CLI display.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Custom theme for Ralph CLI
RALPH_THEME = Theme({
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "bold blue",
    "header": "bold magenta",
    "muted": "dim",
    "highlight": "bold cyan",
})

# Global console instance
console = Console(theme=RALPH_THEME)


def print_success(message: str, prefix: str = "✓") -> None:
    """Print a success message."""
    console.print(f"[success]{prefix}[/success] {message}")


def print_error(message: str, prefix: str = "✗") -> None:
    """Print an error message."""
    console.print(f"[error]{prefix}[/error] {message}")


def print_warning(message: str, prefix: str = "⚠") -> None:
    """Print a warning message."""
    console.print(f"[warning]{prefix}[/warning] {message}")


def print_info(message: str, prefix: str = "ℹ") -> None:
    """Print an info message."""
    console.print(f"[info]{prefix}[/info] {message}")


def print_header(title: str, subtitle: str | None = None) -> None:
    """Print a section header."""
    console.print()
    console.print(f"[header]═══ {title} ═══[/header]")
    if subtitle:
        console.print(f"[muted]{subtitle}[/muted]")
    console.print()


def print_panel(content: str, title: str | None = None, style: str = "blue") -> None:
    """Print content in a panel."""
    console.print(Panel(content, title=title, border_style=style))


def create_table(title: str | None = None, show_header: bool = True) -> Table:
    """Create a styled table."""
    return Table(
        title=title,
        show_header=show_header,
        header_style="bold cyan",
        border_style="dim",
    )


def format_bytes(size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format seconds to human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_cost(usd: float) -> str:
    """Format USD cost."""
    return f"${usd:.4f}"


def format_tokens(count: int) -> str:
    """Format token count with comma separators."""
    return f"{count:,}"


def format_percentage(value: float) -> str:
    """Format percentage."""
    return f"{value:.1f}%"
