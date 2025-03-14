import pysvn
import subprocess
import sys
import os
#def ssl_server_trust_prompt( trust_dict ):
#    return retcode, accepted_failures, save
svncodedir = "C:/Users/hqin/UniqueIDserver/code/"
IDfilesdir = "C:/Users/hqin/UniqueIDserver/branch_ID_files/"


def ssl_server_trust_prompt(trust_dict):
    #Trusts the SVN server automatically.
    return True, trust_dict["failures"], True

def login(*args):
    #Retrieves SVN login credentials from command-line arguments.
    return True, sys.argv[1], sys.argv[2], True

def svn_checkout(client, branch_name, target_path):
    #Checks out the SVN repository based on the branch name.
    svn_base_url = 'https://hdidsvn.hds.com/svn/cofio/AIMstor/'
    
    repo_url = f"{svn_base_url}trunk" if branch_name == "mainline" else f"{svn_base_url}branches/{branch_name}"
    
    print(f"Checking out SVN repository: {repo_url} to {target_path}")
    client.checkout(repo_url, target_path)

def svn_update(client, branch_name):
    #Updates the SVN repository.
    repo_path = os.path.join(svncodedir, branch_name)
    print(f"Updating SVN repository at: {repo_path}")
    return client.update(repo_path)

def save_revision(revision, branch_name):
    #Saves the latest SVN revision number to a file.
    version_file_dir = os.path.join(IDfilesdir, branch_name)

    if not os.path.exists(version_file_dir):
        os.makedirs(version_file_dir)

    revision_number = str(revision[0]).split(" ")[-1][:-1]  # Extracting the actual revision number

    revision_file_path = os.path.join(version_file_dir, "revision.txt")
    with open(revision_file_path, "w") as file:
        file.write(revision_number)

    print(f"Saved SVN revision: {revision_number} to {revision_file_path}")

def main():
    #Main function to handle SVN operations and file management.
    if len(sys.argv) < 5:
        print("Usage: script.py <username> <password> <branch> <target_path>")
        sys.exit(1)

    username, password, branch_name, target_path = sys.argv[1:5]

    print("\n=== SVN Checkout and Update Script ===")
    print(f"Username: {username}")
    print(f"Branch: {branch_name}")
    print(f"Target Path: {target_path}\n")

    # Configure SVN client
    client = pysvn.Client()
    client.callback_get_login = login
    client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt

    try:
        # Checkout repository
        svn_checkout(client, branch_name, target_path)

        # Update repository
        rev = svn_update(client, branch_name)

        # Save revision number
        save_revision(rev, branch_name)

    except pysvn.ClientError as e:
        print(f"SVN operation failed: {e}")
        sys.exit(1)

    print("\n=== SVN Operation Completed Successfully ===")

if __name__ == "__main__":
    main()


