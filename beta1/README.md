# Beta_1 系列 · 多模式条件总线 H3 本地工作流

> **作者**:Project Contributor
> **定位**:Beta 系列第一代 —— 自研多模式条件总线 + 参考素材批处理 + 加速方式切换
> **状态**:纯一采定版(2026-08-29 砍除二采残留,回归纯一采边界),已被 Beta_2/Beta_3 迭代,保留为工程档案(仍可正常使用)

---

## 一、这是什么

Beta_1 是本系列第一代工作流,核心思路:**用自研节点把"多模式切换、参考素材管理、加速方式选择"做成总线**,让一份工作流覆盖 T2V/I2V/L2V/FL2V/Ref2V 全模式。当时 T8 的统一条件节点(`AudioConditioningT8`)尚未成为本系列骨架,Beta_3 起才切换过去。

| 文件 | 定位 | 节点数 |
|---|---|---|
| `workflows/H3全模式本地工作流_Beta_1.json` | 主力:多模式 + 双加速分支 + 1.25× 放大解码 | 43 |
| `workflows/H3全模式本地工作流_Beta_1_Lite.json` | 轻量:低配三件套版本 | 46 |

> **边界(2026-08-29 定版)**:Beta_1 是**纯一采**工作流 —— 一次采样 → AV 分离 → 1.25× latent 放大 → 合并 → 解码输出。不含二采精修/CondSync/SplitSigmas(那是 Beta_2 的画质链)。早先残留的"二采 sigma 支路"(两个 0.35 denoise 调度器)已砍除,`YixuAnH3AccSwitch` 的二采 SIGMAS 输入改为可选,未连线时 `SIGMAS_SECOND` 自动回退主采 sigma,Beta_2/Beta_3 的连线行为不受影响。

## 二、核心特性

1. **YixuAnH3MultiMode** — 单节点 mode 下拉切换 T2V/I2V/L2V/FL2V/Ref(自研,Ref 槽动态扩展,lazy 按需执行)
2. **YixuAnH3AccSwitch** — 加速方式一键切换:turbo+BlockCache ↔ PDD 8 步,lazy 切换,未选中分支零执行(不加载废 LoRA)
3. **参考素材总线** — YixuAnH3LoadRefVideo/LoadRefAudio + BatchVideos/BatchAudios(动态 ≤3 槽)
4. **PDD-Acc** — Jalen-Brunson 的 ComfyUI-MiniMax-H3-PDD-Acc 接入(铁律:euler / CFG1 / 禁叠 turbo)
5. XB_ToolBox 的 XB_BatchImages 聚合参考图
6. 8G 显存适配:BlockCacheT8 + SageAttention + SolAttn + Comfy-Kitchen 后端 + 两级 VRAMCleanup + 1.25× 3D latent 放大
7. Lite 专列:ModelPatchTorchSettings + MiniMaxLowVRAMAttention + MiniMaxChunkFeedForward 低配三件套

## 三、节点依赖(全部节点类型与来源对照)

### ComfyUI 核心自带(无需安装)

`UNETLoader` / `CLIPLoader` / `VAELoader` / `LoraLoaderModelOnly` / `BasicGuider` / `BasicScheduler` / `KSamplerSelect` / `SamplerCustomAdvanced` / `RandomNoise` / `VAEDecode` / `VAEDecodeAudio` / `LoadImage` / `PrimitiveFloat` / `PrimitiveStringMultiline` / `ResolutionSelector` / `ComfyMathExpression` / `ModelAttentionBackend` / `LTXVSeparateAVLatent` / `LTXVConcatAVLatent`

### 社区节点包

| 包 | 版本(实测) | 作者/仓库 | 用到的节点 |
|---|---|---|---|
| **comfyui-minimax-h3-audio-T8** | 1.38.1 | **T8mars** — https://github.com/T8mars/comfyui-minimax-h3-audio-T8 (GPL-3.0) | `MiniMaxH3SigmaShift` / `MiniMaxH3MemoryEfficientSageAttentionPatch` |
| **ComfyUI-MiniMax-H3-PDD-Acc** | da6f6f6 | **Jalen-Brunson** — https://github.com/Jalen-Brunson/ComfyUI-MiniMax-H3-PDD-Acc | `MiniMaxH3PDDAccApply` |
| **comfyui-minimax-h3-blockcache-T8** | 未上架 | 社区 T8 系实验件(源码随本仓库 `../beta2/custom_nodes_src/` 分发) | `MiniMaxH3BlockCacheT8` |
| **sol_attn_minimax_v2** | 未上架 | 社区实现(arXiv 2607.24027,源码随 `../beta2/custom_nodes_src/` 分发) | `SolAttnMiniMax` |
| **Comfyui_Minimax_h3_latent_Upscaler** | 04f7159 + 融合补丁 | **LBH-123-AI** — https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler | `MinimaxH3LatentUpscalerNode3D`(1.25× 放大) |
| **XB_ToolBox** | 0.8.10 | **wjluoxiao(机智罗)** — https://github.com/wjluoxiao/XB_ToolBox | `XB_BatchImages` |
| **ComfyUI-KJNodes** | 1.5.0 | **kijai** — https://github.com/kijai/ComfyUI-KJNodes | `ModelPreviewOverrideKJ`(taeh3 预览)、Lite 三件套 `ModelPatchTorchSettings`/`MiniMaxLowVRAMAttention`/`MiniMaxChunkFeedForward` |
| **Comfyui-Memory_Cleanup** | 1.1.3 | **LAOGOU-666** — https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup | `VRAMCleanup` ×2 |
| **comfyui-videohelpersuite** | 1.7.9 | **Kosinkadink** — https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite | `VHS_VideoCombine` |
| **rgthree-comfy** | 1.0.x | **rgthree** — https://github.com/rgthree/rgthree-comfy | `Seed (rgthree)` |
| **ComfyUI-Custom-Scripts** | — | **pythongosssss** — https://github.com/pythongosssss/ComfyUI-Custom-Scripts | `PlaySound\|pysssss` |

### 自研节点包(必装,完整源码随本仓库分发)

`custom_nodes_src/comfyui-tokendance-h3/` — **Project Contributor 原创**(GPL-3.0-or-later),Beta_1 用到:

| 节点 | 作用 |
|---|---|
| **YixuAnH3MultiMode** | 核心模式入口:单节点 mode 下拉切 T2V/I2V/L2V/FL2V/Ref,Ref 槽动态扩展;按模式 lazy 跳过无关上游 |
| **YixuAnH3AccSwitch** | 加速引擎切换:开=turbo+BlockCache / 关=PDD 8 步;主路 MODEL/SIGMAS 全 lazy。二采 SIGMAS 为可选输入,未连线时 SIGMAS_SECOND 回退主采 sigma(纯一采图兼容) |
| YixuAnH3LoadRefVideo / LoadRefAudio | 本地参考视频/音频精简加载 |
| YixuAnH3BatchVideos / BatchAudios | 参考素材动态聚合(≤3 路) |

> 另有 YixuAnH3ModelSwitch(fl2v↔ref2v 基模切换)、YixuAnH3RefineGate(二采闸门)在包内,Beta_1 未用到。完整源码见 `custom_nodes_src/comfyui-tokendance-h3/`。

## 四、安装与运行

1. 按 §三 安装社区包(comfyui-tokendance-h3 从 `custom_nodes_src/` 复制进 `ComfyUI/custom_nodes/`),重启 ComfyUI
2. 下载模型(清单与来源与 Beta_2 一致,详见 `../beta2/README.md` §2.5):基模 `10Eros_Max_h3_TURBO_ref2va_beta2_int8_convrot_skip_edges`(TURBO 已并入)、CLIP `qwen3vl_32b_heretic_minimax_h3_nvfp4`、视频 VAE int8 / 音频 VAE fp32、放大器 `minimax_h3_latent_upscaler_3d_fp16`(models/latent_upscale_models)、PDD `minimax_h3_ref2va_pdd_acc_8step_comfyui`(models/pdd_acc,可选)、turbo LoRA(基模已内置加速,节点 `2` 可手动旁路)、taeh3 预览小模型(可选,`ModelPreviewOverrideKJ` 用)
3. 把 `workflows/` 两份 JSON 拖进 ComfyUI 画布
4. **模式切换**:只动 `YixuAnH3MultiMode` 的 `mode` 下拉(t2v/i2v/l2v/fl2v/ref);ref 模式把参考素材接到三个"参考组"节点(空槽自动跳过)
5. **加速引擎**:`YixuAnH3AccSwitch` 布尔开关,开=turbo+缓存,关=PDD 8 步
6. 点 Queue;分辨率由 `ResolutionSelector`(megapixels)控制,帧数 = 17k+5 官方合约(时长 ×24 后对齐)

### 显存参考(8G 卡实测,2026-08-29 冒烟)

| 配置 | 结果 |
|---|---|
| 0.5MP @ 9:16 / 3s / 8 步(t2v,turbo 链) | ✅ 全程 211s(含模型加载),输出 MP4 含音频 |
| 1.25× 放大后解码 | 0.5MP → 0.78MP 输出(672×1216) |

