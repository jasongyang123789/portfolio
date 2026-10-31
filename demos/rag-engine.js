/* ============================================================
 * rag-engine.js — 真实检索引擎（纯前端、无依赖）
 * 算法管线：
 *   1. 中文 2-gram + 英文词干分词（含停用词过滤）
 *   2. TF-IDF 向量化（构建倒排索引 + IDF 表）
 *   3. BM25 打分（k1=1.5, b=0.75）
 *   4. 混合排序：0.6*BM25归一 + 0.4*余弦相似度(TF-IDF)
 *   5. Rocchio 相关性反馈：👍/👎 真实调整查询向量（α=1 β=0.75 γ=0.15）
 *   6. TextRank 抽取式摘要：句子相似度图 + 幂迭代打分
 * 暴露：window.RAG = { buildIndex, search, feedback, textrank, explain }
 * ============================================================ */
(function () {
  'use strict';

  const STOP = new Set(('的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 自己 这 那 与 及 或 等 对 为 从 而 以 通过 进行 可以 能够 需要 以及 将 把 被 向 让 使 但 并 且 则 其 本 该 各 每 约 应 应当 从事 使用 基于 基于 开展 负责 完成 包括 其中 如下 以下 如有 优先 熟悉 了解 精细 较强 良好 优秀 相关 主要 所有 对于 关于 由于 因此 同时 此外 目前 目前 具有 拥有 担任 工作 岗位 职位 公司 企业 招聘 要求 职责 任职 资格 条件 描述 内容 方面 部分 以下 以上 一些 一定 一定 能够 熟练 掌握 运用 利用 根据 按照 按照 能够 相关 情况 方式 方法 系统 体系 机制 模式 过程 过程中 基础 前提 重要 核心 有效 显著 明显 更加 更加 以及 或者 甚至 尤其是 特别是').split(/\s+/));

  // ---------- 分词 ----------
  function tokenize(text) {
    const t = String(text || '').toLowerCase();
    const tokens = [];
    // 英文/数字词（保留 Agent、RAG、KPI、SQL 等）
    (t.match(/[a-z][a-z0-9+#.]{1,15}|\d{2,}/g) || []).forEach(w => tokens.push(w));
    // 中文 2-gram
    const cn = t.replace(/[^一-鿿]/g, ' ');
    for (const seg of cn.split(/\s+/)) {
      for (let i = 0; i < seg.length - 1; i++) {
        const g = seg.slice(i, i + 2);
        if (!STOP.has(g)) tokens.push(g);
      }
    }
    return tokens.filter(t => t && !STOP.has(t));
  }

  // ---------- 索引 ----------
  // docs: [{id, title, text, meta...}]
  let INDEX = null;
  function buildIndex(docs) {
    const N = docs.length;
    const df = {};            // 词 -> 文档数
    const docTokens = [];     // 每文档词频
    const docLen = [];
    docs.forEach((d, di) => {
      const tf = {};
      tokenize((d.title || '') + ' ' + (d.title || '') + ' ' + (d.text || '')).forEach(w => {
        tf[w] = (tf[w] || 0) + 1;
      });
      docTokens.push(tf);
      docLen.push(Object.values(tf).reduce((a, b) => a + b, 0) || 1);
      for (const w in tf) df[w] = (df[w] || 0) + 1;
    });
    const idf = {};
    for (const w in df) idf[w] = Math.log((N - df[w] + 0.5) / (df[w] + 0.5) + 1);
    // TF-IDF 向量（归一化）
    const vectors = docTokens.map((tf, di) => {
      const v = {};
      let norm = 0;
      for (const w in tf) {
        const x = (1 + Math.log(tf[w])) * idf[w];
        v[w] = x; norm += x * x;
      }
      norm = Math.sqrt(norm) || 1;
      for (const w in v) v[w] /= norm;
      return v;
    });
    INDEX = { docs, N, df, idf, docTokens, docLen, vectors, avgLen: docLen.reduce((a, b) => a + b, 0) / N };
    return INDEX;
  }

  // ---------- BM25 ----------
  function bm25(queryTokens, di) {
    const K1 = 1.5, B = 0.75;
    const tf = INDEX.docTokens[di];
    let s = 0;
    for (const w of queryTokens) {
      if (!tf[w]) continue;
      const f = tf[w];
      s += INDEX.idf[w] * (f * (K1 + 1)) / (f + K1 * (1 - B + B * INDEX.docLen[di] / INDEX.avgLen));
    }
    return s;
  }

  // ---------- 余弦 ----------
  function cosine(qVec, di) {
    const v = INDEX.vectors[di];
    let s = 0;
    for (const w in qVec) if (v[w]) s += qVec[w] * v[w];
    return s; // qVec 已归一化，v 已归一化 → 点积即余弦
  }

  function queryVector(queryTokens) {
    const tf = {};
    queryTokens.forEach(w => tf[w] = (tf[w] || 0) + 1);
    const v = {}; let norm = 0;
    for (const w in tf) {
      if (!INDEX.idf[w]) continue;
      const x = (1 + Math.log(tf[w])) * INDEX.idf[w];
      v[w] = x; norm += x * x;
    }
    norm = Math.sqrt(norm) || 1;
    for (const w in v) v[w] /= norm;
    return v;
  }

  // ---------- 检索（含 Rocchio 反馈状态） ----------
  let feedbackVec = null;   // Rocchio 调整向量（持久于会话）
  let feedbackLog = [];

  function search(query, topK) {
    topK = topK || 6;
    const qTokens = tokenize(query);
    if (!qTokens.length) return { hits: [], qTokens, explain: { note: '分词后无有效词' } };

    let qVec = queryVector(qTokens);
    // Rocchio：叠加历史反馈
    if (feedbackVec) {
      const alpha = 1, beta = 0.75;
      const merged = {};
      for (const w in qVec) merged[w] = alpha * qVec[w];
      for (const w in feedbackVec) merged[w] = (merged[w] || 0) + beta * feedbackVec[w];
      let norm = 0;
      for (const w in merged) norm += merged[w] * merged[w];
      norm = Math.sqrt(norm) || 1;
      for (const w in merged) merged[w] /= norm;
      qVec = merged;
    }

    const scored = [];
    INDEX.docs.forEach((d, di) => {
      const bm = bm25(qTokens, di);
      const cos = cosine(qVec, di);
      const bmN = INDEX.N ? bm : 0;
      // BM25 归一化（除以该查询理论最大值近似）
      const maxBm = Math.max(...INDEX.docs.map((_, dj) => bm25(qTokens, dj)), 1e-9);
      const mixed = 0.6 * (bm / maxBm) + 0.4 * cos;
      if (mixed > 0.01) scored.push({ doc: d, di, bm, cos, mixed, ref: (INDEX.docRef && INDEX.docRef[di]) || '' });
    });
    scored.sort((a, b) => b.mixed - a.mixed);
    const hits = scored.slice(0, topK).map(s => ({
      doc: s.doc, score: s.mixed, bm: s.bm, cos: s.cos,
      hitTerms: qTokens.filter(w => INDEX.docTokens[s.di][w])
    }));
    return {
      hits, qTokens,
      explain: {
        feedbackActive: !!feedbackVec,
        feedbackLog: feedbackLog.slice(-4),
        bm25Params: 'k1=1.5, b=0.75',
        formula: 'score = 0.6·BM25_norm + 0.4·cos(TF-IDF)'
      }
    };
  }

  // ---------- Rocchio 相关性反馈（针对性训练） ----------
  function feedback(docIndexList, queryTokens, positive) {
    // 相关文档词向量 ± 不相关文档词向量
    const gamma = positive ? 0 : 0.15;
    const beta = positive ? 0.75 : 0;
    const adjust = {};
    docIndexList.forEach(di => {
      const v = INDEX.vectors[di];
      for (const w in v) adjust[w] = (adjust[w] || 0) + (positive ? beta : -gamma) * v[w];
    });
    if (!feedbackVec) feedbackVec = {};
    for (const w in adjust) feedbackVec[w] = (feedbackVec[w] || 0) + adjust[w];
    feedbackLog.push({
      positive, docs: docIndexList.map(di => INDEX.docs[di].title || INDEX.docs[di].id),
      topTerms: Object.entries(adjust).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 6).map(x => x[0])
    });
    return feedbackLog[feedbackLog.length - 1];
  }

  function resetFeedback() { feedbackVec = null; feedbackLog = []; }

  // ---------- TextRank 抽取式摘要 ----------
  function textrank(text, topN) {
    topN = topN || 3;
    const sents = String(text || '')
      .replace(/\s+/g, ' ')
      .split(/(?<=[。；;！!？?])\s*/)
      .map(s => s.trim()).filter(s => s.length >= 12 && s.length <= 220);
    if (sents.length <= topN) return sents;
    const tokSents = sents.map(tokenize);
    // 句子相似度（共词/长度平滑）
    const sim = (a, b) => {
      const A = new Set(a), B = new Set(b);
      let inter = 0;
      A.forEach(w => { if (B.has(w)) inter++; });
      return inter / (A.size + B.size + 1e-9);
    };
    const W = sents.map(() => sents.map(() => 0));
    for (let i = 0; i < sents.length; i++)
      for (let j = i + 1; j < sents.length; j++) {
        const w = sim(tokSents[i], tokSents[j]);
        W[i][j] = W[j][i] = w;
      }
    // 幂迭代
    let score = sents.map(() => 1);
    const d = 0.85;
    for (let it = 0; it < 25; it++) {
      const next = sents.map((_, i) => (1 - d));
      for (let i = 0; i < sents.length; i++) {
        let outSum = 0;
        for (let j = 0; j < sents.length; j++) if (W[j][i]) outSum += W[j][i];
        if (outSum) for (let j = 0; j < sents.length; j++) if (W[i][j]) next[j] += d * W[i][j] / outSum * score[i];
      }
      score = next;
    }
    return sents.map((s, i) => ({ s, r: score[i] }))
      .sort((a, b) => b.r - a.r).slice(0, topN)
      .map(x => x.s);
  }

  // ---------- 导出 ----------
  window.RAG = { buildIndex, search, feedback, resetFeedback, textrank, tokenize,
                 getIndex: () => INDEX, setDocRef: (ref) => { if (INDEX) INDEX.docRef = ref; } };
})();
