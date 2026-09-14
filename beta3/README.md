# Beta_3 系列 · 纯 T8 全家桶 H3 本地工作流

> **作者**:Project Contributor
> **面向**:ComfyUI 本地部署的 MiniMax H3 音视频生成,针对 **8GB 显存**(RTX 4060 Laptop)实测调优
> **状态**:已定版,三流全部冒烟通过 ✅

---

## 一、这是什么

Beta_3 是一套基于 **T8mars `comfyui-minimax-h3-audio-T8` 节点包 v1.38.1** 的工作流系列,包含三份文件:

| 文件 | 定位 | 节点数 |
|---|---|---|
| `workflows/H3全模式本地工作流_Beta_3.json` | **主力流**:8 步双时钟 + 闸门式二采放大精修 | 33 |
| `workflows/H3全模式本地工作流_Beta_3_Lite.json` | **轻量流**:同骨架无二采,低配三件套,最快出片 | 28 |
| `workflows/H3全模式本地工作流_Beta_3_FaceRefine.json` | **人脸精修流**:V2V,只对脸局部重绘精修 | 25 |

与官方 ComfyUI 工作流的核心区别:**一种模式一套文件 → 单节点下拉切模式;20+ 步 → 8 步双时钟;无精修 → 闸门式二采放大精修;大显存专用 → 8G 卡生存套装。**

---

## 二、快速开始

### 2.1 环境要求

| 项 | 要求 |
|---|---|
| ComfyUI | ≥ 0.33.x(本机 0.33.4 验证) |
| Python | 3.12+(本机 3.13.12,`comfy_kitchen` 轮子为 cp312-abi3) |
| GPU | NVIDIA 8GB+ 显存(主流二采开启时建议 ≥8G) |
| 系统 | Windows(其余平台理论可用,未测) |

### 2.2 安装节点包

把下列节点包装进 `ComfyUI/custom_nodes/`(全部可从 ComfyUI-Manager 搜索安装):

| 包 | 版本(实测) | 作者/仓库 | 用途 |
|---|---|---|---|
| **comfyui-minimax-h3-audio-T8** | 1.38.1 | **T8mars** — https://github.com/T8mars/comfyui-minimax-h3-audio-T8 (GPL-3.0) | 核心全家桶(143 节点):条件、双时钟、解码、二采全家、人脸精修全家 |
| comfyui-videohelpersuite | 1.7.9 | Kosinkadink — https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite | VHS_VideoCombine 输出 MP4 |
| rgthree-comfy | 1.0.x | rgthree — https://github.com/rgthree/rgthree-comfy | Seed (rgthree) 种子节点 |
| Comfyui-Memory_Cleanup | 1.1.3 | 图标/清理 — (Manager 可搜) | VRAMCleanup / RAMCleanup / PlaySound(pysssss 附带) |
| ComfyUI-KJNodes | 1.5.0 | kijai — https://github.com/kijai/ComfyUI-KJNodes | ModelPatchTorchSettings / MiniMaxLowVRAMAttention / MiniMaxChunkFeedForward(低配三件套,Lite 流) |

> **T8 包依赖说明**:`requirements.txt` 为空(仅需 ComfyUI 自带的 torch/torchaudio),无额外 Python 依赖。

### 2.3 自研节点包(必装)

`custom_nodes_src/comfyui-tokendance-h3/` — **本项目自研**(Project Contributor),把整个文件夹复制到 `custom_nodes/` 即可。含:

- **YixuAnH3RefineGate** — 二采精修闸门(主力的 🚪 节点)。单开关 + ComfyUI 官方 lazy 求值:关 = 放大照常、仅跳过二采采样(不是 bypass)
- YixuAnH3MultiMode / ModelSwitch / LoadRefVideo / LoadRefAudio / BatchVideos / BatchAudios / AccSwitch(配套系列,beta1/beta2 主用)

完整源码(含 web 前端 js)随仓库分发,license GPL-3.0 与 T8 包一致。

### 2.4 下载模型(HuggingFace 官方仓 + 社区定制)

全部放入 `ComfyUI/models/` 对应子目录。来源:**https://huggingface.co/Comfy-Org/MiniMax-H3**(官方)与社区 10Eros_Max 定制合并模型。

| 类型 | 文件 | 放置目录 | 来源 |
|---|---|---|---|
| diffusion_models | `10Eros_Max_h3_TURBO_ref2va_beta2_int8_convrot_skip_edges.safetensors` | models/diffusion_models | 社区 10Eros_Max 系列(TURBO 加速已并入基模),三流统一基模 |
| text_encoders | `qwen3vl_32b_heretic_minimax_h3_nvfp4.safetensors` | models/text_encoders | 社区 heretic 量化(官方原版 `qwen3vl_32b_minimax_h3_nvfp4_awq` 也可) |
| vae | `minimax_h3_video_vae_int8_convrot.safetensors` | models/vae | 社区 int8 量化版 |
| vae | `minimax_h3_audio_vae_fp32.safetensors` | models/vae | **Comfy-Org 官方** |
| face_detection(FaceRefine 流) | `face_detection_yunet_2023mar.onnx` | models/face_detection | OpenCV Zoo(官方),本仓库 `models_refs/` 已附带(232KB,SHA256 `8f2383e4…`) |

