from __future__ import annotations

import os
import subprocess
import sys
from argparse import ArgumentParser

from sweagent.investigations.instance_data import get_swe_bench_instance_markdown
from sweagent.investigations.run_logs import (
    download_instance_eval_test_output,
    download_instance_patch,
    download_instance_prediction_log,
    download_instance_prediction_trajectory_json,
    get_instance_eval_folder_href,
)

investigation_data_folder_name = "investigation-data"


def get_absolute_path(relative_path: str) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, relative_path)


def get_investigation_data_folder() -> str:
    return get_absolute_path(investigation_data_folder_name)


def get_investigation_data_path(instance_id: str) -> str:
    return os.path.join(get_investigation_data_folder(), f"{instance_id}.md")


##########################################################################################
# SWE-bench data utilities
##########################################################################################


def parse_instance_id(instance_id: str) -> tuple[str, int]:
    parts = instance_id.rsplit("-", 1)
    repo_path = parts[0].replace("__", "/")  # Replace double underscore with slash
    pr_number = int(parts[1])
    return repo_path, pr_number


def make_bug_href(instance_id: str) -> str:
    [repo_path, pr_number] = parse_instance_id(instance_id)
    return f"https://github.com/{repo_path}/pull/{str(pr_number)}"


# NOTE: Markdown requires relative paths.
def make_relative_path(fpath: str):
    return os.path.relpath(fpath, get_investigation_data_folder())

def summarize_instance(instance_id: str):
    print(f"Summarizing Instance {instance_id}...")
    prediction_logs = download_instance_prediction_log(instance_id)
    prediction_trajectories = download_instance_prediction_trajectory_json(instance_id)
    result_patches = download_instance_patch(instance_id)
    eval_folder_href = get_instance_eval_folder_href(instance_id)
    eval_test_output = download_instance_eval_test_output(instance_id)

    summary_fpath = get_investigation_data_path(instance_id)
    with open(summary_fpath, "w", encoding="utf-8") as f:
        contents = f"""
# {instance_id}
## Links

* [PR Link]({make_bug_href(instance_id)})
* Prediction
  * Run Logs: {", ".join([f"[Run Log]({make_relative_path(fpath)})" for fpath in prediction_logs])}
  * Traj Json: {", ".join([f"[Traj]({make_relative_path(fpath)})" for fpath in prediction_trajectories])}
  * {", ".join([f"[Patch]({make_relative_path(fpath)})" for fpath in result_patches])}
* Evaluation
  * {f"[Evaluation Results Folder]({eval_folder_href})" if eval_folder_href else "(no evaluation found)"}
  * Eval Log: {", ".join([f"[Eval Log]({make_relative_path(fpath)})" for fpath in eval_test_output])}

## Bug Data

{get_swe_bench_instance_markdown(instance_id)}

""".strip()
        f.write(contents)
    print(f"  Done: {summary_fpath}")


def run_in_shell(command: str):
    p = subprocess.Popen(
        command,
        shell=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    p.wait()
    return p


def main():
    parser = ArgumentParser(description="Summarize SWE-bench instances")
    parser.add_argument("instance_ids", nargs="+", help="instance_ids from the dataset")
    parser.add_argument(
        "-o",
        "--open-repo",
        action="store_true",
        help="Whether to open the repo of the given instances (default: %(default)s)",
    )

    args = parser.parse_args()
    open_repo: bool = args.open_repo

    os.makedirs(get_investigation_data_folder(), exist_ok=True)
    for i, instance_id in enumerate(args.instance_ids, 1):
        print(f"Summarizing {i}/{len(args.instance_ids)}: {instance_id}")
        summarize_instance(instance_id)

    if open_repo:
        print("Opening repo(s)...")
        open_repo_sh = os.path.join(os.path.join(os.path.dirname(__file__), "../../open_repo.sh"))
        for instance_id in args.instance_ids:
            run_in_shell(f"{open_repo_sh} {instance_id}")


if __name__ == "__main__":
    main()