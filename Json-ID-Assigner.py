import json
import os

def assign_ids_to_dialogs(file_name):
    try:
        with open(file_name, 'r') as file:
            raw_data = json.load(file)

        structured_dialogs = []
        for character, dialogs in raw_data.items():
            for index, dialog in enumerate(dialogs, start=1):
                structured_dialogs.append({
                    "character": character,
                    "dialog": dialog,
                    "id": index
                })

        with open(file_name, 'w') as file:
            json.dump(structured_dialogs, file, indent=4)

        print("IDs assigned successfully!")

    except FileNotFoundError:
        print(f"Error: The file '{file_name}' does not exist.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the file.")
    except Exception as e:
        print(f"An error occurred: {e}")

def unassign_ids_from_dialogs(file_name):
    if not os.path.isfile(file_name):
        print(f"Error: The file '{file_name}' does not exist.")
        return

    try:
        with open(file_name, 'r') as file:
            structured_dialogs = json.load(file)

        raw_data = {}
        for entry in structured_dialogs:
            character = entry.get("character", "Unknown")
            dialog = entry.get("dialog", "")
            if character not in raw_data:
                raw_data[character] = []
            raw_data[character].append(dialog)

        backup_name = file_name + ".bak"
        os.rename(file_name, backup_name)
        print(f"Backup created: {backup_name}")

        with open(file_name, 'w') as file:
            json.dump(raw_data, file, indent=4)

        print("IDs unassigned successfully!")

    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the file. Ensure it is valid JSON.")
    except KeyError:
        print("Error: Missing keys in structured dialogs. Ensure the input format is correct.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():

    while True:
        mode = input("Enter mode ('1' to assign IDs, '2' to unassign IDs, 'q' to quit): ").strip()

        if mode == 'q':
            print("Exiting program.")
            break

        file_name = input("Path to dialog JSON: ").strip()

        if mode == '1':
            assign_ids_to_dialogs(file_name)
        elif mode == '2':
            unassign_ids_from_dialogs(file_name)
        else:
            print("Invalid option. Please choose '1' to assign IDs, '2' to unassign IDs, or 'q' to quit.")

if __name__ == "__main__":
    main()
