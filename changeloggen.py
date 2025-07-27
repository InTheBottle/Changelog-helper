import json
import os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import mobase

def parse_modlist(file_path):
    mods = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('+') or line.startswith('-'):
                    mod_name = line[1:].strip()
                    mods.add(mod_name)
    except Exception as e:
        return None
    return mods

def generate_changelog(old_mods, new_mods):
    if old_mods is None or new_mods is None:
        return None
    
    added = sorted(new_mods - old_mods, key=str.lower)
    removed = sorted(old_mods - new_mods, key=str.lower)
    
    markdown = "# Modlist Changelog\n\n"
    
    markdown += "### Summary\n"
    markdown += f"- **Added:** {len(added)} mods\n"
    markdown += f"- **Removed:** {len(removed)} mods\n\n"
    
    markdown += "## Added Mods\n\n"
    if added:
        markdown += "\n".join(f"- {mod}" for mod in added) + "\n\n"
    else:
        markdown += "No mods added.\n\n"
    
    markdown += "## Removed Mods\n\n"
    if removed:
        markdown += "\n".join(f"- {mod}" for mod in removed) + "\n"
    else:
        markdown += "No mods removed.\n"
    
    return markdown

class ComparerDialog(QDialog):
    def __init__(self, parent, organizer):
        super().__init__(parent)
        self.organizer = organizer
        self.setWindowTitle("Changelog Helper")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        h1 = QHBoxLayout()
        lbl1 = QLabel("Old modlist:")
        self.old_edit = QLineEdit()
        btn1 = QPushButton("Browse")
        btn1.clicked.connect(self.select_old)
        h1.addWidget(lbl1)
        h1.addWidget(self.old_edit)
        h1.addWidget(btn1)
        layout.addLayout(h1)
        
        h2 = QHBoxLayout()
        lbl2 = QLabel("New modlist:")
        self.new_edit = QLineEdit()
        # Prefill with current profile's modlist.txt
        current_profile_path = self.organizer.profilePath()
        modlist_path = os.path.join(current_profile_path, "modlist.txt")
        if os.path.exists(modlist_path):
            self.new_edit.setText(modlist_path)
        btn2 = QPushButton("Browse")
        btn2.clicked.connect(self.select_new)
        h2.addWidget(lbl2)
        h2.addWidget(self.new_edit)
        h2.addWidget(btn2)
        layout.addLayout(h2)
        
        gen_btn = QPushButton("Generate Changelog")
        gen_btn.clicked.connect(self.generate)
        layout.addWidget(gen_btn)
        
        self.setLayout(layout)
    
    def select_old(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Old modlist.txt", "", "Text files (*.txt)")
        if path:
            self.old_edit.setText(path)
    
    def select_new(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select New modlist.txt", "", "Text files (*.txt)")
        if path:
            self.new_edit.setText(path)
    
    def generate(self):
        old_file = self.old_edit.text()
        new_file = self.new_edit.text()
        
        if not old_file or not new_file:
            QMessageBox.warning(self, "Warning", "Please select both files.")
            return
        
        old_mods = parse_modlist(old_file)
        new_mods = parse_modlist(new_file)
        
        if old_mods is None or new_mods is None:
            QMessageBox.error(self, "Error", "Failed to parse files.")
            return
        
        markdown = generate_changelog(old_mods, new_mods)
        if markdown is None:
            return
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Changelog", "changelog.md", "Markdown files (*.md)")
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                QMessageBox.information(self, "Success", f"Saved to {save_path}")
            except Exception as e:
                QMessageBox.error(self, "Error", str(e))

class ModlistComparerTool(mobase.IPluginTool):
    def __init__(self):
        super().__init__()
        self.__organizer = None
        self.__parentWidget = None
    
    def init(self, organizer):
        self.__organizer = organizer
        return True
    
    def name(self):
        return "ModlistComparer"
    
    def author(self):
        return "Bottle"
    
    def description(self):
        return "A tool to compare two modlist.txt files and generate a changelog in Markdown format."
    
    def version(self):
        return mobase.VersionInfo(1, 0, 0)
    
    def settings(self):
        return []
    
    def displayName(self):
        return "Changelog Helper"
    
    def tooltip(self):
        return "Compare modlists and generate a changelog"
    
    def icon(self):
        return QIcon()
    
    def setParentWidget(self, widget):
        self.__parentWidget = widget
    
    def display(self):
        dialog = ComparerDialog(self.__parentWidget, self.__organizer)
        dialog.exec()

def createPlugin():
    return ModlistComparerTool()