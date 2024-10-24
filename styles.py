app_stylesheet = """
    /* Main window style */
    QMainWindow {
        background-color: #d4f1f4; /* Baby Blue background */
    }

    /* QTableWidget styles */
    QTableWidget {
        background-color: #ffffff; /* White background */
        alternate-background-color: #75e6da; /* Blue Green alternate row color */
        selection-background-color: #189ab4; /* Blue Grotto selection background */
        selection-color: white; /* White text color for selection */
        border: 1px solid #05445e; /* Navy Blue border */
    }

    /* QHeaderView (table header) styles */
    QHeaderView::section {
        background-color: #05445e; /* Navy Blue header background */
        color: #d4f1f4; /* Baby Blue header text color */
        padding: 8px; /* Padding */
        border: none; /* No border */
        font-weight: bold; /* Bold font for header text */
        text-align: center; /* Centered text */
        border-bottom: 2px solid #189ab4; /* Blue Grotto bottom border */
    }

    /* QPushButton styles */
    QPushButton {
        background-color: #189ab4; /* Blue Grotto button background */
        color: #ffffff; /* White button text color */
        border-radius: 5px; /* Rounded corners */
        padding: 10px 20px; /* Padding */
        border: none; /* No border */
        font-weight: bold; /* Bold font */
    }

    /* QPushButton hover styles */
    QPushButton:hover {
        background-color: #75e6da; /* Blue Green on hover */
    }

    /* QPushButton pressed styles */
    QPushButton:pressed {
        background-color: #05445e; /* Navy Blue when pressed */
    }

    /* QLineEdit styles */
    QLineEdit {
        background-color: #ffffff; /* White background */
        padding: 8px; /* Padding */
        border-radius: 5px; /* Rounded corners */
        border: 1px solid #189ab4; /* Blue Grotto border */
    }

    /* QComboBox styles */
    QComboBox {
        background-color: #ffffff; /* White background */
        padding: 8px; /* Padding */
        border-radius: 5px; /* Rounded corners */
        border: 1px solid #189ab4; /* Blue Grotto border */
    }

    /* QComboBox drop-down styles */
    QComboBox::drop-down {
        subcontrol-origin: padding; /* Ensure dropdown icon aligns with text */
        subcontrol-position: right center; /* Position dropdown icon */
        width: 20px; /* Width of dropdown icon */
        border-left-width: 1px; /* Left border width */
        border-left-color: #189ab4; /* Blue Grotto left border */
        border-left-style: solid; /* Left border style */
    }

    /* QLabel styles */
    QLabel {
        color: #05445e; /* Navy Blue text color */
    }

    /* QMessageBox styles */
    QMessageBox {
        background-color: #ffffff; /* White background */
        border: 1px solid #189ab4; /* Blue Grotto border */
    }

    /* QMessageBox QPushButton styles */
    QMessageBox QPushButton {
        background-color: #189ab4; /* Blue Grotto button background */
        color: white; /* White button text color */
        border-radius: 5px; /* Rounded corners */
        padding: 10px 20px; /* Padding */
        border: none; /* No border */
        font-weight: bold; /* Bold font */
    }

    /* QMessageBox QPushButton hover styles */
    QMessageBox QPushButton:hover {
        background-color: #75e6da; /* Blue Green on hover */
    }

    /* QMessageBox QPushButton pressed styles */
    QMessageBox QPushButton:pressed {
        background-color: #05445e; /* Navy Blue when pressed */
    }

    /* QTabWidget styles */
    QTabWidget::pane {
        border: 1px solid #189ab4; /* Blue Grotto border */
        background-color: #ffffff; /* White background */
    }

    /* QTabBar::tab styles */
    QTabBar::tab {
        background: #75e6da; /* Blue Green background */
        border: 1px solid #189ab4; /* Blue Grotto border */
        padding: 10px; /* Padding */
        margin: 1px; /* Margin */
    }

    /* QTabBar::tab:selected styles */
    QTabBar::tab:selected {
        background: #05445e; /* Navy Blue background */
        color: white; /* White text color */
    }

    /* QCheckBox styles */
    QCheckBox {
        padding: 5px; /* Padding */
    }

    /* QCheckBox::indicator styles */
    QCheckBox::indicator {
        width: 20px; /* Width */
        height: 20px; /* Height */
    }

    /* QCheckBox::indicator:checked styles */
    QCheckBox::indicator:checked {
        background-color: #189ab4; /* Blue Grotto background */
        border: 1px solid #05445e; /* Navy Blue border */
    }

    /* QCheckBox::indicator:unchecked styles */
    QCheckBox::indicator:unchecked {
        background-color: #ffffff; /* White background */
        border: 1px solid #d1d9e0; /* Light blue-gray border */
    }

    /* QMenuBar styles */
    QMenuBar {
        background-color: #75e6da; /* Blue Green background */
        color: #05445e; /* Navy Blue text color */
    }

    /* QMenuBar::item styles */
    QMenuBar::item {
        background: transparent; /* Transparent background */
        padding: 5px 10px; /* Padding */
    }

    /* QMenuBar::item:selected styles */
    QMenuBar::item:selected {
        background: #189ab4; /* Blue Grotto background */
        color: white; /* White text color */
    }

    /* QMenu styles */
    QMenu {
        background-color: #75e6da; /* Blue Green background */
        color: #05445e; /* Navy Blue text color */
        border: 1px solid #189ab4; /* Blue Grotto border */
    }

    /* QMenu::item styles */
    QMenu::item {
        padding: 5px 20px; /* Padding */
    }

    /* QMenu::item:selected styles */
    QMenu::item:selected {
        background: #05445e; /* Navy Blue background */
        color: white; /* White text color */
    }

    /* QDateEdit styles */
    QDateEdit {
        background-color: #ffffff; /* White background */
        padding: 8px; /* Padding */
        border-radius: 5px; /* Rounded corners */
        border: 1px solid #189ab4; /* Blue Grotto border */
        min-width: 150px; /* Minimum width */
        font-size: 14px; /* Slightly larger font size */
        height: 30px; /* Increase height */
    }

    /* QDateEdit drop-down styles */
    QDateEdit::drop-down {
        subcontrol-origin: padding; /* Ensure dropdown icon aligns with text */
        subcontrol-position: right center; /* Position dropdown icon */
        width: 20px; /* Width of dropdown icon */
        border-left-width: 1px; /* Left border width */
        border-left-color: #189ab4; /* Blue Grotto left border */
        border-left-style: solid; /* Left border style */
    }

    /* QTableWidget QHeaderView styles */
    QTableWidget QHeaderView::section {
        background-color: #05445e; /* Navy Blue background */
        color: #d4f1f4; /* Baby Blue text color */
        padding: 8px; /* Padding */
        border: 1px solid #189ab4; /* Blue Grotto border */
    }

    /* QTabWidget tab bar alignment */
    QTabWidget::tab-bar {
        alignment: center; /* Center align the tabs */
    }

    /* QToolTip styles */
    QToolTip {
        background-color: #189ab4; /* Blue Grotto background */
        color: white; /* White text color */
        border: 1px solid #05445e; /* Navy Blue border */
        padding: 5px; /* Padding */
    }

    /* QScrollBar vertical styles */
    QScrollBar:vertical {
        border: 1px solid #189ab4; /* Blue Grotto border */
        background: #75e6da; /* Blue Green background */
        width: 15px; /* Width */
        margin: 22px 0 22px 0; /* Margin */
    }

    /* QScrollBar handle vertical styles */
    QScrollBar::handle:vertical {
        background: #189ab4; /* Blue Grotto background */
        min-height: 20px; /* Minimum height */
    }

    /* QScrollBar add-line vertical styles */
    QScrollBar::add-line:vertical {
        border: 1px solid #189ab4; /* Blue Grotto border */
        background: #75e6da; /* Blue Green background */
        height: 20px; /* Height */
        subcontrol-position: bottom; /* Position */
        subcontrol-origin: margin; /* Origin */
    }

    /* QScrollBar sub-line vertical styles */
    QScrollBar::sub-line:vertical {
        border: 1px solid #189ab4; /* Blue Grotto border */
        background: #75e6da; /* Blue Green background */
        height: 20px; /* Height */
        subcontrol-position: top; /* Position */
        subcontrol-origin: margin; /* Origin */
    }

    /* QScrollBar horizontal styles */
    QScrollBar:horizontal {
        border: 1px solid #189ab4; /* Blue Grotto border */
        background: #75e6da; /* Blue Green background */
        height: 15px; /* Height */
        margin: 0px 22px 0 22px; /* Margin */
    }

    /* QScrollBar handle horizontal styles */
    QScrollBar::handle:horizontal {
        background: #189ab4; /* Blue Grotto background */
        min-width: 20px; /* Minimum width */
    }

    /* QScrollBar add-line horizontal styles */
    QScrollBar::add-line:horizontal {
        border: 1px solid #189ab4; /* Blue Grotto border */
        background: #75e6da; /* Blue Green background */
        width: 20px; /* Width */
        subcontrol-position: right; /* Position */
        subcontrol-origin: margin; /* Origin */
    }

    /* QScrollBar sub-line horizontal styles */
    QScrollBar::sub-line:horizontal {
        border: 1px solid #189ab4; /* Blue Grotto border */
        background: #75e6da; /* Blue Green background */
        width: 20px; /* Width */
        subcontrol-position: left; /* Position */
        subcontrol-origin: margin; /* Origin */
    }

    /* QListView styles */
    QListView {
        background-color: #ffffff; /* White background */
        border: 1px solid #189ab4; /* Blue Grotto border */
    }

    /* QTreeView styles */
    QTreeView {
        background-color: #ffffff; /* White background */
        border: 1px solid #189ab4; /* Blue Grotto border */
    }

    /* QToolBar styles */
    QToolBar {
        background-color: #75e6da; /* Blue Green background */
        border: 1px solid #189ab4; /* Blue Grotto border */
    }

    /* QStatusBar styles */
    QStatusBar {
        background-color: #75e6da; /* Blue Green background */
        border-top: 1px solid #189ab4; /* Blue Grotto top border */
    }

    /* QGroupBox styles */
    QGroupBox {
        border: 1px solid #189ab4; /* Blue Grotto border */
        border-radius: 5px; /* Rounded corners */
        margin-top: 10px; /* Margin */
        padding: 10px; /* Padding */
    }

    QGroupBox::title {
        subcontrol-origin: margin; /* Origin */
        subcontrol-position: top left; /* Position */
        padding: 0 3px; /* Padding */
        background-color: #75e6da; /* Blue Green background */
    }

    /* QRadioButton styles */
    QRadioButton {
        padding: 5px; /* Padding */
    }

    /* QRadioButton::indicator styles */
    QRadioButton::indicator {
        width: 20px; /* Width */
        height: 20px; /* Height */
    }

    /* QRadioButton::indicator:checked styles */
    QRadioButton::indicator:checked {
        background-color: #189ab4; /* Blue Grotto background */
        border: 1px solid #05445e; /* Navy Blue border */
    }

    /* QRadioButton::indicator:unchecked styles */
    QRadioButton::indicator:unchecked {
        background-color: #ffffff; /* White background */
        border: 1px solid #d1d9e0; /* Light blue-gray border */
    }
"""
