#!/usr/bin/env python3
"""
Docker Monitor - Flicker-free with Rich Live Display
Uses Rich's built-in double buffering via Live display
"""

import subprocess
import json
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

console = Console()

def get_docker_images():
    """Get list of Docker images"""
    try:
        result = subprocess.run(
            ["docker", "images", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            check=True
        )
        images = []
        for line in result.stdout.strip().split('\n'):
            if line:
                images.append(json.loads(line))
        return images
    except:
        return []

def get_docker_containers():
    """Get list of Docker containers"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            check=True
        )
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                containers.append(json.loads(line))
        return containers
    except:
        return []

def get_container_stats():
    """Get stats for running containers"""
    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            check=True
        )
        stats = []
        for line in result.stdout.strip().split('\n'):
            if line:
                stats.append(json.loads(line))
        return stats
    except:
        return []

def parse_size(size_str):
    """Convert size string to MB"""
    size_str = size_str.strip()
    if 'GB' in size_str:
        return float(size_str.replace('GB', '')) * 1024
    elif 'MB' in size_str:
        return float(size_str.replace('MB', ''))
    elif 'KB' in size_str:
        return float(size_str.replace('KB', '')) / 1024
    return 0

def create_bar(percentage, width=20):
    """Create a colored progress bar"""
    filled = int((percentage / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    
    if percentage < 50:
        color = "green"
    elif percentage < 75:
        color = "yellow"
    else:
        color = "red"
    
    return f"[{color}]{bar}[/{color}] {percentage:5.1f}%"

def generate_display():
    """Generate the complete display layout"""
    
    # Get Docker data
    images = get_docker_images()
    containers = get_docker_containers()
    stats = get_container_stats()
    
    # Create main layout
    layout = Layout()
    
    # Split into sections
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="summary_row", size=4),
        Layout(name="images", size=12),
        Layout(name="containers", size=12),
        Layout(name="footer", size=1)
    )

    # Split summary row: Summary occupies 1/3, Resource Usage occupies 2/3
    layout["summary_row"].split_row(
        Layout(name="summary", ratio=1),
        Layout(name="resource_usage", ratio=2)
    )

    # Header
    header_text = Text("Docker Monitor - Flicker Free", style="bold cyan", justify="center")
    layout["header"].update(Panel(header_text, border_style="cyan"))

    # Summary (now occupies only half the width)
    running = sum(1 for c in containers if c['State'] == 'running')
    stopped = len(containers) - running

    summary_table = Table.grid(padding=(0, 2))
    summary_table.add_column(style="bold")
    summary_table.add_column()

    summary_table.add_row("Docker Images:", f"[cyan]{len(images)}[/cyan]")
    summary_table.add_row("Total Containers:", f"[cyan]{len(containers)}[/cyan]")
    summary_table.add_row("Running:", f"[green]{running}[/green]")
    summary_table.add_row("Stopped:", f"[red]{stopped}[/red]")

    layout["summary"].update(Panel(summary_table, title="Summary", border_style="blue"))

    # Resource Usage (adjacent to Summary, occupies 2/3 width)
    if stats:
        stats_table = Table(show_header=True, header_style="bold magenta", expand=True)
        stats_table.add_column("Name", style="cyan", no_wrap=True)
        stats_table.add_column("CPU Usage", width=25)
        stats_table.add_column("Memory Usage", width=25)

        for stat in stats[:5]:  # Show top 5
            cpu_percent = float(stat['CPUPerc'].rstrip('%'))
            mem_percent = float(stat['MemPerc'].rstrip('%'))

            stats_table.add_row(
                stat['Name'][:25],
                create_bar(cpu_percent, width=10),
                create_bar(mem_percent, width=10)
            )

        layout["resource_usage"].update(Panel(stats_table, title="Resource Usage", border_style="green"))
    else:
        layout["resource_usage"].update(Panel("[yellow]No running containers[/yellow]",
                                    title="Resource Usage", border_style="green"))

    # Images Table
    images_table = Table(show_header=True, header_style="bold magenta", expand=True)
    images_table.add_column("Repository", style="cyan", no_wrap=True)
    images_table.add_column("Tag", style="yellow")
    images_table.add_column("Size", justify="right")
    images_table.add_column("Size Bar", width=35)
    
    if images:
        max_size = max(parse_size(img['Size']) for img in images)
        for img in images[:5]:  # Show top 5
            size_mb = parse_size(img['Size'])
            percentage = (size_mb / max_size * 100) if max_size > 0 else 0
            images_table.add_row(
                img['Repository'][:30],
                img['Tag'][:15],
                img['Size'],
                create_bar(percentage, width=15)
            )
    else:
        images_table.add_row("No images", "", "", "")
    
    layout["images"].update(Panel(images_table, title="Docker Images", border_style="magenta"))
    
    # Containers Table
    containers_table = Table(show_header=True, header_style="bold magenta", expand=True)
    containers_table.add_column("Name", style="cyan", no_wrap=True)
    containers_table.add_column("Image", style="yellow", no_wrap=True)
    containers_table.add_column("Status")
    containers_table.add_column("State")
    
    for container in containers[:5]:  # Show top 5
        state = container['State']
        state_color = "green" if state == "running" else "red"
        containers_table.add_row(
            container['Names'][:25],
            container['Image'][:25],
            container['Status'][:20],
            f"[{state_color}]{state}[/{state_color}]"
        )
    
    if not containers:
        containers_table.add_row("No containers", "", "", "")
    
    layout["containers"].update(Panel(containers_table, title="Docker Containers", border_style="magenta"))

    # Footer
    footer_text = Text("Press Ctrl+C to exit | Auto-refresh every 2 seconds", 
                      style="dim", justify="center")
    layout["footer"].update(footer_text)
    
    return layout

def main():
    """Main loop with Live display"""
    try:
        subprocess.run(["docker", "version"], capture_output=True, check=True)
    except:
        console.print("[red]Error: Docker is not installed or not running[/red]")
        return
    
    try:
        # Use Live display for flicker-free updates
        with Live(generate_display(), refresh_per_second=0.5, screen=True) as live:
            while True:
                time.sleep(2)
                live.update(generate_display())
    except KeyboardInterrupt:
        console.print("\n[green]Goodbye![/green]")

if __name__ == "__main__":
    main()
