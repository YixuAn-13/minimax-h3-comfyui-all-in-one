"""Project Contributor H3 多模式本地条件生成节点 (wrapper)。

一个节点带 mode 下拉 (T2V/I2V/L2V/FL2V/Ref), 内部分发到 ComfyUI 核心:
  - MiniMaxH3ImageToVideo     → t2v / i2v / l2v / fl2v
  - MiniMaxH3ReferenceToVideo → ref

【输入面 — Batch 聚合心智 (对齐 XB_BatchImages)】
  Ref 参考物统一走「中间聚合节点」, wrapper 只接一包:
    参考图:   LoadImage → XB_BatchImages       → ref_images  (IMAGE batch)
    参考视频: LoadRefVideo → YixuAnH3BatchVideos → ref_videos  (H3_REF_VIDEOS 包)
    独立音频: LoadRefAudio → YixuAnH3BatchAudios → ref_audios  (H3_REF_AUDIOS 包)

  静态: audio_vae, ref_image_size, first_frame, last_frame

【按模式自动跳过无关上游 (lazy)】
  可选输入均 lazy; check_lazy_status 按 mode 只 strong 真正需要的支路。
"""

from __future__ import annotations

import os
import subprocess
import tempfile

from comfy_extras.nodes_minimax_h3 import (
    MiniMaxH3ImageToVideo,
    MiniMaxH3ReferenceToVideo,
)

from .nodes import _find_ffmpeg, _load_wav_as_audio


def _load_audio_file_to_audio(path):
    """本地音频文件 -> ComfyUI AUDIO dict (依赖 ComfyUI 自带 ffmpeg + torchaudio)。"""
    # 唯一临时文件, finally 统一清理; 避免固定命名在并发/中断时残留竞争
    wav_tmp = None
    try:
        ffmpeg = _find_ffmpeg()
        fd, wav_tmp = tempfile.mkstemp(suffix=".wav", prefix="yixuan_h3_")
        os.close(fd)
        if not ffmpeg:
            raise RuntimeError("未找到 ffmpeg (需要 imageio-ffmpeg, ComfyUI 自带)")
        subprocess.run([ffmpeg, "-y", "-i", path, "-vn", "-ac", "2",
                        "-ar", "44100", wav_tmp],
                       check=False, capture_output=True)
        if not os.path.exists(wav_tmp) or os.path.getsize(wav_tmp) == 0:
            raise RuntimeError(f"音频转换失败: {path}")
        audio = _load_wav_as_audio(wav_tmp)
        if audio is None:
            raise RuntimeError(f"读取音频失败: {path}")
        return audio
    finally:
        if isinstance(wav_tmp, str) and os.path.exists(wav_tmp):
            os.remove(wav_tmp)


# 各 mode 真正需要的静态 optional
_MODE_NEEDS = {
    "t2v": set(),
    "i2v": {"first_frame"},
    "l2v": {"last_frame"},
    "fl2v": {"first_frame", "last_frame"},
    "ref": {"audio_vae", "ref_images", "ref_videos", "ref_audios"},
}

_FILE_WIDGETS = ("image", "video", "audio")
_MAX_REF_VIDEO = 3
_MAX_REF_AUDIO = 3


def _has_file_widget(node_info) -> bool:
    """节点本身是否选了真实文件 (widget 值带扩展名)。"""
    if not isinstance(node_info, dict):
        return False
    ni = node_info.get("inputs") or {}
    for w in _FILE_WIDGETS:
        v = ni.get(w)
        if isinstance(v, str) and "." in v and v.strip():
            return True
    return False


def _source_has_file(dynprompt, my_inputs, input_name, max_hops: int = 3) -> bool:
    """input_name 的上游 (经中转) 是否至少有一路真上传了文件。"""
    if not isinstance(my_inputs, dict):
        return False
    link = my_inputs.get(input_name)
    if not isinstance(link, list) or len(link) < 2:
        return False
    frontier = [link[0]]
    seen = set()
    for _ in range(max_hops + 1):
        nxt = []
        for nid in frontier:
            key = str(nid)
            if key in seen:
                continue
            seen.add(key)
            node = dynprompt.get(key) if isinstance(dynprompt, dict) else None
            if node is None and isinstance(dynprompt, dict):
                node = dynprompt.get(nid)
            if _has_file_widget(node):
                return True
            ni = (node or {}).get("inputs") or {}
            for _name, val in ni.items():
                if isinstance(val, list) and len(val) >= 2 and str(val[0]) not in seen:
                    nxt.append(val[0])
        if not nxt:
            break
        frontier = nxt
    return False


class YixuAnH3MultiMode:
    """H3 多模式: mode 下拉切换 T2V/I2V/L2V/FL2V/Ref, 无需 bypass。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["t2v", "i2v", "l2v", "fl2v", "ref"], {
                    "default": "t2v",
                    "tooltip": (
                        "T2V=纯文; I2V=首帧锁帧; L2V=尾帧锁帧; FL2V=首+尾; "
                        "Ref=图/视频/音频参考注入不锁帧 (建议 ref2va, fl2va 也能跑)"
                    ),
                }),
                "clip": ("CLIP",),
                "video_vae": ("VAE",),
                "prompt": ("STRING", {
                    "default": "", "multiline": True, "dynamicPrompts": True,
                }),
                "width": ("INT", {"default": 1344, "min": 32, "max": 99999, "step": 32}),
                "height": ("INT", {"default": 768, "min": 32, "max": 99999, "step": 32}),
                "length": ("INT", {
                    "default": 124, "min": 5, "max": 3600, "step": 17,
                    "tooltip": "帧数 @24fps, 对齐 17k+5 (124≈5s)",
                }),
            },
            "optional": {
                "audio_vae": ("VAE", {
                    "lazy": True,
                    "tooltip": "Ref 模式必接 (minimax_h3_audio_vae)",
                }),
                "ref_image_size": (["match", "max"], {
                    "default": "match",
                    "tooltip": "Ref 参考图缩放: match=生成分辨率; max=2048 短边更保真更慢",
                }),
                "first_frame": ("IMAGE", {
                    "lazy": True,
                    "tooltip": "I2V/FL2V 首帧 (锁 0.00s)",
                }),
                "last_frame": ("IMAGE", {
                    "lazy": True,
                    "tooltip": "L2V/FL2V 尾帧 (锁末帧)",
                }),
                "ref_images": ("IMAGE", {
                    "lazy": True,
                    "tooltip": "Ref 参考图 batch: 接 XB_BatchImages「图像」。提示词 <Picture 1>..",
                }),
                "ref_videos": ("H3_REF_VIDEOS", {
                    "lazy": True,
                    "tooltip": "Ref 参考视频包: 接「参考视频组」输出。提示词 <Video 1>..",
                }),
                "ref_audios": ("H3_REF_AUDIOS", {
                    "lazy": True,
                    "tooltip": "Ref 独立参考音频包: 接「参考音频组」输出。提示词 <Audio 1>..",
                }),
            },
            "hidden": {
                # 禁止叫 prompt: 会和用户文本 prompt 撞名
                "dynprompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("CONDITIONING", "LATENT")
    RETURN_NAMES = ("positive", "LATENT")
    FUNCTION = "execute"
    CATEGORY = "Project Contributor/H3 本地"
    OUTPUT_NODE = False
    DESCRIPTION = (
        "单节点 mode 下拉: T2V/I2V/L2V/FL2V/Ref。\n"
        "Ref 参考物走 Batch 聚合: ref_images(XB_BatchImages) + ref_videos(参考视频组) + ref_audios(参考音频组)。\n"
        "中间聚合节点各自动态扩槽 (各最多 3), wrapper 只收一包。"
    )

    def check_lazy_status(self, mode,
                          audio_vae=None, ref_image_size="match",
                          first_frame=None, last_frame=None, ref_images=None,
                          ref_videos=None, ref_audios=None,
                          dynprompt=None, unique_id=None, **kwargs):
        """按 mode 决定要把哪些 lazy 输入转 strong。

        - t2v: 什么都不请求
        - i2v/l2v/fl2v: 仅请求对应帧
        - ref: audio_vae(若连) + 真有文件的 ref_images / ref_videos / ref_audios
        """
        if not isinstance(dynprompt, dict) or unique_id is None:
            return []
        node_info = dynprompt.get(str(unique_id)) or dynprompt.get(unique_id)
        my_inputs = node_info.get("inputs") if isinstance(node_info, dict) else None
        if not isinstance(my_inputs, dict):
            return []

        needed = set(_MODE_NEEDS.get(mode, set()))
        values = {
            "audio_vae": audio_vae,
            "first_frame": first_frame,
            "last_frame": last_frame,
            "ref_images": ref_images,
            "ref_videos": ref_videos,
            "ref_audios": ref_audios,
        }

        want = []

        def _maybe(name: str, require_file: bool):
            if name not in my_inputs:
                return
            if values.get(name) is not None:
                return
            if require_file and not _source_has_file(dynprompt, my_inputs, name):
                return
            want.append(name)

        for name in needed:
            if name == "audio_vae":
                _maybe(name, require_file=False)
            elif name in ("first_frame", "last_frame"):
                _maybe(name, require_file=False)
            elif name == "ref_images":
                _maybe(name, require_file=True)
            elif name in ("ref_videos", "ref_audios"):
                # 中间 Batch 节点本身无文件 widget; 必须沿链路找到
                # 真正选过文件的加载器才请求, 否则(空文件)跳过, 不报错。
                _maybe(name, require_file=True)

        return want

    def execute(self, mode, clip, video_vae, prompt, width, height, length,
                audio_vae=None, ref_image_size="match",
                first_frame=None, last_frame=None, ref_images=None,
                ref_videos=None, ref_audios=None, **kwargs):
        if isinstance(prompt, dict):
            raise ValueError(
                "内部错误: 文本 prompt 被工作流 dict 覆盖。"
                "请重启 ComfyUI 加载最新节点后重试。"
            )
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt 不能为空")

        if mode in ("t2v", "i2v", "l2v", "fl2v"):
            ff = first_frame if mode in ("i2v", "fl2v") else None
            lf = last_frame if mode in ("l2v", "fl2v") else None
            if mode == "i2v" and first_frame is None:
                raise ValueError("I2V 模式需要接 first_frame 首帧图")
            if mode == "l2v" and lf is None:
                raise ValueError("L2V 模式需要接 last_frame 尾帧图")
            if mode == "fl2v" and (ff is None or lf is None):
                raise ValueError("FL2V 模式需要同时接 first_frame 和 last_frame")
            out = MiniMaxH3ImageToVideo.execute(
                clip, video_vae, prompt, width, height, length, ff, lf)
            return out.result

        # ---- ref ----
        if audio_vae is None:
            raise ValueError(
                "REF 模式需要接 audio_vae (minimax_h3_audio_vae)。"
                "权重建议 ref2va; fl2va 也能跑 (社区实测)。"
            )

        ref_imgs = {}
        if ref_images is not None:
            try:
                n = int(getattr(ref_images, "shape", (0,))[0] or 0)
            except Exception:
                n = 0
            if n > 9:
                raise ValueError(f"参考图最多 9 张 (官方上限), 当前 batch={n}")
            for i in range(n):
                ref_imgs[f"ref_image_{i}"] = ref_images[i : i + 1]

        # 解包 Batch 聚合输出
        ref_vids, ref_vid_auds = {}, {}
        if isinstance(ref_videos, dict):
            ref_vids = dict(ref_videos.get("videos") or {})
            ref_vid_auds = dict(ref_videos.get("video_audios") or {})

        ref_auds = {}
        if isinstance(ref_audios, dict):
            ref_auds = dict(ref_audios)

        if len(ref_vids) > _MAX_REF_VIDEO:
            raise ValueError(f"参考视频最多 {_MAX_REF_VIDEO} 路, 当前 {len(ref_vids)}")
        if len(ref_auds) > _MAX_REF_AUDIO:
            raise ValueError(f"独立参考音频最多 {_MAX_REF_AUDIO} 路, 当前 {len(ref_auds)}")

        if not ref_imgs and not ref_vids and not ref_auds:
            raise ValueError(
                "REF 模式至少上传并接通一项参考: ref_images / ref_videos / ref_audios"
                " (未上传文件的支路会被自动跳过, 不必全填)"
            )

        out = MiniMaxH3ReferenceToVideo.execute(
            clip, video_vae, audio_vae, prompt, width, height, length,
            ref_image_size, ref_imgs, ref_vids, ref_vid_auds, ref_auds)
        return out.result
