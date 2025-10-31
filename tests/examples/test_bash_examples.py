import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "examples" / "bash"


@pytest.mark.parametrize(
    "script,args,stdin,env_overrides,expect_substring",
    [
        (
            "prompt-loop.sh",
            [],
            "hello\n:quit\n",
            {},
            "[dry-run] cllm",
        ),
        (
            "git-diff-review.sh",
            [],
            "",
            {},
            "No changes detected",
        ),
        (
            "cron-digest.sh",
            ["--dry-run"],
            "",
            {
                "CLLM_DIGEST_SOURCE_CMD": 'printf "Update one\\n"',
            },
            "[dry-run] cllm",
        ),
        (
            "templated-context.sh",
            ["README.md"],
            "",
            {},
            "[dry-run] cllm",
        ),
    ],
)
def test_bash_scripts_support_dry_run(
    script, args, stdin, env_overrides, expect_substring
):
    script_path = SCRIPTS_DIR / script
    assert script_path.exists(), f"Missing script: {script}"

    env = os.environ.copy()
    env.update(env_overrides)
    env["CLLM_EXAMPLE_DRY_RUN"] = "1"

    proc = subprocess.run(
        ["bash", str(script_path), *args],
        input=stdin,
        text=True,
        capture_output=True,
        env=env,
        cwd=REPO_ROOT,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    if expect_substring:
        combined = proc.stdout + proc.stderr
        assert expect_substring in combined
