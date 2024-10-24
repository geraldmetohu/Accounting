from datetime import datetime
import sys
import os
import logging
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QComboBox, QDateEdit, QCheckBox, QPushButton, QMessageBox,
    QHeaderView, QFileDialog, QGridLayout, QApplication,
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QDate
from sqlalchemy import and_
from backend import get_session
from paid_tasks import PaidTasksTab
from models import Task, Files
from google.oauth2.service_account import Credentials 
from googleapiclient.discovery import build 
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_service_account_file_path():
    """Dynamically retrieves the path to the service account file."""
    # Get the current directory where the script is located
    script_dir = os.path.dirname(os.path.realpath(__file__))
    
    # The name of the service account file
    service_account_file = os.path.join(script_dir, "adroit-producer-421409-e1fdc9fd2b6f.json")

    # Check if the file exists
    if not os.path.exists(service_account_file):
        raise FileNotFoundError(f"Service account file not found: {service_account_file}")
    
    return service_account_file

# Get the service account file path dynamically
SERVICE_ACCOUNT_FILE = get_service_account_file_path()

def authenticate_google_drive():
    """Authenticate and return the Google Drive service using a service account."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    return service

class TaskTab(QWidget):
    def __init__(self, tab_widget, parent=None):
        super().__init__(parent)
        self.tasks = []  # Holds loaded tasks
        self.tab_widget = tab_widget
        self.updating_item = False
        self.main_window = parent
        self.initUI()

    def initUI(self):
        """Initialize the UI layout."""
        layout = QVBoxLayout()

        # Search and Sort Layout
        search_sort_layout = QHBoxLayout()

        # Search bar
        self.search_label = QLabel('Search:')
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText('Search...')
        self.search_bar.textChanged.connect(self.search_data)
        search_sort_layout.addWidget(self.search_label)
        search_sort_layout.addWidget(self.search_bar)

        # Sorting Dropdown
        self.sort_dropdown = QComboBox(self)
        self.sort_dropdown.addItems([
            'Default', 'Sort Name Asc', 'Sort Name Desc',
            'Sort Date Added Asc', 'Sort Date Added Desc', 'Sort Price Asc', 'Sort Price Desc'
        ])
        self.sort_dropdown.currentIndexChanged.connect(self.sort_data)
        search_sort_layout.addWidget(self.sort_dropdown)

        # Add Refresh Button
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.refresh)
        search_sort_layout.addWidget(self.refresh_button)

        layout.addLayout(search_sort_layout)

        # Table for displaying tasks
        self.table = QTableWidget(self)
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Name', 'Task Type', 'Date Added', 'Date Finished', 'Price', 'Done By', 'Status',
            'Invoice Sent', 'Invoice Paid', 'Office', 'Files'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.cellDoubleClicked.connect(self.edit_cell)
        layout.addWidget(self.table)

        self.load_data()  # Load initial data into the table

        # Form Layout for entering new data
        form_layout = QGridLayout()
        form_layout.addWidget(QLabel('Task Name:'), 0, 0)
        self.name_input = QLineEdit(self)
        form_layout.addWidget(self.name_input, 1, 0)

        form_layout.addWidget(QLabel('Task Type:'), 0, 1)
        self.task_type_input = QLineEdit(self)
        form_layout.addWidget(self.task_type_input, 1, 1)

        form_layout.addWidget(QLabel('Date Added:'), 0, 2)
        self.date_added_input = QDateEdit(self)
        self.date_added_input.setCalendarPopup(True)
        self.date_added_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.date_added_input, 1, 2)

        form_layout.addWidget(QLabel('Price:'), 0, 3)
        self.price_input = QLineEdit(self)
        form_layout.addWidget(self.price_input, 1, 3)

        form_layout.addWidget(QLabel('Status:'), 0, 4)
        self.status_input = QComboBox(self)
        self.status_input.addItems(['not_started', 'in_process', 'details_missing', 'done', 'paid'])
        form_layout.addWidget(self.status_input, 1, 4)

        form_layout.addWidget(QLabel('Done By:'), 0, 5)
        self.done_by_input = QComboBox(self)
        self.done_by_input.addItems(['Aleks', 'Krista', 'Ledia', 'Denalda', 'Kujtim', 'Other'])
        form_layout.addWidget(self.done_by_input, 1, 5)

        form_layout.addWidget(QLabel('Invoice Sent:'), 0, 6)
        self.invoice_sent_input = QCheckBox(self)
        form_layout.addWidget(self.invoice_sent_input, 1, 6)

        form_layout.addWidget(QLabel('Invoice Paid:'), 0, 7)
        self.invoice_paid_input = QCheckBox(self)
        form_layout.addWidget(self.invoice_paid_input, 1, 7)

        form_layout.addWidget(QLabel('Office:'), 0, 8)
        self.office_input = QComboBox(self)
        self.office_input.addItems(['london', 'leeds'])
        form_layout.addWidget(self.office_input, 1, 8)

        # Save Button
        button_layout = QHBoxLayout()

        # View Paid Button
        self.view_paid_button = QPushButton('View Paid', self)
        self.view_paid_button.clicked.connect(self.view_paid)
        button_layout.addWidget(self.view_paid_button)

        # Upload Files Button
        self.upload_button = QPushButton('Upload Files', self)
        self.upload_button.clicked.connect(self.upload_files)
        button_layout.addWidget(self.upload_button)

        # Save Button
        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save_task)
        button_layout.addWidget(self.save_button)

        # Add the button layout to the form layout in the correct position (row 2, column 0)
        form_layout.addLayout(button_layout, 2, 0)

        # Add the form layout to the main layout
        layout.addLayout(form_layout)

        # Set the layout for the widget
        self.setLayout(layout)

    def load_data(self):
        """Load existing tasks into the table."""
        start_time = time.time()  # Record the start time
        print("Task 1:", datetime.now().strftime("%H:%M:%S"))
        
        self.table.setRowCount(0)  # Clear table before loading new data
        self.tasks = []  # Reset tasks list

        with get_session() as session:
            # Query tasks from the database and sort by status
            tasks = session.query(Task).filter(Task.status != 'paid').all()

            # Sort tasks by status priority
            status_priority = {
                'not_started': 1,
                'in_process': 2,
                'details_missing': 3,
                'done': 4,
            }
            tasks_sorted = sorted(tasks, key=lambda t: status_priority.get(t.status, 5))

            self.table.setRowCount(len(tasks_sorted))  # Set the row count
            for row, task in enumerate(tasks_sorted):
                self.add_task_to_table(row, task)
                # After adding the task, set the row color based on task status
                self.set_row_color(row, task.status)
        print("Task 2:", datetime.now().strftime("%H:%M:%S"))
        end_time = time.time()  # Record the end time
        print("Total Task: {:.2f} seconds".format(end_time - start_time))

    def add_task_to_table(self, row, task):
        """Helper function to add a task to a specific row in the table."""
        # ID column (make this column read-only)
        if task.id:
            item_id = QTableWidgetItem(str(task.id))
            item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable)  # Make ID column uneditable
            self.table.setItem(row, 0, item_id)
        else:
            logging.error(f"Task {row} does not have a valid ID.")

        # Editable columns (Task Name, Task Type)
        self.table.setItem(row, 1, QTableWidgetItem(task.task_name))
        self.table.setItem(row, 2, QTableWidgetItem(task.task_type))

        # Date Added and Date Finished columns
        date_added_str = task.date_added.strftime('%Y-%m-%d') if task.date_added else ''
        self.table.setItem(row, 3, QTableWidgetItem(date_added_str))

        date_finished_str = task.date_finished.strftime('%Y-%m-%d') if task.date_finished else ''
        self.table.setItem(row, 4, QTableWidgetItem(date_finished_str))

        # Price column
        self.table.setItem(row, 5, QTableWidgetItem(f'{task.price:.2f}' if task.price else ''))

        # Done By column (enum dropdown handled in edit_cell)
        self.table.setItem(row, 6, QTableWidgetItem(task.done_by))

        # Status column (enum dropdown handled in edit_cell)
        self.table.setItem(row, 7, QTableWidgetItem(task.status))

        # Invoice Sent and Invoice Paid columns
        invoice_sent_item = QCheckBox()
        invoice_sent_item.setChecked(task.invoice_sent)
        invoice_sent_item.stateChanged.connect(lambda state, task_id=task.id: self.handle_check_change(task_id, row, 'invoice_sent', state))
        self.table.setCellWidget(row, 8, invoice_sent_item)

        invoice_paid_item = QCheckBox()
        invoice_paid_item.setChecked(task.invoice_paid)
        invoice_paid_item.stateChanged.connect(lambda state, task_id=task.id: self.handle_check_change(task_id, row, 'invoice_paid', state))
        self.table.setCellWidget(row, 9, invoice_paid_item)
        
        # Office column
        self.table.setItem(row, 10, QTableWidgetItem(task.office))

        # Files count column (Make read-only)
        item_count = QTableWidgetItem(str(task.files_count))
        item_count.setFlags(item_count.flags() & ~Qt.ItemIsEditable)  # Make last column uneditable
        self.table.setItem(row, 11, item_count)

    def set_row_color(self, row, status):
        """Set the background color of a row based on task status and update checkbox color accordingly."""
        # Define color map for statuses
        color_map = {
            'not_started': QColor(251, 55, 107, 127),  # Red
            'in_process': QColor(247, 131, 34, 127),   # Orange
            'details_missing': QColor(241, 240, 133, 127),  # Yellow
            'done': QColor(87, 242, 141, 127),         # Green
            'paid': QColor(192, 192, 192, 127),        # Gray
        }

        # Get the color for the current status, default to white if not found
        color = color_map.get(status, QColor(255, 255, 255, 127))

        # Set background color for the entire row
        self.set_row_background_color(row, color)

        # Additionally set the background color for the checkboxes in the row
        self.set_checkbox_background(row, color)

    def set_row_background_color(self, row, color):
        """Set the background color of a specific row."""
        for column in range(self.table.columnCount()):
            item = self.table.item(row, column)
            if item:
                item.setBackground(color)

    def set_checkbox_background(self, row, color):
        """Update checkbox background color based on the status color."""
        for col in [8, 9]:  # Columns for 'Invoice Sent' and 'Invoice Paid' checkboxes
            checkbox = self.table.cellWidget(row, col)
            if checkbox and isinstance(checkbox, QCheckBox):
                checkbox.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha() / 255.0});")

    def refresh(self):
        """Refresh the table data."""
        self.update_files_count()
        self.load_data()

    def update_files_count(self):
        """Update the files count for each task."""
        try:
            with get_session() as session:
                tasks = session.query(Task).all()
                for task in tasks:
                    file_count = session.query(Files).filter(and_(Files.company_name == task.task_name, Files.second_id == 'Task')).count()
                    task.files_count = file_count
                session.commit()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while updating file counts: {str(e)}')

    def edit_cell(self, row, column):
        """Handle cell editing for specific columns like enums, dates, and text fields."""
        logging.info(f"Editing cell at row {row}, column {column}")
        if column == 0 or column == 11:
            logging.info(f"Column {column} is not editable.")
            return  # Do nothing if the column is the first or last

        # Enum dropdown for 'Done By', 'Status', and 'Office' columns
        if column in [6, 7, 10]:  # 'Done By', 'Status', 'Office'
            logging.info(f"Initiating dropdown for column {column}")
            combo_box = QComboBox(self.table)

            if column == 6:
                combo_box.addItems(['Aleks', 'Krista', 'Ledia', 'Denalda', 'Kujtim', 'Other'])
            elif column == 7:
                combo_box.addItems(['not_started', 'in_process', 'details_missing', 'done', 'paid'])
            elif column == 10:
                combo_box.addItems(['london', 'leeds'])

            current_text = self.table.item(row, column).text()
            combo_box.setCurrentText(current_text)
            logging.info(f"Current value in combo box: {current_text}")

            self.table.setCellWidget(row, column, combo_box)
            combo_box.activated.connect(lambda: self.save_combo_value(row, column, combo_box))

        # Date picker for 'Date Added' and 'Date Finished' columns
        elif column in [3, 4]:  # 'Date Added', 'Date Finished'
            logging.info(f"Initiating date picker for column {column}")
            date_edit = QDateEdit(self.table)
            date_edit.setCalendarPopup(True)
            current_text = self.table.item(row, column).text()

            if current_text:
                logging.info(f"Setting date from text: {current_text}")
                current_date = QDate.fromString(current_text, 'yyyy-MM-dd')
                if current_date.isValid():
                    date_edit.setDate(current_date)
                else:
                    date_edit.setDate(QDate.currentDate())
            elif column in [1, 2, 5]:
                logging.info(f"Setting default current date")
                date_edit.setDate(QDate.currentDate())

            self.table.setCellWidget(row, column, date_edit)
            date_edit.dateChanged.connect(lambda: self.save_date_value(row, column, date_edit))

        # Text fields for 'Task Name', 'Task Type', etc.
        else:
            logging.info(f"Initiating text editing for column {column}")
            item = self.table.item(row, column)
            if item is not None:
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.table.editItem(item)

                # Temporarily block signals to avoid recursion
                self.table.blockSignals(True)

                # Connect the signal to handle when editing is finished
                self.table.itemChanged.connect(lambda changed_item: self.handle_text_field_save(row, column, changed_item))

                # Re-enable signals after connecting
                self.table.blockSignals(False)

    def handle_text_field_save(self, row, column, item):
        """Save the text field value back to the table and update the database."""
        logging.info(f"Attempting to save text field at row {row}, column {column}")

        if item is None:
            logging.error(f"Item at row {row}, column {column} is None. Aborting save.")
            return  # Prevent further execution if item is None

        if item.row() == row and item.column() == column:
            new_value = item.text()
            logging.info(f"New value entered: {new_value}")

            # Confirm the update with the user
            confirmation = QMessageBox.question(self, "Confirm Update",
                                                "Do you want to save the text field changes to the database?",
                                                QMessageBox.Yes | QMessageBox.No)

            if confirmation == QMessageBox.Yes:
                try:
                    logging.info("Saving changes to the database...")
                    # Validate and save the changes to the database
                    self.validate_before_save(row)
                    self.upload_changes(row)
                    logging.info("Text field changes saved successfully.")
                    self.show_confirmation_message()

                    # Temporarily disconnect signal to prevent multiple triggers
                    self.table.blockSignals(True)
                    self.table.itemChanged.disconnect()  # Disconnect to avoid duplicate signals
                    self.table.blockSignals(False)

                except Exception as e:
                    logging.error(f"Error saving text value: {str(e)}")
                    QMessageBox.critical(self, 'Error', f"Failed to save changes: {str(e)}")
            else:
                logging.info("User canceled the text field changes.")
                # Reset the text field if not confirmed
                self.load_data()  # Reload the data to reset changes
    
    def show_confirmation_message(self):
        """Display a confirmation message after text editing is completed."""
        QMessageBox.information(self, 'Success', 'Changes saved successfully.')

    def save_combo_value(self, row, column, combo_box):
        """Save the selected combo box value back to the table and update the database."""
        selected_value = combo_box.currentText()
        logging.info(f"Combo box selected value for row {row}, column {column}: {selected_value}")

        confirmation = QMessageBox.question(self, "Confirm Update", 
                                            "Do you want to save the changes to the database?",
                                            QMessageBox.Yes | QMessageBox.No)

        if confirmation == QMessageBox.Yes:
            try:
                logging.info(f"Saving combo box value {selected_value} to the database")
                self.table.setItem(row, column, QTableWidgetItem(selected_value))
                self.table.setCellWidget(row, column, None)  # Remove the combo box after saving
                self.validate_before_save(row)
                self.upload_changes(row)

                # After saving, update the row color based on the status
                task_status = self.table.item(row, 7).text()  # Column 7 is the status
                self.set_row_color(row, task_status)
            
                logging.info(f"Combo box value saved and row color updated.")
            except Exception as e:
                logging.error(f"Error saving combo box value: {str(e)}")
                QMessageBox.critical(self, 'Error', f"Failed to save changes: {str(e)}")
        else:
            logging.info("User canceled combo box changes.")

    def save_date_value(self, row, column, date_edit):
        """Save the selected date value back to the table and update the database."""
        selected_date = date_edit.date().toString('yyyy-MM-dd')
        logging.info(f"Date selected for row {row}, column {column}: {selected_date}")

        confirmation = QMessageBox.question(self, "Confirm Update",
                                            "Do you want to save the date changes to the database?",
                                            QMessageBox.Yes | QMessageBox.No)

        if confirmation == QMessageBox.Yes:
            try:
                # Update the date in the table
                logging.info(f"Saving date value {selected_date} for task in row {row} to the database")
                self.table.setItem(row, column, QTableWidgetItem(selected_date))
                self.table.setCellWidget(row, column, None)  # Remove the date edit after saving

                # Validate and commit the changes
                self.validate_before_save(row)
                self.upload_changes(row)

                # After saving, update the row color based on the status
                task_status = self.table.item(row, 7).text()  # Column 7 is the status
                self.set_row_color(row, task_status)
                logging.info(f"Date value saved and row color updated based on status '{task_status}'.")
            
            except Exception as e:
                logging.error(f"Error saving date value for row {row}: {str(e)}")
                QMessageBox.critical(self, 'Error', f"Failed to save changes: {str(e)}")
        else:
            logging.info("User canceled date changes for row {row}.")

    def validate_before_save(self, row):
        """Validate data before saving to the database, ensure finished date is set if status is done/paid."""
        status_column = 7
        date_finished_column = 4

        # Get the current status and date finished values
        status = self.table.item(row, status_column).text()
        date_finished = self.table.item(row, date_finished_column).text()

        logging.info(f"Validating row {row}: status={status}, date_finished={date_finished}")

        # Check if the task is 'done' or 'paid' and date_finished is not set
        if (status == 'done' or status == 'paid') and not date_finished:
            # Set today's date if the date finished is empty
            today_date = QDate.currentDate().toString('yyyy-MM-dd')
            self.table.setItem(row, date_finished_column, QTableWidgetItem(today_date))
            
            logging.info(f"Date Finished set to today's date for row {row} as status changed to {status}")

        else:
            logging.info(f"No changes needed for row {row}: status={status}, date_finished={date_finished}")

    def upload_changes(self, row):
        """Upload the changes from the given row into the database for the corresponding task."""
        try:
            task_id_item = self.table.item(row, 0)
            if task_id_item is None or not task_id_item.text().isdigit():
                raise ValueError(f"Invalid task ID in row {row}. Task ID is either missing or non-numeric.")
            
            task_id = int(task_id_item.text())
            logging.info(f"Task ID for row {row}: {task_id}")

            # Retrieve the updated values from the table
            task_name = self.table.item(row, 1).text()
            task_type = self.table.item(row, 2).text()
            logging.info(f"Task details for row {row}: name={task_name}, type={task_type}")

            # Ensure valid dates are handled before saving
            date_added_text = self.table.item(row, 3).text()
            date_added = QDate.fromString(date_added_text, 'yyyy-MM-dd').toPyDate() if date_added_text else None

            date_finished_text = self.table.item(row, 4).text()
            date_finished = QDate.fromString(date_finished_text, 'yyyy-MM-dd').toPyDate() if date_finished_text else None

            logging.info(f"Dates for row {row}: added={date_added}, finished={date_finished}")

            price_text = self.table.item(row, 5).text()
            price = float(price_text) if price_text else None

            done_by = self.table.item(row, 6).text()
            status = self.table.item(row, 7).text()

            invoice_sent = self.table.cellWidget(row, 8).isChecked()
            invoice_paid = self.table.cellWidget(row, 9).isChecked()

            office = self.table.item(row, 10).text()

            # Update the task within the same session
            with get_session() as session:
                task = session.query(Task).get(task_id)
                if not task:
                    raise ValueError(f"Task with ID {task_id} not found.")

                logging.info(f"Updating task ID {task_id} in the database")

                # Update task fields
                task.task_name = task_name
                task.task_type = task_type
                task.date_added = date_added
                task.date_finished = date_finished
                task.price = price
                task.done_by = done_by
                task.status = status
                task.invoice_sent = invoice_sent
                task.invoice_paid = invoice_paid
                task.office = office

                session.commit()  # Commit the changes to the database

                logging.info(f"Task ID {task_id} successfully updated in the database")

            # Removed `session.refresh(task)` since it's no longer bound after committing.

            QMessageBox.information(self, 'Success', 'Task updated successfully.')

        except Exception as e:
            logging.error(f"Failed to update task: {str(e)}")
            QMessageBox.critical(self, 'Error', f"Failed to update task: {str(e)}")

    def handle_check_change(self, task_id, row, field, state):
        """
        This method is triggered when a checkbox is changed. It handles updating the database
        and performing logic based on state changes in the checkbox fields.
        
        Args:
            task_id (int): The ID of the task being updated.
            row (int): The row of the task in the table.
            field (str): The field being updated (either 'invoice_sent' or 'invoice_paid').
            state (int): The new state of the checkbox (Qt.Checked or Qt.Unchecked).
        """
        try:
            # Update the task within the same session
            with get_session() as session:
                task = session.query(Task).get(task_id)

                if not task:
                    logging.error(f"Task with ID {task_id} not found.")
                    return

                # Update the task's field based on the checkbox state
                if field == 'invoice_sent':
                    task.invoice_sent = (state == Qt.Checked)
                elif field == 'invoice_paid':
                    task.invoice_paid = (state == Qt.Checked)

                # Update the task in the database
                session.commit()

                # Check if both invoice_sent and invoice_paid are True
                if task.invoice_sent and task.invoice_paid:
                    # Prompt the user for confirmation to set status as "paid"
                    confirmation = QMessageBox.question(self, "Confirm Payment",
                                                        "Both 'Invoice Sent' and 'Invoice Paid' are checked. "
                                                        "Do you want to mark this task as 'Paid'?",
                                                        QMessageBox.Yes | QMessageBox.No)

                    if confirmation == QMessageBox.Yes:
                        # Mark the task as 'Paid'
                        task.status = 'paid'

                        # Set the finished date to today if it's not already set
                        if not task.date_finished:
                            task.date_finished = QDate.currentDate().toPyDate()

                        # Update the status and finished date in the table
                        self.table.setItem(row, 7, QTableWidgetItem(task.status))  # Status column
                        self.table.setItem(row, 4, QTableWidgetItem(task.date_finished.strftime('%Y-%m-%d')))  # Date Finished column

                        # Commit the updated task
                        session.commit()

                        # Update row color after the task is paid
                        self.set_row_color(row, task.status)

                        logging.info(f"Task {task_id} has been marked as paid and updated in the database.")
                    else:
                        # If the user selects "No", revert the 'invoice_paid' checkbox to unchecked
                        invoice_paid_item = self.table.cellWidget(row, 9)  # 9 is the column for 'Invoice Paid'
                        invoice_paid_item.setChecked(False)

        except Exception as e:
            logging.error(f"Error updating task {task_id}: {str(e)}")
            QMessageBox.critical(self, 'Error', f"Failed to update task: {str(e)}")

    def save_task(self):
        """Save a new task to the database."""
        logging.info("Saving a new task")
        task_name = self.name_input.text() or 'Other'
        task_type = self.task_type_input.text()
        price = self.price_input.text()
        status = self.status_input.currentText() or 'not_started'

        if not task_type or not price:
            QMessageBox.critical(self, 'Invalid Input', 'Please fill in all required fields (Task Type, Price).')
            return

        try:
            task_price = float(price)
            if task_price <= 0:
                raise ValueError("Price must be greater than zero")
        except ValueError:
            QMessageBox.critical(self, 'Invalid Input', 'Please enter a valid price (a positive number).')
            return

        data = {
            'task_name': task_name,
            'task_type': task_type,
            'date_added': self.date_added_input.date().toPyDate(),
            'date_finished': None,
            'price': task_price,
            'status': status,
            'done_by': self.done_by_input.currentText(),
            'invoice_sent': self.invoice_sent_input.isChecked(),
            'invoice_paid': self.invoice_paid_input.isChecked(),
            'office': self.office_input.currentText(),
            'files_count': 0
        }

        try:
            with get_session() as session:
                new_task = Task(**data)
                session.add(new_task)
                session.commit()
                session.refresh(new_task)

                self.tasks.append(new_task)
                self.load_data()  # Reload data to reflect the new task
                QMessageBox.information(self, 'Task Saved', 'Task successfully saved.')
                self.clear_inputs()
        except Exception as e:
            logging.error(f"Error saving task: {e}")
            QMessageBox.critical(self, 'Error', f'An error occurred while saving the task: {str(e)}')

    def clear_inputs(self):
        """Clear the input fields after saving a task."""
        logging.info("Clearing input fields")
        self.name_input.clear()
        self.task_type_input.clear()
        self.date_added_input.setDate(QDate.currentDate())
        self.price_input.clear()
        self.status_input.setCurrentIndex(0)
        self.done_by_input.setCurrentIndex(0)
        self.invoice_sent_input.setChecked(False)
        self.invoice_paid_input.setChecked(False)
        self.office_input.setCurrentIndex(0)

    def sort_data(self):
        """Sort data in the table based on user selection."""
        sort_option = self.sort_dropdown.currentText()
        column_index, ascending = 0, True

        if sort_option == 'Sort Name Asc':
            column_index, ascending = 1, True
        elif sort_option == 'Sort Name Desc':
            column_index, ascending = 1, False
        elif sort_option == 'Sort Date finished Asc':
            column_index, ascending = 4, True
        elif sort_option == 'Sort Date finished Desc':
            column_index, ascending = 4, False
        elif sort_option == 'Sort Price Asc':
            column_index, ascending = 5, True
        elif sort_option == 'Sort Price Desc':
            column_index, ascending = 5, False

        if sort_option != 'Default':
            self.table.sortItems(column_index, order=Qt.AscendingOrder if ascending else Qt.DescendingOrder)
        else:
            # If "Default" is selected, load data with status-based sorting
            self.load_data()
            
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

    def view_paid(self):
        """Open the PaidTasksTab as a new tab in the main tab widget."""
        # Iterate through all tabs in the main tab widget to check if PaidTasksTab is already open
        for i in range(self.main_window.tab_widget.count()):
            current_tab = self.main_window.tab_widget.widget(i)
            if isinstance(current_tab, PaidTasksTab):
                # If PaidTasksTab is already open, set the current tab to it and return
                self.main_window.tab_widget.setCurrentIndex(i)
                return

        # If PaidTasksTab is not open, create a new instance and add it as a new tab
        paid_tasks_tab = PaidTasksTab(self.main_window.tab_widget)  # Create new PaidTasksTab
        self.main_window.tab_widget.addTab(paid_tasks_tab, "Paid Tasks")  # Add the tab to the tab widget
        self.main_window.tab_widget.setCurrentWidget(paid_tasks_tab)  # Switch to the new PaidTasksTab

    def get_task_id_from_row(self, row):
        """Retrieve the task ID from the selected row."""
        # Assuming the task ID is in the first column (column 0)
        task_id_item = self.table.item(row, 0)
        
        if task_id_item and task_id_item.text().isdigit():
            return int(task_id_item.text())  # Convert task ID to integer and return it
        else:
            return None  # Return None if the ID is invalid or not found

    def upload_files(self):
        """Upload a file for the selected task and save the file details to Google Drive."""
        selected_row = self.table.currentRow()

        if selected_row == -1:
            QMessageBox.warning(self, "No Task Selected", "Please select a task to upload a file.")
            return

        task_id = self.get_task_id_from_row(selected_row)
        task_name_item = self.table.item(selected_row, 1)  # Task name is in column 1
        task_name = task_name_item.text() if task_name_item else None

        if not task_id or not task_name:
            QMessageBox.warning(self, "Invalid Task", "Selected task is invalid.")
            return

        # Open file dialog to select a file
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]  # Get the selected file path

            if not file_path:
                QMessageBox.warning(self, "No File Selected", "Please select a file to upload.")
                return

            file_name = os.path.basename(file_path)

            try:
                service = self.authenticate_google_drive()
                google_drive_file_id = self.upload_file_to_google_drive(service, file_name, file_path)

                if google_drive_file_id:
                    google_drive_link = f"https://drive.google.com/file/d/{google_drive_file_id}/view"
                    
                    # Create a new Files object without a company_id
                    with get_session() as session:
                        new_file = Files(
                            second_id='Task',
                            path=google_drive_link,
                            name=file_name,
                            company_name=task_name,
                            company_id=None  # Set to None for task-related files
                        )
                        session.add(new_file)
                        session.commit()
                        self.update_files_count()
                    QMessageBox.information(self, "File Uploaded", f"File '{file_name}' uploaded successfully for task '{task_name}'.")

            except Exception as e:
                logging.error(f"Failed to upload file to Google Drive for task {task_id}: {str(e)}")
                QMessageBox.critical(self, "Error", f"An error occurred while uploading the file: {str(e)}")

    @staticmethod
    def authenticate_google_drive():
        """Authenticate and return the Google Drive service using a service account."""
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        return service

    def upload_file_to_google_drive(self, service, file_name, file_path):
        """Upload a file to Google Drive and return the file ID."""
        try:
            folder_id = '15OclGTq9SFDYl9pBA69Gs5-jy2dUwxrZ'

            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }

            media = MediaFileUpload(file_path, mimetype='application/octet-stream')
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

            file_id = file.get('id')
            logging.info(f"File '{file_name}' uploaded successfully. File ID: {file_id}")

            # Set file permissions to allow anyone with the link to view
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(fileId=file_id, body=permission).execute()

            return file_id

        except Exception as e:
            logging.error(f"An error occurred while uploading the file to Google Drive: {e}")
            return None

if __name__ == '__main__':
    logging.info("Starting Task Management Application")
    app = QApplication(sys.argv)
    window = TaskTab()
    window.show()
    sys.exit(app.exec_())