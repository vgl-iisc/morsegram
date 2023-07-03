#!/bin/bash

# Check if the correct number of command-line arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 input_folder new_folder"
    exit 1
fi

# Get the input folder and new folder names from the command-line arguments
input_folder="$1"
new_folder="$2"

# Create the new folder if it doesn't exist
mkdir -p "$new_folder"

# Loop through each file in the input folder and rename it
count=1
for file in "$input_folder"/*; do
    # Get the file extension
    extension="${file##*.}"

    # Rename the file and move it to the new folder
    new_filename="$new_folder/$count.$extension"
    cp "$file" "$new_filename"

    # Increment the count
    count=$((count+1))
done
