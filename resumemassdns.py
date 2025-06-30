#!/usr/bin/env python3
"""
Script to remove already processed domains from the original domains file.
This helps resume massdns processing from where it left off.

Usage: python remove_processed_domains.py
"""

import os
from collections import defaultdict

def extract_processed_domains(results_file):
    """
    Extract processed domains from massdns results file.
    Returns a set of processed domain names.
    """
    processed_domains = set()
    
    print(f"reading file from {results_file}...")
    
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            line_count = 0
            for line in f:
                line = line.strip()
                if line and ' A ' in line:
                    domain = line.split(' A ')[0].rstrip('.')
                    processed_domains.add(domain)
                    line_count += 1
                    
                    if line_count % 100000 == 0:
                        print(f"  read {line_count:,} lines, found {len(processed_domains):,} domains")
        
        print(f"done found {len(processed_domains):,} domains")
        return processed_domains
        
    except FileNotFoundError:
        print(f"cant find{results_file}")
        return set()
    except Exception as e:
        print(f"error {results_file} while reading {e}")
        return set()

def filter_domains(original_file, processed_domains, output_file):
    """
    Filter out processed domains from the original domains file.
    """
    print(f"正在從 {original_file} 移除已處理的域名...")
    
    try:
        remaining_count = 0
        removed_count = 0
        total_count = 0
        
        with open(original_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                domain = line.strip()
                total_count += 1
                
                if domain in processed_domains:
                    removed_count += 1
                else:
                    outfile.write(line)
                    remaining_count += 1
                
                # Progress indicator every 100k lines
                if total_count % 100000 == 0:
                    print(f"  done reading {total_count:,} lines (remain: {remaining_count:,}, removed: {removed_count:,})")
        
        print(f"done")
        print(f"total: {total_count:,}")
        print(f"removed: {removed_count:,}")
        print(f"remain: {remaining_count:,}")
        print(f"saved to {output_file}")
        
    except FileNotFoundError:
        print(f"cant find {original_file}")
    except Exception as e:
        print(f"error: {e}")

def main():
    original_domains_file = "domains.txt"
    results_file = "results.txt"
    output_file = "remaining_domains.txt"
    
    if not os.path.exists(original_domains_file):
        print(f"error when find {original_domains_file}")
        return
    
    if not os.path.exists(results_file):
        print(f"cant find {results_file}")
        return
    
    original_size = os.path.getsize(original_domains_file) / (1024**3)  # GB
    results_size = os.path.getsize(results_file) / (1024**3)  # GB
    
    print(f"original file: {original_domains_file} ({original_size:.2f} GB)")
    print(f"result file: {results_file} ({results_size:.2f} GB)")
    print(f"output file: {output_file}")
    print()
    
    response = input("start? (y/N): ").strip().lower()
    if response != 'y':
        print("stopped")
        return
    
    print()
    
    processed_domains = extract_processed_domains(results_file)
    
    if not processed_domains:
        print("cant find and domains")
        return
    
    print()
    
    filter_domains(original_domains_file, processed_domains, output_file)
    
    print()
    print(f"now you can use {output_file} to run massdns")

if __name__ == "__main__":
    main()