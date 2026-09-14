// Project Contributor H3 精简加载器 —— 「上传本地文件」入口
// 给 YixuAnH3LoadRefVideo / YixuAnH3LoadRefAudio 加一个「⬆ 上传本地文件」button widget:
//   点击 → 本机文件选择 → 上传到 ComfyUI input/ 目录 → 回填相对文件名到 STRING。
// 后端 load() 用 folder_paths.get_annotated_filepath 解析该相对名。
// 用原生 button widget, 不覆盖 onDrawForeground/mouseDown, 与灰显扩展零冲突。
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const VIDEO_NODE = "YixuAnH3LoadRefVideo";
const AUDIO_NODE = "YixuAnH3LoadRefAudio";

function uploadFile(node, widget) {
  const input = document.createElement("input");
  input.type = "file";
  input.style.display = "none";
  if (widget.options?.vhs_path_extensions) {
    input.accept = widget.options.vhs_path_extensions
      .map((e) => "." + e)
      .join(",");
  }
  document.body.appendChild(input);
  input.onchange = async () => {
    const file = input.files?.[0];
    input.remove();
    if (!file) return;

    const formData = new FormData();
    formData.append("image", file); // ComfyUI /upload/image 用 image 字段
    try {
      const resp = await api.fetchApi("/upload/image", {
        method: "POST",
        body: formData,
      });
      if (!resp.ok) {
        alert("上传失败: HTTP " + resp.status);
        return;
      }
      const data = await resp.json();
      const name = data?.name || data?.image?.name || file.name;
      widget.value = name;
      widget.callback?.(name);
      node.setDirtyCanvas?.(true, true);
    } catch (err) {
      console.error("[Project Contributor-H3] 上传失败:", err);
      alert("上传失败: " + err);
    }
  };
  input.click();
}

function attachUpload(node, widget) {
  if (node.__yixuan_h3_upload_bound) return;
  const isVideo = node.comfyClass === VIDEO_NODE || node.type === VIDEO_NODE;
  const isAudio = node.comfyClass === AUDIO_NODE || node.type === AUDIO_NODE;
  if (!isVideo && !isAudio) return;
  if (!widget) return;

  // button widget 不参与工作流序列化/执行参数
  node.addWidget("button", "⬆ 上传本地文件", null, () => {
    uploadFile(node, widget);
  }).serialize = false;
  node.__yixuan_h3_upload_bound = true;
}

app.registerExtension({
  name: "Project Contributor.H3.RefUpload",
  async nodeCreated(node) {
    const isVideo = node.comfyClass === VIDEO_NODE || node.type === VIDEO_NODE;
    const isAudio = node.comfyClass === AUDIO_NODE || node.type === AUDIO_NODE;
    if (!isVideo && !isAudio) return;
    const name = isVideo ? "video" : "audio";
    const widget = (node.widgets || []).find((w) => w.name === name);
    attachUpload(node, widget);
  },
  async loadedGraphNode(node) {
    const isVideo = node.comfyClass === VIDEO_NODE || node.type === VIDEO_NODE;
    const isAudio = node.comfyClass === AUDIO_NODE || node.type === AUDIO_NODE;
    if (!isVideo && !isAudio) return;
    const name = isVideo ? "video" : "audio";
    const widget = (node.widgets || []).find((w) => w.name === name);
    attachUpload(node, widget);
  },
});