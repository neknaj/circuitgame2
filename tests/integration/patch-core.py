from pathlib import Path
import json
import subprocess
import sys

CORE_URL = "https://github.com/neknaj/circuitgame2-core"
CORE_PACKAGE = "circuitgame2-core"


def cargo_metadata(directory, *args):
    result = subprocess.run(
        ["cargo", *args],
        cwd=directory,
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def main(core, config, *consumers):
    candidate = cargo_metadata(core, "metadata", "--no-deps", "--format-version", "1")
    manifests = {
        package["name"]: Path(package["manifest_path"]).resolve()
        for package in candidate["packages"]
        if package["id"] in candidate["workspace_members"]
    }
    if CORE_PACKAGE not in manifests:
        raise SystemExit(f"{core} に {CORE_PACKAGE} がない")

    patch = [f'[patch."{CORE_URL}"]']
    for name, manifest in sorted(manifests.items()):
        directory = json.dumps(manifest.parent.as_posix(), ensure_ascii=False)
        patch.append(f"{name} = {{ path = {directory} }}")
    config.write_text("\n".join(patch) + "\n", encoding="utf-8")

    # 候補への切り替えで lockfile を更新し、通常ビルドで解決結果を固定する。
    for consumer in consumers:
        metadata = cargo_metadata(
            consumer, "--config", str(config), "metadata", "--format-version", "1"
        )
        selected_core = []
        for package in metadata["packages"]:
            name = package["name"]
            source = package["source"] or ""
            if name == CORE_PACKAGE:
                selected_core.append(Path(package["manifest_path"]).resolve())
            if source.startswith(f"git+{CORE_URL}"):
                raise SystemExit(f"{consumer} に固定版 {name} が残っている: {source}")
        if selected_core != [manifests[CORE_PACKAGE]]:
            raise SystemExit(f"{consumer} が候補の {CORE_PACKAGE} を使っていない")
        print(f"{consumer}: {selected_core[0]}")


if __name__ == "__main__":
    main(*(Path(arg).resolve() for arg in sys.argv[1:]))
