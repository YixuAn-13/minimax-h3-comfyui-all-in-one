# MiniMax H3 完全体工作流合集 · ComfyUI 本地版

> 🌐 [**English**](./README.en.md) · 中文

> **作者**:Project Contributor
> **一句话**:一份仓库,收齐 MiniMax H3 音视频生成在本地 ComfyUI 上的**完整、完备、低配可跑、开箱实用**的整套工作流 —— 整合多位社区开发者节点包的工程化结晶。
> **license**:工作流 JSON 与自研节点 `GPL-3.0-or-later`;未上架社区源码按原许可随库分发;模型权重不在本库分发。

---

## 这个仓库是什么

针对 **MiniMax H3**(T2V / I2V / FL2V / L2V / Ref2VA 全模式文/图/参考生视频 + 原生音轨)的 **ComfyUI 本地工作流合集**,围绕 **8GB 显存(实测 RTX 4060 Laptop)** 调优,把文生视频、图生视频、首尾帧、参考视频/音频、人脸精修、latent 放大、二次采样、时序细节增强这些散落在社区里的能力,**整合进一份可继承、可运行、可发布的工程**。

三个系列(Beta 1 / 2 / 3)各司其职,覆盖从「多模式一键切换」到「纯 T8 全家桶」到「人脸精修」完整链路:

| 系列 | 定位 | 一句话 | 活跃节点数 |
|---|---|---|---|
| **[Beta_1](./beta1/)** | 第一代 · 多模式条件总线 | 自研单节点 mode 下拉切全模式 + 素材批处理 + 加速一键切换,**纯一采定版** | 43 / 46 |
| **[Beta_2](./beta2/)** | 第二代 · **功能最全** | 模式总线 + latent 3D 放大二采 + CondSync 条件重同步 + TDE 后处理 + 双加速(turbo/PDD) | 52×2 / 54 |
| **[Beta_3](./beta3/)** | 第三代 · **纯 T8 全家桶** | 官方契约骨架 + DualClock 双时钟 + Learned 二采 + FaceRefine 人脸精修,贴近上游最简最稳 | 33 / 28 / 25 |

> 三系列是**演进关系**而非乱堆:Beta_1 打底(总线/加速切换)→ Beta_2 补齐画质链(二采/放大/TDE)→ Beta_3 切到 T8 官方统一条件节点,回归最干净形态。**新用户推荐从 Beta_3 入手**(结构最简、最贴官方、FaceRefine 也在它名下),需要功能最全的画质链再看 Beta_2,想研究多模式总线架构看 Beta_1。

---

## 核心亮点

1. **完整完备完全体**——文/图/首尾帧/参考视频/参考音频/人脸精修六类任务全cover,原生音视频同步输出,不是"只出画面"的半成品
2. **低配置可用**——全程 8GB 显存实测:BlockCache 模型缓存 + SageAttention + SolAttn + comfy-kitchen 后端 + LowVRAM 三件套(Lite 流)+ 两级 VRAM/RAM 清理,低配也能跑 720p
3. **方便实用好用**——自研 `comfyui-tokendance-h3` 把「多模式切换、双加速切换、二采闸门」做成**单节点下拉/一键**,不用在几十个节点里手动改线
4. **整合多社区开发者的结晶**——T8mars / wjluoxiao(机智罗)/ LBH-123-AI / Jalen-Brunson / kijai / Kosinkadink 等作者的节点包被整合进一条可复用的流水线(完整署名见文末)

---

## 快速开始

### 0. 环境要求
- ComfyUI **0.33.4+**(Desktop 或 manual 均可)
- NVIDIA 显卡,**8GB 显存起步**(低配用 Lite 流)
- MiniMax H3 模型权重(见下面「模型清单」,**不在本仓库分发**)

### 1. 装 ComfyUI + 节点包
每个系列的 `子 README` 里有**完整的节点包安装清单**(包名 / 实测版本 / 仓库链接),照着 `ComfyUI-Manager` 搜包名装即可。核心必装:
- `comfyui-minimax-h3-audio-T8`(T8mars,核心骨架)
- `ComfyUI-JZL-MiniMax-H3` / `Comfyui_Minimax_h3_latent_Upscaler` / `ComfyUI-MiniMax-H3-PDD-Acc` / `XB_ToolBox` / `ComfyUI-KJNodes` / `ComfyUI-VideoHelperSuite` / `rgthree-comfy` / `ComfyUI-Custom-Scripts` / `Comfyui-Memory_Cleanup`

