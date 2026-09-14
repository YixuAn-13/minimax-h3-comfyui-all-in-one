"""Project Contributor H3 本地工作流 custom node pack。

节点:
  - YixuAnH3MultiMode      单 mode 下拉 T2V/I2V/L2V/FL2V/Ref (Ref 槽直连动态扩)
  - YixuAnH3ModelSwitch    fl2v↔ref2v 权重切换
  - YixuAnH3LoadRefVideo   精简加载参考视频 (本地文件 -> IMAGE + AUDIO)
  - YixuAnH3LoadRefAudio   精简加载参考音频 (本地文件 -> AUDIO)
  - YixuAnH3BatchVideos    参考视频组 (动态≤3, H3_REF_VIDEOS)
  - YixuAnH3BatchAudios    参考音频组 (动态≤3, H3_REF_AUDIOS)
  - YixuAnH3RefineGate     二采精修闸门 (关=仅跳过二采采样, 放大照常; lazy 执行级跳过)
  - YixuAnH3AccSwitch      加速方式切换 (turbo+BlockCache ↔ PDD; 一/二采一体 lazy 切换)
"""

WEB_DIRECTORY = "./web"

from .src.local_multimode import YixuAnH3MultiMode
from .src.model_switch import YixuAnH3ModelSwitch
from .src.ref_batch import (
    YixuAnH3BatchVideos,
    YixuAnH3BatchAudios,
    YixuAnH3LoadRefVideo,
    YixuAnH3LoadRefAudio,
)
from .src.refine_gate import YixuAnH3RefineGate
from .src.acc_switch import YixuAnH3AccSwitch

NODE_CLASS_MAPPINGS = {
    "YixuAnH3MultiMode": YixuAnH3MultiMode,
    "YixuAnH3ModelSwitch": YixuAnH3ModelSwitch,
    "YixuAnH3LoadRefVideo": YixuAnH3LoadRefVideo,
    "YixuAnH3LoadRefAudio": YixuAnH3LoadRefAudio,
    "YixuAnH3BatchVideos": YixuAnH3BatchVideos,
    "YixuAnH3BatchAudios": YixuAnH3BatchAudios,
    "YixuAnH3RefineGate": YixuAnH3RefineGate,
    "YixuAnH3AccSwitch": YixuAnH3AccSwitch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "YixuAnH3MultiMode": "Project Contributor H3 多模式(本地) T2V/I2V/FL2V/Ref",
    "YixuAnH3ModelSwitch": "Project Contributor H3 模型开关 (fl2v↔ref2v)",
    "YixuAnH3LoadRefVideo": "Project Contributor H3 加载参考视频 (精简)",
    "YixuAnH3LoadRefAudio": "Project Contributor H3 加载参考音频 (精简)",
    "YixuAnH3BatchVideos": "Project Contributor H3 参考视频组 (动态≤3)",
    "YixuAnH3BatchAudios": "Project Contributor H3 参考音频组 (动态≤3)",
    "YixuAnH3RefineGate": "Project Contributor H3 二采闸门 (跳过放大+二采)",
    "YixuAnH3AccSwitch": "Project Contributor H3 加速切换 (turbo+缓存 ↔ PDD)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
