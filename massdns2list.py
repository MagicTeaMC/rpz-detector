def filter_domains_from_file(filepath, output_filepath):
    filtered_domains = set()
    try:
        with open(filepath, "r") as f:
            for line in f:
                if "182.173.0.181" in line or "34.102.218.71" in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        domain = parts[0].rstrip(".")
                        filtered_domains.add(domain)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return
    
    try:
        with open(output_filepath, "a") as outfile:
            for domain in sorted(filtered_domains):
                outfile.write(domain + "\n")
    except Exception as e:
        print(f"Error writing to output file: {e}")

# config
filepath = "results.txt"
output_filepath = "rpz-block-list.txt"
filter_domains_from_file(filepath, output_filepath)