## 五、致谢与参考来源(重要)

本项目是**社区成果的整合与工程化改造**,核心节点全部来自下列作者,感谢他们的开源工作:

### 官方

- **Comfy-Org / MiniMax H3 官方工作流**:https://huggingface.co/Comfy-Org/MiniMax-H3 ・ https://www.minimax.io/blog/minimax-h3 —— 官方三模式工作流存档见 `../beta3/docs/reference_workflows/`,本项目的模式入口、帧数合约(17k+5)、分辨率对齐(32)均遵循官方契约
- **alibaba-pai** — PDD 加速 LoRA 官方发布:https://huggingface.co/alibaba-pai/MiniMax-H3-Acc-LoRAs

### 核心节点作者(完整表见 §三)

- **T8mars**(`comfyui-minimax-h3-audio-T8`,GPL-3.0)— SigmaShift、SageAttention 补丁的基础
- **Jalen-Brunson**(PDD-Acc)— 加速分支
- **LBH-123-AI** — 3D latent 放大器内核;其原版 README 存档于 `../beta2/docs/LBH_upscaler_README*_原版.md`
- **wjluoxiao(机智罗)**(XB_ToolBox / JZL-MiniMax-H3,B站 https://space.bilibili.com/302329373)— XB 节点与二采研究
- **kijai / Kosinkadink / rgthree / pythongosssss / LAOGOU-666** — 基础设施节点

### 参考过的社区工作流(存档见 `../beta3/docs/reference_workflows/` 与 `../beta2/docs/`)

- 官方 t2v/i2v/r2v 三份(帧数合约、分辨率契约)
- wjluoxiao 1141/1143 二采范式(Beta_1 未用二采,但其模式结构影响了本系列)
- RunningHub 8+16G 低配流(Lite 三件套思路)

### 未上架的社区源码(随本仓库分发)

- **`comfyui-minimax-h3-blockcache-T8/`** — T8 系社区实验件,未上架 Comfy Registry,无公开仓库,源码按收到时原样随 `../beta2/custom_nodes_src/` 分发(含 README 原文)。如作者要求署名调整或移除请联系。
- **`sol_attn_minimax_v2.py`** — Sol-Attention 单文件节点,社区实现,未上架;依赖 `comfy_kitchen ≥ 0.2.31`(轮子在 `wheels/`)。Beta_1 turbo 链默认接入。
- **`comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl`** — comfy-kitchen 社区构建 Windows 轮子(cp312 abi3 = Python 3.12+ 通用)。

### 本项目自研(`custom_nodes_src/comfyui-tokendance-h3/`)

- **YixuAnH3MultiMode / AccSwitch / RefBatch 系列** — Project Contributor 原创,完整源码随仓库分发;其中 AccSwitch 在 2026-08-29 升级为"二采 SIGMAS 可选"(向后兼容 Beta_2/Beta_3)

## 六、目录结构

```
beta1/
├── README.md                      ← 本文件
├── workflows/                     ← 两份工作流(拖进 ComfyUI 即用)
│   ├── H3全模式本地工作流_Beta_1.json        主力流
│   └── H3全模式本地工作流_Beta_1_Lite.json   轻量流(低配三件套)
├── custom_nodes_src/
│   └── comfyui-tokendance-h3/     ← ★自研节点包(完整源码,复制进 custom_nodes)
├── wheels/
│   └── comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl  ← sol_attn 依赖轮子
└── docs/
    └── INSTALL_依赖轮子说明.md     ← 轮子安装方法与本机实测环境
```

## 七、与后代的关系

- Beta_2 引入 latent 放大 + 二采精修 + TDE 后处理(完整工程见 `../beta2/`,含 LBH 融合补丁与全部未上架源码分发)
- **Beta_3 改用 T8 原生 `AudioConditioningT8` 单节点做模式入口**(自研 MultiMode 退役为配套),并新增 FaceRefine 专线 —— 新用户请直接使用 Beta_3

## 八、License 与使用条款

- 本仓库的工作流 JSON 与自研节点(comfyui-tokendance-h3):`GPL-3.0-or-later`(与 T8 包一致)
- 未上架社区源码按其原始许可随仓库分发,版权归原作者;如作者要求调整署名或移除请联系
- 模型权重遵循各自发布渠道的许可(HuggingFace Comfy-Org / alibaba-pai / 各社区模型页),**不在本仓库分发**
- 转载请注明本文"致谢与参考来源"一节所列的各位作者