> 用官方原版模型(`minimax_h3_fl2va_pruned_int8_convrot` 等)也能跑,但 8 步双时钟配 TURBO 基模才是设计工作点;用原版时步数建议回到 20。

### 2.5 运行

1. 把 `workflows/` 三份 JSON 拖进 ComfyUI 画布(或放入 `user/default/workflows/`)
2. **模式切换**:只动 `🎛 T8 统一条件·LOW` 一个节点 —— `task_type` 下拉(auto/T2VA/I2VA/FL2VA/L2VA/Ref2VA/Hybrid),`audio_mode` 下拉(native/reference_only/lock_source/remix_source;lock/remix 需接参考音频),参考图/音频拖到对应插槽
3. 点 Queue 即可;帧数由 `⏱ 时长(秒)` 自动换算(17k+5 官方合约),分辨率由 `📐 ResolutionSelector` 控制

### 2.6 显存参考(8G 卡实测)

| 配置 | 分辨率 | 时长 | 结果 |
|---|---|---|---|
| Lite 流 | 0.82MP(1152×640 @32对齐) | 5s | ✅ ~87s |
| 主流,二采关 | 0.82MP + ×1.5 放大 ≈1.85MP | 5s | ✅ ~142s |
| 主流,二采开 | 同上,完整二采链 | 5s | ✅ ~138s |
| 任何流 | 2.09MP | — | ❌ 硬 OOM,勿超 |

---

## 三、工作流结构速览(主力流)

```
🧬 UNET(TURBO并入基模) → ⚡SageAttention → 🌀turbo LoRA(旁路) → 🧱BlockCache
                                                          ↓
🧠CLIP + 🎞视频VAE + 🔊音频VAE → 🎛 统一条件·LOW(唯一模式入口)
                                                          ↓
⏱ DualClock 双时钟 8 步 → [🎞FETA(旁路,见下)] → 🎯Guider → 🧪PASS1
                                                          ↓
              🔍Learned放大×1.5 → 🧹清理 → ⚖️Reconcile → 🧪DetailMixer → 🧪PASS2
                                                          ↓                        ↓
                                            🚪 二采闸门(开/关 lazy 切换)          ↓
                                                          ↓                        ↓
                                                     🎬 AV解码 → 🎞TDE时序增强 → 📦MP4+音频 → 🔔提示音
```

- **闸门关** = 放大照常,二采整段 lazy 跳过(等效 SplitSigmas 二段 0 步),放大后 latent 直通解码
- **闸门开** = Reconcile 契约校验 → DetailMixer 精修 → PASS2 完整二采
- 音频恒取自解码输出,与闸门状态无关

---

## 四、已知事项(透明披露)

1. **FETA 运动增强节点默认旁路(mode=4)**:T8 包的 `MiniMaxH3EnhanceAVideoT8Advanced` 对 ComfyUI **核心源码**做 SHA256 白名单校验(`_assert_core_contract`),ComfyUI 0.33.4 改动了 `PackedLayout` / `MiniMaxH3Model._forward` 导致必然报错;远程 HEAD 同样如此,升级无解。**旁路是安全解**(输出 model 按名直通),等上游适配后可自行接回。
2. **turbo LoRA 节点保持旁路**:TURBO 加速能力已并入基模,再叠独立 LoRA 会双叠过饱和。
3. 主流 `audio_mode` 默认 `native`;改 `lock_source`/`remix_source` 必须接 `drive_audio`,否则报错。
4. FaceRefine 是 V2V:需含人脸的源视频 + 2 张身份帧,检测器用 `local_opencv_yunet`(需要 opencv-contrib,ComfyUI Desktop 自带)。

---

## 五、参考来源与致谢(重要)

本项目是**社区成果的整合与工程化改造**,核心节点全部来自下列作者,感谢他们的开源工作:

### 官方
- **Comfy-Org / MiniMax H3 官方工作流**:https://huggingface.co/Comfy-Org/MiniMax-H3 ・ https://github.com/Comfy-Org/ComfyUI (PR #15224 引入 H3 支持) ・ https://www.minimax.io/blog/minimax-h3 —— 官方 t2v/i2v/r2v/加速版四份工作流存档见 `docs/reference_workflows/official_*.json`,本项目的模式入口、帧数合约(17k+5)、分辨率对齐(32)均遵循官方契约
- **MiniMax H3 模型本身**:MiniMax — https://www.minimax.io

### 核心节点包
- **T8mars** — `comfyui-minimax-h3-audio-T8`(GPL-3.0):本项目骨架的基础,双时钟采样、统一条件节点、AV 解码、Learned 二采全家、Face Refine 全家、TemporalDetailEnhance 全部出自此包
- **kijai** — ComfyUI-KJNodes:低配三件套(ModelPatchTorchSettings/LowVRAMAttention/ChunkFeedForward),数学等价降显存
- **Kosinkadink** — ComfyUI-VideoHelperSuite:MP4 输出
- **rgthree** — rgthree-comfy:Seed 节点

### 参考过的社区工作流(存档见 `docs/reference_workflows/`)
| 存档文件 | 来源与采纳点 |
|---|---|
| `community_dualclock_*.json`(双时钟 8 步三份) | RunningHub 社区双时钟 8 步极速流 —— 本项目"8 步 + 双时钟 + ResolutionSelector 参数表"的直接蓝本 |
| `community_1141/1143_*.json`(latent 放大二采) | **wjluoxiao**(https://github.com/wjluoxiao/XB_ToolBox ・ B站 https://space.bilibili.com/302329373)的 1141/1143 二采范式 —— 主流二采链的范式来源 |
| `community_lowvram_8g16g.json` | RunningHub 8+16G 低配流 —— Lite 流低配三件套的采纳来源 |
| `community_face_refine_parity.json` | T8mars 官方 `H3_Face_Refine_Parity_Advanced_EXP` —— FaceRefine 流的直接拓扑蓝本 |
| `community_mnodes_jerk_t2v.json` | ComfyUI-MAINodes 拖影强化流 —— 评估后未纳入采样层(与二采调度冲突),仅供研究 |
| `community_sigma_latent_upscale.json` | sigma 强化 + 潜空间放大流 —— 二采日程研究参考 |
| `community_10eros_v3_i2v.json` | 10Eros_Max V3 加速版 —— 定制基模选型的参考 |

### 未上架的社区源码(随本仓库分发,`custom_nodes_src/`)
- **`sol_attn_minimax_v2.py`** — Sol-Attention (arXiv 2607.24027) 的 MiniMax-H3 单文件节点实现,作者为社区工作者(未上架 Comfy Registry)。依赖 `comfy_kitchen >= 0.2.31` 的 CUDA kernels(bf16、head_dim 128、sm_80+),轮子在 `wheels/comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl`。**本项目三流未默认接入**(FETA 同类的高级实验件),提供下载以供研究。如作者要求移除请联系。
- **`comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl`** — comfy-kitchen 社区构建的 Windows 轮子(cp312 abi3 = Python 3.12+ 通用)。

### 本项目自研(`custom_nodes_src/comfyui-tokendance-h3/`)
- **YixuAnH3RefineGate**(二采闸门)及配套 MultiMode/ModelSwitch/RefBatch/AccSwitch —— Project Contributor 原创,解决"开关二采"与"多模式切换"的 UX 与执行效率问题

---

## 六、目录结构

```
beta3/
├── README.md                      ← 本文件
├── workflows/                     ← 三份工作流(拖进 ComfyUI 即用)
├── custom_nodes_src/
│   ├── comfyui-tokendance-h3/     ← 自研节点包(完整源码,复制进 custom_nodes)
│   └── sol_attn_minimax_v2.py     ← 未上架社区源码(研究用,未接入)
├── models_refs/
│   └── face_detection_yunet_2023mar.onnx   ← FaceRefine 流检测器(官方 OpenCV Zoo)
├── wheels/
│   └── comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl   ← sol_attn 依赖轮子(可选)
└── docs/
    └── reference_workflows/       ← 官方 + 社区参考工作流完整存档(署名见上表)
```

## 七、License 与使用条款

- 本仓库的工作流 JSON 与自研节点:`GPL-3.0-or-later`(与 T8 包一致)
- 未上架社区源码按其原始许可随仓库分发,版权归原作者;如作者要求调整署名或移除请联系
- 模型权重遵循各自发布渠道的许可(HuggingFace Comfy-Org / 社区模型页),**不在本仓库分发**
- 转载请注明本文"参考来源与致谢"一节所列的各位作者

## 八、与 Beta_1 / Beta_2 的关系

- **Beta_1**(第一代):自研多模式总线 + 加速切换,无二采画质链 —— 工程档案保留,见 `../beta1/`
- **Beta_2**(第二代):模式总线 + latent 放大二采精修 + TDE + 双加速切换,功能最全 —— 见 `../beta2/`(含 LBH 融合补丁与全部未上架源码分发)
- 三代共享闸门/参数语义与显存边界,模型通用;新用户推荐从本目录 Beta_3 上手
