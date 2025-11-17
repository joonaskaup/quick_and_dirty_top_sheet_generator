import sys
import logging
from PySide6.QtWidgets import QApplication
from model.budget import BudgetModel
from view.main_window import MainWindow
from controller.controller import Controller

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app = QApplication(sys.argv)
    # Start with an empty budget.
    model = BudgetModel(grand_total=0)
    model.categories = []
    model.groups = []
    view = MainWindow()
    controller = Controller(model, view)
    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
