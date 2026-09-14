# Beta_2 系列 · latent 放大 + 二采精修 + TDE 后处理 H3 本地工作流

> **作者**:Project Contributor
> **面向**:ComfyUI 本地部署的 MiniMax H3 音视频生成,针对 **8GB 显存**(RTX 4060 Laptop)实测调优
> **状态**:已定版封版。三流 × 加速双分支(turbo/PDD) × 二采开/关 × TDE 后处理,**全组合冒烟通过** ✅(2026-08-28)

---

## 一、这是什么

Beta_2 是本系列第二代工作流。在 Beta_1 的"多模式总线 + 加速切换"基础上,Beta_2 补齐了官方工作流没有的**画质链路**:**latent 3D 放大 → 条件重同步 → 二采精修 → 时序细节增强**,全部围绕 8GB 显存卡实测调校。是系列里**功能最全**的一代(模式总线 + 二采 + 双加速 + TDE 四合一)。

| 文件 | 定位 | 活跃节点数 |
|---|---|---|
| `workflows/H3全模式本地工作流_Beta_2.json` | **主力流**:全功能(二采 + AccSwitch + TDE) | 52 |
| `workflows/H3全模式本地工作流_Beta_2.1.json` | 主力流的姊妹版(语义零差异,版本线正式成员) | 52 |
| `workflows/H3全模式本地工作流_Beta_2_Lite.json` | **轻量流**:低显存三件套版本 | 54 |

与官方 ComfyUI 工作流的核心区别:

| 维度 | 官方工作流 | Beta_2 系列 |
|---|---|---|
| 模式切换 | 一种模式一份文件 | 单节点 mode 下拉(T2V/I2V/L2V/FL2V/Ref) |
| 画质 | 一遍采样直出 | 放大 + 二采精修 + TDE 后处理三连 |
| 加速 | 官方加速 LoRA 一种 | turbo / PDD 双引擎一键切换 |
| 显存 | 大显存专用 | 8G 卡生存套装 + 实测容量边界内置 |

---

## 二、快速开始

### 2.1 环境要求

| 项 | 要求 |
|---|---|
| ComfyUI | ≥ 0.33.x(本机 0.33.4 验证) |
| Python | 3.12+ |
| GPU | NVIDIA 8GB+(二采开启时 8G 卡需重启后 RAM 干净) |
| 系统 | Windows(其余平台理论可用,未测) |

### 2.2 安装节点包

把下列节点包装进 `ComfyUI/custom_nodes/`(全部可从 ComfyUI-Manager 搜索安装):

| 包 | 版本(实测) | 作者/仓库 | 本系列用到的节点 |
|---|---|---|---|
| **comfyui-minimax-h3-audio-T8** | 1.38.1 | **T8mars** — https://github.com/T8mars/comfyui-minimax-h3-audio-T8 (GPL-3.0) | `MiniMaxH3TemporalDetailEnhanceT8Advanced`(TDE 后处理)、`MiniMaxH3MemoryEfficientSageAttentionPatch` |
| **Comfyui_Minimax_h3_latent_Upscaler** | 04f7159 + 本地融合补丁 | **LBH-123-AI** — https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler | `MinimaxH3LatentUpscalerNode3D`(3D latent 放大) |
| **ComfyUI-JZL-MiniMax-H3** | 0.6.22 | **wjluoxiao(机智罗)** — https://github.com/wjluoxiao/ComfyUI-JZL-MiniMax-H3 | `JZL_MiniMaxH3CondSync`(放大后条件重同步) |
| **ComfyUI-MiniMax-H3-PDD-Acc** | da6f6f6 | **Jalen-Brunson** — https://github.com/Jalen-Brunson/ComfyUI-MiniMax-H3-PDD-Acc | `MiniMaxH3PDDAccApply` / `MiniMaxH3PDDAccScheduler`(PDD 加速分支) |
| **XB_ToolBox** | 0.8.10 | **wjluoxiao** — https://github.com/wjluoxiao/XB_ToolBox | `XB_BatchImages`(Ref 参考图聚合) |
| comfyui-minimax-h3-blockcache-T8 | 未上架 | 社区 T8 系实验件(源码随本仓库分发,见 §5) | `MiniMaxH3BlockCacheT8`(模型级缓存加速) |
| ComfyUI-KJNodes | 1.5.0 | **kijai** — https://github.com/kijai/ComfyUI-KJNodes | `ModelPatchTorchSettings`/`MiniMaxLowVRAMAttention`/`MiniMaxChunkFeedForward`(Lite 低配三件套)、`ModelPreviewOverrideKJ` |
| Comfyui-Memory_Cleanup | 1.1.3 | **LAOGOU-666** — https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup | `VRAMCleanup` / `RAMCleanup`(清理六件套) |
| comfyui-videohelpersuite | 1.7.9 | **Kosinkadink** — https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite | `VHS_VideoCombine`(MP4+音频输出) |
| rgthree-comfy | 1.0.x | **rgthree** — https://github.com/rgthree/rgthree-comfy | `Seed (rgthree)` 固定种子 |
| ComfyUI-Custom-Scripts | — | **pythongosssss** — https://github.com/pythongosssss/ComfyUI-Custom-Scripts | `PlaySound\|pysssss`(完成提示音) |

