# Futuristic Terminal

A modern, feature-rich terminal emulator with a professional look and advanced functionality.

## Features

- 🎨 Professional ASCII art banner with customizable image support
- 🖊️ Over 200+ ASCII art fonts for banner text using pyfiglet
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
git clone https://github.com/yourusername/futuristic_terminal.git
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
- pyfiglet (for ASCII art font rendering)

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
   - Change banner text with real-time ASCII art preview
   - Select from over 200+ ASCII art fonts
   - See instant previews of fonts with your custom text
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

4. Font Selection:
   - Choose from a wide variety of ASCII art fonts
   - Preview fonts in real-time with your own text
   - Automatically updates banner text in the selected font
   - No need for external websites or copy-pasting

## Configuration

The terminal uses these configuration files:

1. `~/.terminal_history` - Stores command history
2. `~/.terminal_banner_config.json` - Stores banner customization settings and font selection
3. `~/.terminal_prompt_config.json` - Stores prompt customization settings
4. `~/.terminal_style_config.json` - Stores style customization settings

## Features in Detail

### ASCII Art Font Rendering
- Powered by pyfiglet library for high-quality ASCII art
- Over 200+ different fonts available
- Real-time preview when selecting fonts
- Automatic text conversion to ASCII art
- Error handling for font compatibility

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

## Font Selection Guide

1. Enter the customization menu by typing `customize`
2. Select option `2` for Banner Customization
3. Choose option `7` to Select font for banner text
4. Browse available fonts or search by name/number
5. Enter a sample text to preview how your text will look in the selected font
6. Confirm your selection to apply the font
7. Optionally update your banner text directly from the font selection menu

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- prompt_toolkit for the terminal interface
- rich for text formatting
- colorama for Windows color support
- pillow for image processing
- pyfiglet for ASCII art font rendering

## Created by

Dinesh Patra

## Powered by

Navya 