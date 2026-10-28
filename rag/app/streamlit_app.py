from __future__ import annotations

import html
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import streamlit as st

from tcm_agent import GroundedRAGGenerator, TCMConsultAgent, load_records
from tcm_agent.config import DEFAULT_KB_PATH, DEFAULT_SOURCED_KB_PATH
from tcm_agent.ledger import HashChainLedger
from tcm_agent.llm_providers import PROVIDER_PRESETS, list_provider_models, make_generator
from tcm_agent.query_understanding import SYNONYM_GROUPS
from tcm_agent.safety import RED_FLAG_KEYWORDS, is_negated, normalize


st.set_page_config(
    page_title="中医问诊辅助系统",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
  :root {
    --canvas: #f7f7f2;
    --surface: #ffffff;
    --surface-soft: #f1f4ef;
    --ink: #24342d;
    --muted: #5f7067;
    --line: #dde5dd;
    --green: #286653;
    --green-dark: #1e4c3f;
    --green-pale: #e8f1eb;
    --amber: #7d5a28;
    --amber-pale: #f8f2e6;
    --red: #9f4138;
    --red-pale: #fbefed;
  }
  html, body, [class*="css"] {
    font-family: "Segoe UI", "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
  }
  .stApp {
    background: var(--canvas);
    color: var(--ink);
    font-size: 14px;
  }
  .block-container {
    max-width: 1380px;
    padding-top: 1.15rem;
    padding-bottom: 3.2rem;
  }
  header[data-testid="stHeader"] { background: transparent; }
  .stDeployButton { display: none !important; }
  div[data-testid="stAppDeployButton"] { display: none !important; }
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; }

  [data-testid="stSidebar"] {
    background: #fbfaf6;
    border-right: 1px solid var(--line);
  }
  [data-testid="stSidebar"] .stMarkdown p,
  [data-testid="stSidebar"] label {
    font-size: 13px;
  }

  .tcm-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    margin-bottom: 22px;
  }
  .tcm-brand {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .tcm-brand-mark {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: var(--green);
    color: #fff;
    font-size: 24px;
    font-weight: 600;
    line-height: 1;
  }
  .tcm-brand-name {
    font-size: 15px;
    font-weight: 700;
    color: var(--ink);
  }
  .tcm-brand-sub {
    margin-top: 1px;
    color: var(--muted);
    font-size: 12px;
  }
  .tcm-demo-label {
    padding: 5px 11px;
    border: 1px solid var(--line);
    border-radius: 999px;
    color: var(--muted);
    background: var(--surface);
    font-size: 12px;
    white-space: nowrap;
  }
  .tcm-intro {
    margin: 10px 0 20px;
  }
  .tcm-kicker {
    color: var(--green);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.075em;
  }
  .tcm-intro h1 {
    margin: 6px 0 7px;
    font-size: clamp(29px, 3.1vw, 38px);
    line-height: 1.24;
    letter-spacing: -0.03em;
    color: var(--ink);
  }
  .tcm-intro p {
    max-width: 760px;
    margin: 0;
    color: var(--muted);
    font-size: 14px;
  }
  .tcm-status-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 0 0 16px;
    margin-bottom: 18px;
    border-bottom: 1px solid var(--line);
  }
  .tcm-chip {
    display: inline-flex;
    align-items: center;
    padding: 5px 11px;
    border-radius: 999px;
    border: 1px solid var(--line);
    background: var(--surface);
    color: #4f6157;
    font-size: 12px;
  }
  .tcm-chip::before {
    content: "";
    width: 7px;
    height: 7px;
    margin-right: 6px;
    border-radius: 50%;
    background: #648b6e;
  }
  .tcm-chip.warn::before { background: #b68a4a; }
  .tcm-section-heading {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 9px;
  }
  .tcm-section-heading h3 {
    margin: 0;
    font-size: 17px;
    color: var(--ink);
  }
  .tcm-section-heading span {
    color: var(--muted);
    font-size: 12px;
  }

  div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface);
    border-color: var(--line) !important;
    border-radius: 15px;
  }
  div[data-testid="stForm"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 13px;
    padding: 0.7rem 0.8rem 0.15rem;
  }
  div[data-testid="stChatMessage"] {
    background: var(--surface-soft);
    border: 1px solid #e7ebe6;
    border-radius: 12px;
    padding: 0.25rem 0.55rem;
  }
  div[data-testid="stChatMessage"] p {
    color: var(--ink);
    font-size: 14px;
  }
  .stButton > button,
  .stDownloadButton > button,
  .stFormSubmitButton > button {
    min-height: 44px;
    border-radius: 9px;
    font-size: 14px;
    font-weight: 600;
  }
  .stButton > button:focus-visible,
  .stDownloadButton > button:focus-visible,
  .stFormSubmitButton > button:focus-visible,
  textarea:focus-visible,
  input:focus-visible {
    outline: 3px solid rgba(40, 102, 83, 0.28) !important;
    outline-offset: 2px !important;
  }
  textarea, input {
    font-size: 14px !important;
  }
  .stButton > button[kind="primary"],
  .stFormSubmitButton > button[kind="primary"],
  .stDownloadButton > button[kind="primary"] {
    background: var(--green) !important;
    border-color: var(--green) !important;
    color: #fff !important;
  }

  .tcm-panel {
    padding: 16px 18px;
    border-radius: 15px;
    border: 1px solid var(--line);
    background: var(--surface);
  }
  .tcm-safety {
    background: #fffdfa;
    border-color: #eee5d5;
  }
  .tcm-danger {
    background: var(--red-pale);
    border-color: #f0d9d5;
    color: #803b34;
  }
  .tcm-panel-title {
    margin: 0 0 6px;
    font-size: 15px;
    font-weight: 700;
    color: var(--ink);
  }
  .tcm-panel-copy {
    margin: 0;
    font-size: 13px;
    line-height: 1.65;
    color: #5f7067;
  }
  .tcm-symptom-list {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    margin: 4px 0 14px;
  }
  .tcm-symptom {
    display: inline-block;
    padding: 3px 9px;
    border: 1px solid #dbe7dd;
    border-radius: 999px;
    background: #f1f5f0;
    color: #3f604f;
    font-size: 12px;
  }
  .tcm-symptom.negative {
    border-color: #dfe3db;
    background: #f5f5f1;
    color: #6b746d;
  }
  .tcm-candidate {
    padding: 12px 0 4px;
    border-top: 1px solid var(--line);
  }
  .tcm-candidate:first-of-type { border-top: 0; padding-top: 4px; }
  .tcm-candidate-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 10px;
  }
  .tcm-candidate-name {
    margin: 0;
    color: var(--ink);
    font-size: 15px;
    font-weight: 700;
  }
  .tcm-candidate-meta {
    color: var(--muted);
    font-size: 12px;
    margin-top: 2px;
  }
  .tcm-rank {
    padding: 2px 8px;
    border-radius: 999px;
    background: var(--green-pale);
    color: var(--green);
    font-size: 12px;
    white-space: nowrap;
  }
  .tcm-scorebar {
    height: 5px;
    margin: 10px 0 5px;
    border-radius: 999px;
    background: #e9eee8;
    overflow: hidden;
  }
  .tcm-scorebar > span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #4f8b75, #276653);
  }
  .tcm-score-note {
    color: var(--muted);
    font-size: 12px;
  }
  .tcm-review {
    display: inline-block;
    margin-top: 8px;
    padding: 3px 8px;
    border: 1px solid #f0dfca;
    border-radius: 6px;
    background: var(--amber-pale);
    color: var(--amber);
    font-size: 12px;
  }
  .tcm-evidence {
    margin: 9px 0 0;
    color: #53645a;
    font-size: 12px;
    line-height: 1.55;
  }
  details.tcm-source-details {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--line);
  }
  details.tcm-source-details summary {
    cursor: pointer;
    color: var(--green);
    font-size: 12px;
    font-weight: 600;
  }
  .tcm-source-copy {
    margin-top: 7px;
    color: #5f7067;
    font-size: 12px;
    line-height: 1.55;
  }
  .tcm-footer {
    margin-top: 28px;
    color: #5f7067;
    font-size: 12px;
    text-align: center;
  }

  @media (max-width: 900px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .tcm-header { align-items: flex-start; }
    .tcm-demo-label { font-size: 11px; }
    .tcm-intro h1 { font-size: 30px; }
    .tcm-status-list { gap: 6px; }
    .tcm-chip { font-size: 11px; }
    .tcm-panel { padding: 14px; }
  }
  @media (max-width: 520px) {
    .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
    .tcm-header { gap: 8px; }
    .tcm-brand-name { font-size: 14px; }
    .tcm-brand-sub { font-size: 11px; }
    .tcm-brand-mark { width: 38px; height: 38px; }
    .tcm-demo-label { padding: 4px 8px; }
    .tcm-intro h1 { font-size: 27px; }
    .tcm-intro p { font-size: 13px; }
    .tcm-section-heading h3 { font-size: 16px; }
    .tcm-panel-copy { font-size: 12px; }
  }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

EXAMPLES = {
    "胃胀与反酸": "最近胃胀，打嗝有酸腐味，不想吃饭",
    "怕冷与发热": "怕冷，发热轻，流清鼻涕，不渴",
    "体验安全分流": "胸痛，呼吸困难",
}


@st.cache_data(show_spinner=False)
def get_records(kb_path: str):
    return load_records(Path(kb_path))


def reset_session() -> None:
    st.session_state.state = None
    st.session_state.agent = None
    st.session_state.current_question = None
    st.session_state.messages = []
    st.session_state.agent_config = None


def ensure_agent(retrieval_mode: str, kb_path: str) -> TCMConsultAgent:
    config = (str(kb_path), retrieval_mode)
    if st.session_state.get("agent") is None or st.session_state.get("agent_config") != config:
        if st.session_state.get("state") is not None:
            reset_session()
        st.session_state.agent = TCMConsultAgent(
            get_records(str(kb_path)),
            max_turns=4,
            retrieval_mode=retrieval_mode,
        )
        st.session_state.agent_config = config
    return st.session_state.agent


def provider_available(provider: str) -> bool:
    return make_generator(provider, max_tokens=8).available


def default_provider() -> str:
    for key in PROVIDER_PRESETS:
        if provider_available(key):
            return key
    return "deepseek"


def start_consult(
    agent: TCMConsultAgent,
    text: str,
    llm=None,
    use_llm_slots: bool = False,
) -> None:
    st.session_state.state = agent.start(text, llm=llm, use_llm_slots=use_llm_slots)
    st.session_state.messages.append(("用户", text))
    st.session_state.current_question = agent.next_question(st.session_state.state)


def display_review_status(value: str | None) -> str:
    value = (value or "").strip()
    if "安全优先" in value:
        return "安全优先"
    if not value:
        return "来源信息以记录字段为准"
    if "待" in value or "未登记" in value:
        return "来源信息已登记"
    return value


def render_hero(
    llm_label: str,
    llm_ready: bool,
    kb_label: str,
    retrieval_label: str,
    source_ready: bool,
) -> None:
    source_label = "来源：来源版（来源字段可追溯）" if source_ready else "来源：基础库（来源字段见记录）"
    llm_class = "" if llm_ready else " warn"
    source_class = "" if source_ready else " warn"
    st.markdown(
        '<div class="tcm-header">'
        '<div class="tcm-brand">'
        '<div class="tcm-brand-mark" aria-hidden="true">+</div>'
        "<div><div class=\"tcm-brand-name\">中医问诊辅助系统</div>"
        '<div class="tcm-brand-sub">学习演示原型 · 本地知识库</div></div>'
        "</div>"
        '<div class="tcm-demo-label">仅作学习与竞赛演示</div>'
        "</div>"
        '<div class="tcm-intro">'
        '<div class="tcm-kicker">TCM HEALTH ASSISTANT</div>'
        "<h1>描述身体感受，查看问诊线索</h1>"
        "<p>通过多轮问答整理症状与知识线索；系统只给出候选方向，不提供诊断或处方。</p>"
        "</div>"
        '<div class="tcm-status-list">'
        f'<span class="tcm-chip{llm_class}">大模型：{html.escape(llm_label)}</span>'
        f'<span class="tcm-chip">知识库：{html.escape(kb_label)}</span>'
        f'<span class="tcm-chip">检索：{html.escape(retrieval_label)}</span>'
        f'<span class="tcm-chip{source_class}">{html.escape(source_label)}</span>'
        "</div>",
        unsafe_allow_html=True,
    )


