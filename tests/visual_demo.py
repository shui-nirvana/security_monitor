import time
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
from rich.spinner import Spinner

def demo_guardian_ui():
    """
    [Visual Test]
    Simulates the Guardian Agent UI flow to verify Rich library integration.
    """
    console = Console()
    
    # 1. Start Sequence
    console.print("\n")
    console.rule("[bold green]STARTING GUARDIAN SEQUENCE[/bold green]")
    time.sleep(1)
    
    target = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    amount = "50.0 USDT"
    
    console.print(f"[bold cyan]>>> [COMMAND] INITIATE TRANSFER: {amount} -> {target}[/bold cyan]")
    time.sleep(0.5)

    # 2. Brain Analysis (Spinner)
    with console.status("[bold yellow][BRAIN] Analyzing target address via Gemini/DeepSeek...", spinner="dots"):
        time.sleep(2) # Simulate AI thinking
        
    console.print(f"[bold green]✅ [STATUS] RISK LOW. AUTHORIZING WDK EXECUTION.[/bold green]")
    time.sleep(0.5)

    # 3. WDK Execution (Spinner)
    with console.status("[bold blue][WDK] Preparing secure signature & Broadcasting...", spinner="earth"):
        time.sleep(2) # Simulate signing and broadcasting
        
    console.print(f"[bold green]🚀 [WDK] TRANSACTION SUCCESS: 0xbbbb...[/bold green]")
    time.sleep(0.5)

    # 4. Final Report (Panel)
    console.rule("[bold green]MISSION REPORT[/bold green]")
    console.print(Panel(
        f"[bold]Transaction Hash:[/bold] 0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
        f"[bold]From:[/bold]   0xGuardianWallet\n"
        f"[bold]To:[/bold]     {target}\n"
        f"[bold]Amount:[/bold] {amount}\n"
        f"[bold]Nonce:[/bold]  42",
        title="[bold green]✅ TRANSACTION EXECUTED VIA WDK[/bold green]",
        border_style="green"
    ))

if __name__ == "__main__":
    try:
        demo_guardian_ui()
    except ImportError:
        print("Rich library not installed. Please run: pip install rich")