import time

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

def typewriter_effect(text, style="bold white", speed=0.03):
    """Simulates typing effect for dramatic text."""
    for char in text:
        console.print(char, end="", style=style)
        time.sleep(speed)
    console.print()

def demo_success_flow():
    """Simulates a successful WDK transaction."""
    console.clear()
    console.print(Panel.fit("[bold green]SCENARIO 1: LEGITIMATE ASSET SWAP (USDT -> GOLD)[/bold green]", border_style="green"))
    time.sleep(1)

    amount = "50.0 USDT"

    console.print(f"\n[bold cyan]>>> [AI STRATEGY] MARKET DIP DETECTED (RSI < 30). EXECUTING BUY: {amount} -> XAUT (Gold)[/bold cyan]")
    time.sleep(0.5)

    # 1. Brain Analysis
    with console.status("[bold yellow][AI BRAIN] Analyzing transaction intent & recipient...", spinner="dots"):
        time.sleep(1.5)
        console.print("[green]✔ Intent Verified: ASSET_SWAP[/green]")
        time.sleep(0.5)
        console.print("[green]✔ Recipient Verified: TRUSTED_EXCHANGE[/green]")
        time.sleep(0.5)

    console.print("[bold green]✅ [RISK ASSESSMENT] PASSED. INITIATING WDK SEQUENCE.[/bold green]")
    Prompt.ask("\n[dim]Press Enter to Execute WDK...[/dim]")

    # 2. WDK Execution
    with console.status("[bold blue][WDK] Connecting to Tether Gold Contract...", spinner="earth"):
        time.sleep(1)
        console.print("[blue]ℹ Gas Price: 15 gwei (Optimized)[/blue]")
        time.sleep(0.5)
        console.print("[blue]ℹ Nonce: 42 (Synced)[/blue]")
        time.sleep(1)

    console.print("[bold green]🚀 [WDK] SIGNATURE BROADCASTED: 0x7f9a...[/bold green]")
    Prompt.ask("\n[dim]Press Enter to View Report...[/dim]")

    # 3. Final Report
    console.print(Panel(
        "[bold]Transaction Hash:[/bold] 0x7f9a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1\n"
        "[bold]Status:[/bold] [green]CONFIRMED[/green]\n"
        "[bold]Asset:[/bold]  XAUT (Tether Gold)\n"
        "[bold]Amount:[/bold] 0.025 XAUT (~50 USDT)",
        title="[bold green]✅ MISSION ACCOMPLISHED[/bold green]",
        border_style="green",
        expand=False
    ))

def demo_attack_flow():
    """Simulates a blocked phishing attack with dramatic effects."""
    console.clear()
    console.print(Panel.fit("[bold red]SCENARIO 2: PHISHING ATTACK (GUARDIAN INTERVENTION)[/bold red]", border_style="red"))
    time.sleep(1)

    phishing_target = "0x6666666666666666666666666666666666666666"
    amount = "10,000.0 USDT"

    # Simulate a fast, malicious injection
    console.print(f"\n[bold red blink]>>> [INJECTION DETECTED] UNAUTHORIZED TRANSFER: {amount} -> {phishing_target}[/bold red blink]")
    time.sleep(0.5)

    # 1. Brain Analysis - PANIC MODE
    with console.status("[bold red][AI BRAIN] SCANNING THREAT DATABASES...", spinner="runner"):
        time.sleep(1)
        console.print("[bold red]⚠ ALERT: ADDRESS MATCHES 'OPENCLAW_PHISHING_DB'[/bold red]")
        time.sleep(0.8)
        console.print("[bold red]⚠ ALERT: AMOUNT EXCEEDS SAFETY LIMIT (1000 USDT)[/bold red]")
        time.sleep(0.5)

    # Pause for dramatic effect
    Prompt.ask("\n[dim]Press Enter to Trigger Guardian Protocol...[/dim]")

    # 2. GUARDIAN INTERVENTION
    # Flashing Warning
    for _ in range(3):
        console.print("[bold white on red]!!! SECURITY OVERRIDE TRIGGERED !!![/bold white on red]", justify="center")
        time.sleep(0.2)
        console.print("                                         ", justify="center") # clear line simulation
        time.sleep(0.1)

    console.print("[bold white on red]!!! SECURITY OVERRIDE TRIGGERED !!![/bold white on red]", justify="center")

    # 3. Block Report
    error_panel = Panel(
        "[bold red]⛔ TRANSACTION BLOCKED BY GUARDIAN PROTOCOL[/bold red]\n\n"
        "[bold]Reason 1:[/bold] [red]Phishing Address Detected (Confidence: 99.9%)[/red]\n"
        "[bold]Reason 2:[/bold] [red]Policy Violation: Max Transfer Limit (1000 USDT)[/red]\n\n"
        "[yellow]Action:[/yellow] Wallet Locked. Admin Notification Sent.\n"
        "[yellow]WDK Status:[/yellow] [dim]Signature Rejected.[/dim]",
        title="[bold red]🛡 THREAT NEUTRALIZED[/bold red]",
        border_style="red",
        style="white",
        expand=False
    )
    console.print(error_panel)

def main():
    try:
        while True:
            console.clear()
            console.print(Panel.fit(
                "[1] Play 'Success' Demo (Green)\n"
                "[2] Play 'Attack' Demo (Red/Dramatic)\n"
                "[3] Play Both Sequence\n"
                "[q] Quit",
                title="[bold cyan]Tether Guardian Visualizer[/bold cyan]",
                border_style="cyan"
            ))

            choice = Prompt.ask("Select Mode", choices=["1", "2", "3", "q"], default="3")

            if choice == "1":
                demo_success_flow()
                Prompt.ask("\n[dim]Press Enter to return...[/dim]")
            elif choice == "2":
                demo_attack_flow()
                Prompt.ask("\n[dim]Press Enter to return...[/dim]")
            elif choice == "3":
                demo_success_flow()
                time.sleep(2)
                demo_attack_flow()
                Prompt.ask("\n[dim]Press Enter to finish...[/dim]")
            elif choice == "q":
                console.print("[cyan]Exiting...[/cyan]")
                break

    except KeyboardInterrupt:
        console.print("\n[cyan]Exiting...[/cyan]")

if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("Rich library not installed. Please run: pip install rich")
