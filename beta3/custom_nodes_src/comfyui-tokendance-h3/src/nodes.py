"""Project Contributor wrapper (YixuAnH3MultiMode) 本地参考视频/音频辅助函数。

本文件为 MultiMode 的 Ref 模式在本地加载 ref_video / ref_audio 时使用的工具:
  - _mp4_to_frames_and_audio  mp4 -> IMAGE 帧序列 + AUDIO dict
  - _find_ffmpeg              获取 ComfyUI 自带的 imageio-ffmpeg 可执行路径
  - _load_wav_as_audio        wav -> ComfyUI AUDIO dict

依赖 ComfyUI 自带的 imageio / imageio-ffmpeg / torchaudio。
"""

import os
import tempfile

import numpy as np
import torch


def _mp4_to_frames_and_audio(mp4_path: str):
    """用 imageio 把 mp4 解码成 IMAGE 帧序列 [T,H,W,C] float[0,1] + AUDIO。

    ComfyUI 0.32 自带 imageio-ffmpeg, 可做 pyav 插件逐帧读取;
    音频走 ffmpeg 先转 wav 再用 torchaudio 载入 (torchaudio 是 ComfyUI 强制依赖)。
    """
    import imageio.v3 as iio

    # ---- 视频帧 ----
    frames_np = []
    for frame in iio.imiter(mp4_path, plugin="pyav"):
        frames_np.append(frame)
    if not frames_np:
        raise RuntimeError(f"无法从 {mp4_path} 读取出任何帧")
    arr = np.stack(frames_np, axis=0).astype(np.float32) / 255.0
    images = torch.from_numpy(arr)

    # ---- 音频 ----
    audio = None
    wav_tmp = None
    try:
        import subprocess
        # 唯一临时文件: 避免固定命名(mp4_path+".wav")在并发处理同一源时互相覆盖/读到半文件
        fd, wav_tmp = tempfile.mkstemp(suffix=".wav", prefix="yixuan_h3_")
        os.close(fd)
        ffmpeg = _find_ffmpeg()
        if ffmpeg:
            subprocess.run([ffmpeg, "-y", "-i", mp4_path, "-vn", "-ac", "2",
                            "-ar", "44100", wav_tmp],
                           check=False, capture_output=True)
            if os.path.exists(wav_tmp) and os.path.getsize(wav_tmp) > 0:
                audio = _load_wav_as_audio(wav_tmp)
    except Exception as e:
        print(f"[Project Contributor-H3] 音频提取失败 (可忽略, 视频帧仍可用): {e}")
        audio = None
    finally:
        if wav_tmp and os.path.exists(wav_tmp):
            os.remove(wav_tmp)

    return images, audio


def _find_ffmpeg():
    """优先使用 ComfyUI 自带的 imageio-ffmpeg 路径。"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _load_wav_as_audio(wav_path: str):
    """把 wav 读成 ComfyUI 标准 AUDIO 格式。

    ComfyUI AUDIO = {"waveform": [B, C, L], "sample_rate": sr}
    torchaudio.load 返回 [C, N](channels, samples), 需补 batch 维 → [1, C, N]。
    官方 _encode_ref_audio / VAEEncodeAudio 都期望 [B, C, L]:
      waveform[:1].movedim(1, -1) 在 2D 上会取错并让 VAE 维度报错, 所以必须补 batch。
    """
    try:
        import torchaudio
        waveform, sr = torchaudio.load(wav_path)  # [C, N]
        audio_tensor = waveform.unsqueeze(0).contiguous()  # [1, C, N] = [B, C, L]
        return {"waveform": audio_tensor, "sample_rate": sr}
    except Exception as e:
        print(f"[Project Contributor-H3] torchaudio 读 wav 失败: {e}")
        return None