def negative_clues(text: str, positive_terms: list[str]) -> list[str]:
    normalized = normalize(text)
    positive = set(positive_terms)
    clues: list[str] = []
    for canonical, variants in SYNONYM_GROUPS.items():
        if canonical in positive:
            continue
        if any(
            normalize(variant) in normalized and is_negated(normalized, normalize(variant))
            for variant in variants
        ):
            clues.append(f"无{canonical}")
    for keyword in RED_FLAG_KEYWORDS:
        normalized_keyword = normalize(keyword)
        if (
            normalized_keyword in normalized
            and is_negated(normalized, normalized_keyword)
            and f"无{keyword}" not in clues
        ):
            clues.append(f"无{keyword}")
    return clues


def render_slot_panel(state) -> None:
    negatives = negative_clues(state.combined_text(), state.query_terms)
    chips: list[str] = []
    for term in state.query_terms:
        chips.append(f'<span class="tcm-symptom">{html.escape(term)}</span>')
    for slot, values in state.slots.items():
        value = "、".join(values)
        chips.append(f'<span class="tcm-symptom">{html.escape(slot)}：{html.escape(value)}</span>')
    for clue in negatives:
        chips.append(f'<span class="tcm-symptom negative">{html.escape(clue)}</span>')
    if not chips:
        chips.append('<span class="tcm-symptom negative">暂未抽取到明确线索</span>')
    st.markdown(
        '<div class="tcm-section-heading">'
        "<h3>当前识别线索</h3><span>来自本轮对话</span></div>"
        '<div class="tcm-symptom-list">'
        + "".join(chips)
        + "</div>",
        unsafe_allow_html=True,
    )
    if state.corrections:
        st.caption("术语纠正：" + "、".join(state.corrections))
    elif getattr(state, "slot_error", ""):
        st.caption("槽位增强失败，已保留规则抽取结果。")


def render_match_cards(agent: TCMConsultAgent, state) -> None:
    if state.red_flags:
        return
    matches = agent.current_matches(state)
    st.markdown(
        '<div class="tcm-section-heading">'
        "<h3>候选方向</h3><span>按检索相关度排序</span></div>"
        '<div class="tcm-panel-copy">候选不是诊断结论，相关度也不是诊断置信度。</div>',
        unsafe_allow_html=True,
    )
    if not matches:
        st.caption("当前信息不足，暂无候选方向。")
        return
    for index, (record, score) in enumerate(matches, start=1):
        evidence = (record.differentiation_points or "").strip()
        if not evidence or "待补充" in evidence:
            evidence = "当前记录暂无可直接展示的鉴别要点。"
        if record.source_title and record.source_url:
            source = f"{record.source_title}：{record.source_url}"
        elif record.source_title:
            source = record.source_title
        else:
            source = "当前记录来自基础演示知识库，不附独立来源链接；仅用于学习与演示。"
        width = max(3.0, min(score, 1.0) * 100)
        review_status = (
            display_review_status(record.review_status)
            if record.source_title or record.source_url
            else "基础演示记录"
        )
        card = (
            '<article class="tcm-candidate">'
            '<div class="tcm-candidate-top"><div>'
            f'<h4 class="tcm-candidate-name">{index}. {html.escape(record.name)}</h4>'
            f'<div class="tcm-candidate-meta">{html.escape(record.category or "未分类")}</div>'
            f'</div><span class="tcm-rank">候选 {index}</span></div>'
            f'<div class="tcm-scorebar"><span style="width:{width:.0f}%"></span></div>'
            f'<div class="tcm-score-note">检索相关度 {score:.3f} · 不是诊断置信度</div>'
            f'<div class="tcm-review">{html.escape(review_status)}</div>'
            f'<p class="tcm-evidence">匹配线索：{html.escape(evidence)}</p>'
            '<details class="tcm-source-details">'
            "<summary>查看来源与审核说明</summary>"
            f'<div class="tcm-source-copy">{html.escape(source)}<br>'
            "候选条目展示来源或基础演示标识，本结果不构成诊断或处方。</div>"
            "</details>"
            "</article>"
        )
        st.markdown(card, unsafe_allow_html=True)


