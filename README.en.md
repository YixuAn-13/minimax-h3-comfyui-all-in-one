# MiniMax H3 All-in-One Workflows · ComfyUI (English)

> **Author**: [Project Contributors](<account-url>)
> **TL;DR**: One repo, one complete set of MiniMax H3 audio/video workflows for **local ComfyUI**, tuned for **8GB VRAM laptops** (tested on an RTX 4060 Laptop) — assembled from the best community node packs.
> **License**: workflows + custom nodes `GPL-3.0-or-later`; unlisted community source distributed under its original license; model weights are **not** distributed here.

**中文版见 [README.md](./README.md)**

---

## Is this for me? (the 4060-laptop / 8GB-VRAM question)

Yes — this whole project exists **because I only had 8GB of VRAM**. If you are on an RTX 4060 (or any ~8GB card) and want:

- text-to-video / image-to-video / first-last-frame / reference-video / **face-refine** — all modes, with **native audio**
- something that actually **runs at 720p on 8GB** instead of OOM-ing
- mode & acceleration switching via **one dropdown** instead of rewiring 20 nodes

…then this is made for you.

## Pick your workflow (click to jump)

| | Series | What it does | When to pick |
|---|---|---|---|
| 🟢 **[Start here](./beta3/README.md)** | **Beta_3** — pure T8 stack | Closest to the official MiniMax H3 contract. DualClock sampling + unified conditioning + native audio. Includes **FaceRefine**. Simplest & most stable. | New users, or anyone who just wants it to work |
| 🟡 **[Most complete](./beta2/README.md)** | **Beta_2** — full pipeline | Multi-mode bus + **latent upscale + second pass + temporal detail enhance + dual acceleration (turbo/PDD)**. The most feature-complete generation. | When you want the highest quality chain |
| 🔵 **[Simplest / study](./beta1/README.md)** | **Beta_1** — multi-mode bus | Single-pass, one-dropdown mode switching + reference batching. Cleanest for learning the architecture. | Learning, or pure single-pass reference generation |

> Each series has its own in-depth `README.md` (per-node credits, install list, model list, usage).

**Low-VRAM files**: every series also ships a `*_Lite` workflow (adds FP16 accumulation + LowVRAM attention + chunked FF) for the smallest footprint.

## Quick start

### 1. Requirements
- ComfyUI **0.33.4+** (Desktop or manual)
- NVIDIA GPU, **8GB VRAM+** (Lite workflows for the tightest cards)
- MiniMax H3 model weights (see below — **not in this repo**)

### 2. Install node packs
Each `beta*/README.md` lists the exact packs to install via **ComfyUI-Manager**. The essentials:

```
comfyui-minimax-h3-audio-T8          (T8mars — core skeleton)
ComfyUI-JZL-MiniMax-H3               (conditioning resync)
Comfyui_Minimax_h3_latent_Upscaler   (3D latent upscale)
ComfyUI-MiniMax-H3-PDD-Acc           (8-step distilled acceleration)
XB_ToolBox                           (reference-image batching)
ComfyUI-KJNodes                      (low-VRAM trio + preview)
ComfyUI-VideoHelperSuite             (MP4 + audio mux)
rgthree-comfy                        (seed)
ComfyUI-Custom-Scripts               (completion sound)
Comfyui-Memory_Cleanup               (VRAM/RAM cleanup)
```

### 3. Install the custom node pack (required)
Drop our small custom node pack into `ComfyUI/custom_nodes/`:
```bash
cp -r beta1/custom_nodes_src/comfyui-tokendance-h3  <your ComfyUI>/custom_nodes/
```
This is the pack that gives you **one-dropdown mode/acceleration/gate switching** (`YixuAnH3MultiMode` / `YixuAnH3AccSwitch` / `YixuAnH3RefineGate`).

### 4. Install unlisted community source (as needed)
- `custom_nodes_src/comfyui-minimax-h3-blockcache-T8/` → copy into custom_nodes (BlockCache caching)
- `custom_nodes_src/sol_attn_minimax_v2.py` → drop next to custom_nodes (needs the comfy-kitchen wheel in `wheels/`)
- Beta_2: `custom_nodes_src/Comfyui_Minimax_h3_latent_Upscaler_legacy_patch/` → LBH upscaler local patch

### 5. Install the wheel (Windows acceleration backend)
```bash
pip install wheels/comfy_kitchen-0.2.31-cp312-abi3-win_amd64.whl
```
> Windows / CPython 3.12 only. Without it, SolAttn auto-falls back to regular attention — output is unaffected.