> 其余 `LTXVSeparateAVLatent`/`LTXVConcatAVLatent`、`MiniMaxH3ImageToVideo`/`MiniMaxH3ReferenceToVideo`、`ComfyMathExpression`、`ModelAttentionBackend` 等均为 **ComfyUI 核心自带**(`comfy_extras`),无需另装。

### 2.3 自研节点包(必装)

`custom_nodes_src/comfyui-tokendance-h3/` — **本项目自研**(Project Contributor),把整个文件夹复制到 `custom_nodes/` 即可。节点清单:

| 节点 | 作用 |
|---|---|
| **YixuAnH3MultiMode** | 核心模式入口:单节点 mode 下拉切 T2V/I2V/L2V/FL2V/Ref,Ref 槽动态扩展;按模式 lazy 跳过无关上游 |
| **YixuAnH3AccSwitch** | 加速引擎切换:开=turbo+BlockCache / 关=PDD 8 步;六路 MODEL/SIGMAS 全 lazy,未选中分支完全不执行(不加载废 LoRA) |
| **YixuAnH3RefineGate** | 二采精修闸门:开=放大后二采精修 / 关=放大照常仅跳二采(等效 SplitSigmas 二段 0 步,不是 bypass) |
| YixuAnH3ModelSwitch | fl2v ↔ ref2v 基模下拉切换 |
| YixuAnH3LoadRefVideo / LoadRefAudio | 本地参考视频/音频精简加载 |
| YixuAnH3BatchVideos / BatchAudios | 参考素材动态聚合(≤3 路,对齐官方上限) |

完整源码(含 web 前端 js)随本仓库分发,license GPL-3.0-or-later。

### 2.4 LBH 放大节点"新旧融合"补丁(必装)

`custom_nodes_src/Comfyui_Minimax_h3_latent_Upscaler_legacy_patch/` — 我们对 LBH 仓库的手工融合改动,共 3 处(逐文件分发,`__init__.py.ours` 为改后的注册文件示例):

1. `minimax_h3_latent_upscaler_3d.py`(改) — 上游重构后只注册新 API 节点名;我们**恢复了 legacy 节点名 `MinimaxH3LatentUpscalerNode3D`**(包装新核心,scale 模式),让存量社区工作流(包括本项目)无需改线即可使用新内核
2. `H3_latent_upscaler_3d_v3.py` + `H3LatentResize.py`(上游 pull 时被删,我们恢复为本地文件) — `H3LatentUpscalerNode3DV3` 条件重同步节点(放大时把 conditioning 里的空间张量同步 bilinear 缩放)
3. `nodes/__init__.py`(改) — 同时注册新旧两套(2D / 3D legacy / 3D V3)

> 直接用 LBH 原版仓库也可以,但需要把工作流里的 `MinimaxH3LatentUpscalerNode3D` 换成上游新节点名 `MinimaxH3LatentUpscaler3D`。补丁的意义是**存量工作流零改动**。新版内核同时修了底部光带 bug(align=32)并增加执行后 CPU offload 省显存。

### 2.5 下载模型(HuggingFace 官方仓 + 社区定制)

全部放入 `ComfyUI/models/` 对应子目录:

