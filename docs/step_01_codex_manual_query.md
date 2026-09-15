# 第一步：在官方 Codex 手动追踪一个感觉到输出的候选回路

目标不是证明果蝇一定会逃逸，而是学会官方连接组资源的基本使用，并产出一份任何人都能复查的数据记录。

本步骤选择 looming（逼近物体）候选链：`LC4 / LPLC2 -> DNp01`。这条链常被用于第三方游戏中的逃逸演示。它在这里是**候选回路**，不是由本步骤单独证明的完整行为机制。

## 开始前

1. 浏览器打开 <https://codex.flywire.ai>。
2. 使用自己的 Google 账号登录。Codex 的计算、查询和下载功能要求登录。
3. 选择数据集 `FAFB v783 (CB)`，即成年雌蝇全脑。记录页面显示的数据集名、神经元数、连接数和当天日期。

本数据集没有 VNC，因此本步骤中的 `DNp01` 只作为**脑到神经索的下降输出读出**；不能直接把它解释成完整腿部运动。

## A. 搜索三个候选类型

依次搜索：

```text
LC4
LPLC2
DNp01
```

对每一个搜索结果，打开细胞类型页面或任一个代表性神经元，填写下表。若找不到精确命名，不要自行猜测同义词；先在搜索结果中记录实际名称和注释来源。

| 字段 | LC4 | LPLC2 | DNp01 |
|---|---|---|---|
| Codex 显示名称 |  |  |  |
| 类型内神经元数 |  |  |  |
| representative body/root ID |  |  |  |
| 左/右侧或中线 |  |  |  |
| 主要 neuropil/脑区 |  |  |  |
| 注释来源或置信信息 |  |  |  |
| 页面链接 |  |  |  |

建议截取一张每种类型的 morphology/brain-map 图。截图只作为阅读记录；关键数据必须写入表格。

## B. 检查直接连接

在 Codex 的 connectivity/partners 视图中做四次查询：

```text
LC4   -> DNp01
LPLC2 -> DNp01
DNp01 <- LC4
DNp01 <- LPLC2
```

界面名称可能是 `Connectivity`、`Partners`、`Upstream` 或 `Downstream`，但含义必须保持：箭头左侧是 presynaptic（输出方），右侧是 postsynaptic（输入方）。

记录：

| 查询 | 是否有直接边 | 连接对数 | 突触数/weight | 连接所在脑区 | 截图或页面链接 |
|---|---|---:|---:|---|---|
| LC4 -> DNp01 |  |  |  |  |  |
| LPLC2 -> DNp01 |  |  |  |  |  |

注意：Codex 中的 connection weight 通常是神经元对之间的突触计数或筛选后的计数；它不是已测得的生理突触效能。不能把大 weight 直接写成“强生理连接”。

## C. 看一个具体 neuron pair

从 B 中任选一对有直接连接的 pre/post 神经元，打开这两个神经元的细节页并记录：

```text
pre body/root ID:
post body/root ID:
weight:
ROI/neuropil:
dataset/version:
query date:
```

这是本步骤最小的可复查证据。后续无论是官方 LIF 还是游戏项目，都应从这份具体的“输入候选 -> 输出候选”记录开始，而不是从项目 README 的口头描述开始。

## D. 交付物

完成后，在 `data/processed/` 新建一个小型 Markdown 或 CSV 记录，建议命名为：

```text
codex_looming_candidate_YYYY-MM-DD.md
```

文件头必须包含：

```yaml
dataset: FAFB v783 (CB)
source: https://codex.flywire.ai
query_date: YYYY-MM-DD
purpose: manual candidate-pathway audit
```

以及上面的 A-C 三张表。链接可复查、数据集版本完整，比截图数量更重要。

## 做完后你应当能回答

1. 这三个名称在官方数据里是否存在，且各自包含多少神经元？
2. `LC4/LPLC2` 到 `DNp01` 是不是在所选数据版本中有直接连接？
3. 这些结论是哪个数据集、哪天、哪个页面给出的？
4. 还缺什么，才可以从“候选线路”推到“完整逃逸行为”？

最后一个问题的答案应包括：感觉输入编码、神经动力学参数、VNC/身体、动作读出和行为验证。这些正是第二到第五步要拆开的部分。

