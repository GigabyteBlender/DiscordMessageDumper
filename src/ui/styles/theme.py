"""
Qt styling and theme module for Discord Message Delete Helper.

This module provides a modern, polished UI theme with:
- Discord-inspired color palette
- Rounded corners and shadows
- Smooth transitions
- Custom scrollbar styling
"""

# Color Palettes
DARK_COLORS = {
    'primary': '#5865F2',           # Discord Blurple
    'primary_hover': '#4752C4',     # Darker blurple for hover
    'background': '#36393F',        # Dark gray background
    'surface': '#2F3136',           # Slightly darker surface
    'card': '#40444B',              # Card background
    'text': '#FFFFFF',              # White text
    'text_secondary': '#B9BBBE',    # Gray secondary text
    'success': '#3BA55D',           # Green for success states
    'error': '#ED4245',             # Red for error states
    'warning': '#FAA81A',           # Orange for warning states
    'border': '#202225',            # Border color
    'input_bg': '#202225',          # Input background
    'hover': '#4E5058',             # Hover state
}

LIGHT_COLORS = {
    'primary': '#5865F2',           # Discord Blurple
    'primary_hover': '#4752C4',     # Darker blurple for hover
    'background': '#FFFFFF',        # White background
    'surface': '#F2F3F5',           # Light gray surface
    'card': '#FFFFFF',              # Card background
    'text': '#2E3338',              # Dark text
    'text_secondary': '#5E6772',    # Gray secondary text
    'success': '#3BA55D',           # Green for success states
    'error': '#ED4245',             # Red for error states
    'warning': '#FAA81A',           # Orange for warning states
    'border': '#E3E5E8',            # Border color
    'input_bg': '#EBEDEF',          # Input background
    'hover': '#E3E5E8',             # Hover state
}

# Default to dark theme
COLORS = DARK_COLORS


def get_stylesheet(theme: str = 'dark') -> str:
    """
    Returns the complete QSS stylesheet for the application.
    
    Args:
        theme: Theme name ('dark' or 'light')
    
    Returns:
        str: Complete QSS stylesheet with modern styling
    """
    # Select color palette based on theme
    colors = DARK_COLORS if theme == 'dark' else LIGHT_COLORS
    
    return f"""
    /* Global Styles */
    QWidget {{
        background-color: {colors['background']};
        color: {colors['text']};
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
    }}
    
    /* Main Window */
    QMainWindow {{
        background-color: {colors['background']};
    }}
    
    /* Push Buttons */
    QPushButton {{
        background-color: {colors['primary']};
        color: {colors['text']};
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
        min-height: 38px;
    }}
    
    QPushButton:hover {{
        background-color: {colors['primary_hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {colors['primary_hover']};
        padding-top: 11px;
        padding-bottom: 9px;
    }}
    
    QPushButton:disabled {{
        background-color: {colors['surface']};
        color: {colors['text_secondary']};
    }}
    
    /* Navigation Buttons */
    QPushButton[nav="true"] {{
        background-color: transparent;
        color: {colors['text']};
        border: none;
        border-radius: 6px;
        padding: 10px 14px;
        text-align: left;
        font-weight: 600;
        font-size: 13px;
    }}
    
    QPushButton[nav="true"]:hover {{
        background-color: {colors['hover']};
    }}
    
    QPushButton[nav="true"]:checked {{
        background-color: {colors['primary']};
        color: {colors['text']};
    }}
    
    QPushButton[nav="true"]:pressed {{
        background-color: {colors['primary_hover']};
        padding-top: 10px;
        padding-bottom: 10px;
    }}
    
    /* Secondary Buttons */
    QPushButton[secondary="true"] {{
        background-color: {colors['surface']};
        color: {colors['text']};
    }}
    
    QPushButton[secondary="true"]:hover {{
        background-color: {colors['hover']};
    }}
    
    /* Danger Buttons */
    QPushButton[danger="true"] {{
        background-color: {colors['error']};
    }}
    
    QPushButton[danger="true"]:hover {{
        background-color: #C03537;
    }}
    
    /* Success Buttons */
    QPushButton[success="true"] {{
        background-color: {colors['success']};
    }}
    
    QPushButton[success="true"]:hover {{
        background-color: #2D7D46;
    }}
    
    /* Line Edit (Text Input) */
    QLineEdit {{
        background-color: {colors['input_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 9px 12px;
        min-height: 36px;
    }}
    
    QLineEdit:focus {{
        border-color: {colors['primary']};
    }}
    
    QLineEdit:disabled {{
        background-color: {colors['surface']};
        color: {colors['text_secondary']};
    }}
    
    /* Text Edit (Multi-line) */
    QTextEdit, QPlainTextEdit {{
        background-color: {colors['input_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 10px 12px;
    }}
    
    QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {colors['primary']};
    }}
    
    /* Labels */
    QLabel {{
        color: {colors['text']};
        background-color: transparent;
    }}
    
    QLabel[secondary="true"] {{
        color: {colors['text_secondary']};
    }}
    
    QLabel[heading="true"] {{
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 12px;
        letter-spacing: -0.5px;
    }}
    
    /* Cards/Frames */
    QFrame[card="true"] {{
        background-color: {colors['card']};
        border-radius: 8px;
        padding: 0px;
    }}
    
    QFrame[surface="true"] {{
        background-color: {colors['surface']};
        border-radius: 8px;
        padding: 0px;
    }}
    
    /* Progress Bar */
    QProgressBar {{
        background-color: {colors['surface']};
        border: none;
        border-radius: 6px;
        text-align: center;
        color: {colors['text']};
        min-height: 20px;
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 {colors['primary']},
            stop: 1 {colors['primary_hover']}
        );
        border-radius: 6px;
    }}
    
    /* Combo Box (Dropdown) */
    QComboBox {{
        background-color: {colors['input_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 9px 12px;
        min-height: 36px;
    }}
    
    QComboBox:hover {{
        border-color: {colors['primary']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {colors['text']};
        margin-right: 10px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {colors['card']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        selection-background-color: {colors['primary']};
        padding: 4px;
    }}
    
    /* Scroll Bar */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 10px;
        border-radius: 5px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors['hover']};
        border-radius: 5px;
        min-height: 40px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {colors['text_secondary']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 10px;
        border-radius: 5px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {colors['hover']};
        border-radius: 5px;
        min-width: 40px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {colors['text_secondary']};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    
    /* Scroll Area */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    
    /* Check Box */
    QCheckBox {{
        color: {colors['text']};
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 2px solid {colors['border']};
        background-color: {colors['input_bg']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {colors['primary']};
        border-color: {colors['primary']};
    }}
    
    QCheckBox::indicator:hover {{
        border-color: {colors['primary']};
    }}
    
    /* Radio Button */
    QRadioButton {{
        color: {colors['text']};
        spacing: 8px;
    }}
    
    QRadioButton::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 10px;
        border: 2px solid {colors['border']};
        background-color: {colors['input_bg']};
    }}
    
    QRadioButton::indicator:checked {{
        background-color: {colors['primary']};
        border-color: {colors['primary']};
    }}
    
    QRadioButton::indicator:hover {{
        border-color: {colors['primary']};
    }}
    
    /* Tab Widget */
    QTabWidget::pane {{
        background-color: {colors['card']};
        border: none;
        border-radius: 6px;
        padding: 8px;
    }}
    
    QTabBar::tab {{
        background-color: {colors['surface']};
        color: {colors['text_secondary']};
        border: none;
        border-radius: 6px 6px 0px 0px;
        padding: 8px 16px;
        margin-right: 4px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {colors['card']};
        color: {colors['text']};
    }}
    
    QTabBar::tab:hover {{
        background-color: {colors['hover']};
        color: {colors['text']};
    }}
    
    /* Group Box */
    QGroupBox {{
        background-color: {colors['surface']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 14px;
        font-weight: 600;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: {colors['text']};
        background-color: {colors['surface']};
    }}
    
    /* Status Bar */
    QStatusBar {{
        background-color: {colors['surface']};
        color: {colors['text_secondary']};
        border-top: 1px solid {colors['border']};
    }}
    
    /* Menu Bar */
    QMenuBar {{
        background-color: {colors['surface']};
        color: {colors['text']};
        border-bottom: 1px solid {colors['border']};
    }}
    
    QMenuBar::item {{
        padding: 8px 12px;
        background-color: transparent;
    }}
    
    QMenuBar::item:selected {{
        background-color: {colors['hover']};
        border-radius: 4px;
    }}
    
    /* Menu */
    QMenu {{
        background-color: {colors['card']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 4px;
    }}
    
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {colors['primary']};
    }}
    
    /* Tool Tip */
    QToolTip {{
        background-color: {colors['card']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 8px;
    }}
    
    /* Spin Box */
    QSpinBox, QDoubleSpinBox {{
        background-color: {colors['input_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 9px 12px;
        min-height: 36px;
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {colors['primary']};
    }}
    
    QSpinBox::up-button, QDoubleSpinBox::up-button {{
        background-color: transparent;
        border: none;
        width: 20px;
    }}
    
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background-color: transparent;
        border: none;
        width: 20px;
    }}
    
    /* List Widget */
    QListWidget {{
        background-color: {colors['input_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        padding: 4px;
    }}
    
    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
    }}
    
    QListWidget::item:selected {{
        background-color: {colors['primary']};
    }}
    
    QListWidget::item:hover {{
        background-color: {colors['hover']};
    }}
    
    /* Table Widget */
    QTableWidget {{
        background-color: {colors['input_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 6px;
        gridline-color: {colors['border']};
    }}
    
    QTableWidget::item {{
        padding: 8px;
    }}
    
    QTableWidget::item:selected {{
        background-color: {colors['primary']};
    }}
    
    QHeaderView::section {{
        background-color: {colors['surface']};
        color: {colors['text']};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {colors['border']};
        font-weight: 600;
    }}
    
    /* Dialog */
    QDialog {{
        background-color: {colors['background']};
    }}
    
    /* Message Box */
    QMessageBox {{
        background-color: {colors['background']};
    }}
    
    QMessageBox QLabel {{
        color: {colors['text']};
    }}
    
    /* File Dialog */
    QFileDialog {{
        background-color: {colors['background']};
        color: {colors['text']};
    }}
    
    /* Slider */
    QSlider::groove:horizontal {{
        background-color: {colors['surface']};
        height: 8px;
        border-radius: 4px;
    }}
    
    QSlider::handle:horizontal {{
        background-color: {colors['primary']};
        width: 18px;
        height: 18px;
        margin: -5px 0;
        border-radius: 9px;
    }}
    
    QSlider::handle:horizontal:hover {{
        background-color: {colors['primary_hover']};
    }}
    
    /* Transitions - Note: QSS doesn't support CSS transitions directly */
    /* Smooth transitions are handled through Qt's animation framework */
    """


def apply_theme(app, theme: str = 'dark'):
    """
    Apply the theme stylesheet to the Qt application.
    
    Args:
        app: QApplication instance
        theme: Theme name ('dark' or 'light')
    """
    app.setStyleSheet(get_stylesheet(theme))


# Export color constants for use in custom widgets
__all__ = ['DARK_COLORS', 'LIGHT_COLORS', 'COLORS', 'get_stylesheet', 'apply_theme']