def render_safety_panel(red_flags: list[str] | None = None) -> None:
    red_flags = red_flags or []
    if red_flags:
        chips = "".join(
            f'<span class="tcm-symptom negative">{html.escape(item)}</span>'
            for item in red_flags
        )
        st.markdown(
            '<div class="tcm-panel tcm-danger">'
            '<div class="tcm-panel-title">红旗优先</div>'
            '<p class="tcm-panel-copy">检测到需要优先关注的症状。系统已停止普通证候解释、'
            "调理建议和方剂信息，请优先寻求线下医疗帮助。</p>"
            f'<div class="tcm-symptom-list">{chips}</div>'
            '<p class="tcm-panel-copy">本系统不能替代专业急救判断。</p></div>',
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        '<div class="tcm-panel tcm-safety">'
        '<div class="tcm-panel-title">安全提醒</div>'
        '<p class="tcm-panel-copy">若出现胸痛、呼吸困难、呕血、黑便、持续高热、意识异常等情况，'
        "请及时线下就医。方剂信息仅作传统知识参考，须经专业医师指导。</p></div>",
        unsafe_allow_html=True,
    )


def render_summary(agent: TCMConsultAgent, state, llm=None) -> None:
    st.markdown("### 问诊摘要")
    answer = GroundedRAGGenerator().render_with_llm(
        state.combined_text(),
        state.slots,
        agent.current_matches(state),
        llm=llm,
        known_names=[record.name for record in agent.records],
    )
    st.markdown(answer.text)
    if answer.note:
        if answer.used_llm:
            st.caption(answer.note)
        else:
            st.info(answer.note)
    st.download_button(
        "下载问诊报告（Markdown）",
        data=answer.text,
        file_name="中医问诊辅助报告.md",
        mime="text/markdown",
        type="primary",
        use_container_width=True,
    )


def render_current_summary(state) -> None:
    negatives = negative_clues(state.combined_text(), state.query_terms)
    st.markdown(
        '<div class="tcm-panel">'
        '<div class="tcm-panel-title">当前问诊记录</div>'
        f'<p class="tcm-panel-copy">已整理 {len(state.query_terms)} 项阳性线索'
        f'、{len(negatives)} 项否定信息。完成追问后可下载完整报告；'
        "报告会保留来源范围、安全提示和非诊断声明。</p></div>",
        unsafe_allow_html=True,
    )


def render_ledger_panel(ledger_path: Path, agent: TCMConsultAgent, state) -> None:
    with st.expander("本地存证（简化原型）", expanded=False):
        st.caption(
            "本地 SHA-256 哈希链支持记录追加、完整性校验和篡改检测。"
        )
        ledger_blocks = HashChainLedger(ledger_path).blocks
        st.metric("当前链长度", f"{len(ledger_blocks)} 块")
        if st.button("追加本次小结哈希", use_container_width=True, key="ledger_append"):
            ledger = HashChainLedger(ledger_path)
            local_answer = GroundedRAGGenerator().render(
                state.combined_text(),
                state.slots,
                agent.current_matches(state),
            )
            block = ledger.append(
                {"summary": local_answer, "terms": state.query_terms},
                label="问诊小结",
            )
            st.success(f"已写入第 {block['index']} 块，block_hash={block['block_hash'][:16]}...")
            st.rerun()
        if st.button("校验链完整性", use_container_width=True, key="ledger_verify"):
            ledger = HashChainLedger(ledger_path)
            ok, errors = ledger.verify()
            if ok:
                st.success(f"链校验通过，共 {len(ledger.blocks)} 块")
            else:
                st.error("链校验未通过：" + "；".join(errors))
        st.markdown("**历史存证记录**")
        if not ledger_blocks:
            st.caption("暂无历史区块。")
            return
        for position, block in enumerate(ledger_blocks):
            previous_hash = (
                ledger_blocks[position - 1].get("block_hash", "") if position > 0 else None
            )
            if position == 0:
                link_status = "创世块（previous 为全 0）"
            elif block.get("previous_hash") == previous_hash:
                link_status = "与上一块一致"
            else:
                link_status = "与上一块不一致"
            with st.container(border=True):
                st.markdown(
                    f"**区块 {block.get('index', position)}** · "
                    f"{block.get('timestamp', '')} · {link_status}"
                )
                st.caption(
                    f"摘要（内容指纹）：{block.get('label', '记录')} · "
                    f"{str(block.get('payload_hash', ''))[:12]}…"
                )
                st.code(
                    f"previous_hash: {block.get('previous_hash', '')}\n"
                    f"block_hash:    {block.get('block_hash', '')}",
                    language="text",
                    wrap_lines=True,
                )
        st.caption("历史区块只保存 payload_hash（内容指纹），不保存问诊原文；未做任何伪造。")


