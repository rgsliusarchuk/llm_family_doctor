#!/usr/bin/env python3
"""
Script to reset semantic cache.
This script can be used to reset or clear the semantic index.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache.doctor_semantic_index import reset_semantic_index, clear_semantic_index, get_semantic_index_stats

def main():
    """Main function to reset semantic cache."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset semantic cache")
    parser.add_argument(
        "--clear", 
        action="store_true", 
        help="Clear semantic index completely (set to empty)"
    )
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Show semantic index statistics"
    )
    
    args = parser.parse_args()
    
    if args.stats:
        stats = get_semantic_index_stats()
        print("📊 Semantic Index Statistics:")
        print(f"  Total documents: {stats['total_documents']}")
        print(f"  Dimension: {stats['dimension']}")
        print(f"  Texts count: {stats['texts_count']}")
        return
    
    if args.clear:
        print("🧠 Clearing semantic index...")
        clear_semantic_index()
        print("✅ Semantic index cleared!")
    else:
        print("🔄 Resetting semantic index...")
        reset_semantic_index()
        print("✅ Semantic index reset!")
    
    # Show stats after operation
    stats = get_semantic_index_stats()
    print(f"📊 New stats - Documents: {stats['total_documents']}, Texts: {stats['texts_count']}")

if __name__ == "__main__":
    main() 