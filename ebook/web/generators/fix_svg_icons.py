#!/usr/bin/env python3

import os
import re
import glob

# SVG Icon CSS styles to add
SVG_ICON_CSS = """
        /* Architecture Section Icons and Headers */
        .architecture-title {
            background: #495057;
            color: white;
            padding: 1rem 1.5rem;
            margin: -2rem -2rem 1.5rem -2rem;
            border-radius: 10px 10px 0 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .architecture-icon {
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        }

        .architecture-title h4 {
            margin: 0;
            font-size: 1.1rem;
            font-weight: 600;
        }

        /* War Story Icons and Headers */
        .war-story-header {
            background: #856404;
            color: white;
            padding: 1rem 1.5rem;
            margin: -2rem -2rem 1.5rem -2rem;
            border-radius: 10px 10px 0 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .war-story-icon {
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        }

        .war-story-header h4 {
            margin: 0;
            font-size: 1.1rem;
            font-weight: 600;
        }

        /* Industry Insight Icons and Headers */
        .insight-header {
            background: #28a745;
            color: white;
            padding: 1rem 1.5rem;
            margin: -2rem -2rem 1.5rem -2rem;
            border-radius: 10px 10px 0 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .insight-icon {
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        }

        .insight-header h4 {
            margin: 0;
            font-size: 1.1rem;
            font-weight: 600;
        }
"""

def fix_svg_icons_in_file(file_path):
    """Add SVG icon CSS to a single HTML file if not already present"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if SVG icon styles are already present
    if '.architecture-icon' in content and '.war-story-icon' in content and '.insight-icon' in content:
        print(f"✓ SVG styles already present in: {file_path}")
        return False
    
    # Find the last </style> tag before </head>
    style_pattern = r'(\s*)(</style>\s*</head>)'
    match = re.search(style_pattern, content)
    
    if not match:
        print(f"✗ Could not find closing </style> tag in: {file_path}")
        return False
    
    # Insert the SVG CSS before the closing </style> tag
    indent = match.group(1)  # preserve indentation
    replacement = f"{SVG_ICON_CSS}{indent}{match.group(2)}"
    updated_content = re.sub(style_pattern, replacement, content)
    
    # Write the updated content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✓ Added SVG icon styles to: {file_path}")
    return True

def find_html_files_with_svg_icons(base_dir):
    """Find all HTML files that contain SVG icons but might be missing styles"""
    
    html_files = []
    pattern = os.path.join(base_dir, "**/*.html")
    
    for file_path in glob.glob(pattern, recursive=True):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if file has SVG icons (architecture-icon, war-story-icon, insight-icon)
            has_svg_icons = any(icon_class in content for icon_class in 
                              ['architecture-icon', 'war-story-icon', 'insight-icon'])
            
            if has_svg_icons:
                html_files.append(file_path)
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    return html_files

def main():
    base_dir = "/Users/pelleri/Documents/ai-team-orchestrator/ebook/web"
    
    print("🔍 Finding HTML files with SVG icons...")
    html_files = find_html_files_with_svg_icons(base_dir)
    
    print(f"📊 Found {len(html_files)} files with SVG icons")
    
    updated_count = 0
    for file_path in html_files:
        if fix_svg_icons_in_file(file_path):
            updated_count += 1
    
    print(f"\n✅ COMPLETED: Updated {updated_count} files with SVG icon styles")
    print(f"📄 Total files processed: {len(html_files)}")

if __name__ == "__main__":
    main()