import glob
import os


def merge_datas(data_path="domains/data/", output_filename="domains.txt"):
    """
    Merges all .txt files found in the specified directory patterns within the given data_path:
    - data_path/*/*.txt
    - data_path/*.txt
    - data_path/*/*/txt

    Args:
        data_path: The root directory to search for .txt files.
        output_filename: The name of the file to write the merged content to.
    """

    # Create a list of file paths matching the patterns, using the provided data_path
    file_patterns = [
        os.path.join(data_path, "*/*.txt"),  # data_path/*/*.txt
        os.path.join(data_path, "*.txt"),  # data_path/*.txt
        os.path.join(data_path, "*/*/*.txt"),  # data_path/*/*/*.txt
    ]
    file_paths = []
    for pattern in file_patterns:
        file_paths.extend(glob.glob(pattern))

    # Check if any files were found
    if not file_paths:
        print(f"No .txt files found in '{data_path}' matching the specified patterns.")
        return

    # Merge the contents of the files
    with open(output_filename, "w", encoding="utf-8") as outfile:
        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
                    outfile.write(
                        "\n"
                    )  # Add a newline to separate content from different files
                print(f"Merged: {file_path}")
            except UnicodeDecodeError:
                print(f"Skipped file (likely binary): {file_path}")
            except FileNotFoundError:
                print(f"File not found: {file_path}")

    print(f"Successfully merged files into: {output_filename}")


if __name__ == "__main__":
    merge_datas()
