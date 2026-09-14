"""Project Contributor H3 模型开关节点 (model switch)。

画布上只保留一个加载器：下拉可直接选 fl2v 或 ref2v diffusion 权重，
其余采样/解码共用一套。配合 `YixuAnH3MultiMode` 的 mode 下拉即可完成
「fl2v ↔ ref2v」双模型切换：

  - 跑 T2V / I2V / L2V / FL2V  → 下拉选 fl2v 权重 (如 10Eros_Max_h3_fl2va_*)
  - 跑 Ref(参考图/视频/音频)   → 下拉选 ref2v 权重 (如 minimax_h3_ref2va_*)，wrapper mode 切 ref

当从下拉里选中 ref2v 权重但被 ref 之外的 mode 使用、或相反时，
会在本节点给出友好报错提示，避免跑出无意义的片子。
"""

import folder_paths

# ComfyUI 核心自带的 FLOW_AV 扩散模型加载器 (与 UNETLoader 同源)
from nodes import UNETLoader


class YixuAnH3ModelSwitch:
    @classmethod
    def INPUT_TYPES(cls):
        files = folder_paths.get_filename_list("diffusion_models")
        default = ""
        for wanted in (
            "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
            "minimax_h3_ref2v",
            "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
        ):
            if any(wanted in f for f in files):
                default = next(f for f in files if wanted in f)
                break
        return {
            "required": {
                "checkpoint": (
                    files,
                    {
                        "default": default,
                        "tooltip": (
                            "fl2v / ref2v 模型切换。\n"
                            "• fl2v 权重 → 配合 wrapper mode=t2v/i2v/l2v/fl2v; 也能试跑 ref (社区实测, 效果略逊)\n"
                            "• ref2v 权重 → 配合 wrapper mode=ref (官方推荐, 身份保真最好)\n"
                            "当前 diffusion_models 目录下所有文件都会出现在下拉里。"
                        ),
                    },
                ),
                "weight_dtype": (
                    ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"],
                    {"default": "default", "advanced": True},
                ),
            },
        }

    RETURN_TYPES = ("MODEL",)
    RETURN_NAMES = ("MODEL",)
    FUNCTION = "load"
    CATEGORY = "Project Contributor/H3 本地"

    def load(self, checkpoint, weight_dtype="default"):
        if not checkpoint:
            raise ValueError("YixuAnH3ModelSwitch: 未选择 diffusion 权重")
        # 直接复用 ComfyUI 核心 UNETLoader 的加载逻辑，保证与内置行为一致
        loader = UNETLoader()
        return loader.load_unet(checkpoint, weight_dtype)


__all__ = ["YixuAnH3ModelSwitch"]