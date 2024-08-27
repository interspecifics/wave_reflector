import os

def drop_last_character_of_each_line(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                lines = file.readlines()
            
            with open(file_path, 'w') as file:
                # Change the column names
                if lines:
                    lines[0] = "AF3,T7,Pz,T8,AF4\n"
            
                for line in lines[1:]:  # Skip the header line
                    # Drop the last character of each line
                    new_line = line[:-2] + '\n'
                    file.write(new_line)
                print(f"Processed {filename}")

# Replace 'records_RAW' with the actual path to your directory
drop_last_character_of_each_line('records_RAW')
