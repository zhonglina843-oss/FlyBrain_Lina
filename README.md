# FlyBrain 实验起步包

这个目录用于回答一个可检验的问题：真实果蝇连接组能提供多少现成的计算结构，哪些能力仍需要人为动力学、参数拟合或在线可塑性？

## 先说结论

- `connectome` 是结构先验，不是可直接运行的完整大脑模型。
- Dorkenwald et al. (2024) 的对象是雌蝇全脑 `FlyWire FAFB`，推荐通过 FlyWire Codex/CAVE 访问。
- `neuPrint` 是另一套查询平台，适合先用 `hemibrain:v1.2.1` 熟悉连通组查询，也可能承载 Janelia 的其他数据集；实际可用数据集应登录后动态查询，不能凭名字假定。
- Card & Dickinson (2008) 给的是行为学约束：果蝇会依据威胁方向和起始姿态，在起跳前约 200 ms 调整姿态。它不是连接组论文，也没有给出可直接加载的网络权重。

## 目录

```text
FlyBrain/
├── README.md
├── requirements.txt
├── .env.example
├── docs/
│   ├── experiment_plan.md
│   └── research_notes.md
├── references/
│   ├── citations.bib
│   ├── sources.md
│   └── FlyBrain_果蝇大脑是否无需训练就能推理.pdf
├── scripts/
│   └── neuprint_explore.py
├── data/
│   ├── raw/README.md
│   └── processed/README.md
└── outputs/README.md
```

## 5 分钟开始

需要 Python 3.10 或更高版本。

```bash
cd FlyBrain
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

登录 [neuPrint](https://neuprint.janelia.org)，在 Account 页面复制 token，然后把它填入 `.env`。不要提交 `.env`。

```bash
# 查看服务器当前真正开放的数据集
python scripts/neuprint_explore.py datasets

# 搜索神经元类型。先用 hemibrain 验证工具链
python scripts/neuprint_explore.py search 'LC4.*' --limit 20

# 查看一个 bodyId 的强上游或下游连接
python scripts/neuprint_explore.py partners 5813027016 --direction downstream --min-weight 10
```

命令默认使用 `hemibrain:v1.2.1`。选择其他数据集时，修改 `.env` 中的 `NEUPRINT_DATASET` 或传入 `--dataset`。不同数据集的细胞类型命名、覆盖范围和 body ID 不可混用。

## 建议推进顺序

1. 跑通 `datasets`、`search`、`partners`，保存一份小规模连接表。
2. 在选定数据集中核对 looming/escape 相关细胞类型，不先假定 `LC4`、`LPLC2`、`DNp01` 在每个数据集都有相同名称。
3. 建立“视觉输入 -> 候选中间回路 -> 下降神经元”的子图，并做随机重连对照。
4. 再加入简单神经动力学，比较固定参数、少量 gain 拟合和局部可塑性三种条件。
5. 最后才接行为环境；评价指标必须包含方向误差、反应延迟、成功率和对起始姿态的条件依赖。

详细假设、对照组和交付物见 [docs/experiment_plan.md](docs/experiment_plan.md)。资料入口及数据许可见 [references/sources.md](references/sources.md)。

面向组内汇报的演示定义见 [docs/demo_spec.md](docs/demo_spec.md)，服务器部署和 Git 协作方式见 [docs/server_setup.md](docs/server_setup.md)。

三个第三方开源实现已作为固定版本的 Git submodule 放入 `external/`。完整架构流程图、启动顺序、风险边界和微调位置见 [docs/open_source_projects.md](docs/open_source_projects.md)。首次克隆本仓库请使用：

```bash
git clone --recurse-submodules https://github.com/zhonglina843-oss/FlyBrain_Lina.git
```

已有克隆使用：

```bash
git submodule update --init --recursive
```

## 与 CTM 项目的连接点

值得比较的不是“谁更像大脑”，而是时间尺度与可训练自由度：固定拓扑、快速状态变化、少量 gain、局部可塑性分别贡献多少性能。这样才能把 FlyBrain 变成 CTM 的可证伪对照，而不是演示性质的类比。