### 2. 装自研节点包(必装)
把自研节点包复制进 `ComfyUI/custom_nodes/`:
```bash
# 每个系列目录下都有(同一套自研包,任取一份即可)
cp -r beta1/custom_nodes_src/comfyui-tokendance-h3  <你的 ComfyUI>/custom_nodes/
```
> 这是「多模式单节点切换 / 双加速切换 / 二采闸门」的自研节点,完整源码(含 web 前端 js)随库分发。

### 3. 装未上架社区源码(按需)
- `custom_nodes_src/comfyui-minimax-h3-blockcache-T8/` → 复制进 custom_nodes(BlockCache 缓存加速)
- `custom_nodes_src/sol_attn_minimax_v2.py` → 放到 custom_nodes 下(依赖 `wheels/` 里的 comfy-kitchen 轮子)
- Beta_2 的 `custom_nodes_src/Comfyui_Minimax_h3_latent_Upscaler_legacy_patch/` → LBH 放大器的本地融合补丁(存量工作流零改动)

### 4. 装轮子(Windows 加速后端的 comfy-kitchen)
```bash
pip install wheels/comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl
```
> 仅 Windows / CPython 3.12 需要;无轮子环境 SolAttn 会自动回退常规注意力,不影响出片。

### 5. 放模型
每个系列的「模型清单」章节列清了文件名和放置路径。核心:
- **扩散模型**:`10Eros_Max_h3_TURBO_*_int8_convrot_skip_edges.safetensors` → `models/diffusion_models/`(10Eros-Max 作者的社区量化版)
- **CLIP**:`qwen3vl_32b_heretic_minimax_h3_nvfp4.safetensors` → `models/text_encoders/`
- **VAE**:视频 `minimax_h3_video_vae_int8_convrot` + 音频 `minimax_h3_audio_vae_fp32` → `models/vae/`
- **PDD LoRA**:`models/pdd_acc/`;**latent 放大模型**:`models/latent_upscale_models/`;**YuNet 人脸检测**:`models/face_detection/`(Beta_3 已附带 onnx)

### 6. 打开工作流跑
在 ComfyUI 里加载对应 `workflows/*.json`,按各子 README 的「使用说明」填 prompt / 选模式 / 填参考素材即可出片。

---

## 目录结构

```
.
├── README.md              ← 本文件(总览)
├── beta1/                 ← 第一代:多模式条件总线(纯一采)
│   ├── README.md            (系列说明:定位/特性/依赖/模型/使用/署名)
│   ├── workflows/           工作流 JSON
│   ├── custom_nodes_src/    自研+未上架社区源码
│   ├── wheels/              comfy-kitchen 轮子
│   └── docs/                安装/轮子说明
├── beta2/                 ← 第二代:功能最全(latent放大+二采+TDE+双加速)
│   ├── README.md / workflows / custom_nodes_src / wheels / docs
│   └── docs/reference_*.json  官方/社区参考工作流存档
└── beta3/                 ← 第三代:纯 T8 全家桶(官方契约+FaceRefine)
    ├── README.md / workflows / custom_nodes_src / wheels
    ├── models_refs/         YuNet onnx(人脸检测,官方 OpenCV Zoo)
    └── docs/reference_workflows/  官方+社区参考工作流存档
```

---

## 三系列怎么选

| 你的需求 | 选哪个 |
|---|---|
| 刚上手,想最简最稳、最贴官方 | **Beta_3**(Beta_3_Lite 是低配版) |
| 单人/多人人脸精修(换脸后再稳定五官) | **Beta_3_FaceRefine** |
| 要画质最全:latent 放大 + 二采精修 + TDE 后处理 | **Beta_2** |
| 要低显存跑全功能 | **Beta_2_Lite** |
| 想研究「单节点多模式切换 + 双加速切换」总线架构 | **Beta_1** |
| 只跑最简单单采(reference 模式) | **Beta_1** |

> 一句话记忆:**Beta_1 总线、Beta_2 画质、Beta_3 全家桶与精修**。

---

## 关键设计决策(为什么这么做)