if "state" not in st.session_state:
    reset_session()

with st.sidebar:
    st.markdown("### 运行设置")
    kb_label = st.selectbox(
        "知识库",
        ["基础15条（含方剂名，演示用）", "来源版20条（带来源与审核状态）"],
        index=0,
    )
    kb_path = (
        str(DEFAULT_SOURCED_KB_PATH) if kb_label.startswith("来源版") else str(DEFAULT_KB_PATH)
    )
    source_ready = kb_label.startswith("来源版")

    retrieval_label = st.selectbox("检索模式", ["TF-IDF", "Embedding"], index=0)
    retrieval_mode = "embedding" if retrieval_label == "Embedding" else "tfidf"
    st.caption("Embedding 模式使用本地向量检索实现，无需联网。")

    st.divider()
    st.markdown("**大模型（可插拔）**")
    provider_keys = list(PROVIDER_PRESETS)
    provider = st.selectbox(
        "厂商",
        provider_keys,
        index=provider_keys.index(default_provider()),
        format_func=lambda key: PROVIDER_PRESETS[key]["label"],
    )
    preset = PROVIDER_PRESETS[provider]
    fetched = st.session_state.get(f"models::{provider}") or []
    model_options = list(dict.fromkeys([*preset["models"], *fetched]))
    model_choice = st.selectbox("模型", [*model_options, "自定义输入…"], index=0)
    if model_choice == "自定义输入…":
        model_name = st.text_input(
            "模型名称",
            placeholder="例如 qwen-max / kimi-k3 / 自部署模型名",
        )
    else:
        model_name = model_choice
    if st.button("从厂商获取可用模型", use_container_width=True):
        models, error = list_provider_models(provider)
        if models:
            st.session_state[f"models::{provider}"] = models
            st.rerun()
        else:
            st.warning(f"获取失败：{error}")

    use_llm = st.checkbox(
        "启用大模型生成",
        value=provider_available(provider),
        help="支持 DeepSeek / Kimi / 通义千问等 OpenAI 兼容接口；调用失败或输出不安全时自动回退本地模板。",
    )
    llm = (
        make_generator(provider, model=model_name or preset["default_model"], max_tokens=700)
        if use_llm
        else None
    )
    use_llm_slots = False
    if llm is not None:
        key_state = "已配置" if llm.available else "未配置（将自动回退本地模板）"
        st.caption(f"密钥：{key_state} · 模型：{llm.model}")
        use_llm_slots = st.checkbox(
            "大模型槽位增强（实验）",
            value=False,
            help="用大模型从每轮回答中抽取结构化槽位，失败自动回退规则抽取。",
        )

    st.divider()
    use_ledger = st.checkbox(
        "启用本地哈希链存证（简化原型）",
        value=False,
        help="本地 SHA-256 哈希链支持记录追加、完整性校验和篡改检测。",
    )
    ledger_path = PROJECT_ROOT / "data" / "local_ledger_demo.json"
    st.divider()
    st.caption("安全说明：红旗症状优先就医分流；方剂名称仅为传统知识参考；来源与审核信息见各候选条目。")

agent = ensure_agent(retrieval_mode, kb_path)
llm_label = f"{llm.model}（{preset['label']}）" if llm is not None else "未启用（本地模板）"
llm_ready = llm is not None and llm.available
render_hero(llm_label, llm_ready, kb_label, retrieval_label, source_ready)

pending = st.session_state.pop("pending_initial", None)
if pending:
    start_consult(agent, pending, llm=llm, use_llm_slots=use_llm_slots)
    st.rerun()

