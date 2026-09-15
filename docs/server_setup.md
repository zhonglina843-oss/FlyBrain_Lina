# 服务器与 Git 工作流

## 已确认资源

检查日期：2026-09-15。

- GPU：NVIDIA GeForce RTX 4080 SUPER，约 32 GB 显存；
- 内存：503 GiB；
- 根文件系统：30 GB，不用于保存大型连接组；
- 持久工作目录：`/root/autodl-tmp`；
- Conda：`/root/miniconda3/bin/conda`；
- 服务器入口：`connect.nmb1.seetacloud.com:42524`。

仓库中不保存服务器密码、GitHub token 或 neuPrint token。

## 单一写入源

为避免冲突，当前本地 `FlyBrain` 目录是代码的主要写入源：

```text
本地编辑 -> commit -> GitHub main -> 服务器 pull -> 运行 -> outputs
```

服务器默认不直接修改受版本控制的源文件。需要保留的服务器实验配置或结果摘要先拉回本地审查，再提交到 GitHub。大型数据、模型和逐步日志不进入 Git。

## 服务器目录

```text
/root/autodl-tmp/FlyBrain_Lina/       # Git 仓库
/root/autodl-tmp/FlyBrain_data/       # 大型连接组和缓存
/root/autodl-tmp/FlyBrain_runs/       # 实验运行结果
```

项目中的 `data/raw`、`data/processed` 和 `outputs` 保留小型说明文件；大型文件通过参数指向上述外部目录。

## 环境初始化

首次部署：

```bash
/root/miniconda3/bin/conda create -y -n flybrain python=3.11 pip
/root/miniconda3/bin/conda run -n flybrain python -m pip install -r requirements.txt
```

连接 neuPrint 前，在服务器仓库根目录手动创建 `.env` 并填写 token。`.env` 已被忽略，不会上传。

## 日常同步

本地每个可验证的小阶段提交一次并推送：

```bash
git status
git add <本阶段文件>
git commit -m "描述本阶段可验证结果"
git push origin main
```

服务器在运行前更新：

```bash
cd /root/autodl-tmp/FlyBrain_Lina
git pull --ff-only origin main
/root/miniconda3/bin/conda run -n flybrain python scripts/neuprint_explore.py --help
```

`--ff-only` 会在服务器存在分叉时停止，防止静默覆盖。

## 不应提交的内容

- `.env`、密码、token、SSH 私钥；
- 原始全连接组或大型中间矩阵；
- Conda 环境和缓存；
- 可重新生成的逐步日志；
- 未注明来源和许可证的第三方代码。