1. **单节点 mode 下拉,不做 bypass/toggle 方案**——多模式切换必须是 UX 友好的一处下拉,而非在多组节点里手动 bypass 改线(见 `YixuAnH3MultiMode`)
2. **8GB 显存边界**——全部分辨率锚定 0.82MP(实测上限),2.09MP 会硬 OOM;Lite 流再叠 LowVRAM 三件套下探更低配
3. **PDD-Acc 铁律**——euler / CFG 1.0 / 禁叠 turbo LoRA(turbo 已并入基模),否则 PDD 蒸馏块出噪声
4. **turbo LoRA 不绑死基模**——当可选加速层插 MODEL 链,不因此改基模选择
5. **FETA(EnhanceAVideo)默认旁路**——它对 ComfyUI 核心源码做 SHA256 白名单校验,0.33.4 改了 `PackedLayout` 导致必报错,旁路是安全解,等上游适配再接回

---

## 参考来源与致谢

本项目是**社区成果的整合与工程化改造**,核心节点全部来自下列作者与仓库,感谢他们的开源工作(完整逐节点对照表见各子 README 的「节点依赖」章节):

| 作者 | 仓库 / 来源 | 贡献 |
|---|---|---|
| **T8mars** | [comfyui-minimax-h3-audio-T8](https://github.com/T8mars/comfyui-minimax-h3-audio-T8) (GPL-3.0) | 核心骨架:双时钟采样、统一条件、AV 解码、二采全家、FaceRefine 全家、TDE |
| **wjluoxiao(机智罗)** | [ComfyUI-JZL-MiniMax-H3](https://github.com/wjluoxiao/ComfyUI-JZL-MiniMax-H3) · [XB_ToolBox](https://github.com/wjluoxiao/XB_ToolBox) | CondSync 条件重同步;XB_BatchImages 参考图聚合;1141/1143 二采范式 |
| **LBH-123-AI** | [Comfyui_Minimax_h3_latent_Upscaler](https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler) | 3D latent 放大(本库含本地融合补丁) |
| **Jalen-Brunson** | [ComfyUI-MiniMax-H3-PDD-Acc](https://github.com/Jalen-Brunson/ComfyUI-MiniMax-H3-PDD-Acc) | PDD-Acc 8 步蒸馏加速分支 |
| **kijai** | [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) | ModelPatchTorchSettings / LowVRAMAttention / ChunkFeedForward(低配三件套)、PreviewOverride |
| **Kosinkadink** | [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) | VHS_VideoCombine(MP4+音频输出) |
| **rgthree** | [rgthree-comfy](https://github.com/rgthree/rgthree-comfy) | Seed 固定种子节点 |
| **pythongosssss** | [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts) | PlaySound 完成提示音 |
| **LAOGOU-666** | [Comfyui-Memory_Cleanup](https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup) | VRAM/RAM 清理节点 |
| **Comfy-Org** | [MiniMax-H3 官方](https://huggingface.co/Comfy-Org/MiniMax-H3) · [ComfyUI PR #15224](https://github.com/Comfy-Org/ComfyUI) | 官方 t2v/i2v/r2v/加速版工作流与 H3 契约(帧数 17n+5、分辨率 32 对齐) |
| **10Eros-Max** | 社区量化基模 | 10Eros_Max int8 量化扩散模型(基模) |

### 未上架的社区源码(随库分发)
- `sol_attn_minimax_v2.py` — Sol-Attention(arXiv 2607.24027)的单文件节点,社区工作者实现,依赖 comfy-kitchen CUDA kernels
- `comfyui-minimax-h3-blockcache-T8/` — MiniMax H3 F1B0 Block Cache 节点,T8 系社区实验件,无公开仓库

> 以上未上架源码版权归原作者,按收到时的原样随库分发;如作者要求调整署名或移除,请联系。

---

## 许可证

- **本仓库的工作流 JSON 与自研节点**(`comfyui-tokendance-h3` + LBH 融合补丁):`GPL-3.0-or-later`(与 T8 包一致)
- **未上架社区源码**:按其原始许可随库分发,版权归原作者
- **模型权重**:遵循各自发布渠道的许可(HuggingFace Comfy-Org / alibaba-pai / 各社区模型页),**不在本仓库分发**

## 免责声明

本项目仅供学习与技术研究,生成内容请遵守相关法律法规与模型许可证条款;人脸精修(FaceRefine)请仅用于本人素材或已获授权的人像。

---

## ☕ 请作者喝杯奶茶

如果这个项目对你有帮助，欢迎点个 Star，也可以请我喝一杯奶茶~

<p align="center">
  <img src="docs/alipay_qr.jpeg" width="220" alt="支付宝收款码">
</p>

> 赞赏纯属自愿，你的 Star 就是对项目最大的支持 ⭐
