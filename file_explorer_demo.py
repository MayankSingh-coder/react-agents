#!/usr/bin/env python3
"""Simple demo of FileExplorerTool usage."""

import asyncio
from tools.file_explorer_tool import FileExplorerTool

async def demo():
    """Simple demo of file explorer capabilities."""
    
    # Initialize the explorer
    explorer = FileExplorerTool(safe_mode=False)
    
    # Get current project path
    project_path = "/Users/mayank/Desktop/concepts/react-agents"
    
    print("🔍 FileExplorerTool Demo")
    print("=" * 40)
    
    # 1. Quick project overview
    print("\n📊 Project Overview:")
    result = await explorer.execute(f"project_structure('{project_path}')")
    if result.success:
        data = result.data
        print(f"   Project Type: {data['project_type']}")
        print(f"   Config Files: {len(data['config_files'])}")
        print(f"   Documentation: {len(data['documentation'])}")
        print(f"   Test Files: {len(data['tests'])}")
    
    # 2. Find all Python files
    print("\n🐍 Python Files:")
    result = await explorer.execute(f"find_files_recursive('*.py', '{project_path}')")
    if result.success:
        print(f"   Found {result.data['total_matches']} Python files")
        print("   Top 5 by size:")
        sorted_files = sorted(result.data['matches'], key=lambda x: x['size'], reverse=True)
        for file_info in sorted_files[:5]:
            print(f"   - {file_info['path']} ({file_info['size_formatted']})")
    
    # 3. Code statistics
    print("\n📈 Code Statistics:")
    result = await explorer.execute(f"code_stats('{project_path}')")
    if result.success:
        data = result.data
        print(f"   Total Lines: {data['total_lines']:,}")
        print(f"   Total Size: {data['total_size_formatted']}")
        print("   Languages:")
        for lang, stats in data['languages'].items():
            print(f"   - {lang}: {stats['files']} files, {stats['lines']:,} lines")
    
    # 4. Directory tree (limited depth)
    print("\n🌳 Directory Tree (depth 2):")
    result = await explorer.execute(f"explore_tree('{project_path}', 2)")
    if result.success:
        for line in result.data['tree'][:15]:  # Show first 15 lines
            print(f"   {line}")
        if len(result.data['tree']) > 15:
            print(f"   ... and {len(result.data['tree']) - 15} more items")

if __name__ == "__main__":
    asyncio.run(demo())