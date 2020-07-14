import logging

from .ui import GUI

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    gui = GUI()
    gui.start()