### 6. Put the models
Each series' README has the full model list + paths. The core ones:
- **Diffusion model**: `10Eros_Max_h3_TURBO_*_int8_convrot_skip_edges.safetensors` → `models/diffusion_models/`
- **CLIP**: `qwen3vl_32b_heretic_minimax_h3_nvfp4.safetensors` → `models/text_encoders/`
- **VAE**: `minimax_h3_video_vae_int8_convrot` + `minimax_h3_audio_vae_fp32` → `models/vae/`
- **PDD LoRA**: `models/pdd_acc/` · **latent upscaler**: `models/latent_upscale_models/` · **YuNet face detector**: `models/face_detection/` (onnx bundled in Beta_3)

### 7. Open & run
Load the `workflows/*.json` in ComfyUI, fill prompt / pick mode / add references, run.

## Why these design decisions (the short version)

1. **One dropdown, not 20 rewires** — mode/accel/gate switching must be UX-first
2. **8GB is the hard boundary** — everything anchored at 0.82MP (2.09MP OOMs); Lite adds the low-VRAM trio for tighter cards
3. **PDD-Acc rules** — euler / CFG 1.0 / **no stacked turbo LoRA**, else the distilled blocks render noise
4. **turbo LoRA as an optional layer** — never re-pick the base model just to use it
5. **FETA (EnhanceAVideo) bypassed by default** — it SHA-checks ComfyUI core internals and breaks on 0.33.4; bypass is the safe path until upstream adapts

## Credits (community integration)

This is a **consolidation of community work**, engineered into one reproducible pipeline. Full per-node credits live in each `beta*/README.md`. Key authors:

| Author | Repo | Contribution |
|---|---|---|
| **T8mars** | [comfyui-minimax-h3-audio-T8](https://github.com/T8mars/comfyui-minimax-h3-audio-T8) (GPL-3.0) | core skeleton: dual-clock, unified conditioning, AV decode, 2nd-pass family, FaceRefine family, TDE |
| **wjluoxiao** | [ComfyUI-JZL-MiniMax-H3](https://github.com/wjluoxiao/ComfyUI-JZL-MiniMax-H3) · [XB_ToolBox](https://github.com/wjluoxiao/XB_ToolBox) | CondSync resync; reference batching; 1141/1143 two-pass paradigm |
| **LBH-123-AI** | [Comfyui_Minimax_h3_latent_Upscaler](https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler) | 3D latent upscale (local patch included) |
| **Jalen-Brunson** | [ComfyUI-MiniMax-H3-PDD-Acc](https://github.com/Jalen-Brunson/ComfyUI-MiniMax-H3-PDD-Acc) | PDD-Acc 8-step distilled acceleration |
| **kijai** | [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) | low-VRAM trio, preview override |
| **Kosinkadink** | [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) | VHS_VideoCombine |
| **rgthree** | [rgthree-comfy](https://github.com/rgthree/rgthree-comfy) | Seed node |
| **pythongosssss** | [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts) | PlaySound |
| **LAOGOU-666** | [Comfyui-Memory_Cleanup](https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup) | VRAM/RAM cleanup |
| **Comfy-Org** | [MiniMax-H3 official](https://huggingface.co/Comfy-Org/MiniMax-H3) · [ComfyUI PR #15224](https://github.com/Comfy-Org/ComfyUI) | official H3 contract (17n+5 frames, 32-aligned resolution) |
| **10Eros-Max** | community quant | 10Eros_Max int8 quantized base model |

### Unlisted community source (distributed in `custom_nodes_src/`)
- `sol_attn_minimax_v2.py` — Sol-Attention (arXiv 2607.24027) single-file node, community implementation, needs comfy-kitchen kernels
- `comfyui-minimax-h3-blockcache-T8/` — MiniMax H3 F1B0 block-cache node, T8-ecosystem experimental, no public repo

> These are distributed as received, copyright stays with the original authors. Contact to adjust credits or remove.

## License

- Workflows + custom nodes (`comfyui-tokendance-h3` + LBH patch): `GPL-3.0-or-later`
- Unlisted community source: distributed under original license, copyright remains with authors
- Model weights: follow each publisher's license, **not distributed here**

## Disclaimer

For learning & technical research. Generated content must comply with applicable laws and model license terms. Face-refine should only be used on your own or authorized footage.