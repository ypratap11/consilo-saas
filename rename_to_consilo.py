#!/usr/bin/env python3
"""
Project Rename Script: FlowIQ → Consilo
Automatically renames all references in code, docs, and files
"""

import os
import shutil
from pathlib import Path
import re
from datetime import datetime

# Configuration
OLD_NAME = "FlowIQ"
NEW_NAME = "Consilo"
OLD_LOWER = OLD_NAME.lower()
NEW_LOWER = NEW_NAME.lower()

# Directories to process
INCLUDE_DIRS = ["backend", "docs", "."]
EXCLUDE_DIRS = [".git", "__pycache__", "node_modules", "venv", ".env", "postgres_data"]

# File extensions to update
TEXT_EXTENSIONS = [".py", ".md", ".txt", ".yml", ".yaml", ".json", ".sh", ".env.example"]

def create_backup():
    """Create backup of current state"""
    backup_name = f"backup-{OLD_LOWER}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    backup_path = Path("..") / backup_name
    
    print(f"📦 Creating backup at: {backup_path}")
    
    # Create backup directory
    backup_path.mkdir(exist_ok=True)
    
    # Copy important files (don't copy docker volumes)
    for item in Path(".").iterdir():
        if item.name not in [".git", "postgres_data", "__pycache__", "venv", ".pytest_cache"]:
            if item.is_file():
                shutil.copy2(item, backup_path / item.name)
            elif item.is_dir():
                shutil.copytree(item, backup_path / item.name, ignore=shutil.ignore_patterns(
                    "*.pyc", "__pycache__", ".git", "postgres_data", "venv"
                ))
    
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def should_process_file(filepath):
    """Check if file should be processed"""
    # Skip excluded directories
    for exclude in EXCLUDE_DIRS:
        if exclude in str(filepath):
            return False
    
    # Check extension
    return filepath.suffix in TEXT_EXTENSIONS

def update_file_content(filepath):
    """Update content in a single file"""
    try:
        content = filepath.read_text(encoding='utf-8')
        original_content = content
        
        # Replace all variations
        content = content.replace(OLD_NAME, NEW_NAME)
        content = content.replace(OLD_LOWER, NEW_LOWER)
        content = content.replace(OLD_NAME.upper(), NEW_NAME.upper())
        
        # Special cases
        content = content.replace("flowiq-saas", "consilo-saas")
        content = content.replace("flowiq_engine", "consilo_engine")
        
        # Only write if content changed
        if content != original_content:
            filepath.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"⚠️  Error processing {filepath}: {e}")
        return False

def rename_files():
    """Rename files containing old name"""
    renamed_files = []
    
    for filepath in Path(".").rglob("*"):
        if not filepath.is_file():
            continue
        
        # Skip excluded directories
        skip = False
        for exclude in EXCLUDE_DIRS:
            if exclude in str(filepath):
                skip = True
                break
        if skip:
            continue
        
        # Check if filename contains old name
        if OLD_LOWER in filepath.name.lower():
            new_name = filepath.name.replace(OLD_LOWER, NEW_LOWER).replace(OLD_NAME, NEW_NAME)
            new_path = filepath.parent / new_name
            
            try:
                filepath.rename(new_path)
                renamed_files.append((str(filepath), str(new_path)))
            except Exception as e:
                print(f"⚠️  Error renaming {filepath}: {e}")
    
    return renamed_files

def main():
    """Main rename process"""
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║         Project Rename: {OLD_NAME} → {NEW_NAME}                       ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Create backup
    backup_path = create_backup()
    
    # Step 2: Update file contents
    print(f"\n📝 Updating file contents...")
    updated_files = []
    
    for filepath in Path(".").rglob("*"):
        if filepath.is_file() and should_process_file(filepath):
            if update_file_content(filepath):
                updated_files.append(str(filepath))
    
    print(f"✅ Updated {len(updated_files)} files")
    
    # Step 3: Rename files
    print(f"\n📁 Renaming files...")
    renamed_files = rename_files()
    
    if renamed_files:
        print(f"✅ Renamed {len(renamed_files)} files:")
        for old, new in renamed_files:
            print(f"   {old} → {new}")
    else:
        print("ℹ️  No files to rename")
    
    # Summary
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                    Rename Complete! ✨                         ║
╚════════════════════════════════════════════════════════════════╝

Summary:
  • Files updated: {len(updated_files)}
  • Files renamed: {len(renamed_files)}
  • Backup location: {backup_path}

Next steps:
  1. Review changes: git diff
  2. Test application: docker-compose up -d --build
  3. Run tests: python test_local.py
  4. Commit changes: git commit -am "Rebrand from {OLD_NAME} to {NEW_NAME}"

{NEW_NAME} is ready to ship! 🚀
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Rename cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Restore from backup if needed")
