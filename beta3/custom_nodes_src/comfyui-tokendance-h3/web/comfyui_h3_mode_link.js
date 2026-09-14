// Project Contributor H3 多模式 —— 只做视觉灰显/亮起。
// 禁止改 node.mode / 禁止挂钩 graph.onAfterChange (会触发重绘死循环)。
// 执行层跳过由后端 lazy + check_lazy_status 负责。
import { app } from "../../scripts/app.js";

// 分支组: frame_first / frame_last / ref_images / ref_videos / ref_audios
const MODE_ACTIVE = {
  t2v: { frame_first: 0, frame_last: 0, ref_images: 0, ref_videos: 0, ref_audios: 0 },
  i2v: { frame_first: 1, frame_last: 0, ref_images: 0, ref_videos: 0, ref_audios: 0 },
  l2v: { frame_first: 0, frame_last: 1, ref_images: 0, ref_videos: 0, ref_audios: 0 },
  fl2v: { frame_first: 1, frame_last: 1, ref_images: 0, ref_videos: 0, ref_audios: 0 },
  ref: { frame_first: 0, frame_last: 0, ref_images: 1, ref_videos: 1, ref_audios: 1 },
};

const ACTIVE_STYLE = {
  frame_first: { color: "#9e7a4a", bgcolor: "#5e4a2c" },
  frame_last: { color: "#9e7a4a", bgcolor: "#5e4a2c" },
  ref_images: { color: "#4a7f9e", bgcolor: "#2c4a5e" },
  ref_videos: { color: "#4a9e6a", bgcolor: "#2c5e3c" },
  ref_audios: { color: "#6a4a9e", bgcolor: "#3c2c5e" },
};

const GREY_COLOR = "#333333";
const GREY_BG = "#181818";
const MASK_ALPHA = 0.62;

function slotGroup(name) {
  if (name === "first_frame") return "frame_first";
  if (name === "last_frame") return "frame_last";
  if (name === "ref_images") return "ref_images";
  if (/^ref_video(_audio)?_\d+$/.test(name || "")) return "ref_videos";
  // 旧打包口兼容灰显
  if (name === "ref_videos") return "ref_videos";
  if (/^ref_audio_\d+$/.test(name || "") || name === "ref_audios") return "ref_audios";
  return null;
}

function getLink(graph, linkId) {
  if (!graph || linkId == null) return null;
  if (graph.links?.get) return graph.links.get(linkId);
  return graph.links?.[linkId] ?? null;
}

function linkOriginId(graph, node, inp) {
  if (!inp || inp.link == null) return null;
  const link = getLink(graph, inp.link);
  return link ? link.origin_id : null;
}

function nodeIndex(graph) {
  const map = new Map();
  for (const n of graph._nodes || []) map.set(n.id, n);
  return map;
}

function collectUpstream(graph, originId, byId, maxDepth = 6) {
  const out = new Set();
  if (originId == null) return out;
  const q = [[originId, 0]];
  while (q.length) {
    const [id, d] = q.shift();
    if (out.has(id) || d > maxDepth) continue;
    out.add(id);
    const n = byId.get(id);
    if (!n) continue;
    for (const inp of n.inputs || []) {
      if (inp.link == null) continue;
      const link = getLink(graph, inp.link);
      if (link && !out.has(link.origin_id)) q.push([link.origin_id, d + 1]);
    }
  }
  return out;
}

function ensureOrig(n) {
  if (!n._yixuanOrig) {
    n._yixuanOrig = {
      color: n.color,
      bgcolor: n.bgcolor,
      titleColor: n.titleColor,
      draw: n.onDrawForeground,
    };
  }
}

function paintActive(n, style) {
  ensureOrig(n);
  n.color = style.color;
  n.bgcolor = style.bgcolor;
  if (n.titleColor !== undefined) n.titleColor = "#dddddd";
  if (n._yixuanPainted !== "active") {
    n.onDrawForeground = n._yixuanOrig.draw;
    n._yixuanPainted = "active";
  }
}

function paintGrey(n) {
  ensureOrig(n);
  n.color = GREY_COLOR;
  n.bgcolor = GREY_BG;
  if (n.titleColor !== undefined) n.titleColor = "#3f3f3f";
  if (n._yixuanPainted === "grey") return;
  n._yixuanPainted = "grey";
  const origDraw = n._yixuanOrig.draw;
  n.onDrawForeground = function (ctx) {
    if (origDraw) origDraw.call(this, ctx);
    ctx.save();
    ctx.globalAlpha = MASK_ALPHA;
    ctx.fillStyle = "#0a0a0a";
    const th =
      (typeof LiteGraph !== "undefined" && LiteGraph.NODE_TITLE_HEIGHT) || 30;
    ctx.fillRect(-10, -th - 2, this.size[0] + 20, this.size[1] + th + 4);
    ctx.globalAlpha = MASK_ALPHA * 0.9;
    ctx.fillStyle = "#c8c8c8";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("当前模式不使用", this.size[0] / 2, this.size[1] / 2);
    ctx.restore();
  };
}

function restoreNatural(n) {
  if (!n._yixuanOrig) return;
  n.color = n._yixuanOrig.color;
  n.bgcolor = n._yixuanOrig.bgcolor;
  if (n.titleColor !== undefined) n.titleColor = n._yixuanOrig.titleColor;
  n.onDrawForeground = n._yixuanOrig.draw;
  delete n._yixuanOrig;
  delete n._yixuanPainted;
  if (n._yixuanExecMode != null) {
    n.mode = n._yixuanExecMode;
    delete n._yixuanExecMode;
  }
}

function applyOnce(node, modeWidget) {
  const g = app.graph;
  if (!g) return;
  const mode = modeWidget.value;
  const cfg = MODE_ACTIVE[mode];
  if (!cfg) return;

  const byId = nodeIndex(g);
  const activeMap = new Map();
  const greySet = new Set();

  for (const inp of node.inputs || []) {
    const group = slotGroup(inp.name);
    if (!group) continue;
    const src = linkOriginId(g, node, inp);
    if (src == null) continue;
    const chain = collectUpstream(g, src, byId, 6);
    if (cfg[group]) {
      for (const id of chain) activeMap.set(id, group);
    } else {
      for (const id of chain) greySet.add(id);
    }
  }
  for (const id of activeMap.keys()) greySet.delete(id);

  const sig = `${mode}|a:${[...activeMap.keys()].sort().join(",")}|g:${[...greySet].sort().join(",")}`;
  if (node._yixuanSig === sig) return;
  node._yixuanSig = sig;

  for (const n of g._nodes || []) {
    if (n._yixuanExecMode != null) {
      n.mode = n._yixuanExecMode;
      delete n._yixuanExecMode;
    }
    if (activeMap.has(n.id)) {
      paintActive(n, ACTIVE_STYLE[activeMap.get(n.id)] || ACTIVE_STYLE.ref_images);
    } else if (greySet.has(n.id)) {
      paintGrey(n);
    } else if (n._yixuanOrig) {
      restoreNatural(n);
    }
  }
  g.setDirtyCanvas?.(true, true);
}

function bindMultimode(node) {
  if (!node || node._yixuanModeBound) return;
  const isWrapper =
    node.comfyClass === "YixuAnH3MultiMode" || node.type === "YixuAnH3MultiMode";
  if (!isWrapper) return;

  const modeWidget = (node.widgets || []).find((w) => w.name === "mode");
  if (!modeWidget) return;
  node._yixuanModeBound = true;

  let timer = 0;
  const schedule = () => {
    if (timer) return;
    timer = requestAnimationFrame(() => {
      timer = 0;
      applyOnce(node, modeWidget);
    });
  };

  const prev = modeWidget.callback;
  modeWidget.callback = function () {
    if (prev) prev.apply(this, arguments);
    node._yixuanSig = null;
    schedule();
  };

  const owc = node.onWidgetChanged;
  node.onWidgetChanged = function (name) {
    const r = owc?.apply(this, arguments);
    if (name === "mode") {
      node._yixuanSig = null;
      schedule();
    }
    return r;
  };

  const oc = node.onConnectionsChange;
  node.onConnectionsChange = function () {
    if (oc) oc.apply(this, arguments);
    node._yixuanSig = null;
    schedule();
  };

  schedule();
}

app.registerExtension({
  name: "Project Contributor.H3.ModeLink",
  async nodeCreated(node) {
    bindMultimode(node);
  },
  async loadedGraphNode(node) {
    bindMultimode(node);
  },
});