if st.session_state.state is None:
    with st.container(key="welcome_panel", border=True):
        st.markdown(
            '<div class="tcm-section-heading"><h3>先从主要不适开始</h3>'
            '<span>不需要自行判断证型</span></div>'
            '<p class="tcm-panel-copy">描述出现了什么、持续多久，也可以选择一个示例体验。</p>',
            unsafe_allow_html=True,
        )
        example_cols = st.columns(len(EXAMPLES))
        for index, (label, text) in enumerate(EXAMPLES.items()):
            if example_cols[index].button(label, use_container_width=True, key=f"example::{index}"):
                st.session_state.pending_initial = text
                st.rerun()
        with st.form("initial_form", clear_on_submit=False):
            initial = st.text_area(
                "主要不适",
                placeholder="例如：最近胃胀，打嗝有酸腐味，不想吃饭",
                height=110,
            )
            submitted = st.form_submit_button(
                "开始问诊",
                type="primary",
                use_container_width=True,
            )
        if submitted:
            cleaned = initial.strip()
            if not cleaned:
                st.warning("请先填写主要不适。")
            else:
                start_consult(agent, cleaned, llm=llm, use_llm_slots=use_llm_slots)
                st.rerun()
        st.markdown(
            '<p class="tcm-panel-copy">请勿填写姓名、电话等身份信息。'
            "本系统是学习与竞赛演示原型，不用于医学诊断或自行用药。</p>"
            '<div class="tcm-panel tcm-safety" style="margin-top:12px;">'
            '<div class="tcm-panel-title">安全提醒</div>'
            '<p class="tcm-panel-copy">若出现胸痛、呼吸困难、呕血、黑便、持续高热、意识异常等情况，'
            "请及时线下就医。可在左上角展开运行设置，切换知识库、检索模式和模型。</p></div>",
            unsafe_allow_html=True,
        )
else:
    state = st.session_state.state
    left, right = st.columns([0.64, 0.36], gap="large")
    with left:
        with st.container(border=True):
            st.markdown(
                '<div class="tcm-section-heading"><h3>问诊对话</h3>'
                '<span>补充症状有助于整理更完整的检索线索</span></div>',
                unsafe_allow_html=True,
            )
            for role, text in st.session_state.messages:
                with st.chat_message("user" if role == "用户" else "assistant"):
                    st.write(text)

            if state.red_flags:
                render_summary(agent, state, llm=llm)
            elif agent.should_stop(state) or st.session_state.current_question is None:
                render_summary(agent, state, llm=llm)
            else:
                question = st.session_state.current_question
                with st.chat_message("assistant"):
                    st.write(question)
                st.caption(
                    f"追问 {min(state.turn_count + 1, agent.max_turns)} / {agent.max_turns}"
                )
                with st.form("answer_form", clear_on_submit=True):
                    answer = st.text_area(
                        "补充回答",
                        height=90,
                        placeholder="可以简单回答，也可以补充更多症状；不确定的内容可以留空",
                    )
                    submitted = st.form_submit_button(
                        "继续问诊",
                        type="primary",
                        use_container_width=True,
                    )
                if submitted:
                    cleaned = answer.strip()
                    if not cleaned:
                        st.warning("回答不能为空。")
                    else:
                        state.add_answer(
                            question,
                            cleaned,
                            llm=llm,
                            use_llm_slots=use_llm_slots,
                        )
                        st.session_state.messages.append(("智能体", question))
                        st.session_state.messages.append(("用户", cleaned))
                        st.session_state.current_question = agent.next_question(state)
                        st.rerun()
            st.button("重新开始", on_click=reset_session, use_container_width=True)

    with right:
        render_safety_panel(state.red_flags)
        if state.red_flags:
            render_slot_panel(state)
        else:
            with st.container(border=True):
                render_slot_panel(state)
            with st.container(border=True):
                render_match_cards(agent, state)
            render_current_summary(state)
            if use_ledger:
                render_ledger_panel(ledger_path, agent, state)

st.markdown(
    '<div class="tcm-footer">中医问诊辅助系统 · 学习演示原型 · '
    "不提供诊断与处方 · 全部内容仅用于学习与健康咨询辅助</div>",
    unsafe_allow_html=True,
)
