import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QApplication, QLabel, QFrame
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from datetime import datetime

from sqlalchemy import and_, or_
from models import DataInsights, Invoice, Task, CIS, VAT, Account, PayRun, ConfirmationStatement
from backend import get_session  # Use the context manager for session handling


class DataInsightsTab(QWidget):
    status_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_interface = 1  # Default to Interface 1
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Create control layout and add it to the main layout
        controls_layout = self.create_controls_layout()
        main_layout.addLayout(controls_layout)

        # Create interface frames and add them to the main layout
        self.interfaces_layout = QHBoxLayout()  # Store it as a class attribute
        interfaces_layout = self.create_interfaces_layout()
        main_layout.addLayout(self.interfaces_layout)

        # Create buttons layout (clear buttons) and add it to the main layout
        buttons_layout = self.create_buttons_layout()
        main_layout.addLayout(buttons_layout)

        # Set the final layout
        self.setLayout(main_layout)



    def create_controls_layout(self):
        """Create the layout for interface selection, category, month, year, and action buttons."""

        # Get the current month and year
        current_month = datetime.now().month
        current_year = datetime.now().year

        self.interface_label = QLabel("Select Interface:")
        self.interface_dropdown = QComboBox()
        self.interface_dropdown.addItems(['Interface 1', 'Interface 2'])
        self.interface_dropdown.currentIndexChanged.connect(self.change_interface)

        self.category_label = QLabel("Select Category:")
        self.category_dropdown = QComboBox()
        self.category_dropdown.addItems(['CIS', 'VAT', 'Account', 'PayRun', 'ConfirmationStatement', 'Invoice', 'Task'])

        # Month dropdown
        self.month_label = QLabel("Select Month:")
        self.month_dropdown = QComboBox()
        self.month_dropdown.addItems([str(i) for i in range(1, 13)])

        # Set current month as the default
        self.month_dropdown.setCurrentIndex(current_month - 1)  # Index starts from 0, so subtract 1

        # Year dropdown
        self.year_label = QLabel("Select Year:")
        self.year_dropdown = QComboBox()
        self.year_dropdown.addItems([str(i) for i in range(2024, current_year + 1)])

        # Set current year as the default
        self.year_dropdown.setCurrentText(str(current_year))

        self.execute_button = QPushButton("Execute")
        self.execute_button.setStyleSheet("""QPushButton {font-size: 10pt; padding: 10px;}""")
        self.execute_button.clicked.connect(self.show_pie_chart)

        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.setStyleSheet("""QPushButton {font-size: 10pt; padding: 10px;}""")
        self.refresh_button.clicked.connect(self.update_insights_table)

        # Layout for the controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.interface_label)
        controls_layout.addWidget(self.interface_dropdown)
        controls_layout.addWidget(self.category_label)
        controls_layout.addWidget(self.category_dropdown)
        controls_layout.addWidget(self.month_label)
        controls_layout.addWidget(self.month_dropdown)
        controls_layout.addWidget(self.year_label)
        controls_layout.addWidget(self.year_dropdown)
        controls_layout.addWidget(self.execute_button)
        controls_layout.addWidget(self.refresh_button)

        return controls_layout


    def create_interfaces_layout(self, interface_num=None):
        """Create the layout for the interface frames displaying the charts and total counts.
        If interface_num is provided, only recreate that specific interface (1 or 2).
        """
        if interface_num is None or interface_num == 1:
            print("Debug: Creating Interface 1 layout...")
            self.interface_frame1 = QFrame(self)
            self.interface_frame1.setFrameShape(QFrame.StyledPanel)
            self.interface_frame1.setStyleSheet("background-color: #F4F4F9;")

            self.chart_view1 = QChartView()
            self.chart_view1.setStyleSheet("background-color: #F4F4F9;")

            self.total_label1 = QLabel("")
            self.total_label1.setStyleSheet("font-size: 12pt; font-weight: bold;")

            interface1_layout = QVBoxLayout()
            interface1_layout.addWidget(self.chart_view1)
            interface1_layout.addWidget(self.total_label1)

            self.interface_frame1.setLayout(interface1_layout)
            self.interfaces_layout.addWidget(self.interface_frame1)

        if interface_num is None or interface_num == 2:
            print("Debug: Creating Interface 2 layout...")
            self.interface_frame2 = QFrame(self)
            self.interface_frame2.setFrameShape(QFrame.StyledPanel)
            self.interface_frame2.setStyleSheet("background-color: #F4F4F9;")

            self.chart_view2 = QChartView()
            self.chart_view2.setStyleSheet("background-color: #F4F4F9;")

            self.total_label2 = QLabel("")
            self.total_label2.setStyleSheet("font-size: 12pt; font-weight: bold;")

            interface2_layout = QVBoxLayout()
            interface2_layout.addWidget(self.chart_view2)
            interface2_layout.addWidget(self.total_label2)

            self.interface_frame2.setLayout(interface2_layout)
            self.interfaces_layout.addWidget(self.interface_frame2)


    def create_buttons_layout(self):
        """Create the layout for the clear interface buttons."""
        self.clear_button1 = QPushButton("Clear Interface 1")
        self.clear_button1.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.clear_button1.clicked.connect(lambda: self.clear_interface(1))

        self.clear_button2 = QPushButton("Clear Interface 2")
        self.clear_button2.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.clear_button2.clicked.connect(lambda: self.clear_interface(2))

        # Layout for the buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.clear_button1)
        buttons_layout.addWidget(self.clear_button2)

        return buttons_layout

    def clear_interface(self, interface_num):
        """Clear the chart and the total numbers for the selected interface and reset the frame."""
        try:
            print(f"Debug: Clearing interface {interface_num}...")

            if interface_num == 1:
                print("Debug: Clearing Interface 1...")

                # Clear interface 1 by deleting its contents
                self.interface_frame1.deleteLater()

                # Recreate the interface after clearing
                print("Debug: Interface 1 cleared, recreating after delay...")
                self.recreate_interface(1)  # Correctly calling the method to recreate

            elif interface_num == 2:
                print("Debug: Clearing Interface 2...")

                # Clear interface 2 by deleting its contents
                self.interface_frame2.deleteLater()

                # Recreate the interface after clearing
                print("Debug: Interface 2 cleared, recreating after delay...")
                self.recreate_interface(2)  # Correctly calling the method to recreate

        except Exception as e:
            error_message = f"Error clearing interface {interface_num}: {str(e)}"
            print(f"Debug: {error_message}")  # For debugging
            if interface_num == 1:
                self.total_label1.setText(error_message)
            else:
                self.total_label2.setText(error_message)


    def recreate_interface(self, interface_num):
        """Recreate the interface layout for the specified interface after clearing it."""
        try:
            if interface_num == 1:
                print("Debug: Recreating Interface 1 layout...")

                # Remove and recreate only Interface 1
                if self.interface_frame1 is not None:
                    self.interfaces_layout.removeWidget(self.interface_frame1)
                    self.interface_frame1.deleteLater()

                # Recreate Interface 1
                self.interface_frame1 = QFrame(self)
                self.interface_frame1.setFrameShape(QFrame.StyledPanel)
                self.interface_frame1.setStyleSheet("background-color: #F4F4F9;")

                self.chart_view1 = QChartView()
                self.chart_view1.setStyleSheet("background-color: #F4F4F9;")

                self.total_label1 = QLabel("")
                self.total_label1.setStyleSheet("font-size: 12pt; font-weight: bold;")

                interface1_layout = QVBoxLayout()
                interface1_layout.addWidget(self.chart_view1)
                interface1_layout.addWidget(self.total_label1)

                self.interface_frame1.setLayout(interface1_layout)

                # Ensure Interface 1 is added before Interface 2
                if self.interface_frame2 is not None and self.interface_frame2.isVisible():
                    self.interfaces_layout.insertWidget(0, self.interface_frame1)
                else:
                    self.interfaces_layout.addWidget(self.interface_frame1)

            elif interface_num == 2:
                print("Debug: Recreating Interface 2 layout...")

                # Remove and recreate only Interface 2
                if self.interface_frame2 is not None:
                    self.interfaces_layout.removeWidget(self.interface_frame2)
                    self.interface_frame2.deleteLater()

                # Recreate Interface 2
                self.interface_frame2 = QFrame(self)
                self.interface_frame2.setFrameShape(QFrame.StyledPanel)
                self.interface_frame2.setStyleSheet("background-color: #F4F4F9;")

                self.chart_view2 = QChartView()
                self.chart_view2.setStyleSheet("background-color: #F4F4F9;")

                self.total_label2 = QLabel("")
                self.total_label2.setStyleSheet("font-size: 12pt; font-weight: bold;")

                interface2_layout = QVBoxLayout()
                interface2_layout.addWidget(self.chart_view2)
                interface2_layout.addWidget(self.total_label2)

                self.interface_frame2.setLayout(interface2_layout)

                # Add Interface 2 back to the layout
                self.interfaces_layout.addWidget(self.interface_frame2)

        except Exception as e:
            print(f"Debug: Error while recreating interface {interface_num}: {str(e)}")

    def create_chart(self, early_count, soon_count, urgent_count, overdue_count, paid_count, total, category):
        """Create and display a pie chart with customized fonts, colors, and animation."""
        if total == 0:
            self.display_no_data_message()  # If total is 0, display a no-data message
            return  # Exit early since there is no data to display

        # Calculate percentages
        early_percentage = (early_count / total) * 100 if total > 0 else 0
        soon_percentage = (soon_count / total) * 100 if total > 0 else 0
        urgent_percentage = (urgent_count / total) * 100 if total > 0 else 0
        overdue_percentage = (overdue_count / total) * 100 if total > 0 else 0
        paid_percentage = (paid_count / total) * 100 if category == 'Task' and total > 0 else 0

        # Create a pie chart series
        series = QPieSeries()

        # Set colors for the slices (consistent across categories)
        color_map = {
            'Overdue': QColor('#EA0C00'),  # Red for Overdue
            'Urgent': QColor('#FF9F33'),   # Orange for Urgent
            'Soon': QColor('#F5F44B'),     # Yellow for Soon
            'Early': QColor('#1AB331'),    # Green for Early
            'Paid': QColor('#5380DC')      # Blue for Paid
        }

        # Add slices based on category
        if category == 'Invoice':
            # Custom labels for Invoice
            if early_percentage > 0:
                slice_early = series.append(f"Paid: {early_percentage:.2f}%", early_percentage)
                slice_early.setBrush(color_map['Early'])
            if soon_percentage > 0:
                slice_soon = series.append(f"Sent: {soon_percentage:.2f}%", soon_percentage)
                slice_soon.setBrush(color_map['Soon'])
            if overdue_percentage > 0:
                slice_overdue = series.append(f"Not Done: {overdue_percentage:.2f}%", overdue_percentage)
                slice_overdue.setBrush(color_map['Overdue'])
        elif category == 'Task':
            # Default labels for other categories
            if early_percentage > 0:
                slice_early = series.append(f"Done: {early_percentage:.2f}%", early_percentage)
                slice_early.setBrush(color_map['Early'])
            if soon_percentage > 0:
                slice_soon = series.append(f"Details missing: {soon_percentage:.2f}%", soon_percentage)
                slice_soon.setBrush(color_map['Soon'])
            if urgent_percentage > 0:
                slice_urgent = series.append(f"In proccess: {urgent_percentage:.2f}%", urgent_percentage)
                slice_urgent.setBrush(color_map['Urgent'])
            if overdue_percentage > 0:
                slice_overdue = series.append(f"Not started: {overdue_percentage:.2f}%", overdue_percentage)
                slice_overdue.setBrush(color_map['Overdue'])
            if category == 'Task' and paid_percentage > 0:
                slice_paid = series.append(f"Paid: {paid_percentage:.2f}%", paid_percentage)
                slice_paid.setBrush(color_map['Paid'])

        else:
            # Default labels for other categories
            if early_percentage > 0:
                slice_early = series.append(f"Early: {early_percentage:.2f}%", early_percentage)
                slice_early.setBrush(color_map['Early'])
            if soon_percentage > 0:
                slice_soon = series.append(f"Soon: {soon_percentage:.2f}%", soon_percentage)
                slice_soon.setBrush(color_map['Soon'])
            if urgent_percentage > 0:
                slice_urgent = series.append(f"Urgent: {urgent_percentage:.2f}%", urgent_percentage)
                slice_urgent.setBrush(color_map['Urgent'])
            if overdue_percentage > 0:
                slice_overdue = series.append(f"Overdue: {overdue_percentage:.2f}%", overdue_percentage)
                slice_overdue.setBrush(color_map['Overdue'])


        if series.count() == 0:
            self.display_no_data_message()  # If no slices added, show a no-data message
            return

        # Dynamically set the label properties for the slices
        for slice_ in series.slices():
            slice_.setBorderColor(Qt.black)
            slice_.setBorderWidth(2)
            slice_.setLabelVisible(True)
            slice_.setLabelPosition(QPieSlice.LabelOutside)  # Show labels outside the slices
            slice_.setLabelArmLengthFactor(0.4)  # Longer connecting lines for better spacing

        # Create the chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"{category} Status Distribution - {datetime.now().strftime('%B %Y')}")
        chart.setAnimationOptions(QChart.SeriesAnimations)  # Add animation when chart appears
        chart.setBackgroundBrush(Qt.white)  # Background color for the chart

        # Set font styles and size
        font = chart.titleFont()
        font.setPointSize(16)  # Increase the chart title font size
        chart.setTitleFont(font)

        # Set legend font size
        legend_font = chart.legend().font()
        legend_font.setPointSize(11)  # Increase font size for legend
        chart.legend().setFont(legend_font)

        # Display the total and status numbers on the interface
        if category == 'Invoice':
            total_text = f"Total: {total} | Paid: {early_count} | Sent: {soon_count} | Not Done: {overdue_count}"
        elif category == 'Task':
            total_text = f"Total: {total} | Paid: {paid_count} | Done: {early_count} | Details missing: {soon_count} | In progress: {urgent_count} | Not started: {overdue_count} "

        else:
            total_text = f"Total: {total} | Early: {early_count} | Soon: {soon_count} | Urgent: {urgent_count} | Overdue: {overdue_count}"
            if category == 'Task':
                total_text += f" | Paid: {paid_count}"

        if self.selected_interface == 1:
            self.chart_view1.setChart(chart)
            self.chart_view1.setRenderHint(QPainter.Antialiasing)
            self.total_label1.setText(total_text)
        else:
            self.chart_view2.setChart(chart)
            self.chart_view2.setRenderHint(QPainter.Antialiasing)
            self.total_label2.setText(total_text)

    def display_no_data_message(self):
        """Display a message when no data is found or when the total is zero."""
        if self.selected_interface == 1:
            self.chart_view1.setChart(None)  # Clear the chart if no data
            self.total_label1.setText("No data available for the selected options.")
            print("Debug: No data available for Interface 1.")  # Debugging message
        else:
            self.chart_view2.setChart(None)  # Clear the chart if no data
            self.total_label2.setText("No data available for the selected options.")
            print("Debug: No data available for Interface 2.")  # Debugging message


    def change_interface(self):
        # Switch between Interface 1 and Interface 2
        selected_interface_text = self.interface_dropdown.currentText()
        if selected_interface_text == 'Interface 1':
            self.selected_interface = 1
        else:
            self.selected_interface = 2

    def show_pie_chart(self):
        # Get the selected category, month, and year
        category = self.category_dropdown.currentText()
        month = int(self.month_dropdown.currentText())
        year = int(self.year_dropdown.currentText())
        today = datetime.now()

        try:
            with get_session() as session:
                # Fetch or calculate data based on the current month/year or pre-calculated data
                if month == today.month and year == today.year:
                    if category == 'Task':
                        self.fetch_task_data(session)
                    elif category == 'Invoice':
                        self.fetch_invoice_data(session)
                    else:
                        self.fetch_other_table_data(session, category)
                else:
                    self.fetch_data_insights(session, category, month, year)
        except Exception as e:
            print(f"Error: {e}")

    def fetch_task_data(self, session):
        """Fetch fresh data from Task table."""
        total = session.query(Task).count()
        if total == 0:
            self.display_no_data_message()  # Display message when no data is found
            return

        overdue_count = session.query(Task).filter_by(status='not_started').count()
        urgent_count = session.query(Task).filter_by(status='in_process').count()
        soon_count = session.query(Task).filter_by(status='details_missing').count()
        early_count = session.query(Task).filter_by(status='done').count()
        paid_count = session.query(Task).filter_by(status='paid').count()

        self.save_to_data_insights(
            session, 'Task', datetime.now().month, datetime.now().year,
            early_count, soon_count, urgent_count, overdue_count, paid_count, total
        )

        self.create_chart(early_count, soon_count, urgent_count, overdue_count, paid_count, total, 'Task')

    def fetch_invoice_data(self, session):
        """Fetch fresh data from Task table."""
        total = session.query(Invoice).count()
        if total == 0:
            self.display_no_data_message()  # Display message when no data is found
            return

        overdue_count = session.query(Invoice).filter(and_(Invoice.sent == False, Invoice.paid == False)).count()
        urgent_count = 0
        soon_count = session.query(Invoice).filter(or_(and_(Invoice.sent == False, Invoice.paid == True),and_(Invoice.sent == True, Invoice.paid == False))).count()        
        early_count = session.query(Invoice).filter(and_(Invoice.sent == True, Invoice.paid == True)).count()
        paid_count = 0
        self.save_to_data_insights(
            session, 'Invoice', datetime.now().month, datetime.now().year,
            early_count, soon_count, urgent_count, overdue_count, paid_count, total
        )

        self.create_chart(early_count, soon_count, urgent_count, overdue_count, paid_count, total, 'Invoice')

    def fetch_other_table_data(self, session, category):
        """Fetch fresh data from other tables (CIS, VAT, etc.)."""
        table_mapping = {
            'CIS': CIS,
            'VAT': VAT,
            'Account': Account,
            'PayRun': PayRun,
            'ConfirmationStatement': ConfirmationStatement
        }
        table = table_mapping[category]
        total = session.query(table).count()
        if total == 0:
            self.display_no_data_message()  # Display message when no data is found
            return

        overdue_count = session.query(table).filter_by(status='Overdue').count()
        urgent_count = session.query(table).filter_by(status='Urgent').count()
        soon_count = session.query(table).filter_by(status='Soon').count()
        early_count = session.query(table).filter_by(status='Early').count()

        paid_count = 0  # No 'paid_count' for non-Task tables

        self.save_to_data_insights(
            session, category, datetime.now().month, datetime.now().year,
            early_count, soon_count, urgent_count, overdue_count, paid_count, total
        )

        self.create_chart(early_count, soon_count, urgent_count, overdue_count, paid_count, total, category)

    def fetch_data_insights(self, session, category, month, year):
        """Fetch pre-calculated data from DataInsights table."""
        insights = session.query(DataInsights).filter_by(
            category=category, month=month, year=year
        ).first()
        if not insights:
            self.display_no_data_message()  # Display message when no data is found
            return

        self.create_chart(
            insights.early_count, insights.soon_count, insights.urgent_count,
            insights.overdue_count, insights.paid_count, insights.total_count, category
        )

    def save_to_data_insights(self, session, category, month, year, early_count, soon_count, urgent_count, overdue_count, paid_count, total):
        """Save fresh data into DataInsights table."""
        data_insight = session.query(DataInsights).filter_by(
            category=category, month=month, year=year
        ).first()

        if data_insight:
            # Update the existing row with new counts
            data_insight.early_count = early_count
            data_insight.soon_count = soon_count
            data_insight.urgent_count = urgent_count
            data_insight.overdue_count = overdue_count
            data_insight.paid_count = paid_count
            data_insight.total_count = total
        else:
            # Insert a new row
            data_insight = DataInsights(
                category=category,
                month=month,
                year=year,
                early_count=early_count,
                soon_count=soon_count,
                urgent_count=urgent_count,
                overdue_count=overdue_count,
                paid_count=paid_count,
                total_count=total
            )
            session.add(data_insight)

        session.commit()

    def check_for_auto_update(self):
        """Auto update data at the end of the month."""
        today = datetime.now().day
        if today >= 27:
            self.update_insights_table()


    def update_insights_table(self):
        """Refresh data from all relevant tables."""
        try:
            with get_session() as session:
                self.update_data_insights(session)  # Pass session correctly
        except Exception as e:
            print(f"Error: {e}")

    def update_data_insights(self, session):
        """Update data insights for all relevant categories."""
        categories = ['CIS', 'VAT', 'Account', 'PayRun', 'ConfirmationStatement', 'Invoice', 'Task']
        current_month = datetime.now().month
        current_year = datetime.now().year

        # Mapping table models to their corresponding classes
        table_mapping = {
            'CIS': CIS,
            'VAT': VAT,
            'Account': Account,
            'PayRun': PayRun,
            'ConfirmationStatement': ConfirmationStatement,
            'Invoice': Invoice,
            'Task': Task
        }

        for category in categories:
            # Determine the correct model to query based on the category
            model = table_mapping[category]
            total = session.query(model).count()

            if total == 0:
                continue  # Skip if no data is available

            if category == 'Task':
                # Special handling for the Task table (with a 'paid' status)
                overdue_count = session.query(model).filter_by(status='not_started').count()
                urgent_count = session.query(model).filter_by(status='in_process').count()
                soon_count = session.query(model).filter_by(status='details_missing').count()
                early_count = session.query(model).filter_by(status='done').count()
                paid_count = session.query(model).filter_by(status='paid').count()
            elif category == 'Invoice':
                # Special handling for the Invoice table
                overdue_count = session.query(model).filter(and_(Invoice.sent == False, Invoice.paid == False)).count()
                soon_count = session.query(model).filter(or_(and_(Invoice.sent == False, Invoice.paid == True), and_(Invoice.sent == True, Invoice.paid == False))).count()
                early_count = session.query(model).filter(and_(Invoice.sent == True, Invoice.paid == True)).count()
                paid_count = 0
                urgent_count = 0
            else:
                # Other tables (CIS, VAT, etc.)
                overdue_count = session.query(model).filter_by(status='Overdue').count()
                urgent_count = session.query(model).filter_by(status='Urgent').count()
                soon_count = session.query(model).filter_by(status='Soon').count()
                early_count = session.query(model).filter_by(status='Early').count()
                paid_count = 0  # No 'paid_count' for non-Task tables

            # Check if a row already exists in the data_insights table for this category/month/year
            data_insight = session.query(DataInsights).filter_by(
                category=category, month=current_month, year=current_year
            ).first()

            if data_insight:
                # Update the existing row with new counts
                data_insight.early_count = early_count
                data_insight.soon_count = soon_count
                data_insight.urgent_count = urgent_count
                data_insight.overdue_count = overdue_count
                data_insight.paid_count = paid_count
                data_insight.total_count = total
            else:
                # Insert a new row into the data_insights table
                data_insight = DataInsights(
                    category=category,
                    month=current_month,
                    year=current_year,
                    early_count=early_count,
                    soon_count=soon_count,
                    urgent_count=urgent_count,
                    overdue_count=overdue_count,
                    paid_count=paid_count,
                    total_count=total
                )
                session.add(data_insight)

            session.commit()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)

    insights_tab = DataInsightsTab()
    layout.addWidget(insights_tab)

    window.setLayout(layout)
    window.show()

    insights_tab.check_for_auto_update()

    sys.exit(app.exec_())
