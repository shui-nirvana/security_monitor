import time

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class MatrixConsole:
    """
    [Hackathon Visualizer]
    Provides a "Matrix-style" real-time dashboard for the Guardian Agent.
    """
    def __init__(self):
        self.console = Console()
        self.logs = []
        self.status_message = "Initializing Guardian Protocol..."
        self.risk_level = "ANALYZING..."
        self.current_action = "IDLE"

    def generate_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="status", ratio=1),
            Layout(name="logs", ratio=2)
        )

        # Header
        header_text = Text("GUARDIAN AGENT [WDK EDITION]", style="bold green on black", justify="center")
        layout["header"].update(Panel(header_text, style="green"))

        # Status Panel
        status_table = Table.grid(padding=1)
        status_table.add_column(style="bold green")
        status_table.add_row("MODE: ACTIVE GUARDIAN")
        status_table.add_row(f"ACTION: {self.current_action}")
        status_table.add_row(f"RISK LEVEL: {self.risk_level}")
        status_table.add_row(f"STATUS: {self.status_message}")

        layout["status"].update(Panel(status_table, title="SYSTEM STATUS", border_style="green"))

        # Logs Panel
        log_text = Text()
        for log in self.logs[-10:]: # Show last 10 logs
            log_text.append(log + "\n")
        layout["logs"].update(Panel(log_text, title="EVENT LOG", border_style="green"))

        # Footer
        footer_text = Text("Tether WDK Integrated | AI Security Module Online", style="dim green", justify="center")
        layout["footer"].update(Panel(footer_text, style="green"))

        return layout

    def log(self, message: str, style: str = "green"):
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

    def update_status(self, message: str, action: str | None = None, risk: str | None = None):
        self.status_message = message
        if action:
            self.current_action = action
        if risk:
            self.risk_level = risk

    def show_thinking(self, duration: float = 2.0):
        """Simulate AI 'thinking' effect"""
        self.update_status("Consulting AI Neural Net...", action="THINKING")
        # In a real async loop we would update, but here we just sleep to simulate
        # The Live context manager in the main loop will handle the rendering if we were using it there.
        # But since we are calling this from inside a synchronous function, we might not see animation
        # unless we pass the 'live' object down.
        # For simplicity, we'll just log it.
        self.log(">>> [BRAIN] Analyzing transaction context...", style="bold cyan")
        time.sleep(duration * 0.5)
        self.log(">>> [BRAIN] Pattern matching against known threats...", style="cyan")
        time.sleep(duration * 0.5)

