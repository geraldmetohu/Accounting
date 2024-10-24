from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QScrollArea, QApplication, QTabWidget, QDateEdit, QHeaderView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import logging
from sqlalchemy.exc import IntegrityError
from models import Employer  # Import the Employer model class
from backend import get_session, get_employers_by_company_id, delete_employer  # Import session management and CRUD functions
import sys

class EmployersTab(QWidget):
    def __init__(self, company_id, tab_widget, parent=None):
        super().__init__(parent)
        self.company_id = company_id  # Store company_id for CRUD operations
        self.tab_widget = tab_widget
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Buttons for actions
        button_layout = QHBoxLayout()
        self.add_button = QPushButton('Add')
        self.add_button.clicked.connect(self.add_row)
        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save_data)
        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete_row)
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.close_tab)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.close_button)

        main_layout.addLayout(button_layout)

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # No need for a company_id column
        self.table.setHorizontalHeaderLabels([
            'Name', 'Email', 'UTR', 'NINO', 'Start Date'
        ])
        self.table.itemChanged.connect(self.handle_item_changed)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.load_data()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.table)

        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def load_data(self):
        """Load employer data from the database and populate the table."""
        self.table.blockSignals(True)  # Prevent signals while loading data
        self.table.setRowCount(0)  # Clear table

        try:
            with get_session() as session:
                employers = session.query(Employer).filter_by(company_id=self.company_id).all()  # Ensure correct session context
                self.table.setRowCount(len(employers))

                for row, employer in enumerate(employers):
                    # Populate table with employer data
                    name_item = QTableWidgetItem(employer.name)
                    email_item = QTableWidgetItem(employer.email)
                    utr_item = QTableWidgetItem(employer.utr or "")
                    nino_item = QTableWidgetItem(employer.nino)

                    # Set table items
                    self.table.setItem(row, 0, name_item)
                    self.table.setItem(row, 1, email_item)
                    self.table.setItem(row, 2, utr_item)
                    self.table.setItem(row, 3, nino_item)

                    # Add QDateEdit widget for date input
                    date_edit = QDateEdit(calendarPopup=True)
                    date_edit.setDisplayFormat('yyyy-MM-dd')
                    if employer.start_date:
                        date_edit.setDate(QDate(employer.start_date.year, employer.start_date.month, employer.start_date.day))
                    else:
                        date_edit.setDate(QDate.currentDate())  # Set default to current date if start_date is None
                    self.table.setCellWidget(row, 4, date_edit)

                    # Store the employer ID in the row's Qt.UserRole data for each item
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            item.setData(Qt.UserRole, employer.id)

            self.apply_row_colors()  # Apply row colors after loading data

        except Exception as e:
            logging.exception(f"Error loading data: {e}")
            QMessageBox.critical(self, "Error", f"Error loading data: {e}")
        finally:
            self.table.blockSignals(False)

    def add_row(self):
        """Add a new row to the table for entering new employer data."""
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        for col in range(4):  # First four columns are text data
            item = QTableWidgetItem("")
            self.table.setItem(row_position, col, item)

        # Add QDateEdit widget for date input
        date_edit = QDateEdit(calendarPopup=True)
        date_edit.setDate(QDate.currentDate())
        date_edit.setDisplayFormat('yyyy-MM-dd')
        self.table.setCellWidget(row_position, 4, date_edit)

        self.apply_row_colors()  # Apply row colors after adding a new row

    def save_data(self):
        """Save or update employer data."""
        try:
            with get_session() as session:
                for row in range(self.table.rowCount()):
                    name_item = self.table.item(row, 0)
                    if name_item is None:
                        continue  # Skip empty rows

                    employer_id = name_item.data(Qt.UserRole)
                    employer = session.query(Employer).get(employer_id) if employer_id else None
                    if employer:  # Update existing employer
                        employer.name = name_item.text()
                        employer.email = self.table.item(row, 1).text()
                        employer.utr = self.table.item(row, 2).text()
                        employer.nino = self.table.item(row, 3).text()
                        date_widget = self.table.cellWidget(row, 4)
                        if isinstance(date_widget, QDateEdit):
                            employer.start_date = date_widget.date().toPyDate()
                    else:  # Add new employer
                        new_employer = Employer(
                            name=name_item.text(),
                            email=self.table.item(row, 1).text(),
                            utr=self.table.item(row, 2).text(),
                            nino=self.table.item(row, 3).text(),
                            start_date=self.table.cellWidget(row, 4).date().toPyDate(),
                            company_id=self.company_id
                        )
                        session.add(new_employer)
                session.commit()
                QMessageBox.information(self, "Success", "Employers saved successfully.")
                self.load_data()
        except IntegrityError as e:
            logging.exception("Integrity error during save")
            QMessageBox.critical(self, "Error", "Integrity error, please check your data.")
        except Exception as e:
            logging.exception("Failed to save employer data")
            QMessageBox.critical(self, "Error", f"An error occurred while saving: {e}")

    def delete_row(self):
        """Delete selected row from the table and database."""
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            id_item = self.table.item(selected_row, 0)  # Use the ID stored in the first column's data
            if id_item and id_item.data(Qt.UserRole):
                confirmation = QMessageBox.question(
                    self, 'Confirm Deletion', 'Are you sure you want to delete this employer?',
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirmation == QMessageBox.Yes:
                    try:
                        employer_id = id_item.data(Qt.UserRole)
                        delete_employer(employer_id)  # Use the delete function from backend
                        self.table.removeRow(selected_row)
                        self.apply_row_colors()  # Re-apply row colors after deleting a row
                        QMessageBox.information(self, "Delete Data", "Employer deleted successfully!")
                    except Exception as e:
                        logging.exception(f"Error deleting data: {e}")
                        QMessageBox.critical(self, "Error", f"Error deleting data: {e}")
            else:
                self.table.removeRow(selected_row)
                self.apply_row_colors()  # Re-apply row colors after deleting a row

    def handle_item_changed(self, item):
        """Handle item change events in the table."""
        pass  # Currently, nothing is needed here

    def apply_row_colors(self):
        """Apply alternating row colors for better readability."""
        for row in range(self.table.rowCount()):
            color = QColor(230, 230, 250, 127) if row % 2 == 0 else QColor(255, 240, 230, 127)  # Light purple and light light purple
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(color)

    def close_tab(self):
        """Close the current tab and redirect to the PayRunTab."""
        index = self.tab_widget.indexOf(self)
        if index != -1:
            self.tab_widget.removeTab(index)
            self.redirect_to_payrun_tab()

    def redirect_to_payrun_tab(self):
        """Redirect to the PayRunTab after closing this tab."""
        # Lazy import to avoid circular dependency
        from payrun import PayRunTab
        
        for i in range(self.tab_widget.count()):
            if isinstance(self.tab_widget.widget(i), PayRunTab):
                self.tab_widget.setCurrentIndex(i)  # Set the PayRunTab as the current tab
                break


if __name__ == "__main__":
    app = QApplication(sys.argv)
    company_id = 1  # Example company_id to test
    window = QWidget()
    layout = QVBoxLayout(window)
    
    tab_widget = QTabWidget()
    layout.addWidget(tab_widget)
    
    employers_tab = EmployersTab(company_id, tab_widget)
    tab_widget.addTab(employers_tab, "Employers")

    # Assuming PayRunTab is defined elsewhere and imported
    from payrun import PayRunTab
    payrun_tab = PayRunTab(company_id, tab_widget)
    tab_widget.addTab(payrun_tab, f"Pay Run for Company {company_id}")
    
    window.setLayout(layout)
    window.show()
    
    sys.exit(app.exec_())
