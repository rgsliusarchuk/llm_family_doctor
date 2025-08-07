#!/usr/bin/env python3
"""
Script to reset ALL cache layers (Exact + Semantic).
This script resets Redis cache, database approved answers, and semantic index.
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache.redis_cache import clear_cache
from src.cache.doctor_semantic_index import clear_semantic_index, get_semantic_index_stats
from sqlmodel import Session, select
from src.db import engine
from src.db.models import DoctorAnswer

async def reset_all_cache():
    """Reset all cache layers."""
    print("🧹 Resetting ALL cache layers (Exact + Semantic)...")
    
    # 1. Clear Redis exact cache
    print("🔴 Clearing Redis exact cache...")
    try:
        await clear_cache()
        print("   ✅ Redis cache cleared")
    except Exception as e:
        print(f"   ⚠️  Redis cache clear failed: {e}")
    
    # 2. Clear database approved answers
    print("🗄️  Clearing approved answers from database...")
    try:
        with Session(engine) as session:
            approved_answers = session.exec(
                select(DoctorAnswer).where(DoctorAnswer.approved == True)
            ).all()
            for answer in approved_answers:
                answer.approved = False
            session.commit()
            print(f"   ✅ {len(approved_answers)} approved answers cleared")
    except Exception as e:
        print(f"   ⚠️  Database clear failed: {e}")
    
    # 3. Clear semantic index
    print("🧠 Clearing semantic cache...")
    try:
        clear_semantic_index()
        print("   ✅ Semantic index cleared")
    except Exception as e:
        print(f"   ⚠️  Semantic cache clear failed: {e}")
    
    # 4. Show final status
    print("\n📊 Final cache status:")
    try:
        stats = get_semantic_index_stats()
        print(f"   • Semantic index documents: {stats['total_documents']}")
        print(f"   • Semantic index texts: {stats['texts_count']}")
    except Exception as e:
        print(f"   • Semantic index status: Error - {e}")
    
    print("✅ ALL cache layers reset complete!")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset ALL cache layers")
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Show cache statistics only"
    )
    
    args = parser.parse_args()
    
    if args.stats:
        print("📊 Cache Statistics:")
        try:
            stats = get_semantic_index_stats()
            print(f"  Semantic index documents: {stats['total_documents']}")
            print(f"  Semantic index texts: {stats['texts_count']}")
        except Exception as e:
            print(f"  Error getting stats: {e}")
        return
    
    # Run the async reset function
    asyncio.run(reset_all_cache())

if __name__ == "__main__":
    main() 