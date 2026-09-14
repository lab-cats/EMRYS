"""Record build provenance using the existing setuptools metadata command."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

from setuptools import setup
from setuptools.command.egg_info import egg_info


class BuildMetadata(egg_info):
    def run(self):
        root = Path(__file__).resolve().parent
        environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        provenance = {"git_commit": None, "git_dirty": None}
        try:

            def git(*arguments):
                return subprocess.check_output(
                    ["git", *arguments],
                    cwd=root,
                    env=environment,
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()

            if Path(git("rev-parse", "--show-toplevel")).resolve() == root:
                provenance.update(
                    git_commit=git("rev-parse", "HEAD"),
                    git_dirty=bool(
                        git("status", "--porcelain", "--untracked-files=all")
                    ),
                )
        except (OSError, subprocess.CalledProcessError):
            pass
        lock = root / "uv.lock"
        if lock.is_file():
            provenance["python_lock_sha256"] = hashlib.sha256(
                lock.read_bytes()
            ).hexdigest()
        else:
            previous = root / "src/emrys_rna_workflow.egg-info/emrys-build.json"
            provenance = json.loads(previous.read_text())
        self.mkpath(self.egg_info)
        self.write_file(
            "build provenance",
            str(Path(self.egg_info) / "emrys-build.json"),
            json.dumps(provenance, sort_keys=True) + "\n",
        )
        super().run()


setup(cmdclass={"egg_info": BuildMetadata})
