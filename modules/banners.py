import pyfiglet
import random, os
from colorama import Fore, Back, Style, init

init(autoreset=True)

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def banners():
    #clear_terminal()
    banners = """
    ██████╗ ██╗      █████╗ ██╗   ██╗██████╗ ███████╗ █████╗ ██████╗ ██╗   ██╗      █████╗ ██████╗ ██╗
    ██╔══██╗██║     ██╔══██╗╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝     ██╔══██╗██╔══██╗██║
    ██████╔╝██║     ███████║ ╚████╔╝ ██████╔╝█████╗  ███████║██║  ██║ ╚████╔╝█████╗███████║██████╔╝██║
    ██╔═══╝ ██║     ██╔══██║  ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██║██║  ██║  ╚██╔╝ ╚════╝██╔══██║██╔═══╝ ██║
    ██║     ███████╗██║  ██║   ██║   ██║  ██║███████╗██║  ██║██████╔╝   ██║        ██║  ██║██║     ██║
    ╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝        ╚═╝  ╚═╝╚═╝     ╚═╝
                                                                                                  
            Author: GITHUB.COM/THATNOTEASY
    """
    # Split the banner into lines
    banner_lines = banners.split('\n')
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.CYAN, Fore.MAGENTA]
    for line in banner_lines:
        random_color = random.choice(colors)
        print(random_color + line)