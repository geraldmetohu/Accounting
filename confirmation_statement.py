import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QComboBox, QMessageBox, QScrollArea, QApplication, QPushButton, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from sqlalchemy.orm import joinedload
from models import Company, ConfirmationStatement, Files
from backend import get_session  # Ensure using the context manager from backend.py
import logging
from dateutil.relativedelta import relativedelta
import time  # Import the time module

# Set up logging
logging.basicConfig(level=logging.INFO)

COMPANY_CONFIRMATION_ROLE = Qt.UserRole + 1

class ConfirmationStatementTab(QWidget):
    status_changed = pyqtSignal()  # Signal to emit when status changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.updating_item = False  # Flag to prevent recursion
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Search and Sort Layout
        search_sort_layout = QHBoxLayout()

        self.search_label = QLabel('Search:')
        self.search_bar = QLineEdit()
        self.search_bar.textChanged.connect(self.search_data)
        search_sort_layout.addWidget(self.search_label)
        search_sort_layout.addWidget(self.search_bar)

        self.sort_dropdown = QComboBox()
        self.sort_dropdown.addItems([
            'Default', 'Sort ID Asc', 'Sort ID Desc',
            'Sort Name Asc', 'Sort Name Desc',
            'Sort Date Asc', 'Sort Date Desc'
        ])
        self.sort_dropdown.currentIndexChanged.connect(self.sort_data)
        search_sort_layout.addWidget(self.sort_dropdown)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.refresh_tabs)
        search_sort_layout.addWidget(self.refresh_button)

        main_layout.addLayout(search_sort_layout)

        # Table for Confirmation Statements
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Company Name',
            'Confirmation Date', 'Confirmation Status',
            'Invoice Check', 'Done Check'
        ])
        self.table.itemChanged.connect(self.check_item_changed)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.table)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        # Load data initially
        self.load_data()

    def load_data(self):
        """Load data from the database directly within the method and measure load time."""
        start_time = time.time()  # Start the timer
        print("Loading Confirmation 2:", datetime.now().strftime("%H:%M:%S"))

        self.table.setRowCount(0)  # Clear the table before loading new data
        try:
            with get_session() as session:
                confirmations = (
                    session.query(ConfirmationStatement)
                    .options(joinedload(ConfirmationStatement.company))  # Eagerly load the company relationship
                    .all()
                )

                self.table.setRowCount(len(confirmations))

                # Sort the confirmations based on the status priority
                status_priority = {
                    'Overdue': 0,
                    'Urgent': 1,
                    'Soon': 2,
                    'Early': 3
                }
                confirmations.sort(key=lambda x: status_priority.get(x.status, 4))

                # Block signals while populating the table to avoid unnecessary updates
                self.table.blockSignals(True)
                for row, confirmation in enumerate(confirmations):
                    self.add_confirmation_to_table(row, confirmation)
                self.table.blockSignals(False)

        except Exception as e:
            logging.exception("Failed to load data")
            QMessageBox.critical(self, 'Error', f'Failed to load data: {str(e)}')

        # Measure the time taken to load and populate the table
        end_time = time.time()  # Stop the timer
        print("Confirmation Statement 2:", datetime.now().strftime("%H:%M:%S"))
        print("Confirmation Statement Total: {:.2f} seconds".format(end_time - start_time))

    def add_confirmation_to_table(self, row, confirmation):
        """Add a confirmation entry to the table."""

        id_item = QTableWidgetItem(str(confirmation.company_id))
        id_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 0, id_item)

        name_item = QTableWidgetItem(confirmation.name)
        name_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 1, name_item)

        date_item = QTableWidgetItem(confirmation.date.strftime('%Y-%m-%d'))
        date_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 2, date_item)

        status_item = QTableWidgetItem(confirmation.status)
        status_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 3, status_item)

        invoice_check_item = self.create_checkbox_item(confirmation.invoice_check, confirmation.id)
        self.table.setItem(row, 4, invoice_check_item)

        done_check_item = self.create_checkbox_item(confirmation.done_check, confirmation.id)
        self.table.setItem(row, 5, done_check_item)

        self.set_row_color(row, confirmation.status)

    def create_checkbox_item(self, checked, confirmation_id):
        """Create a checkbox item."""
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        item.setData(COMPANY_CONFIRMATION_ROLE, confirmation_id)
        return item

    def sort_data(self):
        """Sort the data based on the selected option."""
        try:
            sort_option = self.sort_dropdown.currentText()
            column_index, ascending = 0, True
            if sort_option == 'Sort ID Asc':
                column_index, ascending = 0, True
            elif sort_option == 'Sort ID Desc':
                column_index, ascending = 0, False
            elif sort_option == 'Sort Name Asc':
                column_index, ascending = 1, True
            elif sort_option == 'Sort Name Desc':
                column_index, ascending = 1, False
            elif sort_option == 'Sort Date Asc':
                column_index, ascending = 2, True
            elif sort_option == 'Sort Date Desc':
                column_index, ascending = 2, False

            if sort_option != 'Default':
                self.table.sortItems(column_index, order=Qt.AscendingOrder if ascending else Qt.DescendingOrder)
            else:
                self.load_data()
        except Exception as e:
            logging.exception("Error occurred while sorting data")
            QMessageBox.critical(self, 'Error', f'Error occurred while sorting data: {str(e)}')

    def refresh(self):
        """Refresh the data in the table."""
        self.load_data()

    def refresh_tabs(self):
        """Refresh all tabs."""
        try:
            self.update_files_count()
            self.check_status()
            self.refresh()
        except Exception as e:
            logging.exception("Error occurred while refreshing tabs")
            QMessageBox.critical(self, 'Error', f'Error occurred while refreshing tabs: {str(e)}')

    def update_files_count(self):
        """Update the file count for each company."""
        try:
            with get_session() as session:
                companies = session.query(Company).all()
                for company in companies:
                    file_count = session.query(Files).filter_by(company_id=company.id).count()
                    company.files_count = file_count
                    session.add(company)  # Mark the company object as modified
                session.commit()  # Commit all changes
        except Exception as e:
            logging.exception("Error occurred while updating file counts")
            QMessageBox.critical(self, 'Error', f'An error occurred while updating file counts: {str(e)}')

    def search_data(self):
        """Search and highlight data in the table."""
        try:
            search_text = self.search_bar.text().lower()
            for row in range(self.table.rowCount()):
                match = False
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        original_color = item.data(Qt.UserRole)
                        if not original_color:
                            original_color = item.background()
                            item.setData(Qt.UserRole, original_color)

                        if search_text and search_text in item.text().lower():
                            item.setBackground(QColor(255, 255, 0, 127))  # light yellow with transparency
                            match = True
                        else:
                            item.setBackground(original_color)
                self.table.setRowHidden(row, not match if search_text else False)
        except Exception as e:
            logging.exception("Error occurred while searching data")
            QMessageBox.critical(self, 'Error', f'Error occurred while searching data: {str(e)}')

    def check_item_changed(self, item):
        """Handle checkbox item changes."""
        if self.updating_item:
            return
        if item.column() in [4, 5]:  # Invoice Check or Done Check columns
            try:
                confirmation_id = item.data(COMPANY_CONFIRMATION_ROLE)
                with get_session() as session:
                    confirmation = session.query(ConfirmationStatement).filter_by(id=confirmation_id).first()
                    if confirmation:
                        self.updating_item = True  # Prevent recursion
                        if item.column() == 4:
                            confirmation.invoice_check = item.checkState() == Qt.Checked
                        elif item.column() == 5:
                            confirmation.done_check = item.checkState() == Qt.Checked
                        session.commit()
                        self.updating_item = False  # Re-enable updates

                        if confirmation.invoice_check and confirmation.done_check:
                            response = QMessageBox.question(
                                self, 'Confirm',
                                'Both checks are marked. Do you want to update the confirmation date and reset the checks?',
                                QMessageBox.Yes | QMessageBox.No
                            )
                            if response == QMessageBox.Yes:
                                try:
                                    self.table.blockSignals(True)  # Temporarily disconnect the signal to prevent recursion

                                    new_date = confirmation.date + relativedelta(years=1)
                                    confirmation.date = new_date
                                    confirmation.invoice_check = False
                                    confirmation.done_check = False
                                    session.commit()

                                    self.load_data()
                                    self.check_status()
                                except Exception as e:
                                    logging.exception("Error updating confirmation date")
                                    QMessageBox.critical(self, "Error", f"Error updating confirmation date: {str(e)}")
                                finally:
                                    self.table.blockSignals(False)  # Reconnect the signal
            except Exception as e:
                logging.exception("Error handling item change")
                QMessageBox.critical(self, "Error", f"Error handling item change: {str(e)}")

    def check_status(self):
        """Check and update the status of confirmation statements."""
        try:
            with get_session() as session:
                confirmations = session.query(ConfirmationStatement).options(joinedload(ConfirmationStatement.company)).all()
                for confirmation in confirmations:
                    self.update_status(confirmation)
                session.commit()
            self.load_data()
        except Exception as e:
            logging.exception("Error occurred while checking status")
            QMessageBox.critical(self, "Error", f"Error occurred while checking status: {str(e)}")

    def set_row_color(self, row, status):
        """Set the background color of a row based on its status."""
        try:
            color_map = {
                'Overdue': QColor(251, 55, 107, 127),  # light red with transparency
                'Urgent': QColor(247, 131, 34, 127),   # light orange with transparency
                'Soon': QColor(241, 240, 133, 127),    # light yellow with transparency
                'Early': QColor(87, 242, 141, 127)     # light green with transparency
            }
            color = color_map.get(status, QColor(255, 255, 255, 127))  # default to white with transparency

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(color)
                    item.setData(Qt.UserRole, color)  # Store the color
        except Exception as e:
            logging.exception("Error occurred while setting row color")
            QMessageBox.critical(self, "Error", f"Error occurred while setting row color: {str(e)}")

    def update_status(self, confirmation):
        """Update the status of a confirmation based on the date."""
        today = datetime.now().date()
        days_diff = (confirmation.date - today).days
        if days_diff > 7:
            confirmation.status = 'Early'
        elif 3 <= days_diff <= 7:
            confirmation.status = 'Soon'
        elif 3 <= days_diff <= 0:
            confirmation.status = 'Urgent'
        else:
            confirmation.status = 'Overdue'

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)

    tab_widget = ConfirmationStatementTab()
    layout.addWidget(tab_widget)

    window.setLayout(layout)
    window.show()

    sys.exit(app.exec_())
