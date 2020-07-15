import logging
from .ui import GUI

def main():
    logging.basicConfig(level=logging.DEBUG)
    gui = GUI()
    gui.start()
