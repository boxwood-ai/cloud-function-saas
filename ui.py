"""
Terminal UI components for the Cloud Function Generator
"""

from contextlib import contextmanager
from typing import List, Dict, Any

# Terminal UI imports
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.columns import Columns
    from rich.tree import Tree
    from rich.live import Live
    from rich.status import Status
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

# Global console for fancy output
console = Console() if RICH_AVAILABLE else None


class TaskStatus:
    """Simple task status tracker for terminal UI"""
    PENDING = "⏳"
    IN_PROGRESS = "🔄"
    COMPLETED = "✅"
    FAILED = "❌"
    WARNING = "⚠️"


class FancyUI:
    """Fancy terminal UI manager"""
    def __init__(self, use_rich=True):
        self.use_rich = use_rich and RICH_AVAILABLE
        self.console = console if self.use_rich else None
        self.tasks = []
        self.current_task_id = None
        
    def add_task(self, task_id: str, description: str, status: str = TaskStatus.PENDING):
        """Add a task to the list"""
        self.tasks.append({
            'id': task_id,
            'description': description,
            'status': status,
            'details': []
        })
    
    def update_task(self, task_id: str, status: str = None, details: str = None):
        """Update task status or add details"""
        for task in self.tasks:
            if task['id'] == task_id:
                if status:
                    task['status'] = status
                if details:
                    task['details'].append(details)
                break
    
    def print_status(self, force_simple=False):
        """Print current status"""
        if self.use_rich and not force_simple:
            self._print_rich_status()
        else:
            self._print_simple_status()
    
    def _print_rich_status(self):
        """Print status using Rich library"""
        if not self.console:
            return
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Status", width=3)
        table.add_column("Task")
        
        for task in self.tasks:
            status_icon = task['status']
            description = task['description']
            
            if task['status'] == TaskStatus.IN_PROGRESS:
                description = f"[bold cyan]{description}[/bold cyan]"
            elif task['status'] == TaskStatus.COMPLETED:
                description = f"[green]{description}[/green]"
            elif task['status'] == TaskStatus.FAILED:
                description = f"[red]{description}[/red]"
            elif task['status'] == TaskStatus.WARNING:
                description = f"[yellow]{description}[/yellow]"
            
            table.add_row(status_icon, description)
            
            # Add details if any
            for detail in task.get('details', []):
                table.add_row("", f"  [dim]{detail}[/dim]")
        
        self.console.print(table)
    
    def _print_simple_status(self):
        """Print status using simple text"""
        for task in self.tasks:
            status_icon = task['status']
            description = task['description']
            print(f"{status_icon} {description}")
            
            # Add details if any
            for detail in task.get('details', []):
                print(f"    {detail}")
    
    @contextmanager
    def spinner(self, text: str):
        """Context manager for spinner during operations"""
        if self.use_rich and self.console:
            with self.console.status(f"[bold cyan]{text}[/bold cyan]", spinner="dots") as status:
                yield status
        else:
            print(f"🔄 {text}...")
            yield None
    
    def success(self, message: str):
        """Print success message"""
        if self.use_rich:
            self.console.print(f"[bold green]✅ {message}[/bold green]")
        else:
            print(f"✅ {message}")
    
    def error(self, message: str):
        """Print error message"""
        if self.use_rich:
            self.console.print(f"[bold red]❌ {message}[/bold red]")
        else:
            print(f"❌ {message}")
    
    def warning(self, message: str):
        """Print warning message"""
        if self.use_rich:
            self.console.print(f"[bold yellow]⚠️ {message}[/bold yellow]")
        else:
            print(f"⚠️ {message}")
    
    def info(self, message: str):
        """Print info message"""
        if self.use_rich:
            self.console.print(f"[bold blue]ℹ️ {message}[/bold blue]")
        else:
            print(f"ℹ️ {message}")
    
    def panel(self, content: str, title: str = None):
        """Print content in a panel"""
        if self.use_rich:
            self.console.print(Panel(content, title=title, border_style="blue"))
        else:
            border = "=" * 60
            print(border)
            if title:
                print(f" {title}")
                print(border)
            print(content)
            print(border)
    
    def details_section(self, title: str, items: List[str], collapsible: bool = True):
        """Print a details section"""
        if self.use_rich:
            tree = Tree(f"[bold]{title}[/bold]")
            for item in items:
                tree.add(item)
            self.console.print(tree)
        else:
            print(f"\n{title}:")
            for item in items:
                print(f"   • {item}")