import csv
import json
import io


def gr_import_parser(file_content):
    json_file_path = "data.json"
    data = []

    # Use io.StringIO to treat the string like a file
    # This avoids having to save the file to the hard drive
    stream = io.StringIO(file_content)
    csv_reader = csv.DictReader(stream)

    for row in csv_reader:
        data.append(row)

    # Write to JSON (optional, if you need a physical copy)
    with open(json_file_path, "w", encoding="utf-8") as jsonf:
        json.dump(data, jsonf, indent=4)

    # Return the data so your route can use it
    return data
