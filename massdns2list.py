def filter_domains_from_file(filepath, output_filepath):
  filtered_domains = []
  try:
    with open(filepath, 'r') as f:
      for line in f:
        if "182.173.0.181" in line:
          parts = line.split()
          if len(parts) >= 3:
            domain = parts[0].rstrip(".")
            filtered_domains.append(domain)
  except FileNotFoundError:
    print(f"Error: File not found at {filepath}")
    return

  try:
    with open(output_filepath, 'w') as outfile:
      for domain in filtered_domains:
        outfile.write(domain + "\n")
  except Exception as e:
    print(f"Error writing to output file: {e}")

# config
filepath = "results.txt"
output_filepath = "rpz-block-list.txt"
filter_domains_from_file(filepath, output_filepath)