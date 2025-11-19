#!/usr/bin/env python3
"""
Simple Docker Monitor - No external dependencies
Uses ANSI color codes to create htop-like colored bars
"""

import subprocess
import json
import time
import os

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

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

def create_colored_bar(percentage, width=20):
    """Create a colored ASCII bar like htop"""
    filled = int((percentage / 100) * width)
    empty = width - filled
    
    # Choose color based on percentage
    if percentage < 50:
        color = Colors.GREEN
    elif percentage < 75:
        color = Colors.YELLOW
    else:
        color = Colors.RED
    
    bar = color + '█' * filled + Colors.RESET + '░' * empty
    return f"{bar} {percentage:5.1f}%"

def print_header():
    """Print the header"""
    print(f"{Colors.BOLD}{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║              Docker Monitor - htop inspired                           ║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚═══════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()

def display_summary(images, containers):
    """Display summary statistics"""
    running = sum(1 for c in containers if c['State'] == 'running')
    stopped = len(containers) - running
    
    print(f"{Colors.BOLD}Summary:{Colors.RESET}")
    print(f"  Docker Images:    {Colors.CYAN}{len(images)}{Colors.RESET}")
    print(f"  Total Containers: {Colors.CYAN}{len(containers)}{Colors.RESET}")
    print(f"  Running:          {Colors.GREEN}{running}{Colors.RESET}")
    print(f"  Stopped:          {Colors.RED}{stopped}{Colors.RESET}")
    print()

def display_images(images):
    """Display images table"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}Docker Images:{Colors.RESET}")
    print(f"{Colors.BOLD}{'Repository':<30} {'Tag':<15} {'Size':<10} {'Size Bar':<30}{Colors.RESET}")
    print("─" * 90)
    
    if images:
        max_size = max(parse_size(img['Size']) for img in images)
        for img in images[:8]:  # Show top 8
            size_mb = parse_size(img['Size'])
            percentage = (size_mb / max_size * 100) if max_size > 0 else 0
            
            repo = img['Repository'][:28]
            tag = img['Tag'][:13]
            size = img['Size']
            bar = create_colored_bar(percentage, width=15)
            
            print(f"{Colors.CYAN}{repo:<30}{Colors.RESET} {Colors.YELLOW}{tag:<15}{Colors.RESET} {size:<10} {bar}")
    else:
        print(f"{Colors.YELLOW}  No images found{Colors.RESET}")
    print()

def display_containers(containers):
    """Display containers table"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}Docker Containers:{Colors.RESET}")
    print(f"{Colors.BOLD}{'Name':<25} {'Image':<25} {'Status':<20} {'State':<10}{Colors.RESET}")
    print("─" * 90)
    
    for container in containers[:10]:  # Show top 10
        name = container['Names'][:23]
        image = container['Image'][:23]
        status = container['Status'][:18]
        state = container['State']
        
        state_color = Colors.GREEN if state == 'running' else Colors.RED
        
        print(f"{Colors.CYAN}{name:<25}{Colors.RESET} {Colors.YELLOW}{image:<25}{Colors.RESET} {status:<20} {state_color}{state:<10}{Colors.RESET}")
    print()

def display_stats(stats):
    """Display resource usage statistics"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}Resource Usage (Running Containers):{Colors.RESET}")
    
    if not stats:
        print(f"{Colors.YELLOW}  No running containers{Colors.RESET}")
        print()
        return
    
    print(f"{Colors.BOLD}{'Name':<25} {'CPU Usage':<35} {'Memory Usage':<35}{Colors.RESET}")
    print("─" * 100)
    
    for stat in stats[:8]:
        name = stat['Name'][:23]
        cpu_percent = float(stat['CPUPerc'].rstrip('%'))
        mem_percent = float(stat['MemPerc'].rstrip('%'))
        
        cpu_bar = create_colored_bar(cpu_percent, width=15)
        mem_bar = create_colored_bar(mem_percent, width=15)
        
        print(f"{Colors.CYAN}{name:<25}{Colors.RESET} {cpu_bar} {mem_bar}")
    print()

def main():
    """Main loop"""
    try:
        subprocess.run(["docker", "version"], capture_output=True, check=True)
    except:
        print(f"{Colors.RED}Error: Docker is not installed or not running{Colors.RESET}")
        return
    
    try:
        while True:
            clear_screen()
            
            # Get Docker data
            images = get_docker_images()
            containers = get_docker_containers()
            stats = get_container_stats()
            
            # Display everything
            print_header()
            display_summary(images, containers)
            display_images(images)
            display_containers(containers)
            display_stats(stats)
            
            print(f"{Colors.BOLD}Press Ctrl+C to exit{Colors.RESET} | Refreshing every 2 seconds...")
            time.sleep(20)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}Goodbye!{Colors.RESET}")

if __name__ == "__main__":
    main()
