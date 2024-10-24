# https://chatgpt.com/share/671743c4-2c70-8002-932a-8fb01719a926
import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QMenu
from PyQt5.QtCore import Qt

class JsonEditorApp(QWidget):
    def __init__(self, json_file_path):
        super().__init__()

        self.json_file_path = json_file_path
        self.current_item = None
        self.is_modified = False  # To track if the current leaf is modified

        # Main layout
        layout = QHBoxLayout()

        # Left side: Tree view and refresh button
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

        layout.addLayout(left_layout)

        # Right side: Text editor and save button
        right_layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)  # Initially readonly to prevent editing raw JSON
        self.text_area.setStyleSheet("background-color: lightgray;")  # Set initial background color
        self.text_area.textChanged.connect(self.on_text_changed)
        right_layout.addWidget(self.text_area)

        self.save_button = QPushButton("Save")
        self.save_button.setEnabled(False)  # Initially disabled
        self.save_button.clicked.connect(self.save_entry)
        right_layout.addWidget(self.save_button)

        layout.addLayout(right_layout)

        self.setLayout(layout)
        self.setWindowTitle("JSON Editor")

        # Load the initial JSON structure
        self.load_json()

    def load_json(self):
        with open(self.json_file_path, 'r') as file:
            self.json_data = json.load(file)
        self.tree.clear()
        self.load_json_into_tree(self.json_data)

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
                self.text_area.setStyleSheet("background-color: white;")  # Change background to white
                self.text_area.setText(json_value.replace("\\n", "\n"))
            elif isinstance(json_value, (dict, list)):
                self.text_area.setReadOnly(True)  # Deactivate text area (non-leaf node)
                self.text_area.setStyleSheet("background-color: lightgray;")  # Change background to light gray
                self.text_area.setText(json.dumps(json_value, indent=4))
            else:
                self.text_area.setReadOnly(False)  # Activate text area for editing
                self.text_area.setStyleSheet("background-color: white;")  # Change background to white
                self.text_area.setText(str(json_value))

            # Enable the save button only if the item has no children (i.e., it's a leaf node)
            if item.childCount() == 0:
                self.save_button.setEnabled(True)
                self.text_area.setReadOnly(False)  # Allow editing
                self.text_area.setStyleSheet("background-color: white;")  # Change background to white
            else:
                self.save_button.setEnabled(False)
                self.text_area.setReadOnly(True)  # Disable editing for non-leaf nodes
                self.text_area.setStyleSheet("background-color: lightgray;")  # Change background to light gray

            self.is_modified = False  # Reset the modification flag when switching nodes

        except Exception as e:
            self.text_area.setReadOnly(True)  # Deactivate text area in case of error
            self.text_area.setStyleSheet("background-color: lightgray;")  # Change background to light gray
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
        obj[last_key] = value

    def save_entry(self):
        if self.current_item is not None:
            item_path = self.get_item_path(self.current_item)
            new_value = self.text_area.toPlainText().replace("\n", "\\n")
            self.set_json_value(item_path, new_value)

            # Save updated JSON to file
            with open(self.json_file_path, 'w') as json_file:
                json.dump(self.json_data, json_file, indent=4)

            self.is_modified = False  # Reset the modification flag after saving

    def reload_json(self):
        self.load_json()

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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Path to the JSON file
    json_file_path = 'test.json'

    editor = JsonEditorApp(json_file_path)
    editor.resize(800, 600)
    editor.show()

    sys.exit(app.exec_())
