# Futuristic Terminal

A modern, feature-rich terminal emulator with a professional look and advanced functionality.

## Features

- 🎨 Professional ASCII art banner with customizable image support
- 🖼️ Custom background and styling
- 🚀 Automatic command detection across all operating systems
- 📝 Command history
- 🎨 Rich text formatting and colors
- 💻 System information display
- 🔄 Real-time command output
- 🎯 Smart file and directory navigation
- 🎨 Customizable appearance
- 🌐 Cross-platform compatibility (Windows, Linux, macOS)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/navyaXdev/Futherig.git
cd futuristic_terminal
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Dependencies

- Python 3.6+
- prompt_toolkit
- rich
- colorama
- pillow (for image support)

## Usage

1. Start the terminal:
```bash
python futuristic_terminal.py
```

2. Available commands:
   - All commands available in your operating system are automatically detected
   - `customize` - Customize the terminal appearance
   - `help [command]` - Get help for a specific command
   - `exit` or `quit` - Exit the terminal

## Customization

The terminal can be customized in several ways:

1. Banner Customization:
   - Change banner text
   - Add custom ASCII art
   - Customize colors and styles
   - Add system information

2. Style Customization:
   - Change text colors
   - Modify border styles
   - Customize prompt appearance
   - Add custom information

3. Image Support:
   - Add PNG images
   - Adjust image width
   - Position images on the left side of the banner

## Configuration

The terminal uses these configuration files:

1. `~/.terminal_history` - Stores command history
2. `~/.terminal_banner_config.json` - Stores banner customization settings
3. `~/.terminal_prompt_config.json` - Stores prompt customization settings
4. `~/.terminal_style_config.json` - Stores style customization settings

## Features in Detail

### Automatic Command Detection
- Dynamically discovers all available commands in your system's PATH
- Works across Windows, Linux, and macOS
- No hardcoded command lists - uses your actual system commands
- Built-in support for OS-specific commands
- Smart command completion with proper handling of file extensions

### Smart Completion
- Command completion for all system commands
- File and directory completion with detailed information
- Context-aware completions for specific commands
- Directory size and modification information

### System Information
- OS details
- Shell information
- Python version
- Current time
- Directory information
- Username and hostname
- Memory usage
- CPU usage

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- prompt_toolkit for the terminal interface
- rich for text formatting
- colorama for Windows color support
- pillow for image processing

## Created by

Dinesh Patra

## Powered by

Navya 