| 类型 | 文件 | 放置目录 | 来源 |
|---|---|---|---|
| diffusion_models | `10Eros_Max_h3_TURBO_ref2va_beta2_int8_convrot_skip_edges.safetensors` | models/diffusion_models | 社区 10Eros_Max 系列(TURBO 加速已并入基模,int8 量化),三流统一基模 |
| text_encoders | `qwen3vl_32b_heretic_minimax_h3_nvfp4.safetensors` | models/text_encoders | 社区 heretic 量化(官方原版 `qwen3vl_32b` AWQ 也可) |
| vae | `minimax_h3_video_vae_int8_convrot.safetensors` | models/vae | 社区 int8 量化版 |
| vae | `minimax_h3_audio_vae_fp32.safetensors` | models/vae | **Comfy-Org 官方** |
| latent_upscale_models | `minimax_h3_latent_upscaler_3d_fp16.safetensors` | models/latent_upscale_models | LBH 仓库配套(见 §2.4 仓库链接) |
| pdd_acc | `minimax_h3_ref2va_pdd_acc_8step_comfyui.safetensors`(及可选 fl2va 版) | models/pdd_acc | **alibaba-pai** — https://huggingface.co/alibaba-pai/MiniMax-H3-Acc-LoRAs (官方 PDD 加速 LoRA + head bank,经 Jalen-Brunson 封装加载) |
| loras(可选) | `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | models/loras | 社区 turbo 加速 LoRA |
| loras(可选,风格) | `AfterMidnight_ref2va_h3_sexytime_rank64-v1.2.safetensors` / `PinkFluffyBunny-unpruned-fl2va-v2-rank256.safetensors` | models/loras | 社区风格 LoRA(Beta_2 主力用前者,_lite 用后者) |

> 官方原版模型权重总仓:**https://huggingface.co/Comfy-Org/MiniMax-H3**。用官方原版基模也能跑,但 turbo 8 步是本系列的调校工作点;换原版基模时步数建议回到 20。

### 2.6 运行

1. 把 `workflows/` 三份 JSON 拖进 ComfyUI 画布(或放入 `user/default/workflows/`)
2. **模式切换**:只动 `YixuAnH3MultiMode` 一个节点 —— `mode` 下拉(t2v/i2v/l2v/fl2v/ref);ref 模式把参考图/视频/音频接到三个"参考组"节点(空槽自动跳过)
3. **加速引擎**:`YixuAnH3AccSwitch` 布尔开关,开=turbo+缓存,关=PDD 8 步
4. **二采闸门**:`YixuAnH3RefineGate` 布尔开关,开=放大后二采精修,关=只放大省时间
5. 点 Queue;分辨率由 `ResolutionSelector` 控制(megapixels),帧数 124≈5s(17k+5 官方合约)

### 2.7 显存参考(8G 卡实测)

| 配置 | 结果 |
|---|---|
| 一采 0.3MP 最小档(t2v/3s) | ✅ turbo ~6 分钟,PDD ~8.5 分钟(含模型加载) |
| 二采 0.82MP(scale 1.25) | ✅ PDD+二采 510s 实测通过 |
| 二采 1.22MP | ⚠️ RAM 紧张时 >30min,不推荐 |
| 二采 2.09MP(scale 2.0) | ❌ 硬 OOM,勿用 |
| 大任务前 | 建议重启 ComfyUI 清系统 RAM |

---

## 三、工作流结构速览(主力流)

```
🧬 UNET(10ErosMax int8) → ⚡SageAttention → 🎨风格LoRA(共享) → 🌀SigmaShift
        ├─turbo分支: 🎨turbo LoRA → 🌟SolAttn → 🧱BlockCache → ┐
        └─PDD分支:   🧩PDD Acc Apply(nfe8) → ─────────────────┤
                                                              ⚡ AccSwitch(一键切换)
🧠CLIP + 🎞视频VAE + 🔊音频VAE → 🎛 YixuAnH3MultiMode(唯一模式入口)
                                                              ↓
🧪 PASS1(一采 8 步) → 🧹清理 → 📦AV分离 → 🔍3D latent 放大 ×1.25 → 📦AV合并
                                                              ↓
                                              🔄 JZL CondSync(条件重同步)
                                    ┌────────────────────────┤
                              ⚡RefineGate(开/关)        🧪 PASS2(二采精修 4步@denoise0.35)
                                    └──────────┬─────────────┘
                                          🎬 VAEDecode(视频) + 🔊VAEDecodeAudio
                                               ↓
                                     🎞 TDE 时序细节增强(0.35 强度)
                                               ↓
                                     📦VHS 输出 MP4+音频 → 🔔提示音
