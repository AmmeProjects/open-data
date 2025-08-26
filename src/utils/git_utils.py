import subprocess
import sys
import os

def run(cmd):
    if isinstance(cmd, str):
        cmd = cmd.split()
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(result.stdout.decode())
    if result.returncode != 0:
        print(result.stderr.decode(), file=sys.stderr)
    return result.returncode

def setup_git():
    run(["git", "config", "--global", "user.name", "github-actions[bot]"])
    run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])

def checkout_weekly_branch(branch_name, repo_url):
    exists = run(["git", "ls-remote", "--exit-code", "--heads", "origin", branch_name]) == 0
    if exists:
        run(["git", "fetch", "origin", f"{branch_name}:{branch_name}"])
        run(["git", "checkout", branch_name])
    else:
        run(["git", "checkout", "-b", branch_name])
    run(["git", "remote", "set-url", "origin", repo_url])

def commit_and_push(file_path, branch_name, repo_url, message):
    setup_git()
    checkout_weekly_branch(branch_name, repo_url)
    run(["git", "add", file_path])
    run(["git", "commit", "-m", message])
    run(["git", "push", "origin", f"HEAD:{branch_name}"])

if __name__ == "__main__":
    # Usage: python git_utils.py <file_path> <branch_name> <repo_url> <commit_message>
    if len(sys.argv) != 5:
        print("Usage: python git_utils.py <file_path> <branch_name> <repo_url> <commit_message>")
        sys.exit(1)
    file_path = sys.argv[1]
    branch_name = sys.argv[2]
    repo_url = sys.argv[3]
    commit_message = sys.argv[4]
    commit_and_push(file_path, branch_name, repo_url, commit_message)
