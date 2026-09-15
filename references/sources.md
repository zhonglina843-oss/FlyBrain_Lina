# 资料入口

访问日期：2026-09-15。

## 核心论文

- Dorkenwald et al. (2024), *Neuronal wiring diagram of an adult brain*, Nature. DOI: https://doi.org/10.1038/s41586-024-07558-y
- Card & Dickinson (2008), *Visually mediated motor planning in the escape response of Drosophila*, Current Biology. DOI: https://doi.org/10.1016/j.cub.2008.07.094

## 数据和官方工具

- FlyWire Codex: https://codex.flywire.ai/
- FlyWire 数据下载: https://codex.flywire.ai/api/download
- FlyConnectome 教程: https://github.com/flyconnectome
- neuPrint: https://neuprint.janelia.org/
- neuprint-python: https://github.com/connectome-neuprint/neuprint-python
- neuprint-python 文档: https://connectome-neuprint.github.io/neuprint-python/docs/
- Janelia MaleCNS: https://male-cns.janelia.org/

## 第三方工程参考

- FlyWire FAFB 浏览器模拟: https://github.com/snedea/flybrain
- MaleCNS 游戏/闭环模拟: https://github.com/Jhongdlp/FlyBrain
- OpenWorm: https://openworm.org/
- FlyBrain anatomical atlas（R/Bioconductor）: https://bioconductor.org/packages/release/data/annotation/html/flybrain.html

注意：`FlyBrain` 不是唯一项目名，`FlyBrains` 也常被用来泛指模板或资源。引用时必须写明仓库、数据集和版本。

## 数据管理原则

- 大型原始连接组不提交到 Git；记录下载 URL、版本、校验和与许可。
- token 只放在 `.env`，不放进脚本、Notebook 或输出表。
- 每个结果文件记录数据集版本、查询日期和阈值。
- 第三方仓库不要直接复制代码进本项目；优先作为 Git submodule 或在独立目录克隆，并保留原许可证。

