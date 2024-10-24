import logging
import sys
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QComboBox, QPushButton, QMessageBox, QScrollArea, QApplication, QTabWidget, QCheckBox, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from sqlalchemy import and_
from employer_tab import EmployersTab  # Ensure this import matches the correct file name
from models import Company, Files, PayRun  # Import the necessary models
from backend import get_session  # Corrected to use context manager from backend
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import joinedload

logging.basicConfig(level=logging.INFO)

COMPANY_PAYRUN_ROLE = Qt.UserRole + 1

class PayRunTab(QWidget):
    status_changed = pyqtSignal()  # Signal to emit when status changes

    def __init__(self, tab_widget, parent=None):
        super().__init__(parent)
        self.tab_widget = tab_widget
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
            'Sort Company Name Asc', 'Sort Company Name Desc',
            'Sort Date Asc', 'Sort Date Desc'
        ])
        self.sort_dropdown.currentIndexChanged.connect(self.sort_data)
        search_sort_layout.addWidget(self.sort_dropdown)

        self.p60_button_button = QPushButton("Clear P60")
        self.p60_button_button.setMinimumHeight(40)
        self.p60_button_button.clicked.connect(self.clear_p60)
        search_sort_layout.addWidget(self.p60_button_button)

        main_layout.addLayout(search_sort_layout)

        # Table for Pay Runs
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Id', 'Company Name', 'Date', 'Status',
            'Month Check', 'Pay Run', 'P60', 'Files Count','UTR'
        ])

        # Button Layout
        button_layout = QHBoxLayout()
        self.view_employers_button = QPushButton('View Employers')
        self.view_employers_button.clicked.connect(self.view_employers)
        button_layout.addWidget(self.view_employers_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.refresh_tabs)
        button_layout.addWidget(self.refresh_button)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.table)

        main_layout.addWidget(scroll_area)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        self.load_data()

    def sort_data(self):
        """Sort data in the table based on user selection."""
        sort_option = self.sort_dropdown.currentText()
        column_index, ascending = 0, True
        if sort_option == 'Sort ID Asc':
            column_index, ascending = 0, True
        elif sort_option == 'Sort ID Desc':
            column_index, ascending = 0, False
        elif sort_option == 'Sort Company Name Asc':
            column_index, ascending = 1, True
        elif sort_option == 'Sort Company Name Desc':
            column_index, ascending = 1, False
        elif sort_option == 'Sort Date Asc':
            column_index, ascending = 2, True
        elif sort_option == 'Sort Date Desc':
            column_index, ascending = 2, False

        if sort_option != 'Default':
            self.table.sortItems(column_index, order=Qt.AscendingOrder if ascending else Qt.DescendingOrder)
        else:
            # If "Default" is selected, load data with status-based sorting
            self.load_data()

    def refresh(self):
        """Refresh the table data."""
        self.load_data()

    def refresh_tabs(self):
        """Refresh all tabs and update file counts."""
        self.update_files_count()
        self.refresh()
        if hasattr(self, 'tab_widget'):
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, 'refresh') and tab != self:
                    tab.refresh()

    def load_data(self):
        """Load data from the database and populate the table, sorted by status by default."""
        start_time = time.time()  # Record the start time
        print("Payrun time 1:", datetime.now().strftime("%H:%M:%S"))
        

        self.table.setRowCount(0)  # Clear the table before loading new data
        try:
            with get_session() as session:
                payruns = (
                    session.query(PayRun)
                    .options(joinedload(PayRun.company))  # Eagerly load the company relationship
                    .all()
                )

                self.table.setRowCount(len(payruns))

                # Sort the confirmations based on the status priority
                status_priority = {
                    'Overdue': 0,
                    'Urgent': 1,
                    'Soon': 2,
                    'Early': 3
                }
                payruns.sort(key=lambda x: status_priority.get(x.status, 5))

                # Block signals while populating the table to avoid unnecessary updates
                self.table.blockSignals(True)
                for row, payrun in enumerate(payruns):
                    self.add_payrun_to_table(row, payrun)
                self.table.blockSignals(False)

        except Exception as e:
            logging.exception("Failed to load data")
            QMessageBox.critical(self, 'Error', f'Failed to load data: {str(e)}')

        print("Payrun time 2:", datetime.now().strftime("%H:%M:%S"))
        end_time = time.time()  # Record the end time
        print("PAYRUN Total : {:.2f} seconds".format(end_time - start_time))

    def add_payrun_to_table(self, row, payrun):
        """Add an payrun entry to the table."""

        id_item = QTableWidgetItem(str(payrun.id))
        id_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 0, id_item)

        name_item = QTableWidgetItem(payrun.company_name)
        name_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 1, name_item)

        date_item = QTableWidgetItem(payrun.date.strftime('%Y-%m-%d'))
        date_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 2, date_item)

        status_item = QTableWidgetItem(payrun.status)
        status_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 3, status_item)

        month_check_item = self.create_checkbox_item(payrun.month_check, payrun.id)
        self.table.setItem(row, 4, month_check_item)

        payrun_check_item = self.create_checkbox_item(payrun.pay_run, payrun.id)
        self.table.setItem(row, 5, payrun_check_item)

        p60_check_item = self.create_checkbox_item(payrun.p60, payrun.id)
        self.table.setItem(row, 6, p60_check_item)

        files_item = QTableWidgetItem(payrun.files_count)
        files_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 7, files_item)

        utr_item = QTableWidgetItem(str(payrun.company_id))
        utr_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 8, utr_item)

        self.set_row_color(row, payrun.status)
       
    def check_item_changed(self, item):
        """Handle checkbox item changes."""
        if self.updating_item:
            return
        if item.column() in [4,5,6]:  # Invoice Check or Done Check columns
            try:
                payrun_id = item.data(COMPANY_PAYRUN_ROLE)
                with get_session() as session:
                    payrun = session.query(PayRun).filter_by(id=payrun_id).first()
                    if payrun:
                        self.updating_item = True  # Prevent recursion
                        if item.column() == 4:
                            payrun.month_check = item.checkState() == Qt.Checked
                        elif item.column() == 5:
                            payrun.pay_run = item.checkState() == Qt.Checked
                        elif item.column() == 6:
                            payrun.p60 = item.checkState() == Qt.Checked
                        session.commit()
                        self.updating_item = False  # Re-enable updates

                        if payrun.month_check and payrun.pay_run:
                            response = QMessageBox.question(
                                self, 'Confirm',
                                'Both checks are marked. Do you want to update the Payrun date and reset the checks?',
                                QMessageBox.Yes | QMessageBox.No
                            )
                            if response == QMessageBox.Yes:
                                try:
                                    self.table.blockSignals(True)  # Temporarily disconnect the signal to prevent recursion

                                    # Update the date by adding one month
                                    payrun.date += relativedelta(months=1)
                                    # Reset the checkboxes
                                    payrun.month_check = False
                                    payrun.pay_run = False

                                    session.commit()

                                    self.load_data()
                                    self.check_status()
                                except Exception as e:
                                    logging.exception("Error updating payrun date")
                                    QMessageBox.critical(self, "Error", f"Error updating payrun date: {str(e)}")
                                finally:
                                    self.table.blockSignals(False)  # Reconnect the signal
            except Exception as e:
                logging.exception("Error handling item change")
                QMessageBox.critical(self, "Error", f"Error handling item change: {str(e)}")

    def create_checkbox_item(self, checked, payrun_id):
        """Create a checkbox item."""
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        item.setData(COMPANY_PAYRUN_ROLE, payrun_id)
        return item
    
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

    def update_status(self, payrun):
        """Update the status of a payrun based on the date."""
        today = datetime.now().date()
        days_diff = (payrun.date - today).days
        if days_diff > 7:
            payrun.status = 'Early'
        elif 3 <= days_diff <= 7:
            payrun.status = 'Soon'
        elif 3 <= days_diff <= 0:
            payrun.status = 'Urgent'
        else:
            payrun.status = 'Overdue'

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

    def update_files_count(self):
        """Update the files count for each pay run."""
        try:
            with get_session() as session:  # Use context manager for session
                payruns = session.query(PayRun).all()
                for payrun in payruns:
                    file_count = session.query(Files).filter(
                        and_(Files.company_id == payrun.company_id, Files.second_id == 'Payrun')
                    ).count()
                    payrun.files_count = file_count
                session.commit()  # Commit all changes
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while updating file counts: {str(e)}')

    def check_status(self):
        """Check and update the status of payruns."""
        try:
            with get_session() as session:
                payruns = session.query(PayRun).all()
                for payrun in payruns:
                    self.update_status(payrun)
                session.commit()
            self.load_data()  # Refresh the table after status updates
        except Exception as e:
            logging.exception("Error occurred while checking status")
            QMessageBox.critical(self, "Error", f"Error occurred while checking status: {str(e)}")

    def view_employers(self):
        """Open the EmployersTab for the selected company based on payrun.company_id."""
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            try:
                # Get the company_id from the selected row
                company_id_item = self.table.item(selected_row, 0)  # Assuming column 0 has the company ID
                if company_id_item is None:
                    QMessageBox.warning(self, "Invalid Selection", "Please select a valid company.")
                    return

                company_id = int(company_id_item.text())

                # Open the EmployersTab regardless of whether employers are found
                employer_tab = EmployersTab(company_id, self.tab_widget)
                self.tab_widget.addTab(employer_tab, f"Employers of Company {company_id}")
                self.tab_widget.setCurrentWidget(employer_tab)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while opening the Employers tab: {e}")
                print(f"Error while opening EmployersTab: {e}")
   
    def clear_p60(self):
        """Set all p60 values to False in the database and update the table with 2-step confirmation."""
        
        # Step 1: First confirmation dialog
        first_confirmation = QMessageBox.question(
            self, 
            "Clear All P60", 
            "Are you sure you want to clear all P60 values?",
            QMessageBox.Yes | QMessageBox.No
        )

        if first_confirmation == QMessageBox.No:
            return  # User canceled the operation, exit the method
        
        # Step 2: Second confirmation dialog
        second_confirmation = QMessageBox.question(
            self, 
            "Final Confirmation", 
            "This action cannot be undone. Are you absolutely sure?",
            QMessageBox.Yes | QMessageBox.No
        )

        if second_confirmation == QMessageBox.Yes:
            # Proceed with clearing p60 if user confirms
            try:
                with get_session() as session:
                    # Fetch all PayRun records from the database
                    payruns = session.query(PayRun).all()

                    # Set p60 to False for each PayRun
                    for payrun in payruns:
                        payrun.p60 = False

                    # Commit the changes to the database
                    session.commit()

                    # Now update the table in the app to reflect this change
                    self.update_all_p60_in_table()

            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to clear p60: {str(e)}')
        else:
            return  # User canceled the operation after the second confirmation
    
    def update_all_p60_in_table(self):
        """Update all p60 values in the table to reflect the changes."""
        for row in range(self.table.rowCount()):
            # Set the p60 checkbox to unchecked (False)
            p60_check_item = self.table.cellWidget(row, 6)
            if p60_check_item:
                p60_check_item.setChecked(False)



#old

    def get_row_by_payrun_id(self, payrun_id):
        """Find the table row corresponding to the given payrun ID."""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0) and int(self.table.item(row, 0).text()) == payrun_id:  # Now uses payrun.id
                return row
        logging.warning(f"Payrun with ID {payrun_id} not found in the table.")
        return None

    def create_noneditable_item(self, text):
        """Create a non-editable QTableWidgetItem."""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
    
    def update_status_and_color_by_payrun(self, payrun_id):
        """Update status and color for a specific payrun entry."""
        with get_session() as session:
            payrun = session.query(PayRun).get(payrun_id)  # Always fetch the object within the session
            if not payrun:
                logging.error(f"Payrun with ID {payrun_id} not found.")
                return

            status = payrun.status
            row = self.get_row_by_payrun_id(payrun_id)
            if row is not None:  # Ensure row exists before trying to update UI
                self.set_row_color(row, status)
                self.update_checkbox_background(row, status)

    def update_checkbox_background(self, row, status):
        """Update checkbox background color based on status."""
        if row is None:  # Handle invalid row
            logging.warning(f"Row not found for the given payrun. Cannot update checkbox background.")
            return

        color_map = {
            'Overdue': QColor(251, 55, 107, 127),
            'Urgent': QColor(247, 131, 34, 127),
            'Soon': QColor(241, 240, 133, 127),
            'Early': QColor(87, 242, 141, 127)
        }
        color = color_map.get(status, QColor(255, 255, 255, 127))

        for col in [4, 5, 6]:  # Columns for checkboxes
            item = self.table.cellWidget(row, col)
            if item:
                item.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha() / 255.0});")

    def update_row_in_table(self, payrun):
        """Update the specific row in the table with the updated payrun data."""
        row = self.get_row_by_payrun_id(payrun.id)
        if row is None:
            logging.error(f"Payrun with ID {payrun.id} not found in the table.")
            return

        # Update the date and status in the table
        self.table.setItem(row, 2, self.create_noneditable_item(payrun.date.strftime('%Y-%m-%d')))
        self.table.setItem(row, 3, self.create_noneditable_item(payrun.status))

        # Update the checkboxes in the table (uncheck both after the update)
        month_check_item = self.table.cellWidget(row, 4)
        if isinstance(month_check_item, QCheckBox):
            month_check_item.setChecked(payrun.month_check)

        payrun_check_item = self.table.cellWidget(row, 5)
        if isinstance(payrun_check_item, QCheckBox):
            payrun_check_item.setChecked(payrun.pay_run)

        # Update the row color based on the status
        self.set_row_color(row, payrun.status)
        self.update_checkbox_background(row, payrun.status)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()
    main_layout = QVBoxLayout(main_window)

    tab_widget = QTabWidget()
    main_layout.addWidget(tab_widget)

    pay_run_tab = PayRunTab(tab_widget)
    tab_widget.addTab(pay_run_tab, "Pay Runs")

    main_window.setLayout(main_layout)
    main_window.show()

    sys.exit(app.exec_())
