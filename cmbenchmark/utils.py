"""Utility functions for console output and CLI operations."""

from contextlib import contextmanager
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def info(msg: str):
    """Print an info message in bold."""
    console.print(f"[bold]{msg}[/bold]")


def section(title: str):
    """Print a section title in bold blue."""
    console.print(f"[bold blue]{title}[/bold blue]\n")


def success(msg: str):
    """Print a success message with a green checkmark."""
    console.print(f"[green]✓[/green] {msg}")


def warn(msg: str):
    """Print a warning message in yellow."""
    console.print(f"[yellow]{msg}[/yellow]")


def error(msg: str):
    """Print an error message in red."""
    console.print(f"[red]Error: {msg}[/red]")


@contextmanager
def step(description: str):
    """Context manager for running a step with progress indication and error handling.
    
    Args:
        description: Description text to display during the step
        
    Yields:
        None - use this context manager around the code that should run in the step
        
    Raises:
        typer.Exit(1): If a ValueError is raised within the step
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(description, total=None)
        try:
            yield
            progress.update(task, completed=1)
        except ValueError as e:
            progress.stop()
            error(str(e))
            raise typer.Exit(1) from e