```

- **AccSwitch 关(=PDD)**:铁律 euler / CFG 1.0 / 禁叠一切蒸馏 LoRA——共享段天然满足,未选中的 turbo 分支因 lazy 完全不加载
- **RefineGate 关**:放大照常执行,仅二采采样器支路 lazy 跳过,放大后 latent 直通解码(等效 SplitSigmas 二段 0 步)
- **TDE(node 236)**:解码后、保存前的纯张量后处理,零模型加载零显存驻留,不动音频,alpha 通道保护,超 MP 预算 fail-closed 报错。插法 `24(VAEDecode) → 236(TDE) → 133(RAMClean) → 101(VHS)`,默认 strength=0.35 / motion_threshold=0.04 / temporal_guard=0.85 / upscale_factor=1.0(仅增强不放大)

---

## 四、与官方及其他版本的关键差异(改进点)

1. **双引擎加速 + lazy 一键切换**(自研 AccSwitch):官方只有单一加速 LoRA;我们提供 turbo 与 PDD(alibaba-pai 官方 8 步蒸馏)两条互斥加速链,ComfyUI 官方 lazy 求值保证未选中分支零执行
2. **放大 + 二采精修画质链**(官方无):3D latent 放大(懂时间轴,不把动作放大变形)→ CondSync 条件重同步(官方二采范式缺失的一环)→ 低 denoise 二采精修 → TDE 时序增强
3. **二采闸门**(自研 RefineGate):一个开关在"全质量"与"省时省显存"间切换,且**关=放大照常只跳精修**(第一版曾做错成连放大一起跳,已修正定版)
4. **单节点多模式**(自研 MultiMode):官方一种模式一份文件;我们一个下拉切五种模式,bypass/Fast Groups Bypasser 方案被明确否决弃用
5. **8G 卡生存工程**:int8 量化全家 + 清理六件套 + Lite 低配三件套 + 实测容量边界(scale 1.25 安全 / 2.0 必炸写进文档)
6. **LBH 新旧融合补丁**:上游重构不弃存量——legacy 节点名保留,新内核(光带 bug 修复+省显存)直接受益
7. **固定种子**(rgthree Seed):同种子同提示词同输出,可复现可对比

---

## 五、参考来源与致谢(重要)

本项目是**社区成果的整合与工程化改造**,核心节点全部来自下列作者,感谢他们的开源工作:

### 官方
- **Comfy-Org / MiniMax H3 官方工作流**:https://huggingface.co/Comfy-Org/MiniMax-H3 ・ https://www.minimax.io/blog/minimax-h3 —— 官方 t2v/i2v/r2v 三份工作流存档见 `docs/reference_official_*.json`,本项目的模式入口、帧数合约(17k+5)、分辨率对齐(32)均遵循官方契约
- **alibaba-pai** — PDD 加速 LoRA 官方发布:https://huggingface.co/alibaba-pai/MiniMax-H3-Acc-LoRAs (PDD 方法论文 arXiv:2607.26004)

### 核心节点包(见 §2.2 完整表)
- **T8mars** — `comfyui-minimax-h3-audio-T8`(GPL-3.0):TDE 时序细节增强、SageAttention 补丁出自此包
- **LBH-123-AI** — `Comfyui_Minimax_h3_latent_Upscaler`:3D latent 放大器内核;其原版 README 存档于 `docs/LBH_upscaler_README*_原版.md`
- **wjluoxiao(机智罗)** — `ComfyUI-JZL-MiniMax-H3`(CondSync)与 `XB_ToolBox`(BatchImages);其 1141/1143 二采范式工作流是本项目二采链的直接参考(存档 `docs/reference_1141/1143_*.json`),B站 https://space.bilibili.com/302329373
- **Jalen-Brunson** — `ComfyUI-MiniMax-H3-PDD-Acc`:PDD 加速分支的加载封装
- **kijai / Kosinkadink / rgthree / pythongosssss / LAOGOU-666** — 基础设施节点(完整链接见 §2.2)

### 参考过的社区工作流(存档见 `docs/`)
| 存档文件 | 来源与采纳点 |
|---|---|
| `reference_1141_fl2va_twopass_wjluoxiao.json` / `reference_1143_ref2va_twopass_wjluoxiao.json` | wjluoxiao(机智罗)latent 放大+二采范式 —— 本项目二采链结构的直接蓝本;用户明确否决其"SplitSigmas 截断"混合形态后,定版为独立双调度器方案 |
| `reference_official_*.json` | Comfy-Org 官方三模式工作流 —— 帧数合约、分辨率契约来源 |
| `reference_lowvram_8g16g.json` | RunningHub "8+16G 低配置 720p" 流 —— Lite 低配三件套思路参考 |
| `reference_10eros_v3.json` | 社区 10Eros_Max V3 加速版 —— int8 基模选型参考 |

### 未上架的社区源码(随本仓库分发,`custom_nodes_src/`)
- **`comfyui-minimax-h3-blockcache-T8/`** — MiniMax H3 F1B0 Block Cache 节点,T8 系社区实验件,**未上架 Comfy Registry,无公开仓库**,源码按收到时的原样随本仓库分发(含其 README 原文)。功能:Block 0 后按音/视频稳定性指标短路 Block 1-49 残差复用。实测注:动态视频场景命中率低但无害,本项目保留为保险项。如作者要求署名调整或移除请联系。
- **`sol_attn_minimax_v2.py`** — Sol-Attention(arXiv 2607.24027)的 MiniMax-H3 单文件节点,社区工作者实现,未上架。依赖 `comfy_kitchen ≥ 0.2.31` CUDA kernels,轮子在 `wheels/`。**本项目三流 turbo 分支默认接入**(SolAttn),无轮子环境自动回退常规注意力。
- **`comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl`** — comfy-kitchen 社区构建 Windows 轮子(cp312 abi3 = Python 3.12+ 通用),sol_attn 依赖。

### 本项目自研(`custom_nodes_src/`)
- **YixuAnH3MultiMode / AccSwitch / RefineGate / ModelSwitch / RefBatch 系列**(`comfyui-tokendance-h3/`) — Project Contributor 原创,解决多模式 UX、双引擎切换、二采闸门三件事;完整源码随仓库分发
- **LBH legacy 融合补丁**(`Comfyui_Minimax_h3_latent_Upscaler_legacy_patch/`) — Project Contributor 对 LBH 仓库的手工改动(diff 说明见 §2.4)

---

## 六、目录结构

```
beta2/
├── README.md                      ← 本文件
├── workflows/                     ← 三份工作流(拖进 ComfyUI 即用)
│   ├── H3全模式本地工作流_Beta_2.json        主力流
│   ├── H3全模式本地工作流_Beta_2.1.json      姊妹版
│   └── H3全模式本地工作流_Beta_2_Lite.json   轻量流(低配三件套)
├── custom_nodes_src/
│   ├── comfyui-tokendance-h3/     ← ★自研节点包(完整源码,复制进 custom_nodes)
│   ├── Comfyui_Minimax_h3_latent_Upscaler_legacy_patch/  ← ★LBH 融合补丁(4 文件)
│   ├── comfyui-minimax-h3-blockcache-T8/  ← 未上架社区源码(原样分发)
│   └── sol_attn_minimax_v2.py     ← 未上架社区源码(turbo 分支已接入)
├── wheels/
│   └── comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl  ← sol_attn 依赖轮子
└── docs/
    ├── LBH_upscaler_README*_原版.md   ← LBH 仓库原版说明存档
    └── reference_*.json            ← 官方+社区参考工作流完整存档(署名见 §5)
