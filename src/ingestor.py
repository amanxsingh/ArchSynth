"""
ArchSynth Ingestor - Stage 1: Clone and checkout target ROS2 repository.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

try:
    import git
    from git import Repo
except ImportError:
    git = None
    Repo = None

logger = logging.getLogger(__name__)


@dataclass
class RepoInfo:
    """Information about the cloned repository"""
    path: Path
    url: str
    commit_hash: str
    commit_date: str
    branch: str
    is_shallow: bool = False


# Pinned commits for case study repos (update as needed)
CASE_STUDY_COMMITS = {
    "nav2": "6dbf4549",  # Latest as of 2026-08-14
    "nav2_latest": "main",  # Use latest main branch
}


def get_pinned_commit(repo_name: str) -> str:
    """Get pinned commit for a case study repo"""
    return CASE_STUDY_COMMITS.get(repo_name, "main")


class Ingestor:
    """
    Handles cloning and checking out ROS2 repositories at specific commits.
    """

    def __init__(
        self,
        base_dir: str = "case_studies",
        shallow: bool = True,
        depth: int = 1
    ):
        self.base_dir = Path(base_dir).resolve()
        self.shallow = shallow
        self.depth = depth
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def clone_repo(
        self,
        repo_url: str,
        repo_name: Optional[str] = None,
        commit_hash: Optional[str] = None,
        branch: Optional[str] = None,
        force: bool = False
    ) -> RepoInfo:
        """
        Clone a repository and checkout specific commit.

        Args:
            repo_url: Git repository URL
            repo_name: Local directory name (defaults to repo name from URL)
            commit_hash: Specific commit to checkout (defaults to pinned commit)
            branch: Branch to clone (if not checking out specific commit)
            force: Re-clone if directory exists

        Returns:
            RepoInfo with repository details
        """
        if repo_name is None:
            repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')

        repo_path = self.base_dir / repo_name

        # Remove existing if force
        if force and repo_path.exists():
            logger.info(f"Removing existing directory: {repo_path}")
            import shutil
            shutil.rmtree(repo_path)

        # Determine commit to use
        if commit_hash is None:
            commit_hash = get_pinned_commit(repo_name)

        logger.info(f"Cloning {repo_url} into {repo_path}")

        try:
            if repo_path.exists() and (repo_path / ".git").exists():
                # Repository exists, fetch and checkout
                logger.info(f"Repository exists, fetching updates...")
                repo = Repo(repo_path)
                repo.remotes.origin.fetch()

                if commit_hash != "main" and commit_hash != "master":
                    logger.info(f"Checking out commit {commit_hash}")
                    repo.git.checkout(commit_hash)
                elif branch:
                    logger.info(f"Checking out branch {branch}")
                    repo.git.checkout(branch)
            else:
                # Fresh clone
                clone_kwargs = {
                    "depth": self.depth if self.shallow else None,
                    "branch": branch if branch and commit_hash in ("main", "master") else None
                }
                # Remove None values
                clone_kwargs = {k: v for k, v in clone_kwargs.items() if v is not None}

                repo = Repo.clone_from(repo_url, repo_path, **clone_kwargs)

                if commit_hash not in ("main", "master", None):
                    # For shallow clones, we need to fetch the specific commit
                    if self.shallow:
                        logger.info(f"Fetching commit {commit_hash}...")
                        repo.git.fetch("origin", commit_hash, depth=1)
                    logger.info(f"Checking out commit {commit_hash}")
                    repo.git.checkout(commit_hash)

            # Get commit info
            commit = repo.head.commit
            commit_hash = commit.hexsha
            commit_date = commit.committed_datetime.isoformat()
            active_branch = repo.active_branch.name if not repo.head.is_detached else "HEAD (detached)"

            repo_info = RepoInfo(
                path=repo_path,
                url=repo_url,
                commit_hash=commit_hash,
                commit_date=commit_date,
                branch=active_branch,
                is_shallow=self.shallow
            )

            logger.info(f"Successfully cloned {repo_name} at {commit_hash[:8]}")
            return repo_info

        except git.GitCommandError as e:
            logger.error(f"Git error: {e}")
            raise RuntimeError(f"Failed to clone/checkout repository: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def clone_nav2(
        self,
        commit_hash: Optional[str] = None,
        force: bool = False
    ) -> RepoInfo:
        """Convenience method to clone Navigation2"""
        return self.clone_repo(
            repo_url="https://github.com/ros-planning/navigation2.git",
            repo_name="nav2",
            commit_hash=commit_hash,
            force=force
        )

    def get_repo_structure(self, repo_path: Path) -> Dict[str, Any]:
        """
        Get basic repository structure - packages, launch files, etc.
        """
        structure = {
            "packages": [],
            "launch_files": [],
            "python_files": [],
            "cpp_files": [],
            "launch_dirs": []
        }

        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            rel_root = Path(root).relative_to(repo_path)

            for file in files:
                file_path = rel_root / file
                if file.endswith('.py'):
                    structure["python_files"].append(str(file_path))
                elif file.endswith(('.cpp', '.hpp', '.h', '.cc')):
                    structure["cpp_files"].append(str(file_path))
                elif file.endswith(('.launch.py', '.launch.xml', '.launch.yaml')):
                    structure["launch_files"].append(str(file_path))
                    # Track launch directories
                    launch_dir = str(rel_root)
                    if launch_dir not in structure["launch_dirs"]:
                        structure["launch_dirs"].append(launch_dir)

            # Check for package.xml to identify ROS2 packages
            if 'package.xml' in files:
                pkg_name = rel_root.name
                if pkg_name not in structure["packages"]:
                    structure["packages"].append(pkg_name)

        return structure

    def find_ros2_packages(self, repo_path: Path) -> Dict[str, Path]:
        """
        Find all ROS2 packages in the repository (directories with package.xml)
        Returns mapping of package_name -> package_path
        """
        packages = {}

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            if 'package.xml' in files:
                pkg_path = Path(root)
                pkg_name = pkg_path.name
                packages[pkg_name] = pkg_path.relative_to(repo_path)

        return packages


def ingest_repository(
    repo_url: str,
    repo_name: Optional[str] = None,
    commit_hash: Optional[str] = None,
    base_dir: str = "case_studies",
    shallow: bool = True
) -> RepoInfo:
    """
    Convenience function to ingest a repository.

    Usage:
        repo_info = ingest_repository("https://github.com/ros-planning/navigation2.git")
    """
    ingestor = Ingestor(base_dir=base_dir, shallow=shallow)
    return ingestor.clone_repo(repo_url, repo_name, commit_hash)


if __name__ == "__main__":
    # Test the ingestor
    logging.basicConfig(level=logging.INFO)

    ingestor = Ingestor(base_dir="case_studies")
    repo_info = ingestor.clone_nav2()

    print(f"Cloned: {repo_info.path}")
    print(f"Commit: {repo_info.commit_hash}")
    print(f"Date: {repo_info.commit_date}")

    structure = ingestor.get_repo_structure(repo_info.path)
    print(f"\nRepository structure:")
    print(f"  Packages: {len(structure['packages'])}")
    print(f"  Python files: {len(structure['python_files'])}")
    print(f"  C++ files: {len(structure['cpp_files'])}")
    print(f"  Launch files: {len(structure['launch_files'])}")
    print(f"  Launch dirs: {structure['launch_dirs'][:5]}...")