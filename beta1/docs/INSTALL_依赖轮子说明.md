# Beta_1 依赖轮子与环境说明

## 一、为什么需要这个轮子

Beta_1 的 turbo 加速链里接了 `SolAttnMiniMax`(`custom_nodes_src/sol_attn_minimax_v2.py`)。
该节点依赖 **comfy-kitchen ≥ 0.2.31** 的 CUDA kernels(bf16、head_dim 128、sm_80+)。
comfy-kitchen 官方 PyPI 上没有覆盖所有环境的 Windows 轮子,这里附带社区构建的
`comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl`(cp312-abi3 = Python 3.12+ 通用)。

**没有这个轮子也能跑**:`SolAttnMiniMax` 检测不到 comfy-kitchen 时自动回退常规
注意力,只是失去 Sol-Attn 稀疏加速。想完整体验加速链再装。

## 二、安装方法

在 ComfyUI 自带的 Python 环境里执行(ComfyUI Desktop 是 embedded python,便携版是 python_embeded):

```bat
:: ComfyUI Desktop / 便携版示例
"<ComfyUI环境python.exe>" -m pip install wheels\comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl
```

装完重启 ComfyUI。验证:

```bat
"<ComfyUI环境python.exe>" -c "import comfy_kitchen; print('ok')"
```

## 三、本机实测环境(供对照)

| 项 | 值 |
|---|---|
| ComfyUI | 0.33.4(frontend 1.49.6) |
| Python | 3.13.12 |
| PyTorch | 2.12.1+cu130 |
| GPU | NVIDIA RTX 4060 Laptop(8GB) |
| OS | Windows 11 |

- `ModelAttentionBackend` 选 `comfy kitchen attention` 时同样依赖本轮子;
  无轮子时该下拉选回 `auto`/`pytorch` 即可。
- 其余节点包无额外 pip 依赖(T8 包 requirements.txt 为空,只需 ComfyUI 自带的 torch/torchaudio)。

## 四、Python 依赖汇总(全部节点包)

| 依赖 | 来源 | 说明 |
|---|---|---|
| torch / torchaudio | ComfyUI 自带 | 无需另装 |
| comfy_kitchen ≥ 0.2.31 | `wheels/` 本文件 | 仅 SolAttn/kitchen 注意力后端需要,可选 |
| opencv-contrib-python | ComfyUI Desktop 自带 | Beta_1 未用 FaceRefine,不需要 |

> Beta_1 无 FaceRefine / JZL / TDE 链路,依赖比 Beta_2/Beta_3 少;需要更全的功能请直接用 `../beta3/`。
