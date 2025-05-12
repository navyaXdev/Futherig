import os
import sys
import subprocess
import platform
import time
import glob
import shlex
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.completion.base import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.completion.filesystem import PathCompleter
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
import colorama
from datetime import datetime
from typing import Dict, Set, List, Tuple, Optional
import json
from PIL import Image
import io
import base64
from rich.layout import Layout
from rich.columns import Columns

# Initialize colorama for Windows
if platform.system() == 'Windows':
    colorama.init()

# Create Rich console for better output formatting
console = Console()

# Custom style for the terminal with more vibrant colors
style = Style.from_dict({
    'prompt': '#00ff00 bold',  # Bright green
    'input': '#00ffff',        # Cyan
    'output': '#ffffff',       # White
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'completion-menu.meta.completion': 'bg:#004444 #ffffff',
    'completion-menu.meta.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#003333',
    'scrollbar.button': 'bg:#00aaaa',
    # Add more color classes
    'green': '#00ff00',
    'cyan': '#00ffff',
    'red': '#ff0000',
    'blue': '#0000ff',
    'yellow': '#ffff00',
    'magenta': '#ff00ff',
    'white': '#ffffff',
    'black': '#000000'
})

class ProfessionalCompleter(Completer):
    """Professional completer with smart command and file completion"""
    def __init__(self):
        # Command-specific completers
        self.command_completers = {
            'cd': self._complete_directories,
            'ls': self._complete_files_and_dirs,
            'dir': self._complete_files_and_dirs,
            'type': self._complete_files,
            'cat': self._complete_files,
            'del': self._complete_files,
            'rm': self._complete_files,
            'copy': self._complete_files,
            'cp': self._complete_files,
            'move': self._complete_files,
            'mv': self._complete_files
        }

    def get_completions(self, document: Document, complete_event: CompleteEvent):
        """Get completions based on the current context"""
        word = document.get_word_before_cursor()
        line = document.text.strip()
        
        # Simple command parsing without shlex
        parts = line.split()
        
        # If we're completing the first word, suggest commands
        if len(parts) <= 1:
            # Get available commands that match the current word
            for cmd_name in self._get_available_commands(word):
                yield Completion(
                    cmd_name,
                    start_position=-len(word),  # Replace the partial word
                    display=cmd_name
                )
            return

        # Get the command being used
        command = parts[0].lower()
        
        # Special handling for cd command
        if command == 'cd':
            # Get the current text after 'cd '
            current_text = line[3:].strip() if line.startswith('cd ') else ''
            
            # If we're at the start of the path (just after 'cd '), show all directories
            if not current_text:
                yield from self._complete_directories('')
            else:
                # Use the current text as the path for completion
                yield from self._complete_directories(current_text)
            return
        
        # If we have a specific completer for this command, use it
        if command in self.command_completers:
            yield from self.command_completers[command](word)
            return

        # Default to file and directory completion
        yield from self._complete_files_and_dirs(word)

    def _get_available_commands(self, word: str):
        """Get available commands that match the current word from all OS paths"""
        commands = set()
        
        # Add special terminal commands that are always available
        special_commands = ['cd', 'customize', 'help', 'exit', 'quit']
        for cmd in special_commands:
            if cmd.startswith(word.lower()):
                commands.add(cmd)
        
        # Get PATH environment variable based on OS
        if platform.system() == 'Windows':
            path = os.environ.get('PATH', '').split(';')
            # Windows executable extensions
            extensions = ['.exe', '.bat', '.cmd', '.ps1', '.com', '.vbs']
        else:
            path = os.environ.get('PATH', '').split(':')
            extensions = ['']  # Unix-like systems don't require extensions
        
        # Scan each directory in PATH
        for directory in path:
            if not directory or not os.path.exists(directory):
                continue
                
            try:
                # List all files in the directory
                for file in os.listdir(directory):
                    file_lower = file.lower()
                    
                    # Skip if doesn't match the word prefix
                    if not file_lower.startswith(word.lower()):
                        continue
                        
                    file_path = os.path.join(directory, file)
                    if not os.path.isfile(file_path):
                        continue
                        
                    # Handle platform-specific executable detection
                    is_executable = False
                    
                    if platform.system() == 'Windows':
                        # Windows: check for executable extensions
                        is_executable = any(file_lower.endswith(ext) for ext in extensions)
                        if is_executable:
                            # Remove extension for Windows commands
                            base_name = os.path.splitext(file_lower)[0]
                            commands.add(base_name)
                    else:
                        # Unix-like: check if file has execute permission
                        is_executable = os.access(file_path, os.X_OK)
                        if is_executable:
                            commands.add(file_lower)
            except (PermissionError, OSError, FileNotFoundError) as e:
                # Skip directories we can't access
                continue
            except Exception:
                # Skip any other errors and continue with next directory
                continue
        
        # Add OS-specific built-in commands that might not be in PATH
        if platform.system() == 'Windows':
            # Windows built-ins that might not be in PATH
            win_builtins = ['cls', 'dir', 'echo', 'type', 'copy', 'move', 'del', 'ren', 'md', 'rd']
            for cmd in win_builtins:
                if cmd.startswith(word.lower()):
                    commands.add(cmd)
        else:
            # Unix built-ins that might not be in PATH
            unix_builtins = ['ls', 'echo', 'pwd', 'cat', 'cp', 'mv', 'rm', 'mkdir', 'rmdir', 'clear']
            for cmd in unix_builtins:
                if cmd.startswith(word.lower()):
                    commands.add(cmd)
        
        return sorted(commands)

    def _complete_directories(self, word: str):
        """Complete only directories with descriptions"""
        try:
            path = word or '.'
            if platform.system() == 'Windows':
                path = path.replace('/', '\\')
            
            dirname = os.path.dirname(path)
            if not dirname:
                dirname = '.'
            pattern = os.path.basename(path) + '*'
            
            # Get all matching directories
            dirs = []
            for p in glob.glob(os.path.join(dirname, pattern)):
                if os.path.isdir(p):
                    # Get directory size and item count
                    try:
                        total_size = 0
                        item_count = 0
                        for dirpath, dirnames, filenames in os.walk(p):
                            for f in filenames:
                                fp = os.path.join(dirpath, f)
                                if os.path.exists(fp):
                                    total_size += os.path.getsize(fp)
                            item_count += len(filenames) + len(dirnames)
                        
                        # Format size
                        if total_size < 1024:
                            size_str = f"{total_size} B"
                        elif total_size < 1024 * 1024:
                            size_str = f"{total_size/1024:.1f} KB"
                        else:
                            size_str = f"{total_size/(1024*1024):.1f} MB"
                            
                        # Get last modified time
                        mtime = os.path.getmtime(p)
                        last_modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                        
                        # Create display string
                        display = os.path.basename(p) + os.sep
                        meta = f"Items: {item_count} | Size: {size_str} | Modified: {last_modified}"
                        dirs.append((display, meta, p))
                    except Exception:
                        # If we can't get details, just show the directory name
                        display = os.path.basename(p) + os.sep
                        dirs.append((display, "Directory", p))
            
            # Sort directories by name
            dirs.sort(key=lambda x: x[0].lower())
            
            # If there's only one match, autofill it
            if len(dirs) == 1:
                display, meta, _ = dirs[0]
                yield Completion(
                    display,
                    start_position=-len(os.path.basename(word)),  # Replace the partial word
                    display=display,
                    display_meta=meta
                )
            else:
                # Find common prefix among all matches
                if dirs:
                    common_prefix = os.path.commonprefix([d[0] for d in dirs])
                    if common_prefix and common_prefix != os.path.basename(path):
                        yield Completion(
                            common_prefix,
                            start_position=-len(os.path.basename(word)),  # Replace the partial word
                            display=common_prefix,
                            display_meta="Common prefix"
                        )
                
                # Yield all completions
                for display, meta, _ in dirs:
                    yield Completion(
                        display,
                        start_position=-len(os.path.basename(word)),  # Replace the partial word
                        display=display,
                        display_meta=meta
                    )
                
        except Exception:
            pass

    def _complete_files(self, word: str):
        """Complete only files with descriptions"""
        try:
            path = word or '.'
            if platform.system() == 'Windows':
                path = path.replace('/', '\\')
            
            dirname = os.path.dirname(path)
            if not dirname:
                dirname = '.'
            pattern = os.path.basename(path) + '*'
            
            # Get all matching files
            files = []
            for p in glob.glob(os.path.join(dirname, pattern)):
                if os.path.isfile(p):
                    display = os.path.basename(p)
                    files.append((display, f"File ({os.path.getsize(p)} bytes)"))
            
            # Sort files by name
            files.sort(key=lambda x: x[0].lower())
            
            # If there's only one match, autofill it
            if len(files) == 1:
                display, meta = files[0]
                yield Completion(
                    display,
                    start_position=-len(os.path.basename(word)),  # Replace the partial word
                    display=display,
                    display_meta=meta
                )
            else:
                # Find common prefix among all matches
                if files:
                    common_prefix = os.path.commonprefix([f[0] for f in files])
                    if common_prefix and common_prefix != os.path.basename(path):
                        yield Completion(
                            common_prefix,
                            start_position=-len(os.path.basename(word)),  # Replace the partial word
                            display=common_prefix,
                            display_meta="Common prefix"
                        )
                
                # Yield all completions
                for display, meta in files:
                    yield Completion(
                        display,
                        start_position=-len(os.path.basename(word)),  # Replace the partial word
                        display=display,
                        display_meta=meta
                    )
        except Exception:
            pass

    def _complete_files_and_dirs(self, word: str):
        """Complete both files and directories with descriptions"""
        try:
            path = word or '.'
            if platform.system() == 'Windows':
                path = path.replace('/', '\\')
            
            dirname = os.path.dirname(path)
            if not dirname:
                dirname = '.'
            pattern = os.path.basename(path) + '*'
            
            # Get all matching files and directories
            items = []
            for p in glob.glob(os.path.join(dirname, pattern)):
                if os.path.isdir(p):
                    display = os.path.basename(p) + os.sep
                    items.append((display, "Directory"))
                else:
                    display = os.path.basename(p)
                    items.append((display, f"File ({os.path.getsize(p)} bytes)"))
            
            # Sort items by name
            items.sort(key=lambda x: x[0].lower())
            
            # If there's only one match, autofill it
            if len(items) == 1:
                display, meta = items[0]
                yield Completion(
                    display,
                    start_position=-len(os.path.basename(word)),  # Replace the partial word
                    display=display,
                    display_meta=meta
                )
            else:
                # Find common prefix among all matches
                if items:
                    common_prefix = os.path.commonprefix([i[0] for i in items])
                    if common_prefix and common_prefix != os.path.basename(path):
                        yield Completion(
                            common_prefix,
                            start_position=-len(os.path.basename(word)),  # Replace the partial word
                            display=common_prefix,
                            display_meta="Common prefix"
                        )
                
                # Yield all completions
                for display, meta in items:
                    yield Completion(
                        display,
                        start_position=-len(os.path.basename(word)),  # Replace the partial word
                        display=display,
                        display_meta=meta
                    )
        except Exception:
            pass

    def _get_command_help(self, command: str) -> str:
        """Get detailed help for a command"""
        help_text = ""
        
        # Terminal command help
        if command == 'customize':
            return "Terminal command: Customize the terminal appearance and behavior"
        elif command in ['exit', 'quit']:
            return "Terminal command: Exit the terminal"
        elif command == 'help':
            return "Terminal command: Get help for a specific command"
            
        # Try to get help from system command
        try:
            # Try to execute help command
            if platform.system() == 'Windows':
                help_cmd = f"{command} /?"
            else:
                help_cmd = f"{command} --help"
                
            proc = subprocess.Popen(
                help_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate(timeout=2)  # Timeout after 2 seconds
            
            if stdout:
                # Limit output to avoid overwhelming display
                lines = stdout.split('\n')
                if len(lines) > 20:
                    output = '\n'.join(lines[:20]) + "\n...\n(Output truncated)"
                else:
                    output = stdout
                    
                help_text = f"System Command: {command}\n\n"
                help_text += output
                return help_text
            
            # If no stdout, try man page summary (Unix-like systems)
            if platform.system() != 'Windows':
                proc = subprocess.Popen(
                    f"man -f {command} 2>/dev/null || whatis {command} 2>/dev/null",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = proc.communicate(timeout=2)
                
                if stdout:
                    help_text = f"System Command: {command}\n\n"
                    help_text += stdout
                    help_text += f"\n\nUse 'man {command}' for more information."
                    return help_text
        except Exception:
            pass
        
        # If we got here, we couldn't find help information
        help_text = f"No detailed help available for '{command}'.\n"
        help_text += f"Try running '{command} --help' or '{command} -h' directly."
        
        return help_text

def get_system_shell():
    """Get the system's default shell in a cross-platform way"""
    if platform.system() == 'Windows':
        # Check for PowerShell first, then CMD
        powershell_path = os.path.expandvars('%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe')
        if os.path.exists(powershell_path):
            return 'powershell.exe'
        return 'cmd.exe'
    else:
        # Unix-like systems - get from environment or use /bin/bash as fallback
        return os.environ.get('SHELL', '/bin/bash')

def show_loading_animation():
    """Show a professional loading animation when terminal starts"""
    try:
        # Use rich for animation if available
        try:
            from rich.console import Console
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
            from time import sleep
            
            console = Console()
            
            # Create a nice introduction message
            intro_text = """
 ██████╗ ██████╗ ███╗   ██╗███████╗ ██████╗ ██╗     ███████╗
██╔════╝██╔═══██╗████╗  ██║██╔════╝██╔═══██╗██║     ██╔════╝
██║     ██║   ██║██╔██╗ ██║███████╗██║   ██║██║     █████╗  
██║     ██║   ██║██║╚██╗██║╚════██║██║   ██║██║     ██╔══╝  
╚██████╗╚██████╔╝██║ ╚████║███████║╚██████╔╝███████╗███████╗
 ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚══════╝╚══════╝
            """
            console.print(intro_text, style="bold cyan")
            console.print("Initializing Professional Terminal...\n", style="yellow")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[bold green]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                load_system = progress.add_task("[cyan]Loading system information...", total=100)
                load_modules = progress.add_task("[magenta]Initializing modules...", total=100)
                load_ui = progress.add_task("[yellow]Preparing terminal interface...", total=100)
                
                # Simulate loading
                for i in range(101):
                    if i < 30:
                        progress.update(load_system, completed=i * 3.33)
                    elif i < 60:
                        progress.update(load_modules, completed=(i - 30) * 3.33)
                    else:
                        progress.update(load_ui, completed=(i - 60) * 2.5)
                    
                    # Progress task completion logic
                    if i == 30:
                        progress.update(load_system, completed=100)
                    if i == 60:
                        progress.update(load_modules, completed=100)
                    if i == 100:
                        progress.update(load_ui, completed=100)
                    
                    sleep(0.01)  # Adjust speed here
                
            console.print("\n[bold green]System Ready![/bold green]\n")
        
        # Fallback to simple animation if rich module fails
        except (ImportError, Exception):
            animation_frames = "|/-\\"
            loading_text = "Starting Terminal"
            
            # Use ANSI color codes for compatibility
            CYAN = '\033[96m'
            RESET = '\033[0m'
            
            for i in range(40):  # Show animation for ~4 seconds
                frame = animation_frames[i % len(animation_frames)]
                # Clear the line and show the new frame
                sys.stdout.write(f"\r{CYAN}{frame}{RESET} {loading_text}" + "." * (i % 4))
                sys.stdout.flush()
                time.sleep(0.1)
            print("\nTerminal Ready!")
    
    except Exception:
        # Absolute fallback - just print a message
        print("Starting terminal...")

def get_prompt():
    """Create a customized prompt"""
    # Load prompt configuration
    prompt_config = load_prompt_config()
    
    # Get current time
    current_time = datetime.now().strftime(prompt_config['time_format'])
    
    try:
        username = os.getlogin()
    except:
        try:
            import getpass
            username = getpass.getuser()
        except:
            username = "user"
            
    try:
        current_dir = os.path.basename(os.getcwd())
    except:
        current_dir = "~"
    
    # Parse the prompt format and replace placeholders
    format_str = prompt_config['format']
    format_str = format_str.replace('%time%', current_time)
    format_str = format_str.replace('%username%', username)
    format_str = format_str.replace('%directory%', current_dir)
    format_str = format_str.replace('%date%', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        hostname = platform.node()
    except:
        hostname = "localhost"
    format_str = format_str.replace('%hostname%', hostname)
    
    # Parse the style tags and create formatted text
    parts = []
    current_text = ''
    current_color = ''  # Start with empty string instead of None
    i = 0
    
    while i < len(format_str):
        # Check for style tags
        if format_str[i:i+8] == '<purple>':
            if current_text:
                parts.append((current_color, current_text))
            current_color = 'class:magenta'
            current_text = ''
            i += 8
        elif format_str[i:i+7] == '<green>':
            if current_text:
                parts.append((current_color, current_text))
            current_color = 'class:green'
            current_text = ''
            i += 7
        elif format_str[i:i+6] == '<cyan>':
            if current_text:
                parts.append((current_color, current_text))
            current_color = 'class:cyan'
            current_text = ''
            i += 6
        elif format_str[i:i+5] == '<red>':
            if current_text:
                parts.append((current_color, current_text))
            current_color = 'class:red'
            current_text = ''
            i += 5
        elif format_str[i:i+6] == '<blue>':
            if current_text:
                parts.append((current_color, current_text))
            current_color = 'class:blue'
            current_text = ''
            i += 6
        elif format_str[i:i+8] == '<yellow>':
            if current_text:
                parts.append((current_color, current_text))
            current_color = 'class:yellow'
            current_text = ''
            i += 8
        elif format_str[i:i+7] == '<white>':
            if current_text:
                parts.append((current_color, current_text))
            current_color = 'class:white'
            current_text = ''
            i += 7
        elif format_str[i:i+7] == '<black>':
            if current_text:
                parts.append((current_color, current_text))
            current_color = 'class:black'
            current_text = ''
            i += 7
        elif format_str[i:i+3] == '<c>':
            if current_text:
                parts.append((current_color, current_text))
            current_color = ''  # Empty string instead of None
            current_text = ''
            i += 3
        elif format_str[i:i+3] == '<n>':
            if current_text:
                parts.append((current_color, current_text))
            parts.append(('', '\n'))  # Use empty string instead of None
            current_color = ''  # Empty string instead of None
            current_text = ''
            i += 3
        else:
            current_text += format_str[i]
            i += 1
    
    # Add any remaining text
    if current_text:
        parts.append((current_color, current_text))
    
    return FormattedText(parts)

def show_command_execution_animation(command):
    """Show an animation while a command is executing"""
    try:
        from rich.live import Live
        from rich.panel import Panel
        from rich.text import Text
        from rich.console import Console
        from rich.spinner import Spinner
        import time
        
        spinner = Spinner("dots2")
        status_text = Text(f"Executing: {command}", style="cyan")
        
        panel = Panel(
            Text.assemble(spinner, " ", status_text),
            title="Command Execution",
            border_style="blue"
        )
        
        console = Console()
        with Live(panel, refresh_per_second=20, console=console) as live:
            # This will be updated by the actual command execution
            pass
            
    except Exception:
        # If animation fails, do nothing - the command will still execute
        pass

def execute_command(command):
    """Execute the command and show live output"""
    try:
        # Split the command into parts
        parts = command.split()
        
        # Handle cd command separately
        if parts[0] == 'cd':
            if len(parts) > 1:
                try:
                    os.chdir(parts[1])
                except FileNotFoundError:
                    return f"Error: Directory '{parts[1]}' not found"
            return ""
        
        # Start execution animation in a separate thread
        try:
            import threading
            from rich.live import Live
            from rich.panel import Panel
            from rich.text import Text
            from rich.spinner import Spinner
            
            stop_animation = False
            
            def animation_thread():
                spinner = Spinner("dots2")
                with console.status(f"[cyan]Executing: {command}[/cyan]", spinner="dots2") as status:
                    while not stop_animation:
                        time.sleep(0.1)
            
            # Only use animation for longer running commands
            if not command.startswith(('ls', 'dir', 'echo', 'pwd', 'cd')):
                animation = threading.Thread(target=animation_thread)
                animation.daemon = True
                animation.start()
        except Exception:
            # If animation fails, continue without it
            animation = None
            stop_animation = True
        
        # Execute other commands using the system shell
        shell = get_system_shell()
        try:
            # Use the system shell to execute the command
            if platform.system() == 'Windows':
                if shell == 'powershell.exe':
                    process = subprocess.Popen(['powershell.exe', '-Command', command], 
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            text=True,
                                            bufsize=1,
                                            universal_newlines=True)
                else:
                    process = subprocess.Popen(['cmd.exe', '/c', command], 
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            text=True,
                                            bufsize=1,
                                            universal_newlines=True)
            else:
                process = subprocess.Popen(command, 
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        bufsize=1,
                                        universal_newlines=True)
            
            # Read output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            # Get any remaining error output
            error = process.stderr.read()
            
            # Stop the animation
            try:
                if 'animation' in locals() and animation is not None:
                    stop_animation = True
                    animation.join(0.5)  # Wait for animation to stop
            except:
                pass
                
            if error:
                return f"Error: {error}"
            
            # Check return code
            if process.returncode != 0:
                return f"Command failed with return code {process.returncode}"
            return ""
            
        except FileNotFoundError:
            # Stop animation if it's running
            try:
                if 'animation' in locals() and animation is not None:
                    stop_animation = True
                    animation.join(0.5)
            except:
                pass
            
            return f"Error: Command '{parts[0]}' not found"
        except Exception as e:
            # Stop animation if it's running
            try:
                if 'animation' in locals() and animation is not None:
                    stop_animation = True
                    animation.join(0.5)
            except:
                pass
                
            return f"Error: {str(e)}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def convert_image_to_ascii(image, width=40):
    """Convert image to ASCII art with transparent background handling"""
    try:
        # Convert to RGBA if not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Calculate new height maintaining aspect ratio
        aspect_ratio = image.height / image.width
        height = int(width * aspect_ratio * 0.5)  # 0.5 to account for character aspect ratio
        
        # Resize image 
        try:
            # For newer Pillow versions
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        except AttributeError:
            # For older Pillow versions
            image = image.resize((width, height), Image.LANCZOS)
        
        # ASCII characters from dark to light
        ascii_chars = ' .:-=+*#%@'
        
        # Convert to ASCII
        ascii_art = []
        for y in range(height):
            line = ''
            for x in range(width):
                try:
                    pixel = image.getpixel((x, y))
                    # Check if pixel is transparent (handle both RGB and RGBA)
                    if len(pixel) > 3 and pixel[3] < 128:  # Alpha channel < 128 means transparent
                        line += ' '
                    else:
                        # Convert RGB to grayscale
                        if len(pixel) >= 3:
                            gray = 0.299 * pixel[0] + 0.587 * pixel[1] + 0.114 * pixel[2]
                        else:
                            gray = pixel[0]  # Already grayscale
                        # Map to ASCII character
                        char_index = int(gray / 255 * (len(ascii_chars) - 1))
                        line += ascii_chars[char_index]
                except Exception:
                    line += ' '  # Use space for any errors
            ascii_art.append(line)
        
        return '\n'.join(ascii_art)
    except Exception as e:
        print(f"Error converting image: {e}")
        return None

def show_banner():
    """Display a professional banner"""
    # Load banner configuration
    banner_config = load_banner_config()
    
    # Get banner text
    banner_text = banner_config['banner_text']
    
    # Get system information
    system_info = {}
    if banner_config['show_info']:
        info_items = banner_config['info_items']
        if info_items.get('OS', True):
            system_info['OS'] = f"{platform.system()} {platform.release()}"
        if info_items.get('Shell', True):
            system_info['Shell'] = get_system_shell()
        if info_items.get('Python', True):
            system_info['Python'] = platform.python_version()
        if info_items.get('Time', True):
            system_info['Time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if info_items.get('Directory', True):
            try:
                system_info['Directory'] = os.getcwd()
            except:
                system_info['Directory'] = "Unable to determine current directory"
        if info_items.get('Username', True):
            try:
                system_info['Username'] = os.getlogin()
            except:
                try:
                    import getpass
                    system_info['Username'] = getpass.getuser()
                except:
                    system_info['Username'] = "Unknown"
        if info_items.get('Hostname', True):
            try:
                system_info['Hostname'] = platform.node()
            except:
                system_info['Hostname'] = "Unknown"
        if info_items.get('Memory', True):
            try:
                import psutil
                memory = psutil.virtual_memory()
                system_info['Memory'] = f"{memory.percent}% used ({memory.available / (1024*1024*1024):.1f} GB available)"
            except:
                system_info['Memory'] = "N/A"
        if info_items.get('CPU', True):
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                system_info['CPU'] = f"{cpu_percent}% used"
            except:
                system_info['CPU'] = "N/A"
    
    # Add custom information
    system_info.update(banner_config['custom_info'])
    
    # Create info text
    info_text = "\n".join([f"{key}: {value}" for key, value in system_info.items()])
    
    # Combine banner text and image
    banner_content = []
    
    if banner_config.get('banner_image'):
        try:
            # Decode base64 image data
            image_data = base64.b64decode(banner_config['banner_image'])
            
            # Create a BytesIO object for the image data
            image_io = io.BytesIO(image_data)
            
            # Try to open the image
            try:
                image = Image.open(image_io)
                
                # Convert to ASCII art
                ascii_art = convert_image_to_ascii(image, banner_config.get('image_width', 40))
                
                if ascii_art:
                    # Split ASCII art and banner text into lines
                    ascii_lines = ascii_art.split('\n')
                    text_lines = banner_text.strip().split('\n')
                    
                    # Calculate padding for alignment
                    max_ascii_width = max(len(line) for line in ascii_lines)
                    max_text_width = max(len(line) for line in text_lines)
                    
                    # Combine ASCII art and text side by side
                    combined_lines = []
                    for i in range(max(len(ascii_lines), len(text_lines))):
                        ascii_line = ascii_lines[i] if i < len(ascii_lines) else ''
                        text_line = text_lines[i] if i < len(text_lines) else ''
                        
                        # Add padding to align text
                        ascii_line = ascii_line.ljust(max_ascii_width)
                        text_line = text_line.ljust(max_text_width)
                        
                        # Combine lines with some spacing
                        combined_line = f"{ascii_line}    {text_line}"
                        combined_lines.append(combined_line)
                    
                    banner_content.append('\n'.join(combined_lines))
                else:
                    banner_content.append(banner_text)
            except Exception as img_err:
                print(f"Error processing image: {img_err}")
                banner_content.append(banner_text)
        except Exception as e:
            print(f"Error decoding image data: {e}")
            banner_content.append(banner_text)
    else:
        banner_content.append(banner_text)
    
    # Create the banner panel
    try:
        banner_panel = Panel(
            Text("\n".join(banner_content) + "\n" + info_text, style=banner_config['banner_style']),
            border_style=banner_config['border_style'],
            title=banner_config['title'],
            subtitle=banner_config['subtitle']
        )
        
        # Print the banner
        console.print(banner_panel)
    except Exception as panel_err:
        # Fallback to simple print if Rich panel fails
        print("\n" + "=" * 80)
        print(banner_config['title'].center(80))
        print("=" * 80)
        print("\n".join(banner_content))
        print("\n" + info_text)
        print("=" * 80)
        print(banner_config['subtitle'].center(80))
        print("=" * 80)
    
    # Add a blank line after banner
    try:
        console.print()
    except:
        print()

def customize_terminal():
    """Interactive function to customize the terminal appearance"""
    # Show customization animation
    show_customization_animation()
    
    print("\n=== Terminal Customization ===")
    print("1. Change prompt style")
    print("2. Change banner style")
    print("3. Change colors")
    print("4. Reset to default")
    print("0. Save and exit")
    
    while True:
        choice = input("\nEnter your choice (0-4): ")
        
        if choice == '1':
            customize_prompt_style()
            
        elif choice == '2':
            customize_banner()
            
        elif choice == '3':
            customize_colors()
            
        elif choice == '4':
            if input("\nAre you sure you want to reset all settings to default? (y/n): ").lower() == 'y':
                # Show animation for reset
                try:
                    with console.status("[bold yellow]Resetting configuration...[/bold yellow]"):
                        time.sleep(1)
                        reset_configuration()
                except:
                    reset_configuration()
                return  # Exit customization after reset
            
        elif choice == '0':
            # Show animation for saving
            try:
                with console.status("[bold green]Saving configuration...[/bold green]"):
                    time.sleep(0.5)
                    console.print("[bold green]Configuration saved successfully![/bold green]")
            except:
                print("Configuration saved!")
            break
        
        else:
            print("\nInvalid choice. Please try again.")

def get_prompt_library():
    """Return a library of beautiful tech-style prompt designs"""
    return {
        # Classic and modern designs
        "classic": {
            "format": "<green>[%username%@%hostname% %directory%]$<c>",
            "description": "Classic bash-style prompt",
            "preview": "[user@machine ~]$"
        },
        "powerline": {
            "format": "<blue>▓<cyan>▒<green>░<c> <green>%username%<c> <cyan>><c> <blue>%directory%<c> <red>><c> ",
            "description": "Powerline-inspired segmented prompt",
            "preview": "▓▒░ user > ~/documents > "
        },
        "minimal": {
            "format": "<cyan>❯<c> ",
            "description": "Ultra-minimal arrow prompt",
            "preview": "❯ "
        },
        "brackets": {
            "format": "<green>[<c><cyan>%username%<c><green>]<c> <yellow>%directory%<c> <red>><c> ",
            "description": "Bracketed username with directory",
            "preview": "[user] ~/documents > "
        },
        
        # Developer-themed prompts
        "git_branch": {
            "format": "<cyan>%directory%<c> <green>git:(%branch%)<c> <yellow>❯<c> ",
            "description": "Git branch indicator prompt",
            "preview": "~/project git:(main) ❯ "
        },
        "node_dev": {
            "format": "<green>⬢<c> <cyan>%directory%<c> <yellow>$<c> ",
            "description": "Node.js developer prompt",
            "preview": "⬢ ~/node-project $ "
        },
        "py_dev": {
            "format": "<blue>(py)<c> <cyan>%directory%<c> <yellow>><c> ",
            "description": "Python developer prompt",
            "preview": "(py) ~/python-project > "
        },
        "react_dev": {
            "format": "<blue>⚛<c> <cyan>%directory%<c> <green>><c> ",
            "description": "React developer prompt",
            "preview": "⚛ ~/react-app > "
        },
        
        # Tech-themed prompts
        "cyberpunk": {
            "format": "<cyan>┌─[<c><green>%username%<c><cyan>@<c><magenta>%hostname%<c><cyan>]<c><n><cyan>└──┤<c><yellow>%directory%<c><cyan>├─><c> ",
            "description": "Cyberpunk multi-line prompt",
            "preview": "┌─[user@machine]\n└──┤~/documents├─> "
        },
        "matrix": {
            "format": "<green>[%time%]<c> <green>%username%<c> <green>%directory%<c> <green>><c> ",
            "description": "Matrix-inspired monochrome green",
            "preview": "[12:34:56] user ~/documents > "
        },
        "neon": {
            "format": "<magenta>【<c><cyan>%username%<c><magenta>】<c><yellow>ﬦ<c><green>%directory%<c> <red>⟹<c> ",
            "description": "Neon-style prompt with Japanese brackets",
            "preview": "【user】ﬦ~/documents ⟹ "
        },
        "future": {
            "format": "<blue>╔[<cyan>%time%<blue>]╗<c><n><blue>╚═<cyan>%directory%<blue>═><c> ",
            "description": "Futuristic multi-line prompt with time",
            "preview": "╔[12:34:56]╗\n╚═~/documents═> "
        },
        
        # Symbol-rich prompts
        "arrows": {
            "format": "<green>➜<c> <cyan>%directory%<c> <yellow>⟹<c> ",
            "description": "Arrow-style prompt with directory",
            "preview": "➜ ~/documents ⟹ "
        },
        "stars": {
            "format": "<yellow>★<c> <cyan>%username%<c> <yellow>★<c> <green>%directory%<c> <yellow>★<c> ",
            "description": "Star-decorated prompt",
            "preview": "★ user ★ ~/documents ★ "
        },
        "circuit": {
            "format": "<green>┌─◯<c> <cyan>%username%<c> <green>◯<c> <blue>%directory%<c> <green>◯──┐<c><n><green>└─◯▶<c> ",
            "description": "Circuit-inspired multi-line prompt",
            "preview": "┌─◯ user ◯ ~/documents ◯──┐\n└─◯▶ "
        },
        "waves": {
            "format": "<blue>≈≈≈<c> <cyan>%username%<c> <blue>≈<c> <cyan>%directory%<c> <blue>≈≈≈<c> <yellow>><c> ",
            "description": "Wave-pattern prompt with directory",
            "preview": "≈≈≈ user ≈ ~/documents ≈≈≈ > "
        },
        
        # Professional prompts
        "corporate": {
            "format": "<blue>[%time%]<c> <green>%username%<c>:<cyan>%directory%<c>$ ",
            "description": "Professional prompt with time",
            "preview": "[12:34:56] user:~/documents$ "
        },
        "clean": {
            "format": "<cyan>%username%<c> <blue>at<c> <green>%hostname%<c> <blue>in<c> <yellow>%directory%<c> <red>><c> ",
            "description": "Clean, readable prompt with location info",
            "preview": "user at host in ~/documents > "
        },
        "statusline": {
            "format": "<green>┌─[<c><cyan>%time%<c><green>] [<c><blue>%username%<c><green>:<c><yellow>%directory%<c><green>]<c><n><green>└─$<c> ",
            "description": "Status-line style prompt with time",
            "preview": "┌─[12:34:56] [user:~/documents]\n└─$ "
        },
        "formal": {
            "format": "<cyan>%username%<c>@<green>%hostname%<c> <blue>:<c> <yellow>%directory%<c> <blue>|<c> <green>><c> ",
            "description": "Formal prompt with username and host",
            "preview": "user@host : ~/documents | > "
        },
        
        # Unicode and emoji prompts
        "emoji_dev": {
            "format": "<green>🚀<c> <cyan>%directory%<c> <yellow>$<c> ",
            "description": "Rocket emoji developer prompt",
            "preview": "🚀 ~/project $ "
        },
        "emoji_tech": {
            "format": "<cyan>💻<c> <green>%username%<c> <blue>📂<c> <yellow>%directory%<c> <red>⚡<c> ",
            "description": "Tech emoji-rich prompt",
            "preview": "💻 user 📂 ~/documents ⚡ "
        },
        "blocks": {
            "format": "<red>█<c><yellow>█<c><green>█<c><cyan>█<c><blue>█<c> <cyan>%directory%<c> <green>><c> ",
            "description": "Colorful blocks prompt",
            "preview": "█████ ~/documents > "
        },
        "lambda": {
            "format": "<cyan>λ<c> <green>%directory%<c> <yellow>><c> ",
            "description": "Lambda symbol prompt",
            "preview": "λ ~/documents > "
        },
        
        # Fun and themed prompts
        "pacman": {
            "format": "<yellow>ᗧ···<c> <cyan>%directory%<c> <yellow>ᗣ<c> ",
            "description": "Pacman-themed prompt",
            "preview": "ᗧ··· ~/documents ᗣ "
        },
        "tetris": {
            "format": "<cyan>┌─<c><red>▀<c><blue>▀<c><yellow>▀<c><green>▀<c><cyan>─┐<c><n><cyan>└──➤<c> ",
            "description": "Tetris-themed prompt",
            "preview": "┌─▀▀▀▀─┐\n└──➤ "
        },
        "space": {
            "format": "<blue>🌎<c> <cyan>%username%<c> <yellow>✨<c> <green>%directory%<c> <red>🚀<c> ",
            "description": "Space-themed prompt",
            "preview": "🌎 user ✨ ~/documents 🚀 "
        },
        "robot": {
            "format": "<green>ロ<c> <cyan>%username%<c> <blue>⚙<c> <yellow>%directory%<c> <red>><c> ",
            "description": "Robot-themed prompt",
            "preview": "ロ user ⚙ ~/documents > "
        },
        
        # Additional modern prompts
        "sharp": {
            "format": "<red>▶<c> <green>▶<c> <blue>▶<c> <cyan>%directory%<c> <yellow>⯈<c> ",
            "description": "Sharp angles modern prompt",
            "preview": "▶ ▶ ▶ ~/documents ⯈ "
        },
        "dots": {
            "format": "<cyan>•<c> <green>•<c> <yellow>•<c> <blue>%directory%<c> <red>»<c> ",
            "description": "Dotted minimalist prompt",
            "preview": "• • • ~/documents » "
        },
        "hash": {
            "format": "<green># %username%@%hostname%<c> <cyan>[%directory%]<c> <yellow>$<c> ",
            "description": "Hash-prefixed prompt",
            "preview": "# user@host [~/documents] $ "
        },
        "rounded": {
            "format": "<cyan>(</c><green>%username%</c><cyan>)</c> <yellow>⟬</c><blue>%directory%</c><yellow>⟭</c> <green>➔</c> ",
            "description": "Rounded brackets modern prompt",
            "preview": "(user) ⟬~/documents⟭ ➔ "
        }
    }

def preview_prompt(prompt_format, username="user", hostname="machine", directory="~/documents", time_str="12:34:56"):
    """Create a preview of a prompt using sample values"""
    preview = prompt_format
    preview = preview.replace("%username%", username)
    preview = preview.replace("%hostname%", hostname)
    preview = preview.replace("%directory%", directory)
    preview = preview.replace("%time%", time_str)
    preview = preview.replace("%branch%", "main")
    
    # Replace color tags with ANSI color codes
    color_map = {
        "<green>": "\033[32m",
        "<cyan>": "\033[36m",
        "<red>": "\033[31m",
        "<blue>": "\033[34m",
        "<yellow>": "\033[33m",
        "<magenta>": "\033[35m",
        "<white>": "\033[37m",
        "<black>": "\033[30m",
        "<c>": "\033[0m"
    }
    
    for tag, code in color_map.items():
        preview = preview.replace(tag, code)
    
    # Add reset code at the end
    preview += "\033[0m"
    
    # Replace newline
    preview = preview.replace("<n>", "\n")
    
    return preview

def select_prompt_from_library():
    """Allow user to browse and select a prompt from the library"""
    prompt_library = get_prompt_library()
    
    # Try to use rich for better display
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        
        console = Console()
        
        # Display a header
        console.print("\n[bold cyan]== Prompt Style Library ==[/bold cyan]")
        console.print("[yellow]Browse and select from over 30 professional prompt styles[/yellow]\n")
        
        # Create a table to display prompt categories
        table = Table(title="[bold green]Available Prompt Categories[/bold green]")
        table.add_column("Category", style="cyan")
        table.add_column("Description", style="yellow")
        
        categories = {
            "Classic & Modern": ["classic", "powerline", "minimal", "brackets"],
            "Developer": ["git_branch", "node_dev", "py_dev", "react_dev"],
            "Tech-themed": ["cyberpunk", "matrix", "neon", "future"],
            "Symbol-rich": ["arrows", "stars", "circuit", "waves"],
            "Professional": ["corporate", "clean", "statusline", "formal"],
            "Unicode & Emoji": ["emoji_dev", "emoji_tech", "blocks", "lambda"],
            "Fun & Themed": ["pacman", "tetris", "space", "robot"],
            "Additional Modern": ["sharp", "dots", "hash", "rounded"]
        }
        
        for category, prompts in categories.items():
            examples = ", ".join([p.capitalize() for p in prompts])
            table.add_row(category, f"Examples: {examples}")
        
        console.print(table)
        console.print()
        
        # Ask user if they want to see all prompts or browse by category
        console.print("[cyan]How would you like to browse prompts?[/cyan]")
        console.print("1. View all prompts")
        console.print("2. Browse by category")
        console.print("0. Return to main menu")
        
        choice = input("\nEnter your choice (0-2): ")
        
        if choice == '0':
            return None
            
        elif choice == '1':
            # Show all prompts in a table
            prompt_table = Table(title="[bold green]All Available Prompts[/bold green]")
            prompt_table.add_column("ID", style="cyan", width=12)
            prompt_table.add_column("Description", style="yellow", width=30)
            prompt_table.add_column("Preview", style="white")
            
            for i, (prompt_id, prompt_data) in enumerate(prompt_library.items(), 1):
                prompt_table.add_row(
                    f"{i}. {prompt_id}",
                    prompt_data["description"],
                    prompt_data["preview"]
                )
            
            console.print(prompt_table)
            
            # Let user select a prompt
            selection = input("\nEnter the number of the prompt to select (0 to cancel): ")
            if selection == '0':
                return None
                
            try:
                selection_idx = int(selection) - 1
                if 0 <= selection_idx < len(prompt_library):
                    selected_prompt = list(prompt_library.keys())[selection_idx]
                    
                    # Preview the selected prompt
                    console.print(f"\n[green]Selected:[/green] [cyan]{selected_prompt}[/cyan]")
                    console.print(f"[yellow]Description:[/yellow] {prompt_library[selected_prompt]['description']}")
                    console.print("[bold magenta]Preview:[/bold magenta]")
                    
                    # Show a visual preview
                    preview_text = prompt_library[selected_prompt]["preview"]
                    console.print(Panel(preview_text, title="Prompt Preview", border_style="cyan"))
                    
                    # Confirm selection
                    confirm = input("\nUse this prompt? (y/n): ").lower()
                    if confirm == 'y':
                        return prompt_library[selected_prompt]["format"]
                    else:
                        return select_prompt_from_library()  # Let user select again
                else:
                    console.print("[red]Invalid selection. Please try again.[/red]")
                    return select_prompt_from_library()
            except ValueError:
                console.print("[red]Invalid input. Please enter a number.[/red]")
                return select_prompt_from_library()
                
        elif choice == '2':
            # Let user browse by category
            console.print("\n[cyan]Select a category:[/cyan]")
            for i, category in enumerate(categories.keys(), 1):
                console.print(f"{i}. {category}")
            
            cat_choice = input("\nEnter category number (0 to cancel): ")
            if cat_choice == '0':
                return None
                
            try:
                cat_idx = int(cat_choice) - 1
                if 0 <= cat_idx < len(categories):
                    selected_category = list(categories.keys())[cat_idx]
                    prompt_ids = categories[selected_category]
                    
                    # Show prompts in this category
                    console.print(f"\n[bold green]Prompts in {selected_category} Category[/bold green]")
                    category_table = Table()
                    category_table.add_column("ID", style="cyan")
                    category_table.add_column("Name", style="green")
                    category_table.add_column("Description", style="yellow")
                    category_table.add_column("Preview", style="white")
                    
                    for i, prompt_id in enumerate(prompt_ids, 1):
                        prompt_data = prompt_library[prompt_id]
                        category_table.add_row(
                            str(i),
                            prompt_id,
                            prompt_data["description"],
                            prompt_data["preview"]
                        )
                    
                    console.print(category_table)
                    
                    # Let user select a prompt from this category
                    prompt_choice = input("\nEnter prompt number (0 to go back): ")
                    if prompt_choice == '0':
                        return select_prompt_from_library()
                        
                    try:
                        prompt_idx = int(prompt_choice) - 1
                        if 0 <= prompt_idx < len(prompt_ids):
                            selected_prompt = prompt_ids[prompt_idx]
                            
                            # Preview the selected prompt
                            console.print(f"\n[green]Selected:[/green] [cyan]{selected_prompt}[/cyan]")
                            console.print(f"[yellow]Description:[/yellow] {prompt_library[selected_prompt]['description']}")
                            console.print("[bold magenta]Preview:[/bold magenta]")
                            
                            # Show a visual preview
                            preview_text = prompt_library[selected_prompt]["preview"]
                            console.print(Panel(preview_text, title="Prompt Preview", border_style="cyan"))
                            
                            # Confirm selection
                            confirm = input("\nUse this prompt? (y/n): ").lower()
                            if confirm == 'y':
                                return prompt_library[selected_prompt]["format"]
                            else:
                                return select_prompt_from_library()  # Let user select again
                        else:
                            console.print("[red]Invalid selection. Please try again.[/red]")
                            return select_prompt_from_library()
                    except ValueError:
                        console.print("[red]Invalid input. Please enter a number.[/red]")
                        return select_prompt_from_library()
                else:
                    console.print("[red]Invalid category. Please try again.[/red]")
                    return select_prompt_from_library()
            except ValueError:
                console.print("[red]Invalid input. Please enter a number.[/red]")
                return select_prompt_from_library()
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")
            return select_prompt_from_library()
            
    except (ImportError, Exception):
        # Fallback to simple text-based menu
        print("\n=== Prompt Style Library ===")
        print("Browse and select from over 30 professional prompt styles\n")
        
        # Display all prompts in a simple list
        for i, (prompt_id, prompt_data) in enumerate(prompt_library.items(), 1):
            print(f"{i}. {prompt_id} - {prompt_data['description']}")
            
        # Let user select a prompt
        try:
            selection = input("\nEnter the number of the prompt to select (0 to cancel): ")
            if selection == '0':
                return None
                
            selection_idx = int(selection) - 1
            if 0 <= selection_idx < len(prompt_library):
                selected_prompt = list(prompt_library.keys())[selection_idx]
                
                # Preview the selected prompt
                print(f"\nSelected: {selected_prompt}")
                print(f"Description: {prompt_library[selected_prompt]['description']}")
                print("Preview:")
                
                # Show a visual preview using ANSI codes
                preview = preview_prompt(prompt_library[selected_prompt]["format"])
                print(preview)
                
                # Confirm selection
                confirm = input("\nUse this prompt? (y/n): ").lower()
                if confirm == 'y':
                    return prompt_library[selected_prompt]["format"]
                else:
                    return select_prompt_from_library()  # Let user select again
            else:
                print("Invalid selection. Please try again.")
                return select_prompt_from_library()
        except (ValueError, Exception):
            print("Invalid input. Please enter a number.")
            return select_prompt_from_library()

def customize_prompt_style():
    """Interactive function to customize the command prompt style"""
    print("\n=== Command Prompt Style Customization ===")
    print("1. Choose from prompt library")
    print("2. Create custom prompt")
    print("0. Back to main menu")
    
    choice = input("\nEnter your choice (0-2): ")
    
    if choice == '1':
        # Let user select from prompt library
        selected_format = select_prompt_from_library()
        if selected_format:
            config_file = os.path.join(os.path.expanduser('~'), '.terminal_prompt_config.json')
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['format'] = selected_format
            
            try:
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                print("\nPrompt style saved successfully!")
            except Exception as e:
                print(f"\nError saving configuration: {e}")
        
    elif choice == '2':
        # Manual customization
        print("\n=== Custom Prompt Creation ===")
        print("\nAvailable style tags:")
        print("<purple> - Start purple color")
        print("<green>  - Start green color")
        print("<cyan>   - Start cyan color")
        print("<red>    - Start red color")
        print("<blue>   - Start blue color")
        print("<yellow> - Start yellow color")
        print("<white>  - Start white color")
        print("<black>  - Start black color")
        print("<c>      - End current color")
        print("<n>      - New line")
        
        print("\nAvailable placeholders:")
        print("%time%     - Current time")
        print("%date%     - Current date")
        print("%username% - Your username")
        print("%hostname% - Computer name")
        print("%directory% - Current directory")
        
        print("\nExample format:")
        print("<purple>[<c>%time%<purple>]<c><n>[%username%]")
        print("This will show:")
        print("[12:34:56]  (in purple)")
        print("[username]  (in default color)")
        
        new_style = input("\nEnter your custom prompt style: ")
        if new_style:
            # Save configuration with the literal style tags (don't convert)
            config_file = os.path.join(os.path.expanduser('~'), '.terminal_prompt_config.json')
            try:
                with open(config_file, 'w') as f:
                    json.dump({'format': new_style}, f, indent=4)
                print("\nPrompt style saved successfully!")
            except Exception as e:
                print(f"\nError saving configuration: {e}")
                
    elif choice == '0':
        return

def customize_colors():
    """Interactive function to customize terminal colors"""
    global style
    
    print("\n=== Color Customization ===")
    print("1. Change prompt color")
    print("2. Change input color")
    print("3. Change output color")
    print("4. Change completion menu colors")
    print("0. Back to main menu")
    
    while True:
        choice = input("\nEnter your choice (0-4): ")
        
        if choice == '1':
            print("\nAvailable colors:")
            print("black, red, green, yellow, blue, magenta, cyan, white")
            print("You can also use hex colors like #00ff00")
            new_color = input("Enter prompt color: ")
            
            # Save prompt color
            config_file = os.path.join(os.path.expanduser('~'), '.terminal_style_config.json')
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception:
                config = {}
            
            config['prompt_color'] = new_color
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Apply style changes immediately
            style_config = load_style_config()
            style = Style.from_dict({
                'prompt': style_config['prompt_color'] + ' bold',
                'input': style_config['input_color'],
                'output': style_config['output_color'],
                'completion-menu.completion': f"bg:{style_config['completion_bg']} {style_config['completion_text']}",
                'completion-menu.completion.current': f"bg:{style_config['completion_selected_bg']} {style_config['completion_selected_text']}",
                'completion-menu.meta.completion': f"bg:{style_config['completion_bg']} {style_config['completion_text']}",
                'completion-menu.meta.completion.current': f"bg:{style_config['completion_selected_bg']} {style_config['completion_selected_text']}",
                'scrollbar.background': 'bg:#003333',
                'scrollbar.button': 'bg:#00aaaa',
                'green': '#00ff00',
                'cyan': '#00ffff',
                'red': '#ff0000',
                'blue': '#0000ff',
                'yellow': '#ffff00',
                'magenta': '#ff00ff',
                'white': '#ffffff',
                'black': '#000000'
            })
            
            print("\nPrompt color saved and applied!")
            
        elif choice == '2':
            print("\nAvailable colors:")
            print("black, red, green, yellow, blue, magenta, cyan, white")
            print("You can also use hex colors like #00ff00")
            new_color = input("Enter input color: ")
            
            # Save input color
            config_file = os.path.join(os.path.expanduser('~'), '.terminal_style_config.json')
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception:
                config = {}
            
            config['input_color'] = new_color
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Apply style changes immediately
            style_config = load_style_config()
            style = Style.from_dict({
                'prompt': style_config['prompt_color'] + ' bold',
                'input': style_config['input_color'],
                'output': style_config['output_color'],
                'completion-menu.completion': f"bg:{style_config['completion_bg']} {style_config['completion_text']}",
                'completion-menu.completion.current': f"bg:{style_config['completion_selected_bg']} {style_config['completion_selected_text']}",
                'completion-menu.meta.completion': f"bg:{style_config['completion_bg']} {style_config['completion_text']}",
                'completion-menu.meta.completion.current': f"bg:{style_config['completion_selected_bg']} {style_config['completion_selected_text']}",
                'scrollbar.background': 'bg:#003333',
                'scrollbar.button': 'bg:#00aaaa',
                'green': '#00ff00',
                'cyan': '#00ffff',
                'red': '#ff0000',
                'blue': '#0000ff',
                'yellow': '#ffff00',
                'magenta': '#ff00ff',
                'white': '#ffffff',
                'black': '#000000'
            })
            
            print("\nInput color saved and applied!")
            
        elif choice == '3':
            print("\nAvailable colors:")
            print("black, red, green, yellow, blue, magenta, cyan, white")
            print("You can also use hex colors like #00ff00")
            new_color = input("Enter output color: ")
            
            # Save output color
            config_file = os.path.join(os.path.expanduser('~'), '.terminal_style_config.json')
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception:
                config = {}
            
            config['output_color'] = new_color
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Apply style changes immediately
            style_config = load_style_config()
            style = Style.from_dict({
                'prompt': style_config['prompt_color'] + ' bold',
                'input': style_config['input_color'],
                'output': style_config['output_color'],
                'completion-menu.completion': f"bg:{style_config['completion_bg']} {style_config['completion_text']}",
                'completion-menu.completion.current': f"bg:{style_config['completion_selected_bg']} {style_config['completion_selected_text']}",
                'completion-menu.meta.completion': f"bg:{style_config['completion_bg']} {style_config['completion_text']}",
                'completion-menu.meta.completion.current': f"bg:{style_config['completion_selected_bg']} {style_config['completion_selected_text']}",
                'scrollbar.background': 'bg:#003333',
                'scrollbar.button': 'bg:#00aaaa',
                'green': '#00ff00',
                'cyan': '#00ffff',
                'red': '#ff0000',
                'blue': '#0000ff',
                'yellow': '#ffff00',
                'magenta': '#ff00ff',
                'white': '#ffffff',
                'black': '#000000'
            })
            
            print("\nOutput color saved and applied!")
            
        elif choice == '4':
            print("\nCompletion Menu Colors:")
            print("1. Background color")
            print("2. Text color")
            print("3. Selected background color")
            print("4. Selected text color")
            print("0. Back")
            
            subchoice = input("\nEnter your choice (0-4): ")
            if subchoice in ['1', '2', '3', '4']:
                print("\nAvailable colors:")
                print("black, red, green, yellow, blue, magenta, cyan, white")
                print("You can also use hex colors like #00ff00")
                new_color = input("Enter color: ")
                
                # Save completion menu color
                config_file = os.path.join(os.path.expanduser('~'), '.terminal_style_config.json')
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                except Exception:
                    config = {}
                
                color_keys = {
                    '1': 'completion_bg',
                    '2': 'completion_text',
                    '3': 'completion_selected_bg',
                    '4': 'completion_selected_text'
                }
                
                config[color_keys[subchoice]] = new_color
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                print("\nColor saved successfully!")
            
        elif choice == '0':
            break
        
        else:
            print("\nInvalid choice. Please try again.")

def start_terminal():
    """Start the main terminal"""
    # Make style variable global so we can modify it
    global style
    
    # Clear the screen
    os.system('cls' if platform.system() == 'Windows' else 'clear')
    
    # Show the banner
    show_banner()
    
    # Create history file path
    history_file = os.path.join(os.path.expanduser('~'), '.terminal_history')
    
    restart = True
    while restart:
        restart = False
        
        # Create session with current style
        session = PromptSession(
            history=FileHistory(history_file),
            style=style,
            completer=ProfessionalCompleter()
        )
        
        while True:
            try:
                # Get user input with custom prompt
                command = session.prompt(get_prompt())
                
                # Handle exit command
                if command.lower() in ['exit', 'quit']:
                    console.print("[bold red]Goodbye![/bold red]")
                    return
                
                # Handle customize command
                if command.lower() == 'customize':
                    customize_terminal()
                    # Reload configurations
                    style_config = load_style_config()
                    style = Style.from_dict({
                        'prompt': style_config['prompt_color'] + ' bold',
                        'input': style_config['input_color'],
                        'output': style_config['output_color'],
                        'completion-menu.completion': f"bg:{style_config['completion_bg']} {style_config['completion_text']}",
                        'completion-menu.completion.current': f"bg:{style_config['completion_selected_bg']} {style_config['completion_selected_text']}",
                        'completion-menu.meta.completion': f"bg:{style_config['completion_bg']} {style_config['completion_text']}",
                        'completion-menu.meta.completion.current': f"bg:{style_config['completion_selected_bg']} {style_config['completion_selected_text']}",
                        'scrollbar.background': 'bg:#003333',
                        'scrollbar.button': 'bg:#00aaaa',
                        'green': '#00ff00',
                        'cyan': '#00ffff',
                        'red': '#ff0000',
                        'blue': '#0000ff',
                        'yellow': '#ffff00',
                        'magenta': '#ff00ff',
                        'white': '#ffffff',
                        'black': '#000000'
                    })
                    # Clear screen and show new banner
                    os.system('cls' if platform.system() == 'Windows' else 'clear')
                    show_banner()
                    # Restart with new session to apply styles
                    restart = True
                    break
                
                # Handle help command
                if command.lower().startswith('help '):
                    completer = ProfessionalCompleter()
                    help_text = completer._get_command_help(command.split()[1])
                    if help_text:
                        console.print(Panel(help_text, title="Command Help", border_style="blue"))
                    else:
                        console.print(f"[red]No help available for command: {command.split()[1]}[/red]")
                    continue
                
                # Execute command and display output
                if command.strip():
                    output = execute_command(command)
                    if output:
                        # Display command output in a panel
                        console.print(Panel(
                            Syntax(output, "bash", theme="monokai"),
                            border_style="blue"
                        ))
            
            except KeyboardInterrupt:
                continue
            except EOFError:
                return

def main():
    """Main entry point for the terminal application"""
    # Check if configuration files exist, create with defaults if not
    try:
        banner_config_file = os.path.join(os.path.expanduser('~'), '.terminal_banner_config.json')
        prompt_config_file = os.path.join(os.path.expanduser('~'), '.terminal_prompt_config.json')
        style_config_file = os.path.join(os.path.expanduser('~'), '.terminal_style_config.json')
        
        if not os.path.exists(banner_config_file) or not os.path.exists(prompt_config_file) or not os.path.exists(style_config_file):
            print("Creating default configuration files...")
            reset_configuration()
    except Exception as e:
        print(f"Error checking configuration files: {e}")
        print("Continuing with default settings...")
    
    # Try to show loading animation
    try:
        show_loading_animation()
    except:
        print("Starting terminal...")
    
    # Start the terminal with error handling
    try:
        start_terminal()
    except Exception as e:
        print(f"Error starting terminal: {e}")
        print("Please report this error to the developer.")
        input("Press Enter to exit...")
        sys.exit(1)

def load_banner_config():
    """Load banner configuration from file or use defaults"""
    config_file = os.path.join(os.path.expanduser('~'), '.terminal_banner_config.json')
    default_config = {
        'banner_text': """
    ███████╗██╗   ██╗████████╗██╗  ██╗███████╗██████╗ ██╗ ██████╗ 
    ██╔════╝██║   ██║╚══██╔══╝██║  ██║██╔════╝██╔══██╗██║██╔════╝ 
    █████╗  ██║   ██║   ██║   ███████║█████╗  ██████╔╝██║██║  ███╗
    ██╔══╝  ██║   ██║   ██║   ██╔══██║██╔══╝  ██╔══██╗██║██║   ██║
    ██║     ╚██████╔╝   ██║   ██║  ██║███████╗██║  ██║██║╚██████╔╝
    ╚═╝      ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ 
        """,
        'banner_style': 'bold cyan',
        'border_style': 'cyan',
        'title': 'Professional Terminal',
        'subtitle': 'Press TAB for smart completion',
        'show_info': True,
        'info_items': {
            'OS': True,
            'Shell': True,
            'Python': True,
            'Time': True,
            'Directory': True,
            'Username': True,
            'Hostname': True,
            'Memory': True,
            'CPU': True
        },
        'custom_info': {
            'Welcome': 'Welcome to your custom terminal!',
            'Status': 'System Ready'
        },
        'banner_image': None,
        'image_width': 40
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # Merge user config with defaults
                default_config.update(user_config)
    except Exception:
        pass
    
    return default_config

def load_prompt_config():
    """Load prompt configuration from file or use defaults"""
    config_file = os.path.join(os.path.expanduser('~'), '.terminal_prompt_config.json')
    default_config = {
        'format': '<green>[%time% %username%]<c>',
        'time_format': '%H:%M:%S'
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # Merge user config with defaults
                default_config.update(user_config)
    except Exception:
        pass
    
    return default_config

def load_style_config():
    """Load style configuration from file or use defaults"""
    config_file = os.path.join(os.path.expanduser('~'), '.terminal_style_config.json')
    default_config = {
        'prompt_color': '#00ff00',
        'input_color': '#00ffff',
        'output_color': '#ffffff',
        'completion_bg': '#008888',
        'completion_text': '#ffffff',
        'completion_selected_bg': '#00aaaa',
        'completion_selected_text': '#000000'
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # Merge user config with defaults
                default_config.update(user_config)
    except Exception:
        pass
    
    return default_config

def reset_configuration():
    """Reset all configuration files to default values"""
    try:
        # Reset banner configuration
        banner_config_file = os.path.join(os.path.expanduser('~'), '.terminal_banner_config.json')
        default_banner_config = {
            'banner_text': """
    ███████╗██╗   ██╗████████╗██╗  ██╗███████╗██████╗ ██╗ ██████╗ 
    ██╔════╝██║   ██║╚══██╔══╝██║  ██║██╔════╝██╔══██╗██║██╔════╝ 
    █████╗  ██║   ██║   ██║   ███████║█████╗  ██████╔╝██║██║  ███╗
    ██╔══╝  ██║   ██║   ██║   ██╔══██║██╔══╝  ██╔══██╗██║██║   ██║
    ██║     ╚██████╔╝   ██║   ██║  ██║███████╗██║  ██║██║╚██████╔╝
    ╚═╝      ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ 
            """,
            'banner_style': 'bold cyan',
            'border_style': 'cyan',
            'title': 'Professional Terminal',
            'subtitle': 'Press TAB for smart completion',
            'show_info': True,
            'info_items': {
                'OS': True,
                'Shell': True,
                'Python': True,
                'Time': True,
                'Directory': True,
                'Username': True,
                'Hostname': True,
                'Memory': True,
                'CPU': True
            },
            'custom_info': {
                'Welcome': 'Welcome to your custom terminal!',
                'Status': 'System Ready'
            },
            'banner_image': None,
            'image_width': 40
        }
        
        with open(banner_config_file, 'w') as f:
            json.dump(default_banner_config, f, indent=4)
        
        # Reset prompt configuration
        prompt_config_file = os.path.join(os.path.expanduser('~'), '.terminal_prompt_config.json')
        default_prompt_config = {
            'format': '<green>[%time% %username%]<c>',
            'time_format': '%H:%M:%S'
        }
        
        with open(prompt_config_file, 'w') as f:
            json.dump(default_prompt_config, f, indent=4)
        
        # Reset style configuration
        style_config_file = os.path.join(os.path.expanduser('~'), '.terminal_style_config.json')
        default_style_config = {
            'prompt_color': '#00ff00',
            'input_color': '#00ffff',
            'output_color': '#ffffff',
            'completion_bg': '#008888',
            'completion_text': '#ffffff',
            'completion_selected_bg': '#00aaaa',
            'completion_selected_text': '#000000'
        }
        
        with open(style_config_file, 'w') as f:
            json.dump(default_style_config, f, indent=4)
        
        # Reset history file
        history_file = os.path.join(os.path.expanduser('~'), '.terminal_history')
        if os.path.exists(history_file):
            os.remove(history_file)
        
        print("\nConfiguration reset successfully!")
        print("All settings have been restored to default values.")
        return True
    except Exception as e:
        print(f"\nError resetting configuration: {e}")
        return False

def show_customization_animation():
    """Show a nice animation when customizing the terminal"""
    try:
        from rich.console import Console
        from rich.text import Text
        
        console = Console()
        
        # Animated text
        text = "Terminal Customization"
        
        # Animation frames
        for i in range(len(text)):
            # Create colored text with animation effect
            colored_text = Text()
            for j, char in enumerate(text):
                if j <= i:
                    # Rainbow effect through the text
                    colors = ["red", "yellow", "green", "cyan", "blue", "magenta"]
                    color = colors[(j + i) % len(colors)]
                    colored_text.append(char, style=f"bold {color}")
                else:
                    colored_text.append(char, style="white")
            
            # Display the frame
            console.clear()
            console.print("\n\n")
            console.print(colored_text, justify="center")
            console.print("\n\n")
            time.sleep(0.05)
        
        # Final message
        console.print("\n[bold green]Let's customize your terminal![/bold green]\n", justify="center")
        time.sleep(0.5)
        
    except Exception:
        # Fallback to simple message
        print("\n=== Terminal Customization ===\n")

def customize_banner():
    """Interactive function to customize the terminal banner"""
    print("\n=== Banner Customization ===")
    print("1. Change banner text")
    print("2. Change banner style")
    print("3. Change title and subtitle")
    print("4. Configure system information")
    print("5. Add custom information")
    print("6. Set banner image")
    print("0. Back to main menu")
    
    while True:
        choice = input("\nEnter your choice (0-6): ")
        
        if choice == '1':
            print("\nYou can use ASCII art or plain text for your banner.")
            print("Example of ASCII art generator websites: patorjk.com/software/taag/")
            new_text = input("\nEnter new banner text (or press Enter to keep current):\n")
            
            if new_text.strip():
                # Save banner text
                config_file = os.path.join(os.path.expanduser('~'), '.terminal_banner_config.json')
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                except Exception:
                    config = {}
                
                config['banner_text'] = new_text
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                print("\nBanner text saved successfully!")
            
        elif choice == '2':
            print("\nAvailable styles:")
            print("bold, italic, underline, strike, reverse, dim")
            print("Also color names: red, green, blue, cyan, magenta, yellow, white")
            print("Examples: 'bold red', 'italic cyan', 'bold blue underline'")
            
            banner_style = input("Enter banner text style: ")
            border_style = input("Enter border style: ")
            
            # Save style settings
            config_file = os.path.join(os.path.expanduser('~'), '.terminal_banner_config.json')
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception:
                config = {}
            
            if banner_style:
                config['banner_style'] = banner_style
            if border_style:
                config['border_style'] = border_style
                
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            print("\nBanner style saved successfully!")
            
        elif choice == '3':
            title = input("\nEnter banner title: ")
            subtitle = input("Enter banner subtitle: ")
            
            # Save title and subtitle
            config_file = os.path.join(os.path.expanduser('~'), '.terminal_banner_config.json')
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception:
                config = {}
            
            if title:
                config['title'] = title
            if subtitle:
                config['subtitle'] = subtitle
                
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            print("\nBanner title and subtitle saved successfully!")
            
        elif choice == '4':
            print("\n=== System Information Configuration ===")
            print("Select which system information to show in the banner:")
            
            # Get current configuration
            config_file = os.path.join(os.path.expanduser('~'), '.terminal_banner_config.json')
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception:
                config = {}
            
            if 'info_items' not in config:
                config['info_items'] = {}
            
            # Show current settings
            info_items = config['info_items']
            print(f"1. OS            [{'X' if info_items.get('OS', True) else ' '}]")
            print(f"2. Shell         [{'X' if info_items.get('Shell', True) else ' '}]")
            print(f"3. Python        [{'X' if info_items.get('Python', True) else ' '}]")
            print(f"4. Time          [{'X' if info_items.get('Time', True) else ' '}]")
            print(f"5. Directory     [{'X' if info_items.get('Directory', True) else ' '}]")
            print(f"6. Username      [{'X' if info_items.get('Username', True) else ' '}]")
            print(f"7. Hostname      [{'X' if info_items.get('Hostname', True) else ' '}]")
            print(f"8. Memory        [{'X' if info_items.get('Memory', True) else ' '}]")
            print(f"9. CPU           [{'X' if info_items.get('CPU', True) else ' '}]")
            print("0. Back")
            
            # Toggle settings
            subchoice = input("\nEnter number to toggle (0 to go back): ")
            if subchoice == '1':
                info_items['OS'] = not info_items.get('OS', True)
            elif subchoice == '2':
                info_items['Shell'] = not info_items.get('Shell', True)
            elif subchoice == '3':
                info_items['Python'] = not info_items.get('Python', True)
            elif subchoice == '4':
                info_items['Time'] = not info_items.get('Time', True)
            elif subchoice == '5':
                info_items['Directory'] = not info_items.get('Directory', True)
            elif subchoice == '6':
                info_items['Username'] = not info_items.get('Username', True)
            elif subchoice == '7':
                info_items['Hostname'] = not info_items.get('Hostname', True)
            elif subchoice == '8':
                info_items['Memory'] = not info_items.get('Memory', True)
            elif subchoice == '9':
                info_items['CPU'] = not info_items.get('CPU', True)
            
            # Save settings
            config['info_items'] = info_items
            show_info = input("\nShow system information in banner? (y/n): ").lower() == 'y'
            config['show_info'] = show_info
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            print("\nSystem information settings saved!")
            
        elif choice == '5':
            print("\n=== Custom Information Configuration ===")
            
            # Get current configuration
            config_file = os.path.join(os.path.expanduser('~'), '.terminal_banner_config.json')
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception:
                config = {}
            
            if 'custom_info' not in config:
                config['custom_info'] = {}
            
            # Show current custom info
            custom_info = config['custom_info']
            print("Current custom information:")
            if custom_info:
                for i, (key, value) in enumerate(custom_info.items(), 1):
                    print(f"{i}. {key}: {value}")
            else:
                print("No custom information defined")
            
            print("\n1. Add new custom info")
            print("2. Remove custom info")
            print("0. Back")
            
            subchoice = input("\nEnter your choice: ")
            
            if subchoice == '1':
                key = input("\nEnter custom info name: ")
                value = input("Enter custom info value: ")
                
                if key and value:
                    custom_info[key] = value
                    config['custom_info'] = custom_info
                    
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=4)
                    print(f"\nCustom info '{key}' added successfully!")
                    
            elif subchoice == '2':
                if custom_info:
                    remove_key = input("\nEnter the name of the custom info to remove: ")
                    if remove_key in custom_info:
                        del custom_info[remove_key]
                        config['custom_info'] = custom_info
                        
                        with open(config_file, 'w') as f:
                            json.dump(config, f, indent=4)
                        print(f"\nCustom info '{remove_key}' removed successfully!")
                    else:
                        print(f"\nCustom info '{remove_key}' not found")
                else:
                    print("\nNo custom information to remove")
            
        elif choice == '6':
            print("\n=== Banner Image Configuration ===")
            print("You can set an image to display in ASCII art next to your banner text.")
            print("The image needs to be in PNG format with transparency for best results.")
            
            image_path = input("\nEnter path to image file (or press Enter to skip): ")
            
            if image_path and os.path.exists(image_path):
                try:
                    # Open and encode the image
                    with open(image_path, 'rb') as img_file:
                        image_data = base64.b64encode(img_file.read()).decode('utf-8')
                    
                    # Ask for image width
                    try:
                        width = int(input("Enter ASCII art width (20-80, default 40): ") or 40)
                        width = max(20, min(80, width))  # Clamp between 20 and 80
                    except ValueError:
                        width = 40
                    
                    # Save the image data
                    config_file = os.path.join(os.path.expanduser('~'), '.terminal_banner_config.json')
                    try:
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                    except Exception:
                        config = {}
                    
                    config['banner_image'] = image_data
                    config['image_width'] = width
                    
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=4)
                    print("\nBanner image saved successfully!")
                    
                    # Preview the image
                    print("\nPreview of ASCII art:")
                    try:
                        image = Image.open(image_path)
                        ascii_art = convert_image_to_ascii(image, width)
                        print(ascii_art)
                    except Exception as e:
                        print(f"Error previewing image: {e}")
                        
                except Exception as e:
                    print(f"\nError processing image: {e}")
            elif image_path:
                print(f"\nImage file not found: {image_path}")
            
            # Option to remove image
            if not image_path:
                remove = input("\nRemove current banner image? (y/n): ").lower() == 'y'
                if remove:
                    config_file = os.path.join(os.path.expanduser('~'), '.terminal_banner_config.json')
                    try:
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                    except Exception:
                        config = {}
                    
                    config['banner_image'] = None
                    
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=4)
                    print("\nBanner image removed!")
            
        elif choice == '0':
            break
        
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == '__main__':
    main() 