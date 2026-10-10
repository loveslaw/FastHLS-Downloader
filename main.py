"""
FastHLS-Downloader CLI Entrypoint
Author: loveslaw
"""

import argparse
import os
import sys
import time

from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

from core.ui import console, show_banner, print_stream_summary
from core.parser import parse_m3u8
from core.downloader import fetch_url, SegmentDownloader
from core.stitcher import stitch_segments


def download_stream(m3u8_url: str, output_path: str, concurrency: int = 16, retries: int = 3):
    console.print(f"[dim cyan]Fetching M3U8 stream manifest from: {m3u8_url}[/dim cyan]")
    try:
        manifest_raw = fetch_url(m3u8_url, timeout=10, retries=retries).decode("utf-8")
    except Exception as e:
        console.print(f"[bold red]Failed to fetch manifest:[/bold red] {e}")
        sys.exit(1)

    playlist = parse_m3u8(manifest_raw, base_url=m3u8_url)

    # If master playlist, select highest bandwidth variant
    if playlist.is_master:
        if not playlist.variants:
            console.print("[bold red]Master playlist contains no stream variants.[/bold red]")
            sys.exit(1)
        best_bw, best_url = playlist.variants[0]
        console.print(f"[bold green]✔ Master playlist detected. Selecting top quality variant ({best_bw // 1000} kbps)[/bold green]")
        return download_stream(best_url, output_path, concurrency, retries)

    if not playlist.segments:
        console.print("[bold red]No segments found in media playlist.[/bold red]")
        sys.exit(1)

    total_duration = sum(s.duration for s in playlist.segments)
    print_stream_summary(m3u8_url, len(playlist.segments), total_duration, output_path)

    downloader = SegmentDownloader(concurrency=concurrency, retries=retries)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("• [yellow]{task.completed}/{task.total} Segments"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading chunks...", total=len(playlist.segments))

        def on_progress(done, total):
            progress.update(task, completed=done)

        start_time = time.time()
        downloaded_chunks = downloader.download_all(playlist.segments, progress_callback=on_progress)
        elapsed = time.time() - start_time

    console.print(f"[bold green]✔ All {len(downloaded_chunks)} segments downloaded in {elapsed:.1f}s![/bold green]")

    with console.status("[bold cyan]Losslessly stitching and assembling container..."):
        final_file = stitch_segments(downloaded_chunks, output_path)

    size_mb = os.path.getsize(final_file) / (1024 * 1024)
    console.print(f"[bold green]✔ Stream successfully assembled:[/bold green] [white]{final_file}[/white] [dim]({size_mb:.2f} MB)[/dim]")


def main():
    show_banner()

    parser = argparse.ArgumentParser(description="FastHLS-Downloader - Multi-Threaded M3U8 Stream Grabber")
    parser.add_argument("url", nargs="?", help="M3U8 stream URL or master manifest")
    parser.add_argument("-o", "--output", default="stream_output.mp4", help="Output file path (default: stream_output.mp4)")
    parser.add_argument("-c", "--concurrency", type=int, default=16, help="Parallel download workers (default: 16)")
    parser.add_argument("-r", "--retries", type=int, default=3, help="Max chunk download retries (default: 3)")
    args = parser.parse_args()

    url = args.url
    if not url:
        url = input("Enter .m3u8 playlist URL: ").strip()
        if not url:
            console.print("[yellow]No URL provided. Exiting.[/yellow]")
            sys.exit(0)

    download_stream(url, args.output, concurrency=args.concurrency, retries=args.retries)


if __name__ == "__main__":
    main()
