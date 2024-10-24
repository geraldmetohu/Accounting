import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QHBoxLayout, QSpacerItem, QSizePolicy,
    QTabWidget, QFileDialog, QScrollArea, QGroupBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker, joinedload
from time import sleep
import logging
import os
import shutil
from models import Company, Address, Account, ConfirmationStatement, CIS, VAT, Employer, Director, Files, PayRun
from backend import engine, get_session  # Ensure consistent session management
from google.oauth2.service_account import Credentials 
from googleapiclient.discovery import build 
from googleapiclient.http import MediaFileUpload

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set up SQLAlchemy session
Session = sessionmaker(bind=engine)


# Define the scope for Google Drive API access
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_service_account_file_path():
    # Get the current directory where the script is located
    script_dir = os.path.dirname(os.path.realpath(__file__))
    
    # The name of the service account file (change the name if needed)
    service_account_file = os.path.join(script_dir, "adroit-producer-421409-e1fdc9fd2b6f.json")

    # Check if the file exists
    if not os.path.exists(service_account_file):
        raise FileNotFoundError(f"Service account file not found: {service_account_file}")
    
    return service_account_file

# Use the dynamic path
SERVICE_ACCOUNT_FILE = get_service_account_file_path()

# Use SERVICE_ACCOUNT_FILE in the Google API authentication
def authenticate_google_drive():
    """Authenticate and return the Google Drive service using a service account."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    return service



class CompanyForm(QWidget):
    """Form for viewing and editing company details."""
    def __init__(self, tab_widget, company=None):
        super().__init__()
        self.tab_widget = tab_widget
        self.company = company
        self.is_edit_mode = not bool(company)  # If company is None, start in edit mode for creating a new company
        self.initUI()

    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("Company Form")
        main_layout = QVBoxLayout()

        # Scroll area for form layout
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Form sections
        grid_layout = QGridLayout()
        content_layout.addLayout(grid_layout)

        grid_layout.addWidget(self.create_company_address_layout1(), 0, 0)
        grid_layout.addWidget(self.create_company_address_layout2(), 0, 1)
        grid_layout.addWidget(self.create_account_confirmation_payrun_layout(), 0, 2)
        grid_layout.addWidget(self.create_cis_vat_layout(), 0, 3)

        bottom_layout = self.create_employer_director_layout()
        content_layout.addLayout(bottom_layout)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Action buttons
        buttons_layout = self.create_buttons_layout()
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        if self.company:
            self.load_data()  # Load existing company data
        self.toggle_edit_mode(self.is_edit_mode)
        self.toggle_cis_vat_fields()

    def create_group_box(self, title):
        """Helper method to create a styled QGroupBox."""
        group_box = QGroupBox(title)
        group_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        group_box_layout = QVBoxLayout()
        group_box.setLayout(group_box_layout)
        return group_box, group_box_layout

    def create_company_address_layout1(self):
        """Layout for primary company fields."""
        group_box, layout = self.create_group_box("Company Information")

        grid_layout = QGridLayout()
        layout.addLayout(grid_layout)

        self.id_field = self.add_field(grid_layout, "UTR", 0, 0)
        self.company_name_field = self.add_field(grid_layout, "Company Name", 1, 0)
        self.house_number_field = self.add_field(grid_layout, "House Number", 2, 0)
        self.pay_reference_field = self.add_field(grid_layout, "Pay Reference Number", 3, 0)
        self.account_office_field = self.add_field(grid_layout, "Account Office Number", 4, 0)
        self.gateway_id_field = self.add_field(grid_layout, "Government Gateway ID", 5, 0)
        self.cis_check = self.add_checkbox(grid_layout, "Company CIS", 6, 0)
        self.vat_check = self.add_checkbox(grid_layout, "Company VAT", 7, 0)
        self.date_added_field = self.add_date_field(grid_layout, "Date Added", 8, 0)

        self.cis_check.toggled.connect(self.toggle_cis_vat_fields)
        self.vat_check.toggled.connect(self.toggle_cis_vat_fields)

        return group_box

    def create_company_address_layout2(self):
        """Layout for additional company fields."""
        group_box, layout = self.create_group_box("Address")

        grid_layout = QGridLayout()
        layout.addLayout(grid_layout)

        self.email_field = self.add_field(grid_layout, "Company Email", 1, 0)
        self.contact_field = self.add_field(grid_layout, "Contact Number", 2, 0)
        self.nature_field = self.add_field(grid_layout, "Nature of Business", 3, 0)

        self.address_fields = {
            "number": self.add_field(grid_layout, "Address Number", 4, 0),
            "street": self.add_field(grid_layout, "Street", 5, 0),
            "city": self.add_field(grid_layout, "City", 6, 0),
            "postcode": self.add_field(grid_layout, "Postcode", 7, 0),
            "country": self.add_field(grid_layout, "Country", 8, 0),
        }
        return group_box

    def create_account_confirmation_payrun_layout(self):
        """Layout for account, confirmation statement, and payrun fields."""
        group_box, layout = self.create_group_box("Account and Confirmation Statement")

        grid_layout = QGridLayout()
        layout.addLayout(grid_layout)

        self.account_date_field = self.add_date_field(grid_layout, "Account Date", 1, 0)
        self.account_email_check = self.add_checkbox(grid_layout, "Account Email Check", 3, 0)
        self.account_invoice_check = self.add_checkbox(grid_layout, "Account Invoice Check", 4, 0)
        self.account_done_check = self.add_checkbox(grid_layout, "Account Done Check", 5, 0)

        self.confirmation_date_field = self.add_date_field(grid_layout, "Confirmation Date", 6, 0)
        self.confirmation_invoice_check = self.add_checkbox(grid_layout, "Confirmation Invoice Check", 8, 0)
        self.confirmation_done_check = self.add_checkbox(grid_layout, "Confirmation Done Check", 9, 0)

        self.payrun_date_field = self.add_date_field(grid_layout, "PayRun Date", 11, 0)
        self.payrun_month_check = self.add_checkbox(grid_layout, "PayRun Month Check", 13, 0)
        self.payrun_pay_run_check = self.add_checkbox(grid_layout, "PayRun Pay Run Check", 14, 0)
        self.payrun_p60_check = self.add_checkbox(grid_layout, "PayRun P60 Check", 15, 0)

        return group_box

    def create_cis_vat_layout(self):
        """Layout for CIS and VAT fields."""
        group_box, layout = self.create_group_box("CIS and VAT")

        grid_layout = QGridLayout()
        layout.addLayout(grid_layout)

        self.cis_employee_ref_field = self.add_field(grid_layout, "Employees Reference", 0, 0, readonly=True)
        self.cis_last_month_field = self.add_date_field(grid_layout, "CIS Last Month", 1, 0)
        self.cis_next_month_field = self.add_date_field(grid_layout, "CIS Next Month", 2, 0)
        self.cis_email_check = self.add_checkbox(grid_layout, "CIS Email Check", 4, 0, readonly=True)
        self.cis_month_check = self.add_checkbox(grid_layout, "CIS Month Check", 5, 0, readonly=True)

        self.vat_number_field = self.add_field(grid_layout, "VAT Number", 6, 0)
        self.vat_registration_date_field = self.add_date_field(grid_layout, "VAT Registration Date", 7, 0)
        self.vat_start_date_field = self.add_date_field(grid_layout, "Start Date", 8, 0)
        self.vat_end_date_field = self.add_date_field(grid_layout, "End Date", 9, 0)
        self.vat_due_date_field = self.add_date_field(grid_layout, "Due Date", 10, 0)
        self.vat_calculations_field = self.add_field(grid_layout, "VAT Calculations", 11, 0)
        self.vat_done_check = self.add_checkbox(grid_layout, "VAT Done", 12, 0)

        return group_box

    def create_employer_director_layout(self):
        """Create layout for employer, director, and file information."""
        layout = QVBoxLayout()

        employer_section, employer_layout = self.create_group_box("Employer")
        layout.addWidget(employer_section)
        
        self.employer_table = QTableWidget(0, 5)
        self.employer_table.setHorizontalHeaderLabels([
            'Name', 'Email', 'UTR', 'NINO', 'Start Date'
        ])
        self.employer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.employer_table.setFixedHeight(150)
        employer_layout.addWidget(self.employer_table)

        director_section, director_layout = self.create_group_box("Director")
        layout.addWidget(director_section)

        self.director_table = QTableWidget(0, 9)
        self.director_table.setHorizontalHeaderLabels([
            'Name', 'Insurance Number', 'Phone', 'Email', 'Address Number', 'Street', 'City', 'Postcode', 'Country'
        ])
        self.director_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.director_table.setFixedHeight(150)
        director_layout.addWidget(self.director_table)

        files_section, files_layout = self.create_group_box("Files")
        layout.addWidget(files_section)

        self.file_table = QTableWidget(0, 2)
        self.file_table.setHorizontalHeaderLabels(['File Name', 'Type'])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.file_table.setFixedHeight(150)
        files_layout.addWidget(self.file_table)

        return layout

    def create_buttons_layout(self):
        """Create layout for action buttons."""
        layout = QHBoxLayout()

        self.edit_view_button = QPushButton("Edit/View")
        self.edit_view_button.clicked.connect(self.edit_view_data)
        layout.addWidget(self.edit_view_button)

        self.upload_file_button = QPushButton("Upload File")
        self.upload_file_button.clicked.connect(self.upload_file)
        layout.addWidget(self.upload_file_button)

        employer_buttons_layout = QVBoxLayout()

        self.add_employer_button = QPushButton("Add Employer")
        self.add_employer_button.clicked.connect(self.add_employer_row)
        employer_buttons_layout.addWidget(self.add_employer_button)

        self.delete_employer_button = QPushButton("Delete Employer")
        self.delete_employer_button.clicked.connect(self.delete_employer_row)
        employer_buttons_layout.addWidget(self.delete_employer_button)

        layout.addLayout(employer_buttons_layout)

        director_buttons_layout = QVBoxLayout()

        self.add_director_button = QPushButton("Add Director")
        self.add_director_button.clicked.connect(self.add_director_row)
        director_buttons_layout.addWidget(self.add_director_button)

        self.delete_director_button = QPushButton("Delete Director")
        self.delete_director_button.clicked.connect(self.delete_director_row)
        director_buttons_layout.addWidget(self.delete_director_button)

        layout.addLayout(director_buttons_layout)

        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.delete_company_button = QPushButton("Delete Company")
        self.delete_company_button.clicked.connect(self.delete_company)
        layout.addWidget(self.delete_company_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_tab)
        layout.addWidget(self.close_button)

        return layout

    def load_data(self):
        """Load existing company data into the form fields."""
        if not self.company:
            return

        try:
            # Populate fields with company data
            self.id_field.setText(str(self.company.id))
            self.company_name_field.setText(self.company.name)
            self.house_number_field.setText(str(self.company.house_number))
            self.pay_reference_field.setText(str(self.company.pay_reference_number))
            self.account_office_field.setText(self.company.account_office_number)
            self.gateway_id_field.setText(self.company.government_gateway_id)
            self.cis_check.setChecked(self.company.cis)
            self.vat_check.setChecked(self.company.vat)
            self.date_added_field.setDate(self.company.date_added)
            self.email_field.setText(self.company.email)
            self.contact_field.setText(self.company.contact_number)
            self.nature_field.setText(self.company.nature)

            address = self.company.address
            if address:
                self.address_fields["number"].setText(str(address.number))
                self.address_fields["street"].setText(address.street)
                self.address_fields["city"].setText(address.city)
                self.address_fields["postcode"].setText(address.postcode)
                self.address_fields["country"].setText(address.country)

            # Load related data (accounts, confirmation statements, payrun, cis, vat, employers, directors, files)
            self.load_related_data()

        except Exception as e:
            logging.exception("Failed to load company data")
            QMessageBox.critical(self, "Error", f"An error occurred while loading data: {e}")

    def load_related_data(self):
        """Load related data (accounts, confirmation statements, payrun, employers, directors, files) into the form."""
        try:
            with get_session() as session:
                # Fetch the company by ID with eager loading for related data
                company = session.query(Company).options(
                    joinedload(Company.accounts),
                    joinedload(Company.confirmation_statements),
                    joinedload(Company.payrun),
                    joinedload(Company.employers),
                    joinedload(Company.directors),
                    joinedload(Company.files)
                ).filter_by(id=self.company.id).first()
                
                # Ensure company exists and load data
                if not company:
                    QMessageBox.critical(self, "Error", "The specified company does not exist.")
                    return

                # Set all UI fields with loaded data
                self.load_all_data(session)
   

        except Exception as e:
            logging.exception("Failed to load related data")
            QMessageBox.critical(self, "Error", f"An error occurred while loading related data: {e}")
   
    def load_all_data(self,session):
        #for accounts
        try:
            account = session.query(Account).filter_by(company_id=self.company.id).first()
            if account:
                self.account_date_field.setDate(QDate(account.date.year, account.date.month, account.date.day))
                self.account_email_check.setChecked(account.email_check)
                self.account_invoice_check.setChecked(account.invoice_check)
                self.account_done_check.setChecked(account.done_check)
        except Exception as e:
            logging.exception("Failed to load account data")
            QMessageBox.critical(self, "Error", f"An error occurred while loading account data: {e}")
        #for cis
        try:
            cis = session.query(CIS).filter_by(company_id=self.company.id).first()
            if cis:
                # Populate CIS fields
                self.cis_employee_ref_field.setText(cis.employees_reference or "")
                self.cis_last_month_field.setDate(QDate(cis.last_month.year, cis.last_month.month, cis.last_month.day) if cis.last_month else QDate.currentDate())
                self.cis_next_month_field.setDate(QDate(cis.next_month.year, cis.next_month.month, cis.next_month.day) if cis.next_month else QDate.currentDate())
                self.cis_email_check.setChecked(cis.email_check)
                self.cis_month_check.setChecked(cis.month_check)
            else:
                # If no CIS data exists, clear the fields
                self.cis_employee_ref_field.clear()
                self.cis_last_month_field.setDate(QDate.currentDate())
                self.cis_next_month_field.setDate(QDate.currentDate())
                self.cis_email_check.setChecked(False)
                self.cis_month_check.setChecked(False)
        except Exception as e:
            logging.exception("Failed to load CIS data")
            QMessageBox.critical(self, "Error", f"An error occurred while loading CIS data: {e}")
        # for payrun
        try:
            payrun = session.query(PayRun).filter_by(company_id=self.company.id).first()  # Fetch the single payrun
            if payrun:
                self.payrun_date_field.setDate(QDate(payrun.date.year, payrun.date.month, payrun.date.day))
                self.payrun_month_check.setChecked(payrun.month_check)
                self.payrun_pay_run_check.setChecked(payrun.pay_run)
                self.payrun_p60_check.setChecked(payrun.p60)
        except Exception as e:
            logging.exception("Failed to load payrun data")
            QMessageBox.critical(self, "Error", f"An error occurred while loading payrun data: {e}")
        #for confirmation statements
        try:
            confirmation_statement = session.query(ConfirmationStatement).filter_by(company_id=self.company.id).first()  # Fetch the single confirmation statement
            if confirmation_statement:
                self.confirmation_date_field.setDate(QDate(confirmation_statement.date.year, confirmation_statement.date.month, confirmation_statement.date.day))
                self.confirmation_invoice_check.setChecked(confirmation_statement.invoice_check)
                self.confirmation_done_check.setChecked(confirmation_statement.done_check)
        except Exception as e:
            logging.exception("Failed to load confirmation statement data")
            QMessageBox.critical(self, "Error", f"An error occurred while loading confirmation statement data: {e}")
        #for employers
        try:
            # Fetch all employers associated with the company
            employers = session.query(Employer).filter_by(company_id=self.company.id).all()
            self.employer_table.setRowCount(len(employers))

            for row, employer in enumerate(employers):
                self.employer_table.setItem(row, 0, QTableWidgetItem(employer.name))
                self.employer_table.setItem(row, 1, QTableWidgetItem(employer.email))
                self.employer_table.setItem(row, 2, QTableWidgetItem(employer.utr if employer.utr else ""))
                self.employer_table.setItem(row, 3, QTableWidgetItem(employer.nino))

                # Add QDateEdit widget for start date input
                date_edit = QDateEdit(calendarPopup=True)
                date_edit.setDisplayFormat('dd-MM-yyyy')
                if employer.start_date:
                    date_edit.setDate(QDate(employer.start_date.year, employer.start_date.month, employer.start_date.day))
                else:
                    date_edit.setDate(QDate.currentDate())  # Default to the current date if no start date

                self.employer_table.setCellWidget(row, 4, date_edit)

                # Store the employer ID in the first column's Qt.UserRole
                self.employer_table.item(row, 0).setData(Qt.UserRole, employer.id)

            self.employer_table.resizeRowsToContents()  # Adjust row height to content
        except Exception as e:
            logging.exception("Failed to load employer data")
            QMessageBox.critical(self, "Error", f"An error occurred while loading employer data: {e}")
        #for directors
        try:
            directors = session.query(Director).filter_by(company_id=self.company.id).all()
            self.director_table.setRowCount(len(directors))
            
            for row, director in enumerate(directors):
                self.director_table.setItem(row, 0, QTableWidgetItem(director.name))
                self.director_table.setItem(row, 1, QTableWidgetItem(director.insurance_number))
                self.director_table.setItem(row, 2, QTableWidgetItem(director.phone))
                self.director_table.setItem(row, 3, QTableWidgetItem(director.email))
                
                if director.address:
                    self.director_table.setItem(row, 4, QTableWidgetItem(str(director.address.number)))
                    self.director_table.setItem(row, 5, QTableWidgetItem(director.address.street))
                    self.director_table.setItem(row, 6, QTableWidgetItem(director.address.city))
                    self.director_table.setItem(row, 7, QTableWidgetItem(director.address.postcode))
                    self.director_table.setItem(row, 8, QTableWidgetItem(director.address.country))
                else:
                    # If no address, leave these fields blank
                    self.director_table.setItem(row, 4, QTableWidgetItem(""))
                    self.director_table.setItem(row, 5, QTableWidgetItem(""))
                    self.director_table.setItem(row, 6, QTableWidgetItem(""))
                    self.director_table.setItem(row, 7, QTableWidgetItem(""))
                    self.director_table.setItem(row, 8, QTableWidgetItem(""))
        except Exception as e:
            logging.exception("Failed to load director data")
            QMessageBox.critical(self, "Error", f"An error occurred while loading director data: {e}")
        #for files
        try:
            files = session.query(Files).filter_by(company_id=self.company.id).all()
            self.file_table.setRowCount(len(files))
            
            for row, file in enumerate(files):
                self.file_table.setItem(row, 0, QTableWidgetItem(file.name))
                
                # Create a QComboBox for file types
                type_combo = QComboBox()
                type_combo.addItems(['Company', 'Vat', 'Account', 'Payrun'])
                if file.second_id in ['Company', 'Vat', 'Account', 'Payrun']:
                    type_combo.setCurrentText(file.second_id)
                self.file_table.setCellWidget(row, 1, type_combo)
        except Exception as e:
            logging.exception("Failed to load file data")
            QMessageBox.critical(self, "Error", f"An error occurred while loading file data: {e}")
        #for vat
        try:
            vat = session.query(VAT).filter_by(company_id=self.company.id).first()  # Fetch the single VAT
            if vat:
                self.vat_number_field.setText(vat.number)
                self.vat_registration_date_field.setDate(QDate(vat.registration_date.year, vat.registration_date.month, vat.registration_date.day))
                self.vat_start_date_field.setDate(QDate(vat.start_date.year, vat.start_date.month, vat.start_date.day))
                self.vat_end_date_field.setDate(QDate(vat.end_date.year, vat.end_date.month, vat.end_date.day))
                self.vat_due_date_field.setDate(QDate(vat.due_date.year, vat.due_date.month, vat.due_date.day))
                self.vat_calculations_field.setText(vat.calculations)
                self.vat_done_check.setChecked(vat.done)
        except Exception as e:
            logging.exception("Failed to load VAT data")
            QMessageBox.critical(self, "Error", f"An error occurred while loading VAT data: {e}")

    def save_data(self):
        """Save or update company data."""
        try:
            with get_session() as session:
                if not self.company:
                    self.save_new_company(session)
                else:
                    self.update_existing_company(session)
                session.commit()
                QMessageBox.information(self, "Success", "Company data saved successfully!")
                self.close_tab_save()
        except IntegrityError as e:
            logging.exception("Integrity error during save")
            QMessageBox.critical(self, "Error", "Integrity error, please check your data.")
        except Exception as e:
            logging.exception("Failed to save company data")
            QMessageBox.critical(self, "Error", f"An error occurred while saving: {e}")

    def save_new_company(self, session):
        """Save a new company and related records."""
        try:
            # Create and save new Address
            address = Address(
                number=int(self.address_fields["number"].text()),
                street=self.address_fields["street"].text(),
                city=self.address_fields["city"].text(),
                postcode=self.address_fields["postcode"].text(),
                country=self.address_fields["country"].text()
            )
            session.add(address)
            session.flush()  # Ensure address ID is generated

            # Create and save new Company
            self.company = Company(
                id=self.id_field.text(),
                name=self.company_name_field.text(),
                house_number=self.house_number_field.text(),
                pay_reference_number=self.pay_reference_field.text(),
                account_office_number=self.account_office_field.text(),
                government_gateway_id=self.gateway_id_field.text(),
                cis=self.cis_check.isChecked(),
                vat=self.vat_check.isChecked(),
                date_added=self.date_added_field.date().toPyDate(),
                email=self.email_field.text(),
                contact_number=self.contact_field.text(),
                nature=self.nature_field.text(),
                address_id=address.id
            )
            session.add(self.company)
            session.flush()  # Ensure company ID is generated

            # Save related entities
            self.save_other_data(session)
        except ValueError as ve:
            QMessageBox.critical(self, "Error", f"Invalid data: {ve}")
            raise

    def update_existing_company(self, session):
        """Update an existing company's data and related records."""
        try:
            # Re-fetch or merge the company instance with the current session
            self.company = session.merge(self.company)
            
            old_company_id = self.company.id
            new_company_id = self.id_field.text()

            # Check if the company ID has changed and update if necessary
            if old_company_id != new_company_id:
                self.update_foreign_keys(session, old_company_id, new_company_id)

            self.company.id = new_company_id
            self.company.name = self.company_name_field.text()
            self.company.house_number = self.house_number_field.text()
            self.company.pay_reference_number = self.pay_reference_field.text()
            self.company.account_office_number = self.account_office_field.text()
            self.company.government_gateway_id = self.gateway_id_field.text()
            self.company.cis = self.cis_check.isChecked()
            self.company.vat = self.vat_check.isChecked()
            self.company.date_added = self.date_added_field.date().toPyDate()
            self.company.email = self.email_field.text()
            self.company.contact_number = self.contact_field.text()
            self.company.nature = self.nature_field.text()

            # Ensure the address is initialized before accessing it
            if self.company.address is None:
                self.company.address = Address()  # or fetch it from somewhere if it's supposed to exist

            # Update Address
            address = self.company.address
            address.number = self.address_fields["number"].text()
            address.street = self.address_fields["street"].text()
            address.city = self.address_fields["city"].text()
            address.postcode = self.address_fields["postcode"].text()
            address.country = self.address_fields["country"].text()

            # Save related entities
            self.save_other_data(session)

        except Exception as e:
            session.rollback()
            logging.exception("Failed to update company data")
            raise
    
    def save_other_data(self, session):
        #for account
        try:
            # Check if an account already exists for this company
            account = session.query(Account).filter_by(company_id=self.company.id).first()

            if account:  # If an account exists, update it
                account.name = self.company.name
                account.date = self.account_date_field.date().toPyDate()
                account.email_check = self.account_email_check.isChecked()
                account.invoice_check = self.account_invoice_check.isChecked()
                account.done_check = self.account_done_check.isChecked()
                account.status = "Early"  # Update or recalculate status as needed
                account.files_count = 0  # Implement this method to count associated files

            else:  # If no account exists, create a new one
                account = Account(
                    company_id=self.company.id,
                    name=self.company.name,
                    date=self.account_date_field.date().toPyDate(),
                    email_check=self.account_email_check.isChecked(),
                    invoice_check=self.account_invoice_check.isChecked(),
                    done_check=self.account_done_check.isChecked(),
                    status="Early",  # Default status; update as needed
                    files_count=0  # Implement this method to count associated files
                )
                session.add(account)
        except Exception as e:
            logging.exception("Failed to save or update account")
            QMessageBox.critical(self, "Error", f"An error occurred while saving or updating account: {e}")
        #for confirmation statement
        try:
            # Ensure the name field is not None
            company_name = self.company_name_field.text().strip()
            if not company_name:
                raise ValueError("Company name cannot be empty or None")

            # Fetch the existing confirmation statement for the company, if any
            confirmation_statement = session.query(ConfirmationStatement).filter_by(company_id=self.company.id).first()
            
            if confirmation_statement:  # Update the existing confirmation statement
                confirmation_statement.name = self.company_name_field.text()                
                confirmation_statement.date = self.confirmation_date_field.date().toPyDate()
                confirmation_statement.invoice_check = self.confirmation_invoice_check.isChecked()
                confirmation_statement.done_check = self.confirmation_done_check.isChecked()
                confirmation_statement.company_id = self.id_field.text()
                confirmation_statement.status = "Early"
            else:  # Create a new confirmation statement
                confirmation_statement = ConfirmationStatement(
                    company_id=self.company.id,
                    name=company_name,
                    date=self.confirmation_date_field.date().toPyDate(),
                    invoice_check=self.confirmation_invoice_check.isChecked(),
                    done_check=self.confirmation_done_check.isChecked(),
                    status = "Early"
                )
                session.add(confirmation_statement)
        except ValueError as ve:
            logging.exception("Validation error: %s", ve)
            QMessageBox.critical(self, "Error", str(ve))
        except Exception as e:
            logging.exception("Failed to save confirmation statement")
            QMessageBox.critical(self, "Error", f"An error occurred while saving the confirmation statement: {e}")
        #for payrun
        try:
            payrun = session.query(PayRun).filter_by(company_id=self.company.id).first()
            if payrun:  # Update existing payrun
                payrun.date = self.payrun_date_field.date().toPyDate()
                payrun.month_check = self.payrun_month_check.isChecked()
                payrun.pay_run = self.payrun_pay_run_check.isChecked()
                payrun.p60 = self.payrun_p60_check.isChecked()
                payrun.files_count = 0
                payrun.status = "Early"
                payrun.company_name = self.company_name_field.text()
                payrun.company_id = self.id_field.text()
            else:  # Create new payrun
                payrun = PayRun(
                    company_id=self.company.id,
                    date=self.payrun_date_field.date().toPyDate(),
                    month_check=self.payrun_month_check.isChecked(),
                    pay_run=self.payrun_pay_run_check.isChecked(),
                    p60=self.payrun_p60_check.isChecked(),
                    files_count = 0,
                    status = "Early",
                    company_name = self.company_name_field.text(),
                )
                session.add(payrun)
        except Exception as e:
            logging.exception("Failed to save payrun")
            QMessageBox.critical(self, "Error", f"An error occurred while saving payrun: {e}")
        #for cis
        try:
            # Check if the company has CIS enabled
            if self.cis_check.isChecked():
                # Check if a CIS record already exists for the company
                cis = session.query(CIS).filter_by(company_id=self.company.id).first()

                if cis:
                    # Update existing CIS data
                    cis.name = self.company_name_field.text()
                    cis.employees_reference = self.cis_employee_ref_field.text()
                    cis.last_month = self.cis_last_month_field.date().toPyDate()
                    cis.next_month = self.cis_next_month_field.date().toPyDate()
                    cis.email_check = self.cis_email_check.isChecked()
                    cis.month_check = self.cis_month_check.isChecked()
                    cis.status ='Early'
                else:
                    # Create new CIS record
                    cis = CIS(
                        company_id=self.company.id,
                        name = self.company_name_field.text(),
                        employees_reference=self.cis_employee_ref_field.text(),
                        last_month=self.cis_last_month_field.date().toPyDate(),
                        next_month=self.cis_next_month_field.date().toPyDate(),
                        email_check=self.cis_email_check.isChecked(),
                        month_check=self.cis_month_check.isChecked(),
                        status="Early"
                    )
                    session.add(cis)

            else:
                # If CIS is not enabled, delete existing CIS records
                cis = session.query(CIS).filter_by(company_id=self.company.id).first()
                if cis:
                    session.delete(cis)
        except Exception as e:
            logging.exception("Failed to save CIS data")
            QMessageBox.critical(self, "Error", f"An error occurred while saving CIS data: {e}")
        #for vat
        if self.vat_check.isChecked():
            try:
                # Fetch the existing VAT record for the company, if any
                vat = session.query(VAT).filter_by(company_id=self.company.id).first()

                # Ensure that the company name and address are available
                company_name = self.company_name_field.text().strip()
                if not company_name:
                    raise ValueError("Company name cannot be empty or None")
                
                if not self.company.address:
                    raise ValueError("Company address cannot be empty or None")
                
                # Update existing VAT record
                if vat:
                    vat.number = self.vat_number_field.text()
                    vat.registration_date = self.vat_registration_date_field.date().toPyDate()
                    vat.address_id = self.company.address.id  # Ensure this is set correctly
                    vat.company_number = self.company.house_number  # Assuming this field corresponds
                    vat.company_name = company_name
                    vat.start_date = self.vat_start_date_field.date().toPyDate()
                    vat.end_date = self.vat_end_date_field.date().toPyDate()
                    vat.due_date = self.vat_due_date_field.date().toPyDate()
                    vat.calculations = self.vat_calculations_field.text()
                    vat.files_count = 0  # Assuming files count should be reset or recalculated
                    vat.done = self.vat_done_check.isChecked()
                    vat.status = "Early"  # Update the status as needed
                else:
                    # Create a new VAT record
                    vat = VAT(
                        company_id=self.company.id,
                        number=self.vat_number_field.text(),
                        registration_date=self.vat_registration_date_field.date().toPyDate(),
                        address_id=self.company.address.id,  # This must not be None
                        company_number=self.company.house_number,
                        company_name=company_name,
                        start_date=self.vat_start_date_field.date().toPyDate(),
                        end_date=self.vat_end_date_field.date().toPyDate(),
                        due_date=self.vat_due_date_field.date().toPyDate(),
                        calculations=self.vat_calculations_field.text(),
                        files_count=0,
                        done=self.vat_done_check.isChecked(),
                        status="Early"
                    )
                    session.add(vat)
            except ValueError as ve:
                logging.exception("Validation error: %s", ve)
                QMessageBox.critical(self, "Error", str(ve))
            except IntegrityError as ie:
                session.rollback()
                logging.exception("Integrity error during save")
                QMessageBox.critical(self, "Error", f"An integrity error occurred while saving VAT: {ie}")
            except Exception as e:
                session.rollback()
                logging.exception("Failed to save VAT")
                QMessageBox.critical(self, "Error", f"An error occurred while saving VAT: {e}")
        #for employer
        try:
            # Fetch the existing employers from the database
            existing_employers = {emp.id: emp for emp in session.query(Employer).filter_by(company_id=self.company.id).all()}

            for row in range(self.employer_table.rowCount()):
                employer_id = self.employer_table.item(row, 0).data(Qt.UserRole)
                if employer_id:  # Update existing employer
                    employer = existing_employers.get(employer_id)
                    if employer:
                        employer.name = self.employer_table.item(row, 0).text()
                        employer.email = self.employer_table.item(row, 1).text()
                        employer.utr = self.employer_table.item(row, 2).text() if self.employer_table.item(row, 2).text() else None
                        employer.nino = self.employer_table.item(row, 3).text()
                        # Fetch date from QDateEdit
                        date_widget = self.employer_table.cellWidget(row, 4)
                        if isinstance(date_widget, QDateEdit):
                            employer.start_date = date_widget.date().toPyDate()

                else:  # Add new employer
                    new_employer = Employer(
                        name=self.employer_table.item(row, 0).text(),
                        email=self.employer_table.item(row, 1).text(),
                        utr=self.employer_table.item(row, 2).text() if self.employer_table.item(row, 2).text() else None,
                        nino=self.employer_table.item(row, 3).text(),
                        start_date=self.employer_table.cellWidget(row, 4).date().toPyDate(),
                        company_id=self.company.id,
                    )
                    session.add(new_employer)

            # Remove any employers from the database that are no longer in the table
            employer_ids_in_table = [self.employer_table.item(row, 0).data(Qt.UserRole) for row in range(self.employer_table.rowCount())]
            for employer_id in existing_employers:
                if employer_id not in employer_ids_in_table:
                    session.delete(existing_employers[employer_id])
        except Exception as e:
            logging.exception("Failed to save employer data")
            QMessageBox.critical(self, "Error", f"An error occurred while saving employer data: {e}")
        #for director
        try:
            # Fetch existing directors from the database
            existing_directors = {director.id: director for director in session.query(Director).filter_by(company_id=self.company.id).all()}

            for row in range(self.director_table.rowCount()):
                director_id = self.director_table.item(row, 0).data(Qt.UserRole)

                if director_id and director_id in existing_directors:
                    # Update the existing director
                    director = existing_directors[director_id]
                    director.name = self.director_table.item(row, 0).text()
                    director.insurance_number = self.director_table.item(row, 1).text()
                    director.phone = self.director_table.item(row, 2).text()
                    director.email = self.director_table.item(row, 3).text()

                    # Update the director's address
                    if director.address:
                        director.address.number = int(self.director_table.item(row, 4).text())
                        director.address.street = self.director_table.item(row, 5).text()
                        director.address.city = self.director_table.item(row, 6).text()
                        director.address.postcode = self.director_table.item(row, 7).text()
                        director.address.country = self.director_table.item(row, 8).text()
                    else:
                        # If no address exists, create a new one
                        director.address = Address(
                            number=int(self.director_table.item(row, 4).text()),
                            street=self.director_table.item(row, 5).text(),
                            city=self.director_table.item(row, 6).text(),
                            postcode=self.director_table.item(row, 7).text(),
                            country=self.director_table.item(row, 8).text()
                        )
                    # Remove from the existing directors dictionary once processed
                    del existing_directors[director_id]

                else:
                    # Add new director
                    director_address = Address(
                        number=int(self.director_table.item(row, 4).text()),
                        street=self.director_table.item(row, 5).text(),
                        city=self.director_table.item(row, 6).text(),
                        postcode=self.director_table.item(row, 7).text(),
                        country=self.director_table.item(row, 8).text()
                    )
                    session.add(director_address)
                    session.flush()  # Ensure address ID is generated

                    new_director = Director(
                        name=self.director_table.item(row, 0).text(),
                        insurance_number=self.director_table.item(row, 1).text(),
                        phone=self.director_table.item(row, 2).text(),
                        email=self.director_table.item(row, 3).text(),
                        address_id=director_address.id,
                        company_id=self.company.id
                    )
                    session.add(new_director)
                    session.flush()  # Ensure the director ID is generated and added to the table

                    # Store the director ID back in the table's user role for future saves
                    self.director_table.item(row, 0).setData(Qt.UserRole, new_director.id)

            # Any remaining directors in the existing_directors dict are not present in the UI, so they should be deleted
            for director_id, director in existing_directors.items():
                session.delete(director)
        except ValueError as ve:
            logging.exception("Failed to save director")
            QMessageBox.critical(self, "Error", f"Invalid data: {ve}")
        except Exception as e:
            logging.exception("Failed to save director")
            QMessageBox.critical(self, "Error", f"An error occurred while saving directors: {e}")
        self.save_files(session)

    def update_foreign_keys(self, session, old_company_id, new_company_id):
        """Update foreign keys for all related tables if the company ID has changed."""
        try:
            queries = [
                "UPDATE account SET company_id = :new_id WHERE company_id = :old_id",
                "UPDATE confirmation_statement SET company_id = :new_id WHERE company_id = :old_id",
                "UPDATE cis SET company_id = :new_id WHERE company_id = :old_id",
                "UPDATE employer SET company_id = :new_id WHERE company_id = :old_id",
                "UPDATE files SET company_id = :new_id WHERE company_id = :old_id",
                "UPDATE payrun SET company_id = :new_id WHERE company_id = :old_id",
                "UPDATE vat SET company_id = :new_id WHERE company_id = :old_id",
                "UPDATE director SET company_id = :new_id WHERE company_id = :old_id"
            ]
            for query in queries:
                session.execute(text(query), {"new_id": new_company_id, "old_id": old_company_id})
        except Exception as e:
            logging.exception("Failed to update foreign keys")
            raise

    def toggle_edit_mode(self, edit_mode):
        """Enable or disable edit mode for all form fields."""
        for widget in self.findChildren(QLineEdit):
            widget.setReadOnly(not edit_mode)
            widget.setStyleSheet("background-color: white;" if edit_mode else "background-color: lightgray;")

        for widget in self.findChildren(QDateEdit):
            widget.setEnabled(edit_mode)
            widget.setCalendarPopup(True)
            widget.setStyleSheet("background-color: white;" if edit_mode else "background-color: lightgray;")

        for widget in self.findChildren(QCheckBox):
            widget.setEnabled(edit_mode)

        # Toggle edit mode for tables
        self.toggle_table_edit_mode(self.employer_table, edit_mode)
        self.toggle_table_edit_mode(self.director_table, edit_mode)
        self.toggle_table_edit_mode(self.file_table, edit_mode)

        self.upload_file_button.setEnabled(edit_mode)
        self.add_employer_button.setEnabled(edit_mode)
        self.delete_employer_button.setEnabled(edit_mode)
        self.add_director_button.setEnabled(edit_mode)
        self.delete_director_button.setEnabled(edit_mode)

        self.edit_view_button.setText("View" if edit_mode else "Edit")

    def toggle_table_edit_mode(self, table, edit_mode):
        """Helper function to enable or disable edit mode for a table."""
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item:
                    item.setFlags(item.flags() | Qt.ItemIsEditable if edit_mode else item.flags() & ~Qt.ItemIsEditable)

    def upload_file(self):
        """Upload a file and add it to the file table."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Upload File", "", "All Files (*);;PDF Files (*.pdf)", options=options)
        if file_name:
            try:
                target_dir = "files"
                os.makedirs(target_dir, exist_ok=True)  # Ensure directory exists

                target_path = os.path.join(target_dir, os.path.basename(file_name))
                
                # Check if the file already exists to avoid overwriting
                if os.path.exists(target_path):
                    QMessageBox.warning(self, "File Upload", f"File '{os.path.basename(file_name)}' already exists.")
                    return

                shutil.copy(file_name, target_path)  # Copy the file to the target directory

                row_count = self.file_table.rowCount()
                self.file_table.insertRow(row_count)
                self.file_table.setItem(row_count, 0, QTableWidgetItem(os.path.basename(file_name)))
                
                type_combo = QComboBox()
                type_combo.addItems(['Company', 'Vat', 'Account', 'Payrun'])
                self.file_table.setCellWidget(row_count, 1, type_combo)

                QMessageBox.information(self, "File Upload", f"File '{os.path.basename(file_name)}' uploaded successfully!")

            except (FileNotFoundError, PermissionError) as e:
                logging.exception("Failed to upload file due to file system error")
                QMessageBox.critical(self, "File System Error", f"File system error occurred: {e}")
            except Exception as e:
                logging.exception("Failed to upload file")
                QMessageBox.critical(self, "Error", f"An error occurred while uploading the file: {e}")

    def execute_with_retry(self, session, statement, params, retries=5, delay=1):
        attempt = 0
        while attempt < retries:
            try:
                session.execute(statement, params)
                session.commit()
                break
            except OperationalError as e:
                if "database is locked" in str(e):
                    attempt += 1
                    sleep(delay)
                    logging.warning(f"Database is locked, retrying {attempt}/{retries}...")
                    continue
                else:
                    session.rollback()
                    raise
            except Exception as e:
                session.rollback()
                raise

    def add_field(self, layout, label, row, col, readonly=False):
        """Helper method to add a QLineEdit field to the layout."""
        field_label = QLabel(label)
        field_input = QLineEdit()
        field_input.setReadOnly(readonly)
        if readonly:
            field_input.setStyleSheet("background-color: lightgray;")
        layout.addWidget(field_label, row, col)
        layout.addWidget(field_input, row, col + 1)
        return field_input

    def add_checkbox(self, layout, label, row, col, readonly=False):
        """Helper method to add a QCheckBox to the layout."""
        checkbox = QCheckBox(label)
        checkbox.setEnabled(not readonly)
        layout.addWidget(checkbox, row, col)
        return checkbox

    def add_date_field(self, layout, label, row, col, readonly=False):
        """Helper method to add a QDateEdit field to the layout."""
        field_label = QLabel(label)
        field_input = QDateEdit()
        field_input.setCalendarPopup(True)
        field_input.setDisplayFormat("dd-MM-yyyy")
        field_input.setFont(QFont("Arial", 10))
        field_input.setMinimumWidth(120)
        field_input.setFixedHeight(50)
        field_input.setDate(QDate.currentDate())
        layout.addWidget(field_label, row, col)
        layout.addWidget(field_input, row, col + 1)
        return field_input

    def toggle_cis_vat_fields(self):
        """Toggle the enable/disable state of CIS and VAT fields based on the checkboxes."""
        cis_enabled = self.cis_check.isChecked()
        self.cis_employee_ref_field.setEnabled(cis_enabled)
        self.cis_last_month_field.setEnabled(cis_enabled)
        self.cis_next_month_field.setEnabled(cis_enabled)
        self.cis_email_check.setEnabled(cis_enabled)
        self.cis_month_check.setEnabled(cis_enabled)

        vat_enabled = self.vat_check.isChecked()
        self.vat_number_field.setEnabled(vat_enabled)
        self.vat_registration_date_field.setEnabled(vat_enabled)
        self.vat_start_date_field.setEnabled(vat_enabled)
        self.vat_end_date_field.setEnabled(vat_enabled)
        self.vat_due_date_field.setEnabled(vat_enabled)
        self.vat_calculations_field.setEnabled(vat_enabled)
        self.vat_done_check.setEnabled(vat_enabled)


    def edit_view_data(self):
        """Toggle between edit and view modes."""
        self.is_edit_mode = not self.is_edit_mode
        self.toggle_edit_mode(self.is_edit_mode)

    def add_employer_row(self):
        """Add a new row to the employer table."""
        row_count = self.employer_table.rowCount()
        self.employer_table.insertRow(row_count)

        # Create QDateEdit for the new row
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("dd-MM-yyyy")
        date_edit.setDate(QDate.currentDate())
        date_edit.setFont(QFont("Arial", 9))
        date_edit.setMinimumWidth(120)
        date_edit.setFixedHeight(50)
        self.employer_table.setCellWidget(row_count, 4, date_edit)

        # Set the row height to match the QDateEdit height
        self.employer_table.setRowHeight(row_count, date_edit.sizeHint().height())

        # Add other columns with default values
        for col in range(4):
            item = QTableWidgetItem()
            self.employer_table.setItem(row_count, col, item)

    def delete_employer_row(self):
        """Delete the selected row from the employer table."""
        selected_row = self.employer_table.currentRow()
        if selected_row >= 0:
            self.employer_table.removeRow(selected_row)

    def add_director_row(self):
        """Add a new row to the director table."""
        row_count = self.director_table.rowCount()
        self.director_table.insertRow(row_count)

    def delete_director_row(self):
        """Delete the selected row from the director table."""
        selected_row = self.director_table.currentRow()
        if selected_row >= 0:
            self.director_table.removeRow(selected_row)
    

    def save_files(self, session):
        """Save or update file details for the company and upload to Google Drive."""
        # Authenticate with Google Drive using the service account
        service = authenticate_google_drive()

        for row in range(self.file_table.rowCount()):
            try:
                file_name = self.file_table.item(row, 0).text()
                file_type = self.file_table.cellWidget(row, 1).currentText()

                # Validate file data before proceeding
                if not file_name or not file_type:
                    raise ValueError("File name or type is missing.")

                # Ensure the company_id is valid and exists
                if not self.company or not self.company.id:
                    raise ValueError("The company ID is missing or invalid.")

                # Ensure the company_name is not None
                company_name = self.company_name_field.text()
                if not company_name:
                    raise ValueError("The company name cannot be None or empty.")

                # Check if the file already exists for the company
                existing_file = session.query(Files).filter_by(
                    name=file_name,
                    second_id=file_type,
                    company_id=self.company.id
                ).first()

                if existing_file:
                    # If the file exists, log it or handle it accordingly
                    logging.info(f"File '{file_name}' already exists for company '{self.company.id}'. Skipping re-upload.")
                    continue  # Skip to the next file

                # If the file does not exist, upload it to Google Drive and save the path
                local_file_path = os.path.join("files", file_name)  # Local file path
                google_drive_file_id = self.upload_file_to_google_drive(service, file_name, local_file_path)  # Upload to Google Drive

                # Save the file details in the database
                file = Files(
                    name=file_name,
                    second_id=file_type,
                    company_id=self.company.id,
                    path=f"https://drive.google.com/file/d/{google_drive_file_id}/view",  # Google Drive link
                    company_name=company_name
                )
                session.add(file)  # Add the new file to the session

            except ValueError as ve:
                QMessageBox.critical(self, "Error", f"Invalid file data at row {row + 1}: {ve}")
            except SQLAlchemyError as se:
                logging.exception("Database error when saving file")
                QMessageBox.critical(self, "Error", f"Database error while saving file: {se}")
            except Exception as e:
                logging.exception("Failed to save file")
                QMessageBox.critical(self, "Error", f"An unexpected error occurred while saving file: {e}")

    def upload_file_to_google_drive(self, service, file_name, file_path):
        """Upload a file to Google Drive."""
        try:
            # Set the folder ID where the file will be uploaded (your shared folder ID)
            folder_id = '15OclGTq9SFDYl9pBA69Gs5-jy2dUwxrZ'
            
            # Metadata with the folder ID to upload the file to the specific folder
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]  # Specify the folder ID here
            }
            
            media = MediaFileUpload(file_path, mimetype='application/octet-stream')
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = file.get('id')
            logging.info(f"File uploaded successfully. File ID: {file_id}")
            
            # Now set the file permissions so anyone with the link can view the file
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(fileId=file_id, body=permission).execute()
            logging.info(f"Permissions updated for file ID: {file_id}")
            
            return file_id  # Return the file ID from Google Drive

        except Exception as e:
            logging.error(f"An error occurred while uploading the file: {e}")
            return None

    def delete_company(self):
        """Delete the company and all related data."""
        try:
            if self.is_edit_mode:
                response = QMessageBox.question(
                    self, "Confirm Delete", "Are you sure you want to delete this company?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if response == QMessageBox.Yes:
                    with get_session() as session:
                        session.delete(self.company)
                        session.commit()
                    QMessageBox.information(self, "Deleted", "Company deleted successfully!")
                    self.close_tab()
            else:
                QMessageBox.warning(self, "Error", "No company to delete!")
        except Exception as e:
            logging.exception("Failed to delete company data")
            QMessageBox.critical(self, "Error", f"An error occurred while deleting: {e}")

    def close_tab_save(self):
        """Close the form tab."""
        self.tab_widget.removeTab(self.tab_widget.indexOf(self))
        self.redirect_to_all_companies_tab()  # Redirect to the AllCompaniesTab after closing
   
    def close_tab(self):
        """Close the form tab."""
        self.tab_widget.removeTab(self.tab_widget.indexOf(self))
        self.redirect_to_all()
   
    def redirect_to_all_companies_tab(self):
        """Redirect to the AllCompaniesTab after closing this tab and refresh the file tab."""
        from all_companies_tab import AllCompaniesTab
        from tab_file import FilesTab  # Assuming FilesTab is in a file named filestab.py
        
        all_companies_tab_refreshed = False
        file_tab_refreshed = False

        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            
            # Check for the AllCompaniesTab and refresh it
            if isinstance(widget, AllCompaniesTab):
                self.tab_widget.setCurrentIndex(i)
                if hasattr(widget, 'refresh_tabs'):
                    widget.refresh_tabs()  # Refresh all tabs after closing this form
                    all_companies_tab_refreshed = True
                    
            # Check if this is an instance of FilesTab and refresh its data
            elif isinstance(widget, FilesTab):
                widget.refresh_data()  # Call the refresh_data method from FilesTab
                file_tab_refreshed = True

        # Ensure both actions are completed
        if not all_companies_tab_refreshed:
            print("AllCompaniesTab not found or refresh_tabs method missing.")

        if not file_tab_refreshed:
            print("FilesTab not found or refresh_data method missing.")

    def redirect_to_all(self):
        """Redirect to the AllCompaniesTab after closing this tab without refreshing."""
        from all_companies_tab import AllCompaniesTab

        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)

            # Check for the AllCompaniesTab and switch to it
            if isinstance(widget, AllCompaniesTab):
                self.tab_widget.setCurrentIndex(i)
                break

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)

    tab_widget = QTabWidget()
    company_form = CompanyForm(tab_widget)
    tab_widget.addTab(company_form, "Company Form")

    layout.addWidget(tab_widget)
    window.setLayout(layout)
    window.show()

    sys.exit(app.exec_())
