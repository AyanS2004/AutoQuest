#!/usr/bin/env python3
"""
Simple test script for GCC functionality
"""

import sys
import os
sys.path.append('.')

def test_gcc_import():
    """Test if GCC module can be imported"""
    try:
        from autoquest.gcc import FinalPerfectGCCExtractor
        print("✅ GCC module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import GCC module: {e}")
        return False

def test_gcc_instantiation():
    """Test if GCC extractor can be instantiated"""
    try:
        from autoquest.gcc import FinalPerfectGCCExtractor
        
        # Check if required files exist
        input_file = "solutions.xlsx"
        template_file = "template.xlsx"
        
        if not os.path.exists(input_file):
            print(f"⚠️  Input file {input_file} not found")
        if not os.path.exists(template_file):
            print(f"⚠️  Template file {template_file} not found")
        
        # Create extractor instance
        extractor = FinalPerfectGCCExtractor(
            input_file=input_file,
            output_file="test_output.xlsx",
            template_file=template_file
        )
        print("✅ GCC extractor instantiated successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to instantiate GCC extractor: {e}")
        return False

def main():
    print("Testing GCC functionality...")
    print("=" * 50)
    
    # Test imports
    if not test_gcc_import():
        return False
    
    # Test instantiation
    if not test_gcc_instantiation():
        return False
    
    print("=" * 50)
    print("✅ All GCC tests passed!")
    print("\nYou can now:")
    print("1. Run GCC extraction: python run_gcc.py")
    print("2. Start the web interface: cd frontend && npm run dev")
    print("3. Access GCC page at: http://localhost:5173/gcc")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
