import logging
import sys
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QComboBox, QPushButton, QMessageBox, QScrollArea, QApplication, QCheckBox, QHeaderView
)
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtGui import QColor
from sqlalchemy import and_
from models import Company, Account, Files  # Import the necessary models
from backend import get_session  # Ensure correct import for SQLAlchemy session handling
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import joinedload

logging.basicConfig(level=logging.INFO)

COMPANY_ACCOUNT_ROLE = Qt.UserRole + 1

class AccountTab(QWidget):
    status_changed = pyqtSignal()  # Signal to emit when status changes

    def __init__(self ,parent=None):
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
            'Sort Office Asc', 'Sort Office Desc',
            'Sort Date Asc', 'Sort Date Desc'
        ])
        self.sort_dropdown.currentIndexChanged.connect(self.sort_data)
        search_sort_layout.addWidget(self.sort_dropdown)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.refresh)
        search_sort_layout.addWidget(self.refresh_button)

        main_layout.addLayout(search_sort_layout)

        # Table for Accounts
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            'Id', 'Company Name', 'Account Office Number', 'Account Date',
            'Status', 'Email Check', 'Invoice Check', 'Done Check', 'Files Count', 'UTR'
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
        """Sort data in the table based on user selection."""
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
            elif sort_option == 'Sort Office Asc':
                column_index, ascending = 2, True
            elif sort_option == 'Sort Office Desc':
                column_index, ascending = 2, False
            elif sort_option == 'Sort Date Asc':
                column_index, ascending = 3, True
            elif sort_option == 'Sort Date Desc':
                column_index, ascending = 3, False

            if sort_option != 'Default':
                self.table.sortItems(column_index, order=Qt.AscendingOrder if ascending else Qt.DescendingOrder)
            else:
                # If "Default" is selected, load data with status-based sorting
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
        print("Account time 1:", datetime.now().strftime("%H:%M:%S"))
        
        """Load data from the database and populate the table, sorted by status by default."""

        self.table.setRowCount(0)  # Clear the table before loading new data
        try:
            with get_session() as session:
                accounts = (
                    session.query(Account)
                    .options(joinedload(Account.company))  # Eagerly load the company relationship
                    .all()
                )

                self.table.setRowCount(len(accounts))

                # Sort the confirmations based on the status priority
                status_priority = {
                    'Overdue': 0,
                    'Urgent': 1,
                    'Soon': 2,
                    'Early': 3
                }
                accounts.sort(key=lambda x: status_priority.get(x.status, 5))

                # Block signals while populating the table to avoid unnecessary updates
                self.table.blockSignals(True)
                for row, account in enumerate(accounts):
                    self.add_account_to_table(row, account)
                self.table.blockSignals(False)

        except Exception as e:
            logging.exception("Failed to load data")
            QMessageBox.critical(self, 'Error', f'Failed to load data: {str(e)}')

        
        print("Account time 2:", datetime.now().strftime("%H:%M:%S"))
        end_time = time.time()  # Record the end time
        print("Account Total : {:.2f} seconds".format(end_time - start_time))

    def add_account_to_table(self, row, account):
        company =account.company
        id_item = QTableWidgetItem(str(account.id))
        id_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 0, id_item)

        name_item = QTableWidgetItem(account.name)
        name_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 1, name_item)

        a_office_nr_item = QTableWidgetItem(company.account_office_number)
        a_office_nr_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 2, a_office_nr_item)

        date_item = QTableWidgetItem(account.date.strftime('%Y-%m-%d'))
        date_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 3, date_item)

        status_item = QTableWidgetItem(account.status)
        status_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 4, status_item)

        email_check_item = self.create_checkbox_item(account.email_check, account.id)
        self.table.setItem(row, 5, email_check_item)

        invoice_check_item = self.create_checkbox_item(account.invoice_check, account.id)
        self.table.setItem(row, 6, invoice_check_item)

        done_check_item = self.create_checkbox_item(account.done_check, account.id)
        self.table.setItem(row, 7, done_check_item)

        file_item = QTableWidgetItem(str(account.files_count))
        file_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 8, file_item)

        utr_item = QTableWidgetItem(str(account.company_id))
        utr_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row, 9, utr_item)

        self.set_row_color(row, account.status)
       
    def create_checkbox_item(self, checked, account_id):
        """Create a checkbox item."""
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        item.setData(COMPANY_ACCOUNT_ROLE, account_id)
        return item
    
    def check_item_changed(self, item):
        """Handle checkbox item changes."""
        if self.updating_item:
            return
        if item.column() in [5,6,7]:  # Invoice Check or Done Check columns
            try:
                account_id = item.data(COMPANY_ACCOUNT_ROLE)
                with get_session() as session:
                    account = session.query(Account).filter_by(id=account_id).first()
                    if account:
                        self.updating_item = True  # Prevent recursion
                        if item.column() == 5:
                            account.email_check = item.checkState() == Qt.Checked
                        elif item.column() == 6:
                            account.invoice_check = item.checkState() == Qt.Checked
                        elif item.column() == 7:
                            account.done_check = item.checkState() == Qt.Checked
                        session.commit()
                        self.updating_item = False  # Re-enable updates

                        if account.email_check and account.invoice_check and account.done_check:
                            response = QMessageBox.question(
                                self, 'Confirm',
                                'Both checks are marked. Do you want to update the confirmation date and reset the checks?',
                                QMessageBox.Yes | QMessageBox.No
                            )
                            if response == QMessageBox.Yes:
                                try:
                                    self.table.blockSignals(True)  # Temporarily disconnect the signal to prevent recursion

                                    account.date += relativedelta(years=1)
                                    # Reset the checkboxes
                                    account.email_check = False
                                    account.invoice_check = False
                                    account.done_check = False

                                    session.commit()

                                    self.load_data()
                                    self.check_status()
                                except Exception as e:
                                    logging.exception("Error updating account date")
                                    QMessageBox.critical(self, "Error", f"Error updating account date: {str(e)}")
                                finally:
                                    self.table.blockSignals(False)  # Reconnect the signal
            except Exception as e:
                logging.exception("Error handling item change")
                QMessageBox.critical(self, "Error", f"Error handling item change: {str(e)}")

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

    def check_status(self):
        """Check and update the status of accounts."""
        try:
            with get_session() as session:
                accounts = session.query(Account).all()
                for account in accounts:
                    self.update_status(account)
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

    def update_status(self, account):
        """Update the status of an account based on the date."""
        today = datetime.now().date()
        days_diff = (account.date - today).days
        if days_diff > 7:
            account.status = 'Early'
        elif 3 <= days_diff <= 7:
            account.status = 'Soon'
        elif 3 <= days_diff <= 0:
            account.status = 'Urgent'
        else:
            account.status = 'Overdue'

    def update_files_count(self):
        """Update the files count for each account."""
        try:
            with get_session() as session:
                accounts = session.query(Account).all()
                for account in accounts:
                    file_count = session.query(Files).filter(
                        and_(Files.company_id == account.company_id, Files.second_id == 'Account')
                    ).count()
                    account.files_count = file_count
                session.commit()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while updating file counts: {str(e)}')




   # def refresh_tabs(self):
    #    """Refresh all tabs and update file counts."""
      #   self.update_files_count()
       # self.refresh()
 #       if hasattr(self, 'tab_widget'):
  #          for i in range(self.tab_widget.count()):
   #             tab = self.tab_widget.widget(i)
    #            if hasattr(tab, 'refresh') and tab != self:
     #               tab.refresh()


#old

    def confirm_and_update_account(self, account):
        """Confirm and update account date if all checks are checked."""
        confirmation = QMessageBox.question(
            self,
            "Confirm Update",
            "All checks are true. Do you want to update the account date by adding one year and reset the checks?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmation == QMessageBox.Yes:
            try:
                with get_session() as session:
                    # Update the date by adding one year
                    account.date += relativedelta(years=1)
                    # Reset the checkboxes
                    account.email_check = False
                    account.invoice_check = False
                    account.done_check = False

                    # Update the status based on the new date
                    self.update_status(account)

                    # Commit the changes to the database
                    session.commit()

                    # Update the specific row in the table
                    self.update_row_in_table(account)

            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to update account: {str(e)}')

    def update_row_in_table(self, account):
        """Update the specific row in the table with the updated account data."""
        row = self.get_row_by_account_id(account.id)
        if row is None:
            logging.error(f"Account with ID {account.id} not found in the table.")
            return

        # Update the date and status in the table
        self.table.setItem(row, 3, self.create_noneditable_item(account.date.strftime('%Y-%m-%d')))
        self.table.setItem(row, 4, self.create_noneditable_item(account.status))


        email_check_item = self.table.cellWidget(row, 5)
        if isinstance(email_check_item, QCheckBox):
            email_check_item.setChecked(account.email_check)

        invoice_check_item = self.table.cellWidget(row, 6)
        if isinstance(invoice_check_item, QCheckBox):
            invoice_check_item.setChecked(account.invoice_check)
        
        done_check_item = self.table.cellWidget(row, 7)
        if isinstance(done_check_item, QCheckBox):
            done_check_item.setChecked(account.done_check)

        # Update the row color based on the status
        self.set_row_color(row, account.status)
        self.update_checkbox_background(row, account.status)

    def update_checkbox_state(self, row, column, state):
        """Helper function to update checkbox state."""
        checkbox = self.table.cellWidget(row, column)
        if isinstance(checkbox, QCheckBox):
            checkbox.setChecked(state)

    def update_status_and_color_by_account(self, account_id):
        """Update status and color for a specific account entry."""
        with get_session() as session:
            account = session.query(Account).get(account_id)
            if not account:
                logging.error(f"Account with ID {account_id} not found.")
                return

            status = account.status
            row = self.get_row_by_account_id(account_id)
            if row is not None:
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

        for col in [5, 6, 7]:  # Columns for checkboxes
            item = self.table.cellWidget(row, col)
            if item:
                item.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha() / 255.0});")


    def get_row_by_account_id(self, account_id):

        """Find the table row corresponding to the given account ID."""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0) and int(self.table.item(row, 0).text()) == account_id:  # Now uses payrun.id
                return row
        logging.warning(f"Account with ID {account_id} not found in the table.")
        return None

    def create_noneditable_item(self, text):
        """Create a non-editable QTableWidgetItem."""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)

    account_tab = AccountTab()
    layout.addWidget(account_tab)

    window.setLayout(layout)
    window.show()

    sys.exit(app.exec_())
