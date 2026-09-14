"""H3 Ref 参考视频/音频 —— 聚合器 + 精简加载器。

设计对齐 XB_BatchImages:
  - 聚合器动态扩槽, 用户只连「要几路就几路」
  - wrapper 只接聚合器的单一输出, 不再堆 0/1/2 固定端口

官方上限:
  ref_videos / paired audios: max 3
  standalone ref_audios: max 3
"""

from __future__ import annotations

import os

import folder_paths

from .nodes import _mp4_to_frames_and_audio, _load_wav_as_audio, _find_ffmpeg
from .local_multimode import _load_audio_file_to_audio


class FlexibleOptionalInputType(dict):
    """rgthree / XB 同款: 允许 JS 动态加槽, 未知 key 也合法。

    带 prefix_types 前缀→类型映射: JS 动态加出的「音轨N」应判为 AUDIO,
    「视频N」应判为 IMAGE, 而不是一律回退 type_——否则服务端 prompt 校验
    (get_input_info) 会把音轨误判成 IMAGE, 导致 ref 多路音频被拒。
    """

    def __init__(self, type_, data=None, prefix_types=None):
        self.type_ = type_
        self.data = data or {}
        self.prefix_types = prefix_types or []  # [(前缀, "AUDIO"/"IMAGE"), ...]
        for k, v in self.data.items():
            self[k] = v

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        if isinstance(key, str):
            for prefix, typ in self.prefix_types:
                if key.startswith(prefix):
                    return (typ,)
        return (self.type_,)

    def __contains__(self, key):
        return True


def _resolve_local_path(path: str) -> str:
    """解析本地文件路径。

    支持:
      - 绝对路径                 → 原样
      - ComfyUI input/ 下的相对名 → folder_paths 解析 (上传按钮回填的就是这种)
      - folder:xxx 前缀          → folder_paths 注解路径
    返回真实存在的绝对路径; 不存在则返回原值(由调用方报友好错)。
    """
    path = (path or "").strip()
    if not path or path.lower().startswith(("http://", "https://")):
        return path
    resolved = folder_paths.get_annotated_filepath(path)
    if os.path.isfile(resolved):
        return resolved
    return path


def _sorted_slot_items(kwargs, prefix):
    """按 视频1/视频2 或 音频1 编号排序, 跳过 None。"""
    items = []
    for k, v in kwargs.items():
        if not k.startswith(prefix) or v is None:
            continue
        tail = k[len(prefix):]
        if not tail.isdigit():
            continue
        items.append((int(tail), v, k))
    items.sort(key=lambda x: x[0])
    return items


class YixuAnH3BatchVideos:
    """参考视频组 (ref) —— 动态槽, 最多 3 路。

    用法:
      VHS_LoadVideo / 精简加载器 的 IMAGE → 视频1
      同一加载器的 audio → 音轨1 (可选, 配对同一编号)
      接上后自动出现 视频2/音轨2 ...
    输出一包给 wrapper 的 ref_videos 口。
    """

    MAX = 3

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": FlexibleOptionalInputType("IMAGE", {
                "视频1": ("IMAGE",),
                "音轨1": ("AUDIO",),
            }, prefix_types=[("音轨", "AUDIO")]),
        }

    RETURN_TYPES = ("H3_REF_VIDEOS",)
    RETURN_NAMES = ("参考视频包",)
    FUNCTION = "pack"
    CATEGORY = "Project Contributor/H3 本地"
    DESCRIPTION = (
        "Ref 参考视频聚合。接 VHS_LoadVideo 或「精简加载参考视频」。\n"
        "视频N = 帧序列 IMAGE; 音轨N = 同编号配套音轨 (可选)。\n"
        "官方最多 3 路; 接满一路自动冒下一空槽。提示词 <Video 1>..<Video N>。"
    )

    def pack(self, **kwargs):
        videos = {}
        audios = {}
        slots = _sorted_slot_items(kwargs, "视频")
        if len(slots) > self.MAX:
            raise ValueError(f"参考视频最多 {self.MAX} 路 (官方上限), 当前 {len(slots)}")
        for idx, (num, frames, _key) in enumerate(slots):
            n = int(getattr(frames, "shape", (0,))[0] or 0)
            if n < 5:
                raise ValueError(
                    f"视频{num} 帧数 < 5 (约 0.2s@24fps), 无法作为参考视频"
                )
            videos[f"ref_video_{idx}"] = frames
            # 配对同编号音轨: 音轨1 配 视频1
            aud = kwargs.get(f"音轨{num}")
            if aud is not None:
                audios[f"ref_video_audio_{idx}"] = aud
        if not videos:
            return (None,)
        return ({"videos": videos, "video_audios": audios},)


