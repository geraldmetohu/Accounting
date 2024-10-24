import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QComboBox, QCheckBox, QMessageBox, QPushButton, QApplication, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from backend import get_session  # Use context manager for session handling
from models import VAT, Address, Files  # Import the necessary models
from dateutil.relativedelta import relativedelta

class VatTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_edit_flag = False
        self.original_text = ''
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
            'Default', 'Sort VAT Number Asc', 'Sort VAT Number Desc',
            'Sort Registration Date Asc', 'Sort Registration Date Desc',
            'Sort Company Number Asc', 'Sort Company Number Desc',
            'Sort Start Date Asc', 'Sort Start Date Desc',
            'Sort End Date Asc', 'Sort End Date Desc',
            'Sort Due Date Asc', 'Sort Due Date Desc'
        ])
        self.sort_dropdown.currentIndexChanged.connect(self.sort_data)
        search_sort_layout.addWidget(self.sort_dropdown)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.refresh_tabs)
        search_sort_layout.addWidget(self.refresh_button)

        main_layout.addLayout(search_sort_layout)

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(17)
        self.table.setHorizontalHeaderLabels([
            'VAT Number', 'Reg. Date', 'C. Number', 'C. Name', 'C. UTR',
            'Start Date', 'End Date', 'Due Date', 'VAT Status', 'Calculations',
            'VAT Done', 'Number', 'Street',
            'City', 'PostCode', 'Country', 'VAT Files'
        ])
        self.table.itemChanged.connect(self.handle_item_changed)
        self.table.itemDoubleClicked.connect(self.store_original_text)
        self.update_files_count()
        self.load_data()

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

    def sort_data(self):
        """Sort data in the table based on user selection."""
        sort_option = self.sort_dropdown.currentText()
        column_map = {
            'Sort VAT Number Asc': (VAT.number, 'asc'),
            'Sort VAT Number Desc': (VAT.number, 'desc'),
            'Sort Registration Date Asc': (VAT.registration_date, 'asc'),
            'Sort Registration Date Desc': (VAT.registration_date, 'desc'),
            'Sort Company Number Asc': (VAT.company_number, 'asc'),
            'Sort Company Number Desc': (VAT.company_number, 'desc'),
            'Sort Start Date Asc': (VAT.start_date, 'asc'),
            'Sort Start Date Desc': (VAT.start_date, 'desc'),
            'Sort End Date Asc': (VAT.end_date, 'asc'),
            'Sort End Date Desc': (VAT.end_date, 'desc'),
            'Sort Due Date Asc': (VAT.due_date, 'asc'),
            'Sort Due Date Desc': (VAT.due_date, 'desc')
        }

        if sort_option in column_map:
            column, order = column_map[sort_option]
            with get_session() as session:
                records = session.query(VAT).options(joinedload(VAT.address)).filter(VAT.company_id != None).order_by(column.asc() if order == 'asc' else column.desc()).all()
                self.populate_table(records)  # Populate table within the session context
        else:
            self.load_data()

    def load_data(self):
        """Load VAT data from the database."""
        with get_session() as session:
            vat_records = session.query(VAT).options(joinedload(VAT.address)).filter(VAT.company_id != None).all()
            # Update statuses within the session context
            for vat in vat_records:
                self.update_vat_status(session, vat)
            session.commit()  # Commit all status updates in a single transaction
            self.populate_table(vat_records)  # Populate table within the session context

    def populate_table(self, records):
        """Populate the table with VAT records."""
        self.table.itemChanged.disconnect(self.handle_item_changed)

        self.table.setRowCount(0)
        row_count = len(records)
        self.table.setRowCount(row_count)

        for row, vat in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(vat.number))
            self.table.setItem(row, 1, QTableWidgetItem(vat.registration_date.strftime('%Y-%m-%d') if vat.registration_date else ''))
            self.table.setItem(row, 2, QTableWidgetItem(vat.company_number))
            self.table.setItem(row, 3, QTableWidgetItem(vat.company_name))
            self.table.setItem(row, 4, QTableWidgetItem(str(vat.company_id)))
            self.table.setItem(row, 5, QTableWidgetItem(vat.start_date.strftime('%Y-%m-%d') if vat.start_date else ''))
            self.table.setItem(row, 6, QTableWidgetItem(vat.end_date.strftime('%Y-%m-%d') if vat.end_date else ''))
            self.table.setItem(row, 7, QTableWidgetItem(vat.due_date.strftime('%Y-%m-%d') if vat.due_date else ''))

            status_item = QTableWidgetItem(vat.status)
            status_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 8, status_item)

            vat_calc_item = QTableWidgetItem(vat.calculations)
            self.table.setItem(row, 9, vat_calc_item)

            vat_done_checkbox = QCheckBox()
            vat_done_checkbox.setChecked(vat.done)
            vat_done_checkbox.stateChanged.connect(lambda state, vat=vat: self.handle_vat_done_change(state, vat))
            self.table.setCellWidget(row, 10, vat_done_checkbox)

            if vat.address:
                self.table.setItem(row, 11, QTableWidgetItem(str(vat.address.number)))
                self.table.setItem(row, 12, QTableWidgetItem(vat.address.street))
                self.table.setItem(row, 13, QTableWidgetItem(vat.address.city))
                self.table.setItem(row, 14, QTableWidgetItem(vat.address.postcode))
                self.table.setItem(row, 15, QTableWidgetItem(vat.address.country))
            self.table.setItem(row, 16, QTableWidgetItem(str(vat.files_count)))

            self.set_row_color(row, vat.status)
            self.update_checkbox_background(row, vat.status)

        self.table.itemChanged.connect(self.handle_item_changed)

    def handle_vat_done_change(self, state, vat):
        """Handle VAT done checkbox state change."""
        if state == Qt.Checked:
            reply = QMessageBox.question(
                self, 
                'Confirmation', 
                'Are you sure you want to mark this VAT as done? This will update the dates accordingly.',
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                with get_session() as session:
                    vat = session.merge(vat)  # Ensure the VAT instance is attached to the session
                    vat.done = True
                    self.update_vat_dates(session, vat)  # Update dates in a session context
                    vat.done = False  # Reset the 'done' status after updating the dates
                    session.add(vat)  # Ensure changes are tracked by the session
                    session.commit()  # Commit changes to the database
                self.load_data()  # Refresh the table to show the updated data
            else:
                # If the user cancels, reset the checkbox to unchecked
                checkbox = self.sender()
                if isinstance(checkbox, QCheckBox):
                    checkbox.setChecked(False)
                vat.done = False
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

    def update_files_count(self):
        """Update the file count for each VAT entry."""
        try:
            with get_session() as session:
                vats = session.query(VAT).all()
                for vat in vats:
                    file_count = session.query(Files).filter(
                        and_(Files.company_id == vat.company_id, Files.second_id == 'Vat')
                    ).count()
                    vat.files_count = file_count
                    session.add(vat)  # Mark the VAT object as modified
                session.commit()  # Commit all changes
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while updating file counts: {str(e)}')

    def handle_item_changed(self, item):
        """Handle changes to VAT calculations."""
        if self.user_edit_flag and item.column() == 9:  # VAT Calculations column
            try:
                row = item.row()
                vat_number = self.table.item(row, 0).text()
                with get_session() as session:
                    vat = session.query(VAT).filter_by(number=vat_number).first()
                    if vat:
                        new_value = item.text()
                        confirmation = QMessageBox.question(
                            self, 'Confirm Update', f'Do you want to update VAT Calculations to "{new_value}"?',
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if confirmation == QMessageBox.Yes:
                            vat.calculations = new_value
                            session.commit()
                        else:
                            self.table.itemChanged.disconnect(self.handle_item_changed)
                            item.setText(self.original_text)
                            self.table.itemChanged.connect(self.handle_item_changed)
            except Exception as e:
                print(f"Error: {e}")
        self.user_edit_flag = False  # Reset the flag after handling the change

    def store_original_text(self, item):
        """Store original text for a table item when double-clicked."""
        if item.column() == 9:
            self.user_edit_flag = True
            self.original_text = item.text()

    def search_data(self):
        """Search VAT data in the table based on user input."""
        search_text = self.search_bar.text().lower()
        self.user_edit_flag = False  # Disable user edit flag during search
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

    def set_row_color(self, row, status):
        """Set the background color of a row based on its status."""
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

    def update_checkbox_background(self, row, status):
        """Update checkbox background color based on status."""
        color_map = {
            'Overdue': QColor(251, 55, 107, 127),
            'Urgent': QColor(247, 131, 34, 127),
            'Soon': QColor(241, 240, 133, 127),
            'Early': QColor(87, 242, 141, 127)
        }
        color = color_map.get(status, QColor(255, 255, 255, 127))

        checkbox = self.table.cellWidget(row, 10)
        if checkbox:
            checkbox.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha() / 255.0});")

    def update_vat_status(self, session, vat):
        """Update the status of a VAT entry based on the date."""
        today = datetime.now().date()
        if vat.end_date:
            days_to_end = (vat.end_date - today).days
            if days_to_end < 0:
                vat.status = "Overdue"
            elif days_to_end <= 2:
                vat.status = "Urgent"
            elif days_to_end <= 7:
                vat.status = "Soon"
            else:
                vat.status = "Early"
        session.add(vat)  # Mark the VAT object as modified


    def update_vat_dates(self, session, vat):
        """Update the start, end, and due dates for VAT after marking as done."""
        if vat.done:
            vat.start_date = vat.end_date
            vat.end_date = vat.end_date + relativedelta(months=3)
            vat.due_date = vat.due_date + relativedelta(months=3)
        session.add(vat)  # Mark the VAT object as modified
        session.commit()  # Commit changes to the database


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)

    vat_tab = VatTab()
    layout.addWidget(vat_tab)

    window.setLayout(layout)
    window.show()

    sys.exit(app.exec_())
