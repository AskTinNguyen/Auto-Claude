"""
Ralph CLI Progress Utilities
===========================

Progress bars and spinners for long-running operations.
"""

from contextlib import contextmanager
from typing import Generator

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.console import Console

console = Console()


def create_progress() -> Progress:
    """Create a styled progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def create_simple_progress() -> Progress:
    """Create a simple progress bar without time estimates."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )


@contextmanager
def create_spinner(message: str) -> Generator[None, None, None]:
    """Create a spinner context manager."""
    with console.status(f"[bold blue]{message}[/bold blue]") as status:
        yield


class ProgressTracker:
    """
    Track progress of multi-step operations.

    Example:
        tracker = ProgressTracker(total_steps=5)
        tracker.start("Processing files")
        for i in range(5):
            tracker.update(f"Processing file {i+1}")
        tracker.complete("All files processed")
    """

    def __init__(self, total_steps: int = 100):
        self.total_steps = total_steps
        self.current_step = 0
        self.progress: Progress | None = None
        self.task_id = None

    def start(self, description: str) -> None:
        """Start progress tracking."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        )
        self.progress.start()
        self.task_id = self.progress.add_task(description, total=self.total_steps)

    def update(self, description: str | None = None, advance: int = 1) -> None:
        """Update progress."""
        if self.progress and self.task_id is not None:
            self.current_step += advance
            if description:
                self.progress.update(self.task_id, description=description, advance=advance)
            else:
                self.progress.update(self.task_id, advance=advance)

    def set_progress(self, completed: int, description: str | None = None) -> None:
        """Set progress to a specific value."""
        if self.progress and self.task_id is not None:
            self.current_step = completed
            if description:
                self.progress.update(self.task_id, completed=completed, description=description)
            else:
                self.progress.update(self.task_id, completed=completed)

    def complete(self, message: str | None = None) -> None:
        """Complete progress tracking."""
        if self.progress:
            if self.task_id is not None:
                self.progress.update(self.task_id, completed=self.total_steps)
            self.progress.stop()

        if message:
            console.print(f"[green]✓[/green] {message}")
