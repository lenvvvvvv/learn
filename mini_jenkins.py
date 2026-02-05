#!/usr/bin/env python3
"""一个轻量级、类 Jenkins 的 CI/CD 工具（单文件版）。

特性：
1. 读取 YAML 流水线配置，按 stage/step 顺序执行。
2. 失败即停止（可选 continue_on_error）。
3. 记录构建历史（JSONL）。
4. 可作为 daemon 按间隔轮询 Git HEAD 变化触发构建。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import shlex
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


@dataclass
class StepResult:
    name: str
    command: str
    exit_code: int
    duration_sec: float
    stdout: str
    stderr: str


@dataclass
class StageResult:
    name: str
    status: str
    duration_sec: float
    steps: list[StepResult] = field(default_factory=list)


@dataclass
class BuildResult:
    build_id: str
    pipeline_name: str
    started_at: str
    finished_at: str
    status: str
    trigger: str
    branch: str
    stages: list[StageResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "build_id": self.build_id,
            "pipeline_name": self.pipeline_name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "trigger": self.trigger,
            "branch": self.branch,
            "stages": [
                {
                    "name": s.name,
                    "status": s.status,
                    "duration_sec": round(s.duration_sec, 3),
                    "steps": [
                        {
                            "name": st.name,
                            "command": st.command,
                            "exit_code": st.exit_code,
                            "duration_sec": round(st.duration_sec, 3),
                            "stdout": st.stdout,
                            "stderr": st.stderr,
                        }
                        for st in s.steps
                    ],
                }
                for s in self.stages
            ],
        }


class MiniJenkins:
    def __init__(self, config_path: str) -> None:
        self.config_path = pathlib.Path(config_path)
        self.config = self._load_config()

        pipeline_cfg = self.config.get("pipeline", {})
        self.pipeline_name = pipeline_cfg.get("name", "mini-jenkins-pipeline")
        self.workspace = pathlib.Path(pipeline_cfg.get("workspace", ".")).resolve()
        self.history_file = pathlib.Path(pipeline_cfg.get("history_file", ".mini_jenkins_history.jsonl"))

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        suffix = self.config_path.suffix.lower()
        with self.config_path.open("r", encoding="utf-8") as f:
            raw = f.read()

        if suffix == ".json":
            data = json.loads(raw)
        elif yaml is not None:
            data = yaml.safe_load(raw) or {}
        else:
            raise RuntimeError(
                "当前环境未安装 pyyaml，无法读取 YAML。请改用 JSON 配置或安装: pip install pyyaml"
            )

        if "pipeline" not in data:
            raise ValueError("配置必须包含顶层字段 pipeline")
        return data

    def _run_command(self, command: str, env: dict[str, str] | None = None, timeout: int | None = None) -> StepResult:
        start = time.perf_counter()
        proc_env = os.environ.copy()
        if env:
            proc_env.update({k: str(v) for k, v in env.items()})

        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(self.workspace),
            env=proc_env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.perf_counter() - start

        return StepResult(
            name=command,
            command=command,
            exit_code=proc.returncode,
            duration_sec=duration,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    def _stage_enabled(self, stage: dict[str, Any], branch: str) -> bool:
        when = stage.get("when", {})
        only_branch = when.get("branch")
        if only_branch and only_branch != branch:
            return False
        return True

    def run_pipeline(self, trigger: str = "manual", branch: str = "main") -> BuildResult:
        started = dt.datetime.now(dt.timezone.utc)
        build_id = uuid.uuid4().hex[:10]
        pipeline_cfg = self.config.get("pipeline", {})
        stages_cfg = pipeline_cfg.get("stages", [])

        build = BuildResult(
            build_id=build_id,
            pipeline_name=self.pipeline_name,
            started_at=started.isoformat(),
            finished_at="",
            status="SUCCESS",
            trigger=trigger,
            branch=branch,
            stages=[],
        )

        print(f"\n🚀 Build {build_id} started | pipeline={self.pipeline_name} | branch={branch} | trigger={trigger}")

        for stage_cfg in stages_cfg:
            stage_name = stage_cfg.get("name", "unnamed-stage")
            if not self._stage_enabled(stage_cfg, branch):
                print(f"⏭️  Skip stage: {stage_name} (branch mismatch)")
                continue

            s_start = time.perf_counter()
            stage_result = StageResult(name=stage_name, status="SUCCESS", duration_sec=0.0)
            print(f"\n== Stage: {stage_name} ==")

            for idx, step_cfg in enumerate(stage_cfg.get("steps", []), start=1):
                command = step_cfg.get("run")
                if not command:
                    raise ValueError(f"stage={stage_name} 的 step#{idx} 缺少 run")

                step_name = step_cfg.get("name", f"step-{idx}")
                timeout = step_cfg.get("timeout")
                env = step_cfg.get("env")
                print(f"▶ {step_name}: {shlex.split(command)[0] if command else command}")

                try:
                    step_result = self._run_command(command=command, env=env, timeout=timeout)
                except subprocess.TimeoutExpired as e:
                    step_result = StepResult(
                        name=step_name,
                        command=command,
                        exit_code=124,
                        duration_sec=float(timeout or 0),
                        stdout=e.stdout or "",
                        stderr=(e.stderr or "") + "\n[mini-jenkins] timeout",
                    )

                step_result.name = step_name
                stage_result.steps.append(step_result)

                if step_result.stdout:
                    print(step_result.stdout.rstrip())
                if step_result.stderr:
                    print(step_result.stderr.rstrip(), file=sys.stderr)

                if step_result.exit_code != 0:
                    stage_result.status = "FAILED"
                    print(f"❌ Step failed: {step_name} (exit={step_result.exit_code})")
                    if not bool(step_cfg.get("continue_on_error", False)):
                        break

            stage_result.duration_sec = time.perf_counter() - s_start
            build.stages.append(stage_result)

            if stage_result.status == "FAILED":
                build.status = "FAILED"
                break

        finished = dt.datetime.now(dt.timezone.utc)
        build.finished_at = finished.isoformat()
        print(f"\n🏁 Build {build.build_id} finished with status={build.status}")

        self._append_history(build)
        return build

    def _append_history(self, build: BuildResult) -> None:
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with self.history_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(build.to_dict(), ensure_ascii=False) + "\n")

    def list_history(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.history_file.exists():
            return []
        lines = self.history_file.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(x) for x in lines if x.strip()]
        return rows[-limit:]


def get_git_head(repo: pathlib.Path) -> str:
    try:
        proc = subprocess.run(
            "git rev-parse HEAD",
            cwd=str(repo),
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()
    except Exception:
        return ""


def cmd_run(args: argparse.Namespace) -> int:
    app = MiniJenkins(args.file)
    build = app.run_pipeline(trigger=args.trigger, branch=args.branch)
    return 0 if build.status == "SUCCESS" else 1


def cmd_history(args: argparse.Namespace) -> int:
    app = MiniJenkins(args.file)
    rows = app.list_history(limit=args.limit)
    if not rows:
        print("暂无构建历史")
        return 0
    for r in rows:
        print(f"{r['started_at']} | {r['pipeline_name']} | {r['build_id']} | {r['status']} | {r['trigger']}")
    return 0


def cmd_daemon(args: argparse.Namespace) -> int:
    app = MiniJenkins(args.file)
    repo = app.workspace

    print(f"🤖 daemon started. repo={repo}, interval={args.interval}s, branch={args.branch}")
    last_head = None
    while True:
        current_head = get_git_head(repo)
        if current_head and current_head != last_head:
            if last_head is None:
                print(f"初始化 HEAD={current_head[:8]}，不触发构建")
            else:
                print(f"检测到提交变更: {last_head[:8]} -> {current_head[:8]}")
                app.run_pipeline(trigger="scm", branch=args.branch)
            last_head = current_head
        time.sleep(args.interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mini Jenkins-like CI/CD tool (Python)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="立即执行一次流水线")
    p_run.add_argument("-f", "--file", default="pipeline.yml", help="pipeline 配置文件")
    p_run.add_argument("--branch", default="main", help="当前分支名，用于 stage when 条件")
    p_run.add_argument("--trigger", default="manual", help="触发来源: manual/scm/api")
    p_run.set_defaults(func=cmd_run)

    p_daemon = sub.add_parser("daemon", help="以守护模式轮询 Git 提交触发构建")
    p_daemon.add_argument("-f", "--file", default="pipeline.yml", help="pipeline 配置文件")
    p_daemon.add_argument("--branch", default="main", help="分支名")
    p_daemon.add_argument("--interval", type=int, default=10, help="轮询间隔(秒)")
    p_daemon.set_defaults(func=cmd_daemon)

    p_history = sub.add_parser("history", help="查看构建历史")
    p_history.add_argument("-f", "--file", default="pipeline.yml", help="pipeline 配置文件")
    p_history.add_argument("--limit", type=int, default=20, help="最多显示多少条")
    p_history.set_defaults(func=cmd_history)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
