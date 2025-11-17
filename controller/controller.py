import os
import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox
from model.budget import BudgetModel
from view.main_window import MainWindow

class Controller:
    def __init__(self, model: BudgetModel, view: MainWindow):
        self.model = model
        self.view = view
        self.was_over_budget = False
        self.group_mapping = {}   # mapping from group label to {member_rows, total_row}
        self.group_collapsed = {} # group label -> bool
        self.setup_connections()
        self.refresh_view()

    def setup_connections(self):
        self.view.catPercentageChanged.connect(self.handle_cat_percentage_changed)
        self.view.catAmountChanged.connect(self.handle_cat_amount_changed)
        self.view.adminPctChanged.connect(self.handle_adminPctChanged)
        self.view.contingencyPctChanged.connect(self.handle_contingencyPctChanged)
        self.view.grandTotalChanged.connect(self.handle_grand_total_changed)
        self.view.lockTypeChanged.connect(self.handle_lock_type_changed)
        self.view.saveBudgetClicked.connect(self.handle_save_budget)
        self.view.loadBudgetClicked.connect(self.handle_load_budget)
        self.view.lockAllAmountsClicked.connect(self.handle_lock_all_amounts)
        self.view.lockAllPercentagesClicked.connect(self.handle_lock_all_percentages)
        self.view.unlockAllClicked.connect(self.handle_unlock_all)
        self.view.importExcelClicked.connect(self.handle_import_excel)
        self.view.copyBudgetClicked.connect(self.handle_copy_budget)
        # New fee signals:
        self.view.feeAmountChanged.connect(self.handle_fee_amount_changed)
        self.view.feePercentageChanged.connect(self.handle_fee_percentage_changed)
        self.view.table.cellClicked.connect(self.on_table_cell_clicked)

    def handle_cat_percentage_changed(self, cat_index, new_pct):
        self.model.update_category_percentage(cat_index, new_pct)
        self.refresh_view()

    def handle_cat_amount_changed(self, cat_index, new_amt):
        self.model.update_category_amount(cat_index, new_amt)
        self.refresh_view()

    def handle_adminPctChanged(self, new_pct):
        self.model.set_admin_pct(new_pct)
        self.refresh_view()

    def handle_contingencyPctChanged(self, new_pct):
        self.model.set_contingency_pct(new_pct)
        self.refresh_view()

    def handle_grand_total_changed(self, new_total):
        self.model.set_grand_total(new_total)
        self.refresh_view()

    def handle_lock_type_changed(self, cat_index, lock_type):
        self.model.update_lock_type(cat_index, lock_type)
        self.refresh_view()

    def handle_lock_all_amounts(self):
        self.model.lock_all(1)
        self.refresh_view()

    def handle_lock_all_percentages(self):
        self.model.lock_all(2)
        self.refresh_view()

    def handle_unlock_all(self):
        self.model.unlock_all()
        self.refresh_view()

    def handle_save_budget(self):
        filename, _ = QFileDialog.getSaveFileName(self.view, "Save Budget", "", "JSON Files (*.json)")
        if filename:
            try:
                self.model.save_to_file(filename)
                QMessageBox.information(self.view, "Save Budget", "Budget saved successfully!")
            except Exception as e:
                QMessageBox.critical(self.view, "Error", f"Failed to save budget: {str(e)}")

    def handle_load_budget(self):
        filename, _ = QFileDialog.getOpenFileName(self.view, "Load Budget", "", "JSON Files (*.json)")
        if filename:
            try:
                self.model.load_from_file(filename)
                QMessageBox.information(self.view, "Load Budget", "Budget loaded successfully!")
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self.view, "Error", f"Failed to load budget: {str(e)}")

    def handle_import_excel(self):
        filename, _ = QFileDialog.getOpenFileName(self.view, "Import Excel Budget", "", "Excel Files (*.xlsx *.xls)")
        if filename:
            try:
                self.model.import_from_excel(filename)
                QMessageBox.information(self.view, "Import Excel", "Budget imported successfully!")
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self.view, "Error", f"Failed to import Excel budget: {str(e)}")

    def handle_copy_budget(self):
        self.view.copy_data()

    def handle_fee_amount_changed(self, fee_index, new_amount):
        fee = self.model.fees[fee_index]
        if fee.fee_type == "fixed":
            fee.value = new_amount
            self.model.recalc()
            self.refresh_view()

    def handle_fee_percentage_changed(self, fee_index, new_percentage):
        fee = self.model.fees[fee_index]
        if fee.fee_type == "percentage":
            fee.value = new_percentage
            self.model.recalc()
            self.refresh_view()

    def on_table_cell_clicked(self, row, column):
        item = self.view.table.item(row, 0)
        if not item:
            return
        row_type = item.data(Qt.UserRole)
        if row_type == "group_total":
            group_label = item.data(Qt.UserRole + 2)
            if not group_label:
                return
            collapsed = self.group_collapsed.get(group_label, False)
            new_state = not collapsed
            self.group_collapsed[group_label] = new_state
            if group_label in self.group_mapping:
                member_rows = self.group_mapping[group_label]["member_rows"]
                for r in member_rows:
                    self.view.table.setRowHidden(r, new_state)
                total_row = self.group_mapping[group_label]["total_row"]
                group_item = self.view.table.item(total_row, 0)
                if group_item:
                    text = group_item.text()
                    if new_state:
                        if not text.startswith("+ "):
                            group_item.setText("+ " + text)
                    else:
                        if text.startswith("+ "):
                            group_item.setText(text[2:])

    def refresh_view(self):
        table_data, group_mapping = self.model.get_table_data()
        self.group_mapping = group_mapping
        fixed_amt = sum(cat.amount for cat in self.model.categories if cat.lock_type in [1, 2])
        fixed_pct = sum(cat.percentage for cat in self.model.categories if cat.lock_type in [1, 2])
        remaining_amt = self.model.subtotal - fixed_amt
        remaining_pct = 100 - fixed_pct
        self.view.set_locked_remaining(fixed_amt, fixed_pct, remaining_amt, remaining_pct)
        self.view.update_table(
            table_data,
            over_budget=self.model.over_budget,
            over_budget_rows=self.model.over_budget_rows
        )
        if remaining_amt < 0:
            QMessageBox.warning(self.view, "Over Budget", f"Over budget by {abs(remaining_amt):,}.")