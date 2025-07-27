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

def get_current_mod_versions(organizer):
    mod_versions = {}
    mod_list = organizer.modList()
    for mod_name in mod_list.allMods():
        mod = organizer.getMod(mod_name)
        if mod:
            version = mod.version().displayString() if mod.version() else "Unknown"
            mod_versions[mod_name] = version
    return mod_versions

def load_versions(file_path):
    if not file_path:
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

def generate_changelog(old_mods, new_mods, old_versions=None, new_versions=None):
    if old_mods is None or new_mods is None:
        return None
    
    added = sorted(new_mods - old_mods, key=str.lower)
    removed = sorted(old_mods - new_mods, key=str.lower)
    common = old_mods & new_mods
    updated = []
    if old_versions and new_versions:
        for mod in sorted(common, key=str.lower):
            old_v = old_versions.get(mod, "Unknown")
            new_v = new_versions.get(mod, "Unknown")
            if old_v != new_v:
                updated.append((mod, old_v, new_v))
    
    markdown = "# Modlist Changelog\n\n"
    
    markdown += "### Summary\n"
    markdown += f"- **Added:** {len(added)} mods\n"
    markdown += f"- **Removed:** {len(removed)} mods\n"
    markdown += f"- **Updated:** {len(updated)} mods\n\n"
    
    markdown += "## Added Mods\n\n"
    if added:
        markdown += "\n".join(f"- {mod}" for mod in added) + "\n\n"
    else:
        markdown += "No mods added.\n\n"
    
    markdown += "## Removed Mods\n\n"
    if removed:
        markdown += "\n".join(f"- {mod}" for mod in removed) + "\n\n"
    else:
        markdown += "No mods removed.\n\n"
    
    markdown += "## Updated Mods\n\n"
    if updated:
        for mod, old_v, new_v in updated:
            markdown += f"- {mod}: {old_v} → {new_v}\n"
        markdown += "\n"
    else:
        markdown += "No mods updated.\n\n"
    
    return markdown

class ComparerDialog(QDialog):
    def __init__(self, parent, organizer):
        super().__init__(parent)
        self.organizer = organizer
        self.setWindowTitle("Changelog Helper")
        self.setMinimumWidth(600)  # Make the dialog wider by default
        
        layout = QVBoxLayout(self)
        
        # Modlists
        h1 = QHBoxLayout()
        lbl1 = QLabel("Old modlist:")
        self.old_modlist_edit = QLineEdit()
        btn1 = QPushButton("Browse")
        btn1.clicked.connect(self.select_old_modlist)
        h1.addWidget(lbl1)
        h1.addWidget(self.old_modlist_edit)
        h1.addWidget(btn1)
        layout.addLayout(h1)
        
        h2 = QHBoxLayout()
        lbl2 = QLabel("New modlist:")
        self.new_modlist_edit = QLineEdit()
        current_profile_path = self.organizer.profilePath()
        modlist_path = os.path.join(current_profile_path, "modlist.txt")
        if os.path.exists(modlist_path):
            self.new_modlist_edit.setText(modlist_path)
        btn2 = QPushButton("Browse")
        btn2.clicked.connect(self.select_new_modlist)
        h2.addWidget(lbl2)
        h2.addWidget(self.new_modlist_edit)
        h2.addWidget(btn2)
        layout.addLayout(h2)
        
        # Versions
        h3 = QHBoxLayout()
        lbl3 = QLabel("Old versions:")
        self.old_versions_edit = QLineEdit()
        btn3 = QPushButton("Browse")
        btn3.clicked.connect(self.select_old_versions)
        h3.addWidget(lbl3)
        h3.addWidget(self.old_versions_edit)
        h3.addWidget(btn3)
        layout.addLayout(h3)
        
        # Buttons
        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Export Current Versions")
        export_btn.clicked.connect(self.export_current_versions)
        gen_btn = QPushButton("Generate Changelog")
        gen_btn.clicked.connect(self.generate)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(gen_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def select_old_modlist(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Old modlist.txt", "", "Text files (*.txt)")
        if path:
            self.old_modlist_edit.setText(path)
    
    def select_new_modlist(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select New modlist.txt", "", "Text files (*.txt)")
        if path:
            self.new_modlist_edit.setText(path)
    
    def select_old_versions(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Old versions.json", "", "JSON files (*.json)")
        if path:
            self.old_versions_edit.setText(path)
    
    def export_current_versions(self):
        mod_versions = get_current_mod_versions(self.organizer)
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Current Versions", "versions.json", "JSON files (*.json)")
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(mod_versions, f, indent=4, sort_keys=True)
                QMessageBox.information(self, "Success", f"Versions exported to {save_path}")
            except Exception as e:
                QMessageBox.error(self, "Error", str(e))
    
    def generate(self):
        old_modlist_file = self.old_modlist_edit.text()
        new_modlist_file = self.new_modlist_edit.text()
        
        old_mods = parse_modlist(old_modlist_file) if old_modlist_file else None
        new_mods = parse_modlist(new_modlist_file) if new_modlist_file else None
        
        old_versions_file = self.old_versions_edit.text()
        old_versions = load_versions(old_versions_file) if old_versions_file else None
        if old_versions_file and old_versions is None:
            QMessageBox.error(self, "Error", "Failed to load old versions.")
            return
        
        new_versions = get_current_mod_versions(self.organizer)
        
        if old_mods is None and old_versions is None and new_mods is None:
            QMessageBox.warning(self, "Warning", "Please provide at least an old modlist or old versions for comparison.")
            return
        
        if old_mods is None and old_versions:
            old_mods = set(old_versions.keys())
        if new_mods is None:
            new_mods = set(new_versions.keys())
        
        if old_mods is None or new_mods is None:
            QMessageBox.warning(self, "Warning", "Insufficient data for comparison.")
            return
        
        markdown = generate_changelog(old_mods, new_mods, old_versions, new_versions)
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

class ChangelogTool(mobase.IPluginTool):
    def __init__(self):
        super().__init__()
        self.__organizer = None
        self.__parentWidget = None
    
    def init(self, organizer):
        self.__organizer = organizer
        return True
    
    def name(self):
        return "Changelog Helper"
    
    def author(self):
        return "Bottle"
    
    def description(self):
        return "A tool to compare modlists/versions and generate a changelog in Markdown format."
    
    def version(self):
        return mobase.VersionInfo(1, 2, 0)
    
    def settings(self):
        return []
    
    def displayName(self):
        return "Changelog Helper"
    
    def tooltip(self):
        return "Compare modlists and generate changelog"
    
    def icon(self):
        return QIcon()
    
    def setParentWidget(self, widget):
        self.__parentWidget = widget
    
    def display(self):
        dialog = ComparerDialog(self.__parentWidget, self.__organizer)
        dialog.exec()

def createPlugin():
    return ChangelogTool()
