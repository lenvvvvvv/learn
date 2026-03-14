# Mini Jenkins（Python 版）

这是一个用 Python 实现的轻量级 CI/CD 工具，思路类似 Jenkins：

- 支持 **pipeline / stage / step**。
- 每个 step 执行 shell 命令，失败默认中断流水线。
- 支持按分支条件执行 stage（`when.branch`）。
- 支持 daemon 模式：轮询 Git HEAD 变化自动触发构建。
- 自动记录构建历史到 JSONL 文件。
- 配置支持 YAML（需 `pyyaml`）和 JSON（零额外依赖）。

## 1. 安装依赖（可选）

如果你使用 YAML 配置：

```bash
pip install pyyaml
```

如果你使用 JSON 配置，则无需额外依赖。

## 2. 准备配置

### 方案 A：JSON（推荐，开箱即用）

```bash
cp pipeline.example.json pipeline.json
```

### 方案 B：YAML

```bash
cp pipeline.example.yml pipeline.yml
```

## 3. 手动触发一次构建

JSON 配置：

```bash
python3 mini_jenkins.py run -f pipeline.json --branch main --trigger manual
```

YAML 配置：

```bash
python3 mini_jenkins.py run -f pipeline.yml --branch main --trigger manual
```

## 4. 查看历史

```bash
python3 mini_jenkins.py history -f pipeline.json --limit 10
```

## 5. 启动守护进程（监听 Git 提交）

```bash
python3 mini_jenkins.py daemon -f pipeline.json --branch main --interval 10
```

> daemon 会在检测到仓库 HEAD 变化后触发构建。

## 配置格式

### JSON 示例

```json
{
  "pipeline": {
    "name": "demo-python-cicd",
    "workspace": ".",
    "history_file": ".mini_jenkins_history.jsonl",
    "stages": [
      {
        "name": "install",
        "steps": [
          { "name": "show-python", "run": "python3 --version" }
        ]
      }
    ]
  }
}
```

### step 可选字段

- `name`: 步骤名称
- `run`: shell 命令（必填）
- `timeout`: 超时时间（秒）
- `env`: 传给该 step 的环境变量
- `continue_on_error`: `true` 时失败也继续下一个 step
