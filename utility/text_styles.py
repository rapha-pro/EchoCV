"""
Text styling utilities for terminal output
Provides ANSI color codes and text formatting
"""


class Colors:
    """ANSI color codes for terminal text styling"""

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Text styles
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'


# Common exit codes
EXIT_CODES = ["q", "e", "!", "exit", "quit"]


# Utility functions for common styling patterns
def success(text):
    """Format text as success message"""
    return f"{Colors.GREEN}{text}{Colors.RESET}"


def error(text):
    """Format text as error message"""
    return f"{Colors.RED}{text}{Colors.RESET}"


def warning(text):
    """Format text as warning message"""
    return f"{Colors.YELLOW}{text}{Colors.RESET}"


def info(text):
    """Format text as info message"""
    return f"{Colors.CYAN}{text}{Colors.RESET}"


def highlight(text):
    """Format text as highlighted"""
    return f"{Colors.BOLD}{text}{Colors.RESET}"


def question(text):
    """Format text as question (blue italic)"""
    return f"{Colors.BLUE}{Colors.ITALIC}{text}{Colors.RESET}"


def header(text):
    """Format text as header (cyan bold)"""
    return f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.RESET}"


def dim(text):
    """Format text as dimmed"""
    return f"{Colors.DIM}{text}{Colors.RESET}"