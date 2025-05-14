import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QMenu, QLabel, QSpacerItem, QSizePolicy, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os

class JsonEditorApp(QWidget):
    def __init__(self):
        super().__init__()

        # Prompt the user to select a file on startup
        self.json_file_path = self.open_file_dialog()
        if not self.json_file_path:
            # If no file is selected, quit the application and exit completely
            QApplication.quit()
            sys.exit()

        self.current_item = None
        self.is_modified = False  # To track if the current leaf is modified
        self.original_font_size = 12  # Original font size for tree view and text area
        self.tree_font_size = self.original_font_size  # Current font size for tree view
        self.text_font_size = self.original_font_size  # Current font size for text area

        # Main layout
        layout = QVBoxLayout()

        # Horizontal layout for tree view and text editor
        side_by_side_layout = QHBoxLayout()

        # Left side: Tree view
        left_layout = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["JSON Structure"])
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        left_layout.addWidget(self.tree)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.reload_json)
        left_layout.addWidget(self.refresh_button)

        # Create a widget to contain the left layout and set its size policy
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        side_by_side_layout.addWidget(left_widget, 1)  # 1 unit of stretch

        # Right side: Text editor
        right_layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)  # Initially readonly to prevent editing raw JSON
        self.text_area.textChanged.connect(self.on_text_changed)
        right_layout.addWidget(self.text_area)

        self.save_button = QPushButton("Save")
        self.save_button.setEnabled(False)  # Initially disabled
        self.save_button.clicked.connect(self.save_entry)
        right_layout.addWidget(self.save_button)

        # Create a widget to contain the right layout and set its size policy
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        side_by_side_layout.addWidget(right_widget, 2)  # 2 units of stretch

        layout.addLayout(side_by_side_layout)

        # Font size adjustment, Open File controls, and Information button
        controls_layout = QHBoxLayout()

        # Open file button - moved to the left
        self.open_file_button = QPushButton("📂 Open File")
        self.open_file_button.clicked.connect(self.open_file)
        controls_layout.addWidget(self.open_file_button)

        # Font size options
        font_label = QLabel("Font size:")
        controls_layout.addWidget(font_label)

        self.increase_font_button = QPushButton("+")
        self.increase_font_button.clicked.connect(self.increase_font_size)
        controls_layout.addWidget(self.increase_font_button)

        self.decrease_font_button = QPushButton("-")
        self.decrease_font_button.clicked.connect(self.decrease_font_size)
        controls_layout.addWidget(self.decrease_font_button)

        self.reset_font_button = QPushButton("↻")
        self.reset_font_button.clicked.connect(self.reset_font_size)
        controls_layout.addWidget(self.reset_font_button)

        # Spacer to center the buttons
        controls_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Information button with a question mark icon
        self.info_button = QPushButton("?")
        self.info_button.setFixedSize(30, 30)
        self.info_button.clicked.connect(self.show_information)
        controls_layout.addWidget(self.info_button, alignment=Qt.AlignRight)

        layout.addLayout(controls_layout)

        self.setLayout(layout)
        self.setWindowTitle(f"JSON Editor - {os.path.basename(self.json_file_path)}")

        # Set less bold font and line spacing
        self.set_font_styles()

        # Load and process the JSON structure
        self.load_json()

        # Set initial font sizes
        self.set_tree_font_size(self.tree_font_size)
        self.set_text_font_size(self.text_font_size)

    def open_file_dialog(self):
        """Open a file dialog to select a JSON file on startup."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
        return file_path if file_path else None

    def open_file(self):
        """Open a file dialog to select a new JSON file after startup."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            self.json_file_path = file_path
            self.setWindowTitle(f"JSON Editor - {os.path.basename(file_path)}")
            
            # Clear the current item reference before loading new JSON
            self.current_item = None
            self.is_modified = False
            self.save_button.setEnabled(False)
            self.text_area.clear()

            self.load_json()

    def set_font_styles(self):
        """Set font styles with lighter weight and increased line spacing."""
        font = QFont()
        font.setPointSize(self.text_font_size)
        font.setWeight(QFont.Normal)  # Less bold appearance
        self.tree.setFont(font)
        self.text_area.setFont(font)
        self.text_area.setStyleSheet("QTextEdit { line-height: 1.5; }")  # Line spacing in text area

    def load_json(self):
        """Load JSON data from the file, clear tree, and populate it."""
        try:
            with open(self.json_file_path, 'r') as file:
                self.json_data = json.load(file)

            # Convert all numeric strings to actual numbers in the JSON data
            self.json_data = self.convert_numerics(self.json_data)

            # Clear the existing tree to avoid access to deleted items
            self.tree.clear()

            # Reload the updated JSON tree view
            self.load_json_into_tree(self.json_data)

            # Refresh the text area with the new JSON content
            self.text_area.setText(json.dumps(self.json_data, indent=4))

        except Exception as e:
            self.tree.clear()
            self.text_area.setText(f"Failed to load JSON: {e}")

    def reload_json(self):
        """Clear current references and reload JSON data."""
        # Clear any references to tree items to avoid accessing deleted objects
        self.current_item = None
        self.is_modified = False
        self.save_button.setEnabled(False)
        self.text_area.clear()

        # Reload the JSON data and refresh the view
        self.load_json()

    def show_information(self):
        """Display an information popup about the application."""
        info_text = (
            "<div style='text-align: center;'>&#9432; <b>JSON Editor Information</b> &#9432;</div><br><br>"
            "This JSON Editor application allows you to:<br>"
            "<br>"
            "• <b>View JSON Structure:</b> The tree view on the left displays the JSON structure. "
            "You can click on items to view their content on the right.<br>"
            "<br>"
            "• <b>Edit JSON Values:</b> Select a leaf node (non-nested value) to edit its content in the text editor on the right.<br>"
            "<br>"
            "• <b>Save Changes:</b> After editing a leaf node, click 'Save' to update the JSON.<br>"
            "<br>"
            "• <b>Refresh JSON:</b> Click 'Refresh' to reload the JSON file in case of external modifications.<br>"
            "<br>"
            "• <b>Adjust Font Size:</b> Use the + and - buttons to increase or decrease font size, and the ↻ button to reset to the original size.<br>"
            "<br>"
            "• <b>Open JSON Files:</b> Click the 'Open File' button to load a new JSON file.<br>"
            "<br>"
            "<i>Note:</i> Only non-nested values (leaf nodes) are editable. Changes to nested structures "
            "need to be made in an external JSON editor.<br>"
            "<div style='text-align: center;'><b>Current Open File:</b></div><br>"
            f"<b>File Name:</b> {os.path.basename(self.json_file_path)}<br>"
            "<br>"
            "<b>File Path:</b><br>"
            f"{os.path.abspath(self.json_file_path)}"
        )

        # Create the message box and set a larger width for better readability, with lighter font
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Information")
        msg_box.setTextFormat(Qt.RichText)  # Enable HTML formatting
        msg_box.setText(info_text)
        msg_box.setStyleSheet("QLabel{min-width: 600px; font-weight: normal;}")  # Set lighter font weight and width
        msg_box.exec_()

    def convert_numerics(self, data):
        """Recursively convert numeric strings in dictionaries or lists to integers/floats."""
        if isinstance(data, dict):
            return {k: self.convert_numerics(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.convert_numerics(v) for v in data]
        elif isinstance(data, str):
            if data.isdigit():
                return int(data)
            try:
                return float(data)
            except ValueError:
                return data
        else:
            return data

    def load_json_into_tree(self, data, parent=None):
        if parent is None:
            parent = self.tree
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem([key])
                parent.addTopLevelItem(item) if parent is self.tree else parent.addChild(item)
                if isinstance(value, (dict, list)):  # Only add children for dicts and lists
                    self.load_json_into_tree(value, item)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item = QTreeWidgetItem([str(index)])
                parent.addTopLevelItem(item) if parent is self.tree else parent.addChild(item)
                if isinstance(value, (dict, list)):  # Only add children for lists of dicts/lists
                    self.load_json_into_tree(value, item)

    def on_item_clicked(self, item):
        # Check if there are unsaved changes before switching to a new item
        if self.is_modified:
            self.save_entry()

        self.current_item = item
        item_path = self.get_item_path(item)
        # Access the selected item's content from the JSON data
        try:
            json_value = self.get_json_value(item_path)
            # Show the item's value in the text editor
            if isinstance(json_value, str):
                self.text_area.setReadOnly(False)  # Activate text area for editing
                self.text_area.setText(json_value.replace("\\n", "\n"))
            elif isinstance(json_value, (dict, list)):
                self.text_area.setReadOnly(True)  # Deactivate text area (non-leaf node)
                self.text_area.setText(json.dumps(json_value, indent=4))
            else:
                self.text_area.setReadOnly(False)  # Activate text area for editing
                self.text_area.setText(str(json_value))

            # Enable the save button only if the item has no children (i.e., it's a leaf node)
            if item.childCount() == 0:
                self.save_button.setEnabled(True)
                self.text_area.setReadOnly(False)  # Allow editing
            else:
                self.save_button.setEnabled(False)
                self.text_area.setReadOnly(True)  # Disable editing for non-leaf nodes

            self.is_modified = False  # Reset the modification flag when switching nodes

        except Exception as e:
            self.text_area.setReadOnly(True)  # Deactivate text area in case of error
            self.text_area.setText(f"Error: {e}")
            self.save_button.setEnabled(False)

    def get_item_path(self, item):
        path = []
        while item is not None:
            path.append(item.text(0))
            item = item.parent()
        path.reverse()
        return path

    def get_json_value(self, path):
        obj = self.json_data
        for key in path:
            if isinstance(obj, list):
                key = int(key)
            obj = obj[key]
        return obj

    def set_json_value(self, path, value):
        obj = self.json_data
        for key in path[:-1]:
            if isinstance(obj, list):
                key = int(key)
            obj = obj[key]
        last_key = path[-1]
        if isinstance(obj, list):
            last_key = int(last_key)

        # Convert numeric strings back to numeric types if possible
        updated_value = self.convert_to_numeric(value)
        obj[last_key] = updated_value

        # Auto-save if there was a numeric change
        if value != str(updated_value):
            self.auto_save_and_reload()

    def convert_to_numeric(self, value):
        """Converts string values to integers or floats if possible"""
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value

    def auto_save_and_reload(self):
        """Save the JSON file and reload the tree structure to reflect changes"""
        with open(self.json_file_path, 'w') as json_file:
            json.dump(self.json_data, json_file, indent=4)
        self.load_json()

    def save_entry(self):
        if self.current_item is not None:
            item_path = self.get_item_path(self.current_item)
            new_value = self.text_area.toPlainText().replace("\n", "\\n")
            self.set_json_value(item_path, new_value)

            # Save updated JSON to file
            with open(self.json_file_path, 'w') as json_file:
                json.dump(self.json_data, json_file, indent=4)

            self.is_modified = False  # Reset the modification flag after saving

    def on_text_changed(self):
        # Mark the current node as modified if text changes
        self.is_modified = True

        # Disable save button if the selected item is not a leaf node
        if self.current_item is None or self.current_item.childCount() > 0:
            self.save_button.setEnabled(False)
        else:
            self.save_button.setEnabled(True)

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if item:
            menu = QMenu()

            delete_action = menu.addAction("Delete")
            add_action = menu.addAction("Add")

            action = menu.exec_(self.tree.viewport().mapToGlobal(position))

            if action == delete_action:
                self.delete_item(item)
            elif action == add_action:
                self.add_item(item)

    def delete_item(self, item):
        # Get the item path
        item_path = self.get_item_path(item)
        if len(item_path) > 0:
            # Remove from the JSON structure
            parent = self.get_json_value(item_path[:-1])
            key_to_remove = item_path[-1]
            if isinstance(parent, list):
                parent.pop(int(key_to_remove))
            elif isinstance(parent, dict):
                parent.pop(key_to_remove)

            # Remove from the tree
            parent_item = item.parent()
            if parent_item:
                parent_item.removeChild(item)
            else:
                index = self.tree.indexOfTopLevelItem(item)
                self.tree.takeTopLevelItem(index)

            # Save the updated JSON after deletion
            with open(self.json_file_path, 'w') as json_file:
                json.dump(self.json_data, json_file, indent=4)

    def add_item(self, item):
        # Get the item path
        item_path = self.get_item_path(item)
        parent_item = item.parent()
        parent = self.get_json_value(item_path[:-1])  # Get parent of the selected node

        # Check if it's a dictionary node or a list node
        if isinstance(parent, dict):
            # Generate a new key for the duplicated node
            base_key = item.text(0)
            new_key = base_key + "_copy"
            parent[new_key] = self.copy_json_value(self.get_json_value(item_path))

            # Add new tree item
            new_item = QTreeWidgetItem([new_key])
            parent_item.addChild(new_item)
            self.load_json_into_tree(parent[new_key], new_item)

        elif isinstance(parent, list):
            # Get the index of the selected node
            index = int(item.text(0))
            parent.append(self.copy_json_value(parent[index]))

            # Add new tree item
            new_item = QTreeWidgetItem([str(len(parent) - 1)])
            parent_item.addChild(new_item)
            self.load_json_into_tree(parent[-1], new_item)

        # Save the updated JSON after adding the duplicate entry
        with open(self.json_file_path, 'w') as json_file:
            json.dump(self.json_data, json_file, indent=4)

    def copy_json_value(self, value):
        """Recursively copy a JSON value (dicts, lists, or primitives)"""
        if isinstance(value, dict):
            return {k: self.copy_json_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.copy_json_value(v) for v in value]
        else:
            return value

    def set_tree_font_size(self, size):
        """Set the font size for the tree view."""
        font = self.tree.font()
        font.setPointSize(size)
        self.tree.setFont(font)

    def set_text_font_size(self, size):
        """Set the font size for the text area."""
        font = self.text_area.font()
        font.setPointSize(size)
        self.text_area.setFont(font)

    def increase_font_size(self):
        """Increase font size for both tree and text area."""
        self.tree_font_size += 1
        self.text_font_size += 1  # Increase text area font size too
        self.set_tree_font_size(self.tree_font_size)
        self.set_text_font_size(self.text_font_size)

    def decrease_font_size(self):
        """Decrease font size for both tree and text area."""
        self.tree_font_size = max(1, self.tree_font_size - 1)  # Prevent font size from going below 1
        self.text_font_size = max(1, self.text_font_size - 1)  # Prevent font size from going below 1
        self.set_tree_font_size(self.tree_font_size)
        self.set_text_font_size(self.text_font_size)

    def reset_font_size(self):
        """Reset font size to the original size for both tree and text area."""
        self.tree_font_size = self.original_font_size
        self.text_font_size = self.original_font_size
        self.set_tree_font_size(self.tree_font_size)
        self.set_text_font_size(self.text_font_size)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    editor = JsonEditorApp()
    editor.resize(800, 600)  # Standard window size
    editor.show()

    sys.exit(app.exec_())

