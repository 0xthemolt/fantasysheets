import shutil
import os
import subprocess 

source_dir = r"C:\fantasy_top_analysis\pages"
dest_dir = r"C:\Users\jeff.moltenberry\OneDrive - Slalom\Documents\fantasysheets"

# Copy all files from source to destination
for item in os.listdir(source_dir):
    source_item = os.path.join(source_dir, item)
    dest_item = os.path.join(dest_dir, item)
    
    if os.path.isfile(source_item):
        shutil.copy2(source_item, dest_item)
        print(f"Copied: {item}")
    elif os.path.isdir(source_item):
        if os.path.exists(dest_item):
            shutil.rmtree(dest_item)
        shutil.copytree(source_item, dest_item)
        print(f"Copied directory: {item}")


# Change directory to the GitHub repository
repo_path = "C:\\Users\\jeff.moltenberry\\OneDrive - Slalom\\Documents\\fantasysheets"
os.chdir(repo_path)

# Add these lines after changing the directory
token = "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"
repo_url = f"https://0xthemolt:{token}@github.com/0xthemolt/fantasysheets.git"

# Update the remote URL with the token
subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True)


# Git commands
git_commands = [
    ["git", "add", "."],  # Changed to add all files
    ["git", "commit", "-m", "Update repository files"],  # Updated commit message to be more generic
    ["git", "push", "origin", "main"]
]

# Execute Git commands
for command in git_commands:
    try:
        subprocess.run(command, check=True)
        print(f"Executed: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing {' '.join(command)}: {e}")

print("File committed and pushed to GitHub repository.")