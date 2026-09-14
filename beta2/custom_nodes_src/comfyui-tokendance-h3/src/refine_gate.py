"""Project Contributor H3 二采精修闸门节点 (wrapper)。

单 BOOLEAN 开关决定输出:
  - 开: latent_refined  (放大桥 → 二采精修后的 AV latent)
  - 关: latent_raw      (一采直通的原始 AV latent, 未放大)

【执行级跳过 (lazy)】
  两个 LATENT 输入均声明 lazy; check_lazy_status 只请求当前开关
  真正需要的那一路。被跳过的支路 (放大桥 / 二采链) 因无消费者
  请求而完全不执行 —— 不是 bypass, 是 ComfyUI 官方 lazy 求值。
"""

from __future__ import annotations


class YixuAnH3RefineGate:
    """二采闸门: 单开关在「精修」与「放大后直通」间切换, 关=仅跳过二采采样。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "second_pass": ("BOOLEAN", {
                    "default": True,
                    "label_on": "二采开启",
                    "label_off": "跳过二采",
                    "tooltip": (
                        "开 = 放大后走二采精修; "
                        "关 = 放大照常执行, 仅跳过二采采样, "
                        "放大后 latent 直接解码 (等效 SplitSigmas 第二段 0 步)"
                    ),
                }),
                "latent_refined": ("LATENT", {
                    "lazy": True,
                    "tooltip": "二采输出 (120 精修采样结果)",
                }),
                "latent_raw": ("LATENT", {
                    "lazy": True,
                    "tooltip": "放大后未精修 (CondSync 输出; 关闸门时直通解码)",
                }),
            },
        }

    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("LATENT",)
    FUNCTION = "execute"
    CATEGORY = "Project Contributor/H3 本地"
    OUTPUT_NODE = False
    DESCRIPTION = (
        "二采精修闸门 (等效 SplitSigmas 二段 0 步)。\n"
        "开: 放大 → 二采精修; 关: 放大照常, 跳过二采采样, 放大后 latent 直接解码。\n"
        "关闭时仅二采采样器支路因 lazy 不执行, 放大桥零影响。"
    )

    def check_lazy_status(self, second_pass,
                          latent_refined=None, latent_raw=None, **kwargs):
        want = []
        if second_pass and latent_refined is None:
            want.append("latent_refined")
        if not second_pass and latent_raw is None:
            want.append("latent_raw")
        return want

    def execute(self, second_pass,
                latent_refined=None, latent_raw=None):
        if second_pass:
            if latent_refined is None:
                raise ValueError("二采开启但 latent_refined 未接通")
            return (latent_refined,)
        if latent_raw is None:
            raise ValueError("跳过二采但 latent_raw 未接通")
        return (latent_raw,)
