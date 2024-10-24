from datetime import datetime
import logging
import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QComboBox, QDateEdit, QCheckBox, QPushButton, QMessageBox, QInputDialog, QHeaderView
)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt, QDate
from backend import get_session  # Import get_session for session management
from models import Invoice  # Import your SQLAlchemy Invoice model

# Set up logging to display on the console
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')


class InvoiceTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.invoices = []  # Initialize as empty; will be filled on data load
        self.current_sort_option = 'Default'
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Invoice Management')
        layout = QVBoxLayout()

        # Search and Sort Layout
        search_sort_layout = QHBoxLayout()

        self.search_label = QLabel('Search:')
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText('Search...')
        self.search_bar.textChanged.connect(self.search_data)
        search_sort_layout.addWidget(self.search_label)
        search_sort_layout.addWidget(self.search_bar)

        self.sort_dropdown = QComboBox(self)
        self.sort_dropdown.addItems([
            'Default', 'Sort Name Asc', 'Sort Name Desc',
            'Sort Date Asc', 'Sort Date Desc', 'Sort Amount Asc', 'Sort Amount Desc'
        ])
        self.sort_dropdown.currentIndexChanged.connect(self.sort_data)
        search_sort_layout.addWidget(self.sort_dropdown)

        layout.addLayout(search_sort_layout)

        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(['Name', 'Type', 'Service Description', 'Invoice Date', 'Service Amount', 'Invoice Sent', 'Invoice Paid', 'Company ID'])
        self.table.cellDoubleClicked.connect(self.edit_cell)
        layout.addWidget(self.table)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Form Layout for entering new data
        form_layout = QHBoxLayout()

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText('Name')
        form_layout.addWidget(self.name_input)

        self.type_input = QComboBox(self)
        self.type_input.addItems(['individual','company'])  # Company or individual
        self.type_input.currentIndexChanged.connect(self.update_company_id_editable)
        form_layout.addWidget(self.type_input)

        self.service_description_input = QLineEdit(self)
        self.service_description_input.setPlaceholderText('Service Description')
        form_layout.addWidget(self.service_description_input)

        self.invoice_date_input = QDateEdit(self)
        self.invoice_date_input.setCalendarPopup(True)
        self.invoice_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.invoice_date_input)

        self.service_amount_input = QLineEdit(self)
        self.service_amount_input.setPlaceholderText('Service Amount')
        form_layout.addWidget(self.service_amount_input)

        self.invoice_sent_input = QCheckBox('Invoice Sent', self)
        form_layout.addWidget(self.invoice_sent_input)

        self.invoice_paid_input = QCheckBox('Invoice Paid', self)
        form_layout.addWidget(self.invoice_paid_input)

        self.company_id_input = QLineEdit(self)
        self.company_id_input.setPlaceholderText('Company ID')
        self.company_id_input.setEnabled(False)
        form_layout.addWidget(self.company_id_input)

        layout.addLayout(form_layout)

        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save_invoice)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

        self.load_existing_invoices()

    def load_existing_invoices(self):
        """Load existing invoices into the table within session context."""
        start_time = time.time()  # Record the start time
        print("Invoice 1:", datetime.now().strftime("%H:%M:%S"))
        
        with get_session() as session:
            self.invoices = session.query(Invoice).all()
            self.table.setRowCount(0)
            for row, invoice in enumerate(self.invoices):
                self.add_invoice_to_table(invoice, row, session)

        print("Invoice 2:", datetime.now().strftime("%H:%M:%S"))
        end_time = time.time()  # Record the end time
        print("Total Invoice: {:.2f} seconds".format(end_time - start_time))

    def add_invoice_to_table(self, invoice, row, session):
        """Add an invoice to the table at the specified row."""
        invoice = session.merge(invoice)  # Ensure the invoice is attached to the session
        self.table.insertRow(row)
        self.table.setItem(row, 0, self.create_highlighted_item(invoice.name, None))
        self.table.setItem(row, 1, self.create_highlighted_item(invoice.type, None))
        self.table.setItem(row, 2, self.create_highlighted_item(invoice.service_description, None))
        self.table.setItem(row, 3, self.create_highlighted_item(invoice.date.strftime('%Y-%m-%d'), None))
        self.table.setItem(row, 4, self.create_highlighted_item(str(invoice.amount), None))

        checkbox_sent = QCheckBox()
        checkbox_sent.setChecked(invoice.sent)
        checkbox_sent.stateChanged.connect(lambda state, r=row: self.checkbox_state_changed(state, r, 'sent'))
        checkbox_sent.setStyleSheet("background-color: white;")  # Set white background explicitly
        self.table.setCellWidget(row, 5, checkbox_sent)

        checkbox_paid = QCheckBox()
        checkbox_paid.setChecked(invoice.paid)
        checkbox_paid.stateChanged.connect(lambda state, r=row: self.checkbox_state_changed(state, r, 'paid'))
        checkbox_paid.setStyleSheet("background-color: white;")  # Set white background explicitly
        self.table.setCellWidget(row, 6, checkbox_paid)

        self.table.setItem(row, 7, self.create_highlighted_item(str(invoice.company_id), None))

        self.update_row_color(row)

    def create_highlighted_item(self, text, search_text):
        """Create a QTableWidgetItem with optional highlighted text."""
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def save_invoice(self):
        """Save a new invoice to the database."""
        name = self.name_input.text()
        type_ = self.type_input.currentText()
        service_description = self.service_description_input.text()
        amount = self.service_amount_input.text()

        if not name or not type_ or not service_description or not amount:
            QMessageBox.critical(self, 'Invalid Input', 'Please fill in all required fields (Name, Type, Service Description, Service Amount).')
            return

        # Check if Company ID is required and filled
        if type_ == 'company' and not self.company_id_input.text():
            QMessageBox.critical(self, 'Invalid Input', 'Please enter a valid Company ID for a company invoice.')
            return

        try:
            service_amount = float(amount)
            if service_amount <= 0:
                raise ValueError("Service amount must be greater than zero")
        except ValueError:
            QMessageBox.critical(self, 'Invalid Input', 'Please enter a valid service amount (a positive number).')
            return

        data = {
            'name': name,
            'type': type_,
            'service_description': service_description,
            'date': self.invoice_date_input.date().toPyDate(),
            'amount': service_amount,
            'sent': self.invoice_sent_input.isChecked(),
            'paid': self.invoice_paid_input.isChecked(),
            'company_id': int(self.company_id_input.text()) if type_ == 'company' else None
        }

        try:
            with get_session() as session:
                new_invoice = Invoice(**data)
                session.add(new_invoice)
                session.commit()
                session.refresh(new_invoice)

                self.invoices.append(new_invoice)
                self.load_existing_invoices()
                QMessageBox.information(self, 'Invoice Saved', 'Invoice successfully saved.')
                self.clear_inputs()
        except Exception as e:
            logging.error(f"Error saving invoice: {e}")
            QMessageBox.critical(self, 'Error', f'An error occurred while saving the invoice: {str(e)}')

    def clear_inputs(self):
        """Clear the input fields."""
        self.name_input.clear()
        self.type_input.setCurrentIndex(0)
        self.service_description_input.clear()
        self.service_amount_input.clear()
        self.invoice_sent_input.setChecked(False)
        self.invoice_paid_input.setChecked(False)
        self.company_id_input.clear()

    def search_data(self):
        """Search and highlight invoices based on user input."""
        search_text = self.search_bar.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item_text = item.text().lower()
                    if search_text and search_text in item_text:
                        match = True
                        item.setBackground(QColor('yellow'))
                    else:
                        item.setBackground(QColor('white') if not search_text else item.background())
            self.table.setRowHidden(row, not match if search_text else False)
            if not search_text:
                self.update_row_color(row)

    def edit_cell(self, row, column):
        """Edit a cell's value in the table and update the database."""
        item = self.table.item(row, column)
        if item is not None:
            current_value = item.text()
            new_value, ok = QInputDialog.getText(self, 'Edit Cell', f'Edit value:', QLineEdit.Normal, current_value)
            if ok and new_value:
                confirmation = QMessageBox.question(
                    self,
                    'Confirm Edit',
                    f"Do you want to change '{current_value}' to '{new_value}'?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirmation == QMessageBox.Yes:
                    self.update_database(row, column, new_value)
                    item.setText(new_value)

    def update_database(self, row, column, new_value):
        """Update the database with new values for a specific invoice."""
        try:
            with get_session() as session:
                invoice = session.merge(self.invoices[row])
                column_map = {0: 'name', 1: 'type', 2: 'service_description', 3: 'date', 4: 'amount', 5: 'sent', 6: 'paid', 7: 'company_id'}
                column_key = column_map.get(column)

                if column_key:
                    if column_key == 'date':
                        try:
                            invoice.date = QDate.fromString(new_value, Qt.ISODate).toPyDate()
                        except ValueError:
                            QMessageBox.critical(self, 'Invalid Input', 'Please enter a valid date in ISO format (YYYY-MM-DD).')
                            return
                    elif column_key == 'amount':
                        try:
                            invoice.amount = float(new_value)
                            if invoice.amount <= 0:
                                raise ValueError("Service amount must be greater than zero")
                        except ValueError:
                            QMessageBox.critical(self, 'Invalid Input', 'Please enter a valid service amount (a positive number).')
                            return
                    elif column_key in ['sent', 'paid']:
                        setattr(invoice, column_key, new_value.lower() == 'yes')
                    else:
                        setattr(invoice, column_key, new_value)

                session.commit()
                self.invoices[row] = invoice  # Update local cache after commit
        except Exception as e:
            logging.error(f"Error updating invoice in the database: {e}")
            QMessageBox.critical(self, 'Error', f'An error occurred while updating the invoice: {str(e)}')

    def checkbox_state_changed(self, state, row, column_key):
        """Handle checkbox state change for 'Invoice Sent' or 'Invoice Paid'."""
        new_value = 'yes' if state == Qt.Checked else 'no'
        confirmation = QMessageBox.question(
            self,
            'Confirm Change',
            f'Do you want to update the database with this change?',
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmation == QMessageBox.Yes:
            column = 5 if column_key == 'sent' else 6
            self.update_database(row, column, new_value)
            self.update_row_color(row)

    def update_row_color(self, row):
        """Update the color of a row based on the checkbox states."""
        checkbox_sent = self.table.cellWidget(row, 5)
        checkbox_paid = self.table.cellWidget(row, 6)

        if checkbox_sent and checkbox_paid:
            if checkbox_sent.isChecked() and checkbox_paid.isChecked():
                color = QColor(87, 242, 141, 127)  # Light green
            elif checkbox_sent.isChecked() or checkbox_paid.isChecked():
                color = QColor(241, 240, 133, 127)  # Light yellow
            else:
                color = QColor(251, 55, 107, 127)  # Light red
            
            # Update the row background color
            self.set_row_background_color(row, color)
            
            # Update the checkbox backgrounds to match the row background color
            self.update_checkbox_backgrounds(row, color)

    def update_checkbox_backgrounds(self, row, color):
        """Update the background color of all checkboxes in the specified row."""
        # Get the checkbox widgets for 'Invoice Sent' and 'Invoice Paid'
        checkbox_sent = self.table.cellWidget(row, 5)
        checkbox_paid = self.table.cellWidget(row, 6)

        # Update the stylesheet of each checkbox to match the new background color
        if checkbox_sent:
            checkbox_sent.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()});")
        if checkbox_paid:
            checkbox_paid.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()});")


    def set_row_background_color(self, row, color):
        """Set the background color of a row."""
        for column in range(self.table.columnCount()):
            item = self.table.item(row, column)
            if item is not None:
                item.setBackground(color)

    def update_company_id_editable(self):
        """Enable or disable the Company ID field based on the selected type."""
        self.company_id_input.setEnabled(self.type_input.currentText() == 'company')

    def sort_data(self):
        """Sort the data in the table based on the selected option."""
        self.current_sort_option = self.sort_dropdown.currentText()
        self.apply_current_sorting()

    def apply_current_sorting(self):
        """Apply the current sorting option to the table."""
        if self.current_sort_option == 'Default':
            self.sort_invoices()
            self.load_existing_invoices()
        else:
            column_index, ascending = 0, True
            if self.current_sort_option == 'Sort Name Asc':
                column_index, ascending = 0, True
            elif self.current_sort_option == 'Sort Name Desc':
                column_index, ascending = 0, False
            elif self.current_sort_option == 'Sort Date Asc':
                column_index, ascending = 3, True
            elif self.current_sort_option == 'Sort Date Desc':
                column_index, ascending = 3, False
            elif self.current_sort_option == 'Sort Amount Asc':
                column_index, ascending = 4, True
            elif self.current_sort_option == 'Sort Amount Desc':
                column_index, ascending = 4, False

            self.table.sortItems(column_index, order=Qt.AscendingOrder if ascending else Qt.DescendingOrder)
        self.update_all_row_colors()

    def update_all_row_colors(self):
        """Update the colors of all rows."""
        for row in range(self.table.rowCount()):
            self.update_row_color(row)

    def sort_invoices(self):
        """Sort invoices based on their status and other criteria."""
        def sort_key(invoice):
            return (
                (invoice.sent, invoice.paid),
                invoice.date,
                invoice.name.lower(),
                invoice.amount
            )

        with get_session() as session:
            self.invoices = [session.merge(inv) for inv in self.invoices]  # Reattach all invoices to session
            self.invoices.sort(key=sort_key)  # Sort invoices while they are attached to a session

    def reset_default_sorting(self):
        """Reset the sorting option to default."""
        self.sort_dropdown.setCurrentIndex(0)
        self.current_sort_option = 'Default'
        self.sort_invoices()
        self.load_existing_invoices()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InvoiceTab()
    window.show()
    sys.exit(app.exec_())
