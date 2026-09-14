"""Project Contributor H3 加速方式切换节点 (wrapper)。

单 BOOLEAN 开关决定输出 (一采+二采一体切换):
  - turbo+缓存: turbo LoRA + SolAttn + BlockCache 链, sigmas 来自 BasicScheduler
  - PDD: 官方 PDD Acc LoRA + head bank, sigmas 来自 PDD Apply / PDDScheduler

【执行级跳过 (lazy)】
  四个主路 MODEL/SIGMAS 输入均声明 lazy; check_lazy_status 只请求当前
  开关选定的一路信号。被跳过的分支 (turbo 链或 PDD 链) 因无消费者
  请求而完全不执行 —— 未选中的 LoRA 不加载, 是 ComfyUI 官方 lazy 求值。

【二采 sigma 可选 (2026-08-29)】
  sigmas2_turbo / sigmas2_pdd 移入 optional:
    - 未连线 (纯一采图, 如 Beta_1 系列): check_lazy_status 不请求该输入,
      二采支路完全不执行; execute 将 SIGMAS_SECOND 回退为主采 sigma
      (该输出在纯一采图上无消费者, 回退值无副作用)。
    - 已连线 (Beta_2/Beta_3 二采链): 行为与旧版完全一致, 照常请求求值。
  连线与否通过隐藏 PROMPT+UNIQUE_ID 在提交图中检测 —— 若不检测而直接
  请求未连线输入, ComfyUI 的 make_input_strong_link 会抛 NodeInputError。

【PDD 模式约束 (由共享段保证)】
  Euler + CFG 1.0 (BasicGuider 单条件) + SigmaShift 12/3。
  PDD 模式下二采建议关闭闸门 (head 在放大 latent 上质量未验证)。
"""

from __future__ import annotations


class YixuAnH3AccSwitch:
    """加速切换: turbo+BlockCache ↔ PDD (MODEL + 一/二采 SIGMAS 一体切换)。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "acc_mode": ("BOOLEAN", {
                    "default": True,
                    "label_on": "turbo+缓存",
                    "label_off": "PDD 8步",
                    "tooltip": (
                        "开 = turbo LoRA + BlockCache 加速链 (现状); "
                        "关 = PDD Acc 官方 8 步 (CFG 1.0, Euler, 训练网格 sigma)。"
                        "两路互斥, 未选中分支完全不执行。"
                    ),
                }),
                "model_turbo": ("MODEL", {
                    "lazy": True,
                    "tooltip": "turbo 链输出 (BlockCache 之后)",
                }),
                "model_pdd": ("MODEL", {
                    "lazy": True,
                    "tooltip": "PDD Apply 输出 (含 trunk LoRA + head bank patch)",
                }),
                "sigmas_turbo": ("SIGMAS", {
                    "lazy": True,
                    "tooltip": "turbo 一采 sigma (BasicScheduler 所见即所得)",
                }),
                "sigmas_pdd": ("SIGMAS", {
                    "lazy": True,
                    "tooltip": "PDD 一采 sigma (Apply 输出的训练网格边界)",
                }),
            },
            "optional": {
                "sigmas2_turbo": ("SIGMAS", {
                    "lazy": True,
                    "tooltip": "turbo 二采 sigma (精修 BasicScheduler); 未连线时 SIGMAS_SECOND 回退主采 sigma",
                }),
                "sigmas2_pdd": ("SIGMAS", {
                    "lazy": True,
                    "tooltip": "PDD 二采 sigma (PDDScheduler 低 denoise, 网格内); 未连线时 SIGMAS_SECOND 回退主采 sigma",
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("MODEL", "SIGMAS", "SIGMAS")
    RETURN_NAMES = ("MODEL", "SIGMAS_PRIMARY", "SIGMAS_SECOND")
    FUNCTION = "execute"
    CATEGORY = "Project Contributor/H3 本地"
    OUTPUT_NODE = False
    DESCRIPTION = (
        "加速方式切换 (turbo+BlockCache ↔ PDD)。\n"
        "MODEL 与一采 SIGMAS 必接; 二采 SIGMAS 可选 (未连线则 SIGMAS_SECOND "
        "回退主采 sigma, 供纯一采图使用)。\n"
        "未选中分支因 lazy 完全不执行。\n"
        "PDD 模式要求 Euler + CFG 1.0 + SigmaShift 12/3 (共享段已保证);\n"
        "PDD 模式下建议关二采闸门 (head 在放大 latent 上未验证)。"
    )

    @staticmethod
    def _input_connected(prompt, unique_id, key):
        """判断提交图中本节点某输入是否真的有连线。

        prompt = dynprompt.get_original_prompt(), unique_id = 本节点 id
        (均为 ComfyUI 隐藏输入)。连线检测失败时保守按已连接处理,
        保持旧图 (Beta_2/Beta_3) 的求值行为。
        """
        try:
            node = (prompt or {}).get(str(unique_id)) or {}
            return key in (node.get("inputs") or {})
        except Exception:
            return True

    def check_lazy_status(self, acc_mode,
                          model_turbo=None, model_pdd=None,
                          sigmas_turbo=None, sigmas_pdd=None,
                          sigmas2_turbo=None, sigmas2_pdd=None,
                          prompt=None, unique_id=None, **kwargs):
        want = []
        if acc_mode:
            if model_turbo is None:
                want.append("model_turbo")
            if sigmas_turbo is None:
                want.append("sigmas_turbo")
            if sigmas2_turbo is None and self._input_connected(prompt, unique_id, "sigmas2_turbo"):
                want.append("sigmas2_turbo")
        else:
            if model_pdd is None:
                want.append("model_pdd")
            if sigmas_pdd is None:
                want.append("sigmas_pdd")
            if sigmas2_pdd is None and self._input_connected(prompt, unique_id, "sigmas2_pdd"):
                want.append("sigmas2_pdd")
        return want

    def execute(self, acc_mode,
                model_turbo=None, model_pdd=None,
                sigmas_turbo=None, sigmas_pdd=None,
                sigmas2_turbo=None, sigmas2_pdd=None,
                prompt=None, unique_id=None, **kwargs):
        if acc_mode:
            if model_turbo is None or sigmas_turbo is None:
                raise ValueError("turbo+缓存模式但 turbo 路主输入未接通")
            return (model_turbo, sigmas_turbo,
                    sigmas2_turbo if sigmas2_turbo is not None else sigmas_turbo)
        if model_pdd is None or sigmas_pdd is None:
            raise ValueError("PDD 模式但 PDD 路主输入未接通")
        return (model_pdd, sigmas_pdd,
                sigmas2_pdd if sigmas2_pdd is not None else sigmas_pdd)
