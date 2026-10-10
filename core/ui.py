"""
Rich Terminal Interface for FastHLS-Downloader
Author: loveslaw
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

BANNER = """[bold yellow]
  ███████╗ █████╗ ███████╗████████╗██╗  ██╗██╗     ███████╗
  ██╔════╝██╔══██╗██╔════╝╚══██╔══╝██║  ██║██║     ██╔════╝
  █████╗  ███████║███████╗   ██║   ███████║██║     ███████╗
  ██╔══╝  ██╔══██║╚════██║   ██║   ██╔══██║██║     ╚════██║
  ██║     ██║  ██║███████║   ██║   ██║  ██║███████╗███████║
  ╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝
[/bold yellow]
[dim cyan]  Multi-Threaded HLS Stream Grabber · AES-128 Decryptor · TS Stitcher[/dim cyan]
[dim white]  Author: loveslaw | Version: 1.0.0[/dim white]
"""


def show_banner():
    console.print(BANNER)


def print_stream_summary(url: str, segments_count: int, total_duration: float, output: str):
    mins = int(total_duration // 60)
    secs = int(total_duration % 60)
    table = Table(title="Stream Ingestion Summary", border_style="dim white")
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", style="bold white")
    table.add_row("Manifest URL", url[:60] + ("..." if len(url) > 60 else ""))
    table.add_row("Total Segments", str(segments_count))
    table.add_row("Estimated Duration", f"{mins}m {secs}s ({total_duration:.1f}s)")
    table.add_row("Target Output File", output)
    console.print(table)