class YixuAnH3BatchAudios:
    """参考音频组 (ref) —— 动态槽, 最多 3 路独立音频 (不绑视频)。

    用法:
      VHS_LoadAudioUpload / 精简加载参考音频 → 音频1
      接上后自动出现 音频2 ...
    输出一包给 wrapper 的 ref_audios 口。提示词 <Audio 1>..
    """

    MAX = 3

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": FlexibleOptionalInputType("AUDIO", {
                "音频1": ("AUDIO",),
            }),
        }

    RETURN_TYPES = ("H3_REF_AUDIOS",)
    RETURN_NAMES = ("参考音频包",)
    FUNCTION = "pack"
    CATEGORY = "Project Contributor/H3 本地"
    DESCRIPTION = (
        "Ref 独立参考音频聚合 (不绑视频)。\n"
        "官方最多 3 路; 接一路自动冒下一空槽。提示词 <Audio 1>..<Audio N>。"
    )

    def pack(self, **kwargs):
        audios = {}
        slots = _sorted_slot_items(kwargs, "音频")
        if len(slots) > self.MAX:
            raise ValueError(f"独立参考音频最多 {self.MAX} 路 (官方上限), 当前 {len(slots)}")
        for idx, (_num, aud, _key) in enumerate(slots):
            audios[f"ref_audio_{idx}"] = aud
        if not audios:
            return (None,)
        return (audios,)


class YixuAnH3LoadRefVideo:
    """精简加载参考视频 —— 选本地文件即可, 无 VHS 一堆参数。

    内部固定按原片解码; 输出 IMAGE 帧 + AUDIO 音轨, 接到「参考视频组」。
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "vhs_path_extensions": [
                        "mp4", "webm", "mov", "avi", "mkv", "m4v", "gif",
                    ],
                    "tooltip": "点输入框选本地视频。无需设置 force_rate/width 等; 内部自动解码。",
                }),
            },
            "optional": {
                "max_frames": ("INT", {
                    "default": 360, "min": 5, "max": 3600, "step": 1,
                    "tooltip": "最多取多少帧 (24fps 下 360≈15s, 官方参考视频建议 2–15s)。0=不截断",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "AUDIO")
    RETURN_NAMES = ("图像", "audio")
    FUNCTION = "load"
    CATEGORY = "Project Contributor/H3 本地"
    DESCRIPTION = "Ref 用精简视频加载。选文件 → 接到「参考视频组」的 视频N + 音轨N。"

    def load(self, video, max_frames=360):
        path = _resolve_local_path(video or "")
        # 未选文件 → 返回 None, 由 lazy 跳过 / Batch 聚合器忽略空输入。
        # 不抛错, 避免用户只传图/音频时被空加载器卡住。
        if not path:
            return (None, None)
        if path.lower().startswith(("http://", "https://")):
            raise ValueError("仅支持本地文件路径, 请先下载")
        if not os.path.isfile(path):
            raise ValueError(f"文件不存在: {video or ''}")
        frames, aud = _mp4_to_frames_and_audio(path)
        n = int(frames.shape[0])
        if n < 5:
            raise ValueError(f"视频帧数 < 5: {path}")
        if max_frames and max_frames > 0 and n > max_frames:
            frames = frames[:max_frames]
        return (frames, aud)


class YixuAnH3LoadRefAudio:
    """精简加载参考音频 —— 选本地文件即可。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "vhs_path_extensions": [
                        "wav", "mp3", "ogg", "m4a", "flac", "aac",
                    ],
                    "tooltip": "点输入框选本地音频。接到「参考音频组」的 音频N。",
                }),
            },
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "load"
    CATEGORY = "Project Contributor/H3 本地"
    DESCRIPTION = "Ref 用精简音频加载。选文件 → 接到「参考音频组」。"

    def load(self, audio):
        path = _resolve_local_path(audio or "")
        # 未选文件 → 返回 None, 由 lazy 跳过 / Batch 聚合器忽略空输入。
        if not path:
            return (None,)
        if path.lower().startswith(("http://", "https://")):
            raise ValueError("仅支持本地文件路径")
        if not os.path.isfile(path):
            raise ValueError(f"文件不存在: {audio or ''}")
        return (_load_audio_file_to_audio(path),)


__all__ = [
    "YixuAnH3BatchVideos",
    "YixuAnH3BatchAudios",
    "YixuAnH3LoadRefVideo",
    "YixuAnH3LoadRefAudio",
]
