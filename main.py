import sys
import logging
from PySide6.QtWidgets import QApplication
from model.budget import BudgetModel
from view.main_window import MainWindow
from controller.controller import Controller

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # --- Terminal handler (INFO and above) ---
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # --- File handler (DEBUG and above) ---
    fh = logging.FileHandler("app.log", mode="a")
    fh.setLevel(logging.DEBUG)

    # --- Format ---
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Add handlers
    logger.addHandler(ch)
    logger.addHandler(fh)

def main():
    setup_logging()

    app = QApplication(sys.argv)

    # Start with an empty model (same as before)
    model = BudgetModel(grand_total=0)
    model.categories = []
    model.groups = []

    view = MainWindow()
    controller = Controller(model, view)

    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