```

## 七、已知事项(透明披露)

1. **PDD 模式画质**:基模 10ErosMax 的 adaln 表与 ref2va PDD 权重异 trunk(配对 auto-refit 放行,残差 5.24e-04);能跑、画面正常,若实测劣化可下拉换 `fl2va` PDD 权重对照
2. **BlockCache 命中率**:动态视频场景命中率低(audio_diff≈0.32-0.40 vs 阈值 0.08),不建议盲目提高阈值;开启无害
3. **风格 LoRA 三流不同**:Beta_2/Beta_2.1 = AfterMidnight(rank64),Lite = PinkFluffyBunny(rank256),属作者个人配置,可自由替换
4. 二采容量边界与 RAM 清理建议见 §2.7;2.09MP 硬 OOM 为实测定案
5. 冒烟记录(2026-08-28):完整链含 TDE success;TDE 独立最小流 314ms(纯后处理开销可忽略);三流 × turbo/PDD × 二采开/关全组合通过

## 八、与 Beta_1 / Beta_3 的关系

- **Beta_1**(第一代):多模式总线 + 加速切换,无二采画质链 —— Beta_2 的直接前身
- **Beta_3**(第三代):T8 原生统一条件节点骨架 + 人脸精修专线,结构更精简 —— 新用户推荐
- 三代共享闸门/参数语义与显存边界,模型通用;Beta_2 是功能最全的一代

## 九、License 与使用条款

- 本仓库的工作流 JSON 与自研节点(comfyui-tokendance-h3 + LBH 融合补丁):`GPL-3.0-or-later`(与 T8 包一致)
- 未上架社区源码按其原始许可随仓库分发,版权归原作者;如作者要求调整署名或移除请联系
- 模型权重遵循各自发布渠道的许可(HuggingFace Comfy-Org / alibaba-pai / 各社区模型页),**不在本仓库分发**
- 转载请注明本文"参考来源与致谢"一节所列的各位作者
