"""H3 conditioning resize utilities."""
import torch
import torch.nn.functional as F


def _resize_conditioning(conditioning, width, height):
    if conditioning is None:
        return None
    out = []
    for item in conditioning:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            out.append(item)
            continue
        cond_tensor, params = item[0], item[1]
        new_params = dict(params) if isinstance(params, dict) else params
        if isinstance(new_params, dict):
            for key, value in list(new_params.items()):
                if isinstance(value, torch.Tensor) and value.ndim == 4:
                    if value.shape[-2] != height or value.shape[-1] != width:
                        resized = F.interpolate(
                            value.to(torch.float32),
                            size=(height, width),
                            mode="bilinear",
                            align_corners=False,
                        )
                        new_params[key] = resized.to(value.dtype)
        out.append([cond_tensor, new_params])
    return out
