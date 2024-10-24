import calendar
import logging
import time  # Import time module for measuring execution time
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QComboBox, QMessageBox, QScrollArea, QPushButton, QApplication, QCheckBox, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from models import Company, CIS, Files
from backend import get_session  # Use the context manager for session handling
from datetime import date, datetime, timedelta
from sqlalchemy.orm import joinedload


logging.basicConfig(level=logging.INFO)

COMPANY_CIS_ROLE = Qt.UserRole + 1

class CISTab(QWidget):
    status_changed = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.updating_item = False  # Prevent recursion flag
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
            'Default', 'Sort UTR Asc', 'Sort UTR Desc',
            'Sort Name Asc', 'Sort Name Desc',
            'Sort Last Month Asc', 'Sort Last Month Desc',
            'Sort Next Month Asc', 'Sort Next Month Desc'
        ])
        self.sort_dropdown.currentIndexChanged.connect(self.sort_data)
        search_sort_layout.addWidget(self.sort_dropdown)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.refresh)
        search_sort_layout.addWidget(self.refresh_button)

        main_layout.addLayout(search_sort_layout)

        # Table for CIS Records
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Company ID', 'Company Name', 'Employees Reference',
            'CIS Last Month', 'CIS Next Month', 'Email Check', 'Month Check', 'Status'
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

        self.load_data()

    def sort_data(self):
        try:
            sort_option = self.sort_dropdown.currentText()
            column_index, ascending = 0, True
            if sort_option == 'Sort UTR Asc':
                column_index, ascending = 0, True
            elif sort_option == 'Sort UTR Desc':
                column_index, ascending = 0, False
            elif sort_option == 'Sort Name Asc':
                column_index, ascending = 2, True
            elif sort_option == 'Sort Name Desc':
                column_index, ascending = 2, False
            elif sort_option == 'Sort Last Month Asc':
                column_index, ascending = 4, True
            elif sort_option == 'Sort Last Month Desc':
                column_index, ascending = 4, False
            elif sort_option == 'Sort Next Month Asc':
                column_index, ascending = 5, True
            elif sort_option == 'Sort Next Month Desc':
                column_index, ascending = 5, False

            if sort_option != 'Default':
                self.table.sortItems(column_index, order=Qt.AscendingOrder if ascending else Qt.DescendingOrder)
            else:
                self.load_data()
        except Exception as e:
            logging.exception("Error occurred while sorting data")
            QMessageBox.critical(self, 'Error', f'Error occurred while sorting data: {str(e)}')

    def refresh(self):
        """Refresh the table data."""
        self.load_data()

    def load_data(self):
        """Load data from the database and populate the table."""
        start_time = time.time()  # Record the start time
        print("CIS 1:", datetime.now().strftime("%H:%M:%S"))
        
        self.table.setRowCount(0)
        try:
            with get_session() as session:
                #companies_with_cis = session.query(CIS).all()
                companies_with_cis = (
                    session.query(CIS)
                    .options(joinedload(CIS.company))  # Eagerly load the company relationship
                    .all()
                )

                self.table.setRowCount(len(companies_with_cis))

                status_priority = {
                    'Overdue': 0,
                    'Urgent': 1,
                    'Soon': 2,
                    'Early': 3
                }
                companies_with_cis.sort(key=lambda x: status_priority.get(x.status, 9))

                self.table.blockSignals(True)
                for row, cis in enumerate(companies_with_cis):
                    self.add_cis_to_table(row, cis)
                self.table.blockSignals(False)

        except Exception as e:
            logging.exception("Failed to load data")
            QMessageBox.critical(self, 'Error', f'Failed to load data: {str(e)}')

        print("CIS 2:", datetime.now().strftime("%H:%M:%S"))
        end_time = time.time()  # Record the end time
        print("Total CIS: {:.2f} seconds".format(end_time - start_time))

    def add_cis_to_table(self, row, cis):
        id_item = QTableWidgetItem(str(cis.id))
        id_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 0, id_item)

        c_id_item = QTableWidgetItem(str(cis.company_id))
        c_id_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 1, c_id_item)

        c_name = QTableWidgetItem(str(cis.name))
        c_name.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 2, c_name)

        emp_ref = QTableWidgetItem(str(cis.employees_reference))
        emp_ref.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 3, emp_ref)

        last_date_item = QTableWidgetItem(cis.last_month.strftime('%Y-%m-%d'))
        last_date_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 4, last_date_item)

        next_date_itme = QTableWidgetItem(cis.next_month.strftime('%Y-%m-%d'))
        next_date_itme.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 5, next_date_itme)

        email_check_item = self.create_checkbox_item(cis.email_check, cis.id)
        self.table.setItem(row, 6, email_check_item)

        month_check_item = self.create_checkbox_item(cis.month_check, cis.id)
        self.table.setItem(row, 7, month_check_item)

        status_item = QTableWidgetItem(cis.status)
        status_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 8, status_item)

        self.set_row_color(row, cis.status)

    def create_checkbox_item(self, checked, cis_id):
        """Create a checkbox item."""
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        item.setData(COMPANY_CIS_ROLE, cis_id)
        return item

    def check_item_changed(self, item):
        """Handle checkbox state changes."""
        if self.updating_item:
            return
        if item.column() in [6,7]:
            try:
                cis_id = item.data(COMPANY_CIS_ROLE)
                with get_session() as session:
                    # Re-fetch the CIS object within an active session
                    cis = session.query(CIS).filter_by(id=cis_id).first()
                    if  cis:
                        self.updating_item = True  # Prevent recursion
                        if item.column() == 6:
                            cis.email_check = item.checkState() == Qt.Checked
                        elif item.column() == 7:
                            cis.month_check = item.checkState() == Qt.Checked
                        session.commit()
                        self.updating_item = False  # Re-enable updates

                        if cis.email_check and cis.month_check:
                            response = QMessageBox.question(
                                self, 'Confirm',
                                'Both checks are marked. Do you want to update the CIS date and reset the checks?',
                                QMessageBox.Yes | QMessageBox.No
                            )
                            if response == QMessageBox.Yes:
                                try:
                                    self.table.blockSignals(True)  # Temporarily disconnect the signal to prevent recursion

                                    
                                    next_month = cis.next_month
                                    new_last_month = next_month
                                    new_next_month = self.add_months(next_month, 1)
                                    
                                    cis.last_month = new_last_month
                                    cis.next_month = new_next_month
                                    cis.email_check = False
                                    cis.month_check = False

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

    def search_data(self):
        """Search data in the table based on user input."""
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
                        item.setBackground(QColor(255, 255, 0, 127))
                        match = True
                    else:
                        item.setBackground(original_color)
            self.table.setRowHidden(row, not match if search_text else False)

    def add_months(self, source_date, months):
        """Add a specified number of months to a date."""
        month = source_date.month - 1 + months
        year = int(source_date.year + month / 12)
        month = month % 12 + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    def check_status(self):
        """Check and update the status of confirmation statements."""
        try:
            with get_session() as session:
                cises = session.query(CIS).options(joinedload(CIS.company)).all()
                for cis in cises:
                    self.update_status(cis)
                session.commit()
            self.load_data()
        except Exception as e:
            logging.exception("Error occurred while checking status")
            QMessageBox.critical(self, "Error", f"Error occurred while checking status: {str(e)}")

    def update_status(self, cis):
        """Update the status of a confirmation based on the date."""
        today = datetime.now().date()
        days_diff = (cis.next_month - today).days
        if days_diff > 7:
            cis.status = 'Early'
        elif 3 <= days_diff <= 7:
            cis.status = 'Soon'
        elif 3 <= days_diff <= 0:
            cis.status = 'Urgent'
        else:
            cis.status = 'Overdue'

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
                    item.setData(Qt.UserRole, color)  # Store the original color
        except Exception as e:
            logging.exception("Error occurred while setting row color")
            QMessageBox.critical(self, "Error", f"Error occurred while setting row color: {str(e)}")

#old
    def update_status_and_color(self, row, cis):
        """Update the status and color of a CIS entry in the table."""
        today = date.today()
        status = "Early"
        if cis.next_month <= today:
            status = "Overdue"
        elif cis.next_month <= today + timedelta(days=3):
            status = "Urgent"
        elif cis.next_month <= today + timedelta(days=7):
            status = "Soon"

        self.table.setItem(row, 8, self.create_noneditable_item(status))
        self.set_row_color(row, status)
        self.update_checkbox_background(row, status)

    def update_status_and_color_by_cis(self, cis_id):
        """Update status and color for a specific CIS entry."""
        with get_session() as session:
            cis = session.query(CIS).get(cis_id)
            if not cis:
                return

            today = date.today()
            status = "Early"
            if cis.next_month <= today:
                status = "Overdue"
            elif cis.next_month <= today + timedelta(days=3):
                status = "Urgent"
            elif cis.next_month <= today + timedelta(days=7):
                status = "Soon"
            cis.status = status
            session.commit()

            # Update the table view
            companies_with_cis = session.query(Company).filter(Company.cis == True).all()
            for row, company in enumerate(companies_with_cis):
                if company.id == cis.company_id:
                    self.update_status_and_color(row, cis)

    def update_checkbox_background(self, row, status):
        """Update checkbox background color based on status."""
        color_map = {
            'Overdue': QColor(251, 55, 107, 127),
            'Urgent': QColor(247, 131, 34, 127),
            'Soon': QColor(241, 240, 133, 127),
            'Early': QColor(87, 242, 141, 127)
        }
        color = color_map.get(status, QColor(255, 255, 255, 127))

        for col in [6, 7]:  # Columns for checkboxes
            item = self.table.cellWidget(row, col)
            if item:
                item.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha() / 255.0});")
    def create_noneditable_item(self, text):
        """Create a non-editable QTableWidgetItem."""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)

    cis_tab = CISTab()
    layout.addWidget(cis_tab)

    window.setLayout(layout)
    window.show()

    sys.exit(app.exec_())
