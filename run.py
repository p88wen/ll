import os
import sys

def main():
    files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py')]
    if len(files) == 0:
        print("No .py files found in the directory.")
        sys.exit(1)

    print("Select a Python file to run:")
    for idx, file in enumerate(files):
        print(f"{idx + 1}. {file}")

    selection = input("Enter the number of the file you want to run: ")
    try:
        selected_file = files[int(selection) - 1]
        os.system(f"python {selected_file}")
    except (IndexError, ValueError):
        print("Invalid selection.")

if __name__ == "__main__":
    main()
