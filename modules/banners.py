import random, os
from colorama import Fore, Back, Style, init

init(autoreset=True)

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def banners():
    clear_terminal()
    banners = """
██████╗ ██╗      █████╗ ██╗   ██╗██████╗ ███████╗ █████╗ ██████╗ ██╗   ██╗       █████╗ ██████╗ ██╗
██╔══██╗██║     ██╔══██╗╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝      ██╔══██╗██╔══██╗██║
██████╔╝██║     ███████║ ╚████╔╝ ██████╔╝█████╗  ███████║██║  ██║ ╚████╔╝ █████╗███████║██████╔╝██║
██╔═══╝ ██║     ██╔══██║  ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██║██║  ██║  ╚██╔╝  ╚════╝██╔══██║██╔═══╝ ██║
██║     ███████╗██║  ██║   ██║   ██║  ██║███████╗██║  ██║██████╔╝   ██║         ██║  ██║██║     ██║
╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝         ╚═╝  ╚═╝╚═╝     ╚═╝
                                                                                                  
            Author: GITHUB.COM/THATNOTEASY
    """
    # Define a list of colors to cycle through
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    
    # Print each line of the banner with a different color
    for i, line in enumerate(banners.strip().split('\n')):
        color = colors[i % len(colors)]  # Cycle through the colors
        print(color + line + Style.RESET_ALL)