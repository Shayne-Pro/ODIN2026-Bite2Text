# Bite2Text RadFact-Lite（GLM-5.2）

该目录使用 `radfact_lite` 的 Bite2Text prompts 和计分逻辑，通过智谱 GLM Coding Plan 的 OpenAI-compatible 端点执行 OOF RadFact 评估。

## 安全约束

- API Key 只从 `RADFACT_API_KEY` 环境变量读取；
- 不要把 Key 写入 `.env`、脚本、终端历史或 Git；
- `run_config.json` 和缓存均不包含 Key；
- 已在聊天、日志或其他明文位置出现过的 Key 应尽快轮换。

## 安装

```bash
cd task2_bite2text/radfact_glm_eval
python3.13 -m venv .venv313
source .venv313/bin/activate
python -m pip install -r requirements.txt
```

依赖固定到官方公开仓库 commit：

```text
053f680be1c57225f94d67b198a34aa871b1127d
```

## 配置密钥

在当前终端使用隐藏输入，Key 不会回显：

```bash
read -s RADFACT_API_KEY
export RADFACT_API_KEY
```

完成后清除：

```bash
unset RADFACT_API_KEY
```

## 自检

无密钥数据检查：

```bash
.venv313/bin/python run_radfact_glm.py --dry-run --sample-size 10
```

API 和 JSON 结构化输出探测：

```bash
.venv313/bin/python run_radfact_glm.py --probe --run-dir runs/probe_glm52
```

## 运行

先运行固定的 10 例冒烟测试：

```bash
.venv313/bin/python run_radfact_glm.py \
  --sample-size 10 \
  --seed 20260813 \
  --run-dir runs/v7_glm52_pilot10
```

再运行固定的 100 例试验：

```bash
.venv313/bin/python run_radfact_glm.py \
  --sample-size 100 \
  --seed 20260813 \
  --run-dir runs/v7_glm52_pilot100
```

全量 867 例：

```bash
.venv313/bin/python run_radfact_glm.py --run-dir runs/v7_glm52_full867
```

重复同一命令会跳过已完成病例，并复用 `llm_cache/` 中的解析、过滤和蕴含判断。

## 输出

- `run_config.json`：固定配置与样本 ID；
- `per_sample.jsonl`：病例级 Logical Precision、Recall、F1 及逐事实判断；
- `summary.json`：宏平均汇总；
- `failures.jsonl`：失败病例，可重复运行恢复；
- `llm_cache/`：按完整请求内容寻址的 API 响应缓存。

默认开启 `remove_normal_findings=True`。组织方尚未明确发布该开关的最终调用参数；需要对照官方反馈时，建议同时用 `--keep-normal-findings` 建立另一运行目录进行敏感性分析。

## 与官方分数的关系

该运行使用官方公开 prompts 和计分逻辑，但模型为 `glm-5.2`，只能作为 RadFact 代理指标和错误分析工具。最终官方结果使用 `gpt-5.6-luna`，数值不会完全一致。
