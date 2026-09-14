from comfy_extras.nodes_lt import LTXVConcatAVLatent, LTXVSeparateAVLatent
from .H3LatentResize import _resize_conditioning

_H3_VAE_DOWNSAMPLE = 16


class H3LatentUpscalerNode3DV3:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"latent": ("LATENT",)},
            "optional": {
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
            },
        }

    RETURN_TYPES = ("LATENT", "CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("latent", "positive", "negative")
    FUNCTION = "run"
    CATEGORY = "video/MinimaxH3"

    def run(self, latent, positive=None, negative=None):
        video_latent, audio_latent = LTXVSeparateAVLatent.execute(latent)
        samples = video_latent["samples"]
        target_width = int(samples.shape[-1]) * _H3_VAE_DOWNSAMPLE
        target_height = int(samples.shape[-2]) * _H3_VAE_DOWNSAMPLE
        out_pos = _resize_conditioning(positive, target_width, target_height)
        out_neg = _resize_conditioning(negative, target_width, target_height)
        out_latent, = LTXVConcatAVLatent.execute(video_latent, audio_latent)
        return (out_latent, out_pos, out_neg)


NODE_CLASS_MAPPINGS = {"H3LatentUpscalerNode3DV3": H3LatentUpscalerNode3DV3}
NODE_DISPLAY_NAME_MAPPINGS = {"H3LatentUpscalerNode3DV3": "H3 Latent Cond Sync (3D)"}
