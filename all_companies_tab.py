import sys
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QMessageBox, QLineEdit, QComboBox, QApplication, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from sqlalchemy import and_
from models import Company, Files
from create1 import CompanyForm
from backend import get_session

class AllCompaniesTab(QWidget):

    def __init__(self, tab_widget):
        super().__init__()
        self.tab_widget = tab_widget
        self.company_data = []  # Preload data into memory
        self.initUI()

    def initUI(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()

        # Search and Sort Layout
        search_sort_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_data)
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        search_sort_layout.addWidget(self.search_bar)

        self.sort_dropdown = QComboBox()
        self.sort_dropdown.addItems([
            'Sort UTR Asc', 'Sort UTR Desc',
            'Sort Name Asc', 'Sort Name Desc',
            'Sort Date Added Asc', 'Sort Date Added Desc'
        ])
        self.sort_dropdown.currentIndexChanged.connect(self.sort_dropdown_changed)
        search_sort_layout.addWidget(self.sort_dropdown)

        main_layout.addLayout(search_sort_layout)

        # Table for Companies
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            'UTR', 'House Number', 'Name', 'Nature', 'Pay Reference Number',
            'Account Office Number', 'CIS', 'VAT', 'Email', 'Contact Number',
            'Government Gateway ID', 'Files', 'Address ID'
        ])
        self.load_companies()

        # Adjust header width
        for column in range(self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(column, self.table.horizontalHeader().ResizeToContents)

        self.table.horizontalHeader().setStretchLastSection(True)

        main_layout.addWidget(self.table)

        # Buttons Layout
        buttons_layout = QHBoxLayout()
        self.create_button = QPushButton("Create")
        self.create_button.setMinimumHeight(40)
        self.create_button.clicked.connect(self.open_create_company_tab)
        buttons_layout.addWidget(self.create_button)

        self.view_button = QPushButton("View")
        self.view_button.setMinimumHeight(40)
        self.view_button.clicked.connect(self.open_view_company_tab)
        buttons_layout.addWidget(self.view_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.refresh_tabs)
        buttons_layout.addWidget(self.refresh_button)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def on_search_text_changed(self):
        """Delay search trigger to improve performance."""
        self.search_timer.start(1000)  # 300ms delay


    def load_companies(self):
        """Load companies into memory and display them in the table."""
        start_time = time.time()  # Record the start time
        try:
            print("Loading data started at:", datetime.now().strftime("%H:%M:%S"))
            self.company_data.clear()
            with get_session() as session:
                companies = session.query(Company).all()
                for company in companies:
                    self.company_data.append({
                        'id': company.id,
                        'house_number': company.house_number,
                        'name': company.name,
                        'nature': company.nature,
                        'pay_reference_number': company.pay_reference_number,
                        'account_office_number': company.account_office_number,
                        'cis': 'Yes' if company.cis else 'No',
                        'vat': 'Yes' if company.vat else 'No',
                        'email': company.email,
                        'contact_number': company.contact_number,
                        'government_gateway_id': company.government_gateway_id,
                        'files_count': company.files_count,
                        'address_id': company.address_id
                    })
            print("Data loaded at:", datetime.now().strftime("%H:%M:%S"))

            self.populate_table(self.company_data)  # Populate the table with the loaded data
            print("Table populated at:", datetime.now().strftime("%H:%M:%S"))
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while loading data: {str(e)}')

        end_time = time.time()  # Record the end time
        print("Total time to load and populate table: {:.2f} seconds".format(end_time - start_time))

    def populate_table(self, companies):
        """Populate the table with preloaded data."""
        self.table.setRowCount(len(companies))
        for row, company in enumerate(companies):
            self.table.setItem(row, 0, self.create_noneditable_item(str(company['id'])))
            self.table.setItem(row, 1, self.create_noneditable_item(company['house_number']))
            self.table.setItem(row, 2, self.create_noneditable_item(company['name']))
            self.table.setItem(row, 3, self.create_noneditable_item(company['nature']))
            self.table.setItem(row, 4, self.create_noneditable_item(company['pay_reference_number']))
            self.table.setItem(row, 5, self.create_noneditable_item(company['account_office_number']))
            self.table.setItem(row, 6, self.create_noneditable_item(company['cis']))
            self.table.setItem(row, 7, self.create_noneditable_item(company['vat']))
            self.table.setItem(row, 8, self.create_noneditable_item(company['email']))
            self.table.setItem(row, 9, self.create_noneditable_item(company['contact_number']))
            self.table.setItem(row, 10, self.create_noneditable_item(company['government_gateway_id']))
            self.table.setItem(row, 11, self.create_noneditable_item(f"Files: {company['files_count']}"))
            self.table.setItem(row, 12, self.create_noneditable_item(str(company['address_id'])))

        self.apply_row_colors()

    def create_noneditable_item(self, text):
        """Create a non-editable QTableWidgetItem."""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def search_data(self):
        """Search and highlight data in the preloaded dataset with minimal UI interaction."""
        search_text = self.search_bar.text().lower()

        # If no search text, reset the table with all data
        if not search_text:
            self.populate_table(self.company_data)
            return

        # Determine if the search text is numeric
        is_numeric_search = search_text.isdigit()

        # Determine if the search text is 'yes' or 'no'
        is_yes_no_search = search_text in ['yes', 'no', 'ye']

        # Use a single pass to filter and highlight companies
        filtered_companies = []
        for company in self.company_data:
            row_data = {
                'id': str(company['id']),
                'house_number': str(company['house_number']),
                'name': company['name'].lower(),  # Ensure lowercase for case-insensitive search
                'nature': company['nature'].lower(),
                'pay_reference_number': company['pay_reference_number'].lower(),
                'account_office_number': company['account_office_number'].lower(),
                'cis': 'yes' if company['cis'].lower() == 'yes' else 'no',
                'vat': 'yes' if company['vat'].lower() == 'yes' else 'no',
                'email': company['email'].lower(),
                'contact_number': company['contact_number'].lower(),
                'government_gateway_id': str(company['government_gateway_id']),
                'files_count': f"Files: {company['files_count']}",
                'address_id': str(company['address_id'])
            }

            # Skip numeric fields if the search text is not a number
            if not is_numeric_search:
                del row_data['id']
                del row_data['house_number']
                del row_data['government_gateway_id']
                del row_data['address_id']

            # Skip cis and vat columns if the search text is not 'yes' or 'no'
            if not is_yes_no_search:
                del row_data['cis']
                del row_data['vat']

            # If any column in this row contains the search text, add it to filtered companies
            if any(search_text in str(field).lower() for field in row_data.values()):
                filtered_companies.append(company)

        # Populate table with filtered data and highlight the matches
        self.populate_table_with_highlighting(filtered_companies, search_text)



    def populate_table_with_highlighting(self, companies, search_text):
        """Populate the table and highlight matching cells with minimal UI updates."""
        self.table.setRowCount(len(companies))

        for row, company in enumerate(companies):
            row_data = [
                str(company['id']),
                company['house_number'],
                company['name'],
                company['nature'],
                company['pay_reference_number'],
                company['account_office_number'],
                company['cis'],
                company['vat'],
                company['email'],
                company['contact_number'],
                company['government_gateway_id'],
                f"Files: {company['files_count']}",
                str(company['address_id'])
            ]

            for col, field in enumerate(row_data):
                item = self.create_noneditable_item(field)
                
                # Only highlight matching text in the relevant cells
                if search_text in field.lower():
                    item.setBackground(QColor(255, 255, 0, 127))  # Highlight yellow
                self.table.setItem(row, col, item)

        # Apply alternating row colors after the entire table is populated
        self.set_row_colors()

    def apply_row_colors(self):
        """Apply alternating colors to table rows."""
        for row in range(self.table.rowCount()):
            color = QColor(155, 135, 212, 127) if row % 2 == 0 else QColor(196, 193, 233, 127)  # Light purple and light light purple
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(color)

    def set_row_colors(self):
        """Apply a single color to all table rows, but preserve existing highlights."""
        color = QColor(196, 193, 233, 127)  # Single color (light purple)

        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    # If the cell is not already highlighted, apply the single color
                    if item.background().color() != QColor(255, 255, 0, 127):  # Check if it's not yellow
                        item.setBackground(color)


    def create_noneditable_item(self, text):
        """Create a non-editable QTableWidgetItem."""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item


    def sort_dropdown_changed(self):
        """Handle sorting dropdown changes."""
        current_text = self.sort_dropdown.currentText()
        if 'UTR' in current_text:
            column = 'id'
        elif 'Name' in current_text:
            column = 'name'
        elif 'Date Added' in current_text:
            column = 'date_added'
        ascending = 'Asc' in current_text
        self.sort_data(column, ascending)

    def sort_data(self, column, ascending):
        """Sort data in the preloaded dataset."""
        sorted_companies = sorted(self.company_data, key=lambda x: x[column], reverse=not ascending)
        self.populate_table(sorted_companies)

    # Other methods remain unchanged (e.g., open_create_company_tab, open_view_company_tab)
    def open_create_company_tab(self):
        """Open the create company tab."""
        try:
            create_view = CompanyForm(self.tab_widget)
            index = self.tab_widget.addTab(create_view, "Create Company")
            self.tab_widget.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while creating the company tab: {str(e)}")

    def open_view_company_tab(self):
        """Open the view company tab."""
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            company_id = int(self.table.item(selected_row, 0).text())
            
            with get_session() as session:
                # Query the company and ensure all necessary data is loaded
                company = session.query(Company).filter(Company.id == company_id).first()
                
                if company:
                    # Load all necessary fields while the session is still open
                    company_name = company.name
                    address = company.address
                    if address:
                        address_number = address.number
                        address_street = address.street
                        address_city = address.city
                        address_postcode = address.postcode
                        address_country = address.country

                    # Create and populate the CompanyForm
                    create_view = CompanyForm(self.tab_widget, company)
                    create_view.toggle_edit_mode(False)  # Set fields to read-only for view mode

                    # Set tab name with loaded data
                    index = self.tab_widget.addTab(create_view, f"View Company - {company_name}")
                    self.tab_widget.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, 'Warning', 'Company not found.')
        else:
            QMessageBox.warning(self, 'Warning', 'Please select a company to view.')

    def refresh(self):
        """Refresh the company data in the table."""
        self.load_companies()

    def refresh_tabs(self):
        """Refresh all tabs."""
        self.update_files_count()  # Call the new method to update file counts
        self.refresh()  # Refresh current tab
        if hasattr(self, 'tab_widget'):
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, 'refresh') and tab != self:
                    tab.refresh()

    def update_files_count(self):
        """Update the file count for each company."""
        try:
            with get_session() as session:
                companies = session.query(Company).all()
                for company in companies:
                    file_count = session.query(Files).filter(
                        and_(Files.company_id == company.id, Files.second_id == 'Company')
                    ).count()
                    company.files_count = file_count
                    session.add(company)  # Mark the company object as modified
                session.commit()  # Commit all changes
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while updating file counts: {str(e)}')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)

    tab_widget = QTabWidget()
    all_companies_tab = AllCompaniesTab(tab_widget)
    tab_widget.addTab(all_companies_tab, "All Companies")

    layout.addWidget(tab_widget)
    window.setLayout(layout)
    window.show()

    sys.exit(app.exec_())
