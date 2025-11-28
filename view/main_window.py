from PySide6.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QComboBox, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QBrush, QFont, QGuiApplication

def format_amount(val):
    return "{:,.0f}".format(val).replace(",", " ")

def format_percentage(val):
    return "{:.2f}".format(val).replace(".", ",")

class MainWindow(QMainWindow):
    catPercentageChanged = Signal(int, float)   # cat_index, new percentage
    catAmountChanged = Signal(int, float)         # cat_index, new amount
    adminPctChanged = Signal(float)
    contingencyPctChanged = Signal(float)
    grandTotalChanged = Signal(float)
    lockTypeChanged = Signal(int, int)            # cat_index, new lock type (0,1,2)
    feeAmountChanged = Signal(int, float)           # fee_index, new fixed fee amount
    feePercentageChanged = Signal(int, float)       # fee_index, new percentage fee value
    saveBudgetClicked = Signal()
    loadBudgetClicked = Signal()
    lockAllAmountsClicked = Signal()
    lockAllPercentagesClicked = Signal()
    unlockAllClicked = Signal()
    copyBudgetClicked = Signal()
    importExcelClicked = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Resource Allocation Budgeting Tool")
        self.resize(1100, 600)
        self.setup_ui()
        self.groupClickedCallback = None

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        # Top bar for summary and buttons.
        top_bar = QHBoxLayout()
        self.locked_label = QLabel("Locked: 0 (0,00%)")
        self.remaining_label = QLabel("Remaining: 0 (0,00%)")
        top_bar.addWidget(self.locked_label)
        top_bar.addWidget(self.remaining_label)
        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.clicked.connect(lambda: self.copyBudgetClicked.emit())
        top_bar.addWidget(self.copy_button)
        self.save_button = QPushButton("Save Budget")
        self.save_button.clicked.connect(lambda: self.saveBudgetClicked.emit())
        top_bar.addWidget(self.save_button)
        self.load_button = QPushButton("Load Budget")
        self.load_button.clicked.connect(lambda: self.loadBudgetClicked.emit())
        top_bar.addWidget(self.load_button)
        self.import_excel_button = QPushButton("Import Excel")
        self.import_excel_button.clicked.connect(lambda: self.importExcelClicked.emit())
        top_bar.addWidget(self.import_excel_button)
        self.unlock_all_button = QPushButton("Unlock All")
        self.unlock_all_button.clicked.connect(lambda: self.unlockAllClicked.emit())
        top_bar.addWidget(self.unlock_all_button)
        self.lock_all_amounts_button = QPushButton("Lock All Amounts")
        self.lock_all_amounts_button.clicked.connect(lambda: self.lockAllAmountsClicked.emit())
        top_bar.addWidget(self.lock_all_amounts_button)
        self.lock_all_percentages_button = QPushButton("Lock All Percentages")
        self.lock_all_percentages_button.clicked.connect(lambda: self.lockAllPercentagesClicked.emit())
        top_bar.addWidget(self.lock_all_percentages_button)
        main_layout.addLayout(top_bar)

        # Table with 4 columns: Description, Amount, Percentage, Lock.
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Description", "Amount", "Percentage", "Lock"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 300)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 120)
        main_layout.addWidget(self.table)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.cellClicked.connect(self.on_cell_clicked)

    def set_locked_remaining(self, locked_amt, locked_pct, remaining_amt, remaining_pct):
        self.locked_label.setText(f"Locked: {format_amount(locked_amt)} ({format_percentage(locked_pct)}%)")
        self.remaining_label.setText(f"Remaining: {format_amount(remaining_amt)} ({format_percentage(remaining_pct)}%)")
        if remaining_amt < 0:
            self.remaining_label.setStyleSheet("color: red")
            self.remaining_label.setToolTip(f"Over budget by {format_amount(abs(remaining_amt))}")
        else:
            self.remaining_label.setStyleSheet("")
            self.remaining_label.setToolTip("")

    def show_over_budget_error(self):
        QMessageBox.critical(self, "Over Budget", "The fixed allocations exceed the available budget.")

    def update_table(self, table_data, over_budget=False, over_budget_rows=None):
        if over_budget_rows is None:
            over_budget_rows = []
        self.table.blockSignals(True)
        self.table.setRowCount(len(table_data))
        category_counter = 0
        for row, data in enumerate(table_data):
            row_type = data.get("row_type")
            item_desc = QTableWidgetItem(data.get("description", ""))
            item_desc.setFlags(Qt.ItemIsEnabled)
            item_desc.setData(Qt.UserRole, row_type)
            if row_type == "group_total":
                font = QFont()
                font.setBold(True)
                item_desc.setFont(font)
                item_desc.setData(Qt.UserRole + 2, data.get("group_label"))
            self.table.setItem(row, 0, item_desc)
            amt = data.get("amount", 0)
            txt_amt = format_amount(amt)
            if row_type in ["category", "fee", "grand_total"]:
                item_amt = QTableWidgetItem(txt_amt)
                item_amt.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                if row_type == "category":
                    item_amt.setData(Qt.UserRole + 1, data.get("cat_index"))
            else:
                item_amt = QTableWidgetItem(txt_amt)
                item_amt.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 1, item_amt)
            pct = data.get("percentage", 0)
            txt_pct = format_percentage(pct) if pct is not None else ""
            # Show 100% on SUBTOTAL row
            if row_type == "subtotal":
                txt_pct = "100,00"
            if row_type in ["category", "fee"]:
                item_pct = QTableWidgetItem(txt_pct)
                item_pct.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                if row_type == "category":
                    item_pct.setData(Qt.UserRole + 1, data.get("cat_index"))
                elif row_type == "fee" and "fee_index" in data:
                    item_pct.setData(Qt.UserRole + 2, data["fee_index"])
            else:
                item_pct = QTableWidgetItem(txt_pct)
                item_pct.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 2, item_pct)
            if row_type == "category":
                combo = QComboBox()
                combo.addItems(["Unlocked", "Lock Amount", "Lock Percentage"])
                lock_type = data.get("lock_type", 0)
                combo.setCurrentIndex(lock_type)
                combo.setProperty("cat_index", data.get("cat_index"))
                combo.currentIndexChanged.connect(self.on_lock_combobox_changed)
                self.table.setCellWidget(row, 3, combo)
            else:
                blank = QTableWidgetItem("")
                blank.setFlags(Qt.ItemIsEnabled)
                self.table.setItem(row, 3, blank)
            if row_type == "category":
                if category_counter % 2 == 0:
                    for col in range(4):
                        cell = self.table.item(row, col)
                        if cell:
                            cell.setBackground(QBrush(QColor("#fafafa")))
                category_counter += 1
            if row_type == "category" and data.get("cat_index") in over_budget_rows and over_budget:
                for col in range(4):
                    cell = self.table.item(row, col)
                    if cell:
                        cell.setBackground(QBrush(QColor("red")))
        self.table.blockSignals(False)

    @Slot(int, int)
    def on_cell_changed(self, row, column):
        row_type = self.table.item(row, 0).data(Qt.UserRole)
        item = self.table.item(row, column)
        if not item:
            return
        text = item.text().replace(" ", "").replace(",", ".")
        try:
            new_val = float(text)
        except ValueError:
            return
        if row_type == "category":
            if column == 1:
                cat_index = self.table.item(row, 1).data(Qt.UserRole + 1)
                self.catAmountChanged.emit(cat_index, new_val)
            elif column == 2:
                cat_index = self.table.item(row, 2).data(Qt.UserRole + 1)
                self.catPercentageChanged.emit(cat_index, new_val)
        elif row_type == "fee":
            fee_index = self.table.item(row, 2).data(Qt.UserRole + 2)
            # Assume if column 1 (Amount) is edited, then it's a fixed fee;
            # if column 2 (Percentage) is edited, then percentage fee.
            if column == 1:
                self.feeAmountChanged.emit(fee_index, new_val)
            elif column == 2:
                self.feePercentageChanged.emit(fee_index, new_val)
        elif row_type == "grand_total" and column == 1:
            self.grandTotalChanged.emit(new_val)

    @Slot(int)
    def on_lock_combobox_changed(self, index):
        sender = self.sender()
        if sender:
            cat_index = sender.property("cat_index")
            new_lock_type = index  # 0 = Unlocked, 1 = Lock Amount, 2 = Lock Percentage
            print(f"[View] ComboBox changed: cat_index={cat_index}, new_lock_type={new_lock_type}")
            self.lockTypeChanged.emit(int(cat_index), new_lock_type)

    @Slot(int, int)
    def on_cell_clicked(self, row, column):
        item = self.table.item(row, 0)
        if not item:
            return
        row_type = item.data(Qt.UserRole)
        if row_type == "group_total":
            group_label = item.data(Qt.UserRole + 2)
            if not group_label:
                return
            if hasattr(self, "groupClickedCallback") and self.groupClickedCallback:
                self.groupClickedCallback(row)

    @Slot()
    def copy_data(self):
        rows = []
        row_count = self.table.rowCount()
        col_count = self.table.columnCount()
        for row in range(row_count):
            cols = []
            for col in range(col_count):
                widget = self.table.cellWidget(row, col)
                if widget and isinstance(widget, QComboBox):
                    val = widget.currentText()
                else:
                    item = self.table.item(row, col)
                    val = item.text() if item else ""
                cols.append(val)
            rows.append("\t".join(cols))
        final_text = "\n".join(rows)
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(final_text)
        QMessageBox.information(self, "Copied", "Data copied to clipboard!\nYou can now paste directly into Excel.")