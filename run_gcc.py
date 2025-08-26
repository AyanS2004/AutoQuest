#!/usr/bin/env python3
"""
Simple script to run GCC extraction
"""

from autoquest.gcc import FinalPerfectGCCExtractor

def main():
    # Create extractor instance
    extractor = FinalPerfectGCCExtractor(
        input_file="solutions.xlsx",
        output_file="solutions_processed.xlsx", 
        template_file="template.xlsx"
    )

    # Run the extraction
    print("Starting GCC extraction...")
    extractor.run_final_perfect_gcc_extraction()
    print("GCC extraction completed!")

if __name__ == "__main__":
    main()
