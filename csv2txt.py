input_file = "input.csv"
output_file = "domains.txt"

with open(input_file, "r", encoding="utf-8") as csv_file, \
     open(output_file, "w", encoding="utf-8") as txt_file:

    for line in csv_file:
        parts = line.strip().split(",")
        if len(parts) == 2:
            txt_file.write(parts[1] + "\n")