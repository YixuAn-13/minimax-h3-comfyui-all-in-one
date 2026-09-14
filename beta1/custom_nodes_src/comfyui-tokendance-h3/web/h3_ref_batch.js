/**
 * Project Contributor H3 参考视频组 / 参考音频组 —— 动态扩槽 (对齐 XB_BatchImages UX)
 *
 * 视频组: 视频1 + 音轨1; 视频1 接上后冒 视频2+音轨2 ... 最多 3
 * 音频组: 音频1; 接上后冒 音频2 ... 最多 3
 * 断开中间空槽会自动收拢重编号。
 */
import { app } from "../../scripts/app.js";

const MAX_AV = 3;

function isVideoSlot(inp) {
  return inp?.name && /^视频\d+$/.test(inp.name);
}
function isVideoAudioSlot(inp) {
  return inp?.name && /^音轨\d+$/.test(inp.name);
}
function isAudioSlot(inp) {
  return inp?.name && /^音频\d+$/.test(inp.name);
}

function ensureVideoPair(node, n) {
  const names = (node.inputs || []).map((i) => i.name);
  if (!names.includes(`视频${n}`)) node.addInput(`视频${n}`, "IMAGE");
  if (!names.includes(`音轨${n}`)) node.addInput(`音轨${n}`, "AUDIO");
}

function linkOf(graph, id) {
  if (!graph) return null;
  return graph.links?.get ? graph.links.get(id) : graph.links?.[id] ?? null;
}

function setLinkTarget(graph, linkId, nodeId, slotIdx, input) {
  const link = linkOf(graph, linkId);
  if (link) {
    link.target_id = nodeId;
    link.target_slot = slotIdx;
  }
  input.link = linkId;
}

function renumberVideos(node) {
  const g = node.graph;
  if (!g) return;
  const audioByNum = {};
  for (const inp of node.inputs || []) {
    if (isVideoAudioSlot(inp)) {
      const num = parseInt(inp.name.slice(2), 10);
      audioByNum[num] = inp.link;
    }
  }
  const pairs = [];
  for (const inp of node.inputs || []) {
    if (isVideoSlot(inp)) {
      const num = parseInt(inp.name.slice(2), 10);
      pairs.push({ vLink: inp.link, aLink: audioByNum[num] ?? null });
    }
  }
  for (let i = (node.inputs || []).length - 1; i >= 0; i--) {
    if (isVideoSlot(node.inputs[i]) || isVideoAudioSlot(node.inputs[i])) {
      node.removeInput(i);
    }
  }
  const kept = pairs.filter((p) => p.vLink != null);
  let nPairs = kept.length === 0 ? 1 : kept.length;
  if (kept.length > 0 && kept.length < MAX_AV) nPairs = kept.length + 1;
  if (kept.length >= MAX_AV) nPairs = MAX_AV;
  for (let n = 1; n <= nPairs; n++) {
    node.addInput(`视频${n}`, "IMAGE");
    node.addInput(`音轨${n}`, "AUDIO");
  }
  for (let n = 1; n <= kept.length; n++) {
    const p = kept[n - 1];
    const vIdx = node.inputs.findIndex((i) => i.name === `视频${n}`);
    const aIdx = node.inputs.findIndex((i) => i.name === `音轨${n}`);
    if (p.vLink != null && vIdx >= 0) setLinkTarget(g, p.vLink, node.id, vIdx, node.inputs[vIdx]);
    if (p.aLink != null && aIdx >= 0) setLinkTarget(g, p.aLink, node.id, aIdx, node.inputs[aIdx]);
  }
}

function stabilizeVideos(node) {
  if (!node.graph || node.__h3_removed) return;
  const inputs = node.inputs || [];
  const vidIdx = [];
  for (let i = 0; i < inputs.length; i++) {
    if (isVideoSlot(inputs[i])) vidIdx.push(i);
  }
  if (vidIdx.length === 0) {
    ensureVideoPair(node, 1);
    return;
  }
  let needRenumber = false;
  for (let di = 0; di < vidIdx.length - 1; di++) {
    if (inputs[vidIdx[di]].link == null) {
      needRenumber = true;
      break;
    }
  }
  const last = inputs[vidIdx[vidIdx.length - 1]];
  const full = last?.link != null;
  if (needRenumber) {
    renumberVideos(node);
  } else if (full && vidIdx.length < MAX_AV) {
    ensureVideoPair(node, vidIdx.length + 1);
  }
  const vids = (node.inputs || []).filter(isVideoSlot);
  const connected = vids.filter((v) => v.link != null).length;
  const empties = vids.length - connected;
  if (empties > 1 || (connected === 0 && vids.length > 1)) {
    renumberVideos(node);
  }
}

function renumberAudios(node) {
  const g = node.graph;
  if (!g) return;
  const links = [];
  for (const inp of node.inputs || []) {
    if (isAudioSlot(inp) && inp.link != null) links.push(inp.link);
  }
  for (let i = (node.inputs || []).length - 1; i >= 0; i--) {
    if (isAudioSlot(node.inputs[i])) node.removeInput(i);
  }
  let n = links.length === 0 ? 1 : links.length;
  if (links.length > 0 && links.length < MAX_AV) n = links.length + 1;
  if (links.length >= MAX_AV) n = MAX_AV;
  for (let i = 1; i <= n; i++) node.addInput(`音频${i}`, "AUDIO");
  for (let i = 0; i < links.length; i++) {
    const idx = node.inputs.findIndex((inp) => inp.name === `音频${i + 1}`);
    if (idx >= 0) setLinkTarget(g, links[i], node.id, idx, node.inputs[idx]);
  }
}

function stabilizeAudios(node) {
  if (!node.graph || node.__h3_removed) return;
  const inputs = node.inputs || [];
  const aIdx = [];
  for (let i = 0; i < inputs.length; i++) {
    if (isAudioSlot(inputs[i])) aIdx.push(i);
  }
  if (aIdx.length === 0) {
    node.addInput("音频1", "AUDIO");
    return;
  }
  let midEmpty = false;
  for (let di = 0; di < aIdx.length - 1; di++) {
    if (inputs[aIdx[di]].link == null) {
      midEmpty = true;
      break;
    }
  }
  const last = inputs[aIdx[aIdx.length - 1]];
  if (midEmpty) {
    renumberAudios(node);
  } else if (last?.link != null && aIdx.length < MAX_AV) {
    node.addInput(`音频${aIdx.length + 1}`, "AUDIO");
  }
  const slots = (node.inputs || []).filter(isAudioSlot);
  const connected = slots.filter((s) => s.link != null).length;
  const empties = slots.length - connected;
  if (empties > 1 || (connected === 0 && slots.length > 1)) {
    renumberAudios(node);
  }
}

function hookNode(nodeType, kind) {
  const orig = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function () {
    const r = orig?.apply(this, arguments);
    const self = this;
    const stabilize = () => {
      if (kind === "video") stabilizeVideos(self);
      else stabilizeAudios(self);
      if (!self.__h3_removed) {
        self.__h3_timer = setTimeout(stabilize, 300);
      }
      self.graph?.setDirtyCanvas(true, true);
    };
    const oc = self.onConnectionsChange;
    self.onConnectionsChange = function () {
      if (oc) oc.apply(this, arguments);
      if (self.__h3_timer) clearTimeout(self.__h3_timer);
      self.__h3_timer = setTimeout(stabilize, 80);
    };
    const or_ = self.onRemoved;
    self.onRemoved = function () {
      self.__h3_removed = true;
      if (self.__h3_timer) clearTimeout(self.__h3_timer);
      if (or_) or_.apply(this, arguments);
    };
    if (kind === "video") {
      if (!(self.inputs || []).some(isVideoSlot)) ensureVideoPair(self, 1);
    } else if (!(self.inputs || []).some(isAudioSlot)) {
      self.addInput("音频1", "AUDIO");
    }
    stabilize();
    return r;
  };
}

app.registerExtension({
  name: "Project Contributor.H3.RefBatch",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData?.name === "YixuAnH3BatchVideos") hookNode(nodeType, "video");
    if (nodeData?.name === "YixuAnH3BatchAudios") hookNode(nodeType, "audio");
  },

  async loadedGraphNode(node) {
    if (node.type === "YixuAnH3BatchVideos") {
      if (!(node.inputs || []).some(isVideoSlot)) ensureVideoPair(node, 1);
    }
    if (node.type === "YixuAnH3BatchAudios") {
      if (!(node.inputs || []).some(isAudioSlot)) node.addInput("音频1", "AUDIO");
    }
  },
});
