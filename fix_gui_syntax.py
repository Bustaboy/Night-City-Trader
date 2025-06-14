#!/usr/bin/env python3
"""Fix syntax error in gui/main.py"""
import os
import re

print("🔧 Fixing GUI syntax error...")

gui_file = "gui/main.py"

# Read the current file
with open(gui_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the problematic line
problem_line = None
for i, line in enumerate(lines):
    if "response.raise_for_status()" in line and i > 0:
        # Check if there's a try block above without except
        j = i - 1
        while j >= 0:
            if lines[j].strip().startswith("try:"):
                # Found try block, now check if there's an except before our line
                has_except = False
                for k in range(j + 1, i):
                    if lines[k].strip().startswith(("except", "finally")):
                        has_except = True
                        break
                if not has_except:
                    problem_line = i
                    print(f"Found problematic try block starting at line {j+1}")
                    break
            j -= 1

if problem_line is None:
    print("❌ Could not locate the exact syntax error")
    print("Let me search more broadly...")
    
    # Alternative fix: Find all response.raise_for_status() calls and ensure they're in proper try-except blocks
    content = ''.join(lines)
    
    # Pattern to find try blocks that might be incomplete
    pattern = r'(\s*)try:\s*\n((?:.*\n)*?)(\s*response\.raise_for_status\(\))'
    
    def fix_try_block(match):
        indent = match.group(1)
        block_content = match.group(2)
        statement = match.group(3)
        
        # Check if there's already an except clause
        if 'except' in block_content:
            return match.group(0)
        
        # Add proper except block
        return f"""{indent}try:
{block_content}{statement}
{indent}except requests.exceptions.RequestException as e:
{indent}    logger.error(f"Request failed: {{e}}")
{indent}    raise"""
    
    content = re.sub(pattern, fix_try_block, content, flags=re.MULTILINE)
    
    # Write the fixed content
    with open(gui_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Applied general fix for try-except blocks")

else:
    # Specific fix for the found problem
    # Insert except block after the raise_for_status() line
    indent_level = len(lines[problem_line]) - len(lines[problem_line].lstrip())
    indent = ' ' * indent_level
    
    # Find where to insert the except block
    insert_line = problem_line + 1
    
    # Create except block
    except_block = [
        f"{indent}except requests.exceptions.RequestException as e:\n",
        f"{indent}    logger.error(f\"Request failed: {{e}}\")\n",
        f"{indent}    raise\n"
    ]
    
    # Insert the except block
    for i, line in enumerate(except_block):
        lines.insert(insert_line + i, line)
    
    # Write the fixed file
    with open(gui_file, "w", encoding="utf-8") as f:
        f.writelines(lines)
    
    print(f"✅ Fixed syntax error at line {problem_line + 1}")

# Additional safety check - ensure all try blocks have except clauses
print("\n🔍 Performing safety check...")

with open(gui_file, "r", encoding="utf-8") as f:
    content = f.read()

# More comprehensive fix
fixes_made = 0

# Pattern to match try blocks without except
def ensure_try_except(content):
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        fixed_lines.append(lines[i])
        
        # If we find a try: line
        if lines[i].strip() == 'try:':
            indent = len(lines[i]) - len(lines[i].lstrip())
            indent_str = ' ' * indent
            
            # Look ahead to find the end of the try block
            j = i + 1
            try_block_lines = []
            found_except = False
            
            while j < len(lines):
                # Check if we've reached the same or lower indentation level
                if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= indent:
                    # Check if it's an except or finally
                    if lines[j].strip().startswith(('except', 'finally')):
                        found_except = True
                    break
                try_block_lines.append(lines[j])
                j += 1
            
            # Add all the try block lines
            for line in try_block_lines:
                fixed_lines.append(line)
                i += 1
            
            # If no except was found, add one
            if not found_except and try_block_lines:
                fixed_lines.append(f"{indent_str}except Exception as e:")
                fixed_lines.append(f"{indent_str}    logger.error(f\"Error: {{e}}\")")
                fixed_lines.append(f"{indent_str}    raise")
                global fixes_made
                fixes_made += 1
        
        i += 1
    
    return '\n'.join(fixed_lines)

# Apply comprehensive fix
fixed_content = ensure_try_except(content)

with open(gui_file, "w", encoding="utf-8") as f:
    f.write(fixed_content)

print(f"✅ Safety check complete - {fixes_made} additional fixes applied")
print("\n📋 Summary:")
print("- Fixed syntax error with missing except blocks")
print("- Added proper exception handling")
print("- Ensured all try blocks have except clauses")
print("\n🚀 GUI should now start without syntax errors!")
print("\nRun: python gui/main.py")