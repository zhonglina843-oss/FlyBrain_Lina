# FlyVis 神经动力学进度

## 已完成

服务器上的 `flyvis` 官方源码已恢复并安装到 `flyvis` conda 环境。GPU 验证通过：

- GPU：NVIDIA GeForce RTX 4080 SUPER
- PyTorch：2.14.0+cu130
- FlyVis：1.2.0
- 节点：45,669
- 边：1,513,231
- 感光输入：721 个

使用 20 帧输入，其中第 5--14 帧为全场亮度刺激，官方 `Network.simulate()` 成功返回 `(1, 20, 45669)` 的活动序列，且全部为有限值。刺激期间平均活动高于刺激前，说明输入确实经过了网络动力学并改变了全脑活动。

## 重要边界

这次是官方网络结构和动力学的 smoke test，不是预训练模型结果。FlyVis 的网络可以先用默认初始化参数运行；预训练模型需要额外下载 `results_pretrained_models.zip`，官方脚本通过 Google Drive API 下载。服务器访问 `www.googleapis.com` 超时，因此预训练权重尚未取得。

```text
721 个感光输入
        ↓
FlyVis 光视觉网络
        ↓
45,669 个神经元、1,513,231 条有向边
        ↓
随时间变化的神经活动
```

## 与官方 LIF 实验的区别

`Drosophila_brain_model` 实验从指定 LC4/LPLC2 神经元直接注入 Poisson spike，观察 DNp01 是否放电；FlyVis 实验从 721 个感光输入开始，输入是随时间变化的视觉信号，输出是整个视觉网络的连续活动。两者都使用连接结构和时间动力学，但刺激入口不同，输出读出也不同。
