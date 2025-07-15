#!/usr/bin/env python
"""
Test script for the FAISS index database.

This script tests:
1. Index loading and consistency
2. Model loading and encoding
3. Search functionality
4. Various medical queries
5. Index statistics

Usage:
    python tests/test_index.py
"""

import os
import sys
import pickle
import numpy as np
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Disable tokenizers parallelism to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import faiss
from sentence_transformers import SentenceTransformer

# Set default environment variables for testing
os.environ.setdefault("MODEL_ID", "intfloat/multilingual-e5-base")
os.environ.setdefault("INDEX_PATH", "data/faiss_index")
os.environ.setdefault("MAP_PATH", "data/doc_map.pkl")

class IndexTester:
    """Test class for the FAISS index database."""
    
    def __init__(self):
        self.model = None
        self.index = None
        self.doc_map = None
        self.test_queries = [
            "головний біль в скроневій ділянці",
            "кашель температура",
            "біль в животі",
            "гіпертонія артеріальний тиск",
            "діабет цукровий діабет",
            "алергія реакція",
            "травма перелом",
            "інфекція вірус",
            "серцево-судинні захворювання",
            "пневмонія легені",
            "астма бронхіальна астма",
            "артрит суглоби",
            "депресія психічні розлади",
            "рак онкологія",
            "інсульт мозковий інсульт"
        ]
    
    def load_components(self):
        """Load the model, index, and document map."""
        print("🔄 Loading components...")
        
        try:
            # Check if files exist
            index_path = Path(os.environ["INDEX_PATH"])
            map_path = Path(os.environ["MAP_PATH"])
            
            if not index_path.exists():
                print(f"❌ Index file not found: {index_path}")
                return False
            
            if not map_path.exists():
                print(f"❌ Map file not found: {map_path}")
                return False
            
            # Load model
            model_id = os.environ["MODEL_ID"]
            print(f"🤖 Loading model: {model_id}")
            self.model = SentenceTransformer(model_id)
            print("✅ Model loaded successfully")
            
            # Load index
            print(f"📊 Loading FAISS index: {index_path}")
            self.index = faiss.read_index(str(index_path))
            print(f"✅ Index loaded: {self.index.ntotal} documents, {self.index.d} dimensions")
            
            # Load document map
            print(f"🗺️ Loading document map: {map_path}")
            with open(map_path, "rb") as f:
                self.doc_map = pickle.load(f)
            print(f"✅ Document map loaded: {len(self.doc_map)} entries")
            
            # Verify consistency
            if self.index.ntotal != len(self.doc_map):
                print(f"⚠️  Warning: Index has {self.index.ntotal} docs, map has {len(self.doc_map)} entries")
                return False
            
            print("✅ All components loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading components: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_encoding(self):
        """Test model encoding functionality."""
        print("\n🧪 Testing model encoding...")
        
        try:
            test_query = "тест запит"
            vec = self.model.encode(test_query, normalize_embeddings=True).astype("float32")
            
            print(f"✅ Encoding successful")
            print(f"   Query: '{test_query}'")
            print(f"   Vector shape: {vec.shape}")
            print(f"   Vector dtype: {vec.dtype}")
            print(f"   Vector norm: {np.linalg.norm(vec):.6f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Encoding test failed: {e}")
            return False
    
    def test_search(self, query, k=3):
        """Test search functionality with a specific query."""
        try:
            # Encode query
            vec = self.model.encode(query, normalize_embeddings=True).astype("float32")[None]
            
            # Search
            D, I = self.index.search(vec, k)
            
            print(f"🔍 Query: '{query}'")
            print(f"📊 Found {len(I[0])} results:")
            
            results = []
            for rank, (idx, score) in enumerate(zip(I[0], D[0]), 1):
                if 0 <= idx < len(self.doc_map):
                    content = self.doc_map[idx]
                    lines = content.split('\n')
                    title = lines[0] if lines else "No title"
                    preview = content[:150].replace('\n', ' ').strip()
                    
                    result = {
                        'rank': rank,
                        'score': score,
                        'title': title,
                        'preview': preview
                    }
                    results.append(result)
                    
                    print(f"   {rank}. Similarity: {score:.3f}")
                    print(f"      📄 {title}")
                    print(f"      📝 {preview}...")
                else:
                    print(f"   {rank}. ❌ Index {idx} out of range!")
            
            return results
            
        except Exception as e:
            print(f"❌ Search test failed: {e}")
            return []
    
    def run_comprehensive_tests(self):
        """Run all tests."""
        print("🚀 Starting comprehensive index tests...")
        print("=" * 60)
        
        # Test 1: Load components
        if not self.load_components():
            print("❌ Component loading failed. Exiting.")
            return False
        
        # Test 2: Encoding
        if not self.test_encoding():
            print("❌ Encoding test failed.")
            return False
        
        # Test 3: Search with test queries
        print("\n🧪 Testing search with various queries...")
        successful_searches = 0
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n{'='*50}")
            print(f"Test {i}/{len(self.test_queries)}: {query}")
            results = self.test_search(query, k=2)
            
            if results:
                successful_searches += 1
                # Check if results make sense
                if any(r['score'] > 0.5 for r in results):
                    print("   ✅ Good quality results found")
                else:
                    print("   ⚠️  Low similarity scores")
            else:
                print("   ❌ No results returned")
        
        # Test 4: Index statistics
        print(f"\n📊 Test Summary:")
        print(f"   Total queries tested: {len(self.test_queries)}")
        print(f"   Successful searches: {successful_searches}")
        print(f"   Success rate: {successful_searches/len(self.test_queries)*100:.1f}%")
        
        # Test 5: Show index statistics
        self.show_statistics()
        
        return successful_searches == len(self.test_queries)
    
    def show_statistics(self):
        """Show detailed index statistics."""
        print(f"\n📈 Index Statistics:")
        print(f"   📄 Total documents: {self.index.ntotal}")
        print(f"   🔢 Vector dimensions: {self.index.d}")
        print(f"   🗂️  Document map entries: {len(self.doc_map)}")
        print(f"   🤖 Model: {os.environ['MODEL_ID']}")
        print(f"   💾 Index file: {os.environ['INDEX_PATH']}")
        print(f"   🗺️  Map file: {os.environ['MAP_PATH']}")
        
        # Document length statistics
        doc_lengths = [len(doc) for doc in self.doc_map]
        print(f"\n📏 Document Length Statistics:")
        print(f"   Min: {min(doc_lengths):,} characters")
        print(f"   Max: {max(doc_lengths):,} characters")
        print(f"   Avg: {sum(doc_lengths)/len(doc_lengths):,.0f} characters")
        
        # Show sample document titles
        print(f"\n📋 Sample Document Titles:")
        for i, doc in enumerate(self.doc_map[:5]):
            title = doc.split('\n')[0] if doc else "No title"
            print(f"   {i+1}. {title[:60]}...")
        
        if len(self.doc_map) > 5:
            print(f"   ... and {len(self.doc_map) - 5} more documents")
    
    def interactive_search(self):
        """Run interactive search mode."""
        if not self.model or not self.index or not self.doc_map:
            print("❌ Components not loaded. Run load_components() first.")
            return
        
        print("\n🎯 Interactive Search Mode")
        print("Enter medical queries (or 'quit' to exit):")
        
        while True:
            try:
                query = input("\n🔍 Query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not query:
                    print("⚠️  Please enter a query.")
                    continue
                
                # Get number of results
                try:
                    k_input = input("📊 Number of results (default 3): ").strip()
                    k = int(k_input) if k_input else 3
                    k = max(1, min(k, 10))  # Limit between 1 and 10
                except ValueError:
                    k = 3
                
                print()
                self.test_search(query, k)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function to run the tests."""
    tester = IndexTester()
    
    # Run comprehensive tests
    success = tester.run_comprehensive_tests()
    
    if success:
        print("\n✅ All tests passed!")
        
        # Ask if user wants interactive search
        try:
            response = input("\n🎯 Would you like to try interactive search? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                tester.interactive_search()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
    
    print("\n🏁 Testing completed.")

if __name__ == "__main__":
    main() 