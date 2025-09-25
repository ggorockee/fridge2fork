
import os
import sys
import tempfile
import shutil
from git import Repo, exc
from ruamel.yaml import YAML

def update_yaml_file(repo_url, token, image_tag, service_type="onedaypillo", branches_to_try=None):
    """
    Clones a git repository from a list of possible branches, updates a YAML file,
    and pushes the changes back to the repository.
    
    Args:
        repo_url: Git repository URL
        token: GitHub token for authentication
        image_tag: Docker image tag to update
        service_type: Service type ('onedaypillo' or 'scraper')
        branches_to_try: List of branches to try cloning
    """
    if branches_to_try is None:
        branches_to_try = ["develop", "dev"]

    temp_dir = tempfile.mkdtemp()
    try:
        authenticated_repo_url = repo_url.replace("https://", f"https://oauth2:{token}@")
        
        repo = None
        cloned_branch = None
        for branch in branches_to_try:
            try:
                print(f"Attempting to clone branch: {branch}...")
                # Clean up temp_dir before a new clone attempt to avoid conflicts
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)

                repo = Repo.clone_from(authenticated_repo_url, temp_dir, branch=branch)
                cloned_branch = branch
                print(f"Successfully cloned branch: {cloned_branch}")
                break  # Exit loop on success
            except exc.GitCommandError as e:
                if "branch not found" in e.stderr.lower() or "couldn't find remote ref" in e.stderr.lower() or "not found in upstream" in e.stderr.lower():
                    print(f"Branch '{branch}' not found. Trying next...")
                else:
                    raise e
        
        if repo is None:
            print(f"Error: Could not find any of the specified branches: {branches_to_try}")
            sys.exit(1)

        # Configure git user
        repo.config_writer().set_value("user", "name", "Gemini CI").release()
        repo.config_writer().set_value("user", "email", "gemini-ci@example.com").release()

        # Determine file path and field based on service type
        if service_type == "scraper":
            yaml_file_path = os.path.join(temp_dir, "charts/helm/fridge2fork/values.yaml")
            field_path = ["scrape", "image", "tag"]
        else:  # onedaypillo (default)
            yaml_file_path = os.path.join(temp_dir, "charts/argocd/applicationsets/valuefiles/dev/onedaypillo/values.yaml")
            field_path = ["image", "tag"]

        if not os.path.exists(yaml_file_path):
            print(f"Error: File not found at {yaml_file_path}")
            return

        # Update the YAML file
        yaml = YAML()
        yaml.preserve_quotes = True
        with open(yaml_file_path, 'r') as f:
            data = yaml.load(f)

        print(f"Updating {service_type} image tag to: {image_tag}")
        
        # Navigate to the correct field and update it
        current_data = data
        for key in field_path[:-1]:
            if key not in current_data:
                current_data[key] = {}
            current_data = current_data[key]
        
        current_data[field_path[-1]] = image_tag

        with open(yaml_file_path, 'w') as f:
            yaml.dump(data, f)
        print("YAML file updated successfully.")

        # Commit and push the changes
        if repo.is_dirty(untracked_files=True):
            print("Committing changes...")
            repo.git.add(A=True)
            commit_message = f"ci: Update image tag to {image_tag} for {service_type}"
            repo.index.commit(commit_message)
            
            print("Pushing changes...")
            origin = repo.remote(name="origin")
            origin.push()
            print("Changes pushed successfully.")
        else:
            print("No changes to commit.")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1) # Exit with a non-zero status code to indicate failure
    finally:
        # Clean up the temporary directory
        print(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python update_infra_values.py <IMAGE_TAG> <INFRA_GITHUB_TOKEN> [SERVICE_TYPE]")
        print("SERVICE_TYPE: 'onedaypillo' (default) or 'scraper'")
        sys.exit(1)

    image_tag_arg = sys.argv[1]
    infra_token_arg = sys.argv[2]
    service_type_arg = sys.argv[3] if len(sys.argv) == 4 else "onedaypillo"
    
    infra_repo_url = "https://github.com/ggorockee/infra.git"

    update_yaml_file(infra_repo_url, infra_token_arg, image_tag_arg, service_type_arg)
