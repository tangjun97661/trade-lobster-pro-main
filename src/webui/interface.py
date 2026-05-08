import base64
import mimetypes
import os
import gradio as gr

from src.webui.webui_manager import WebuiManager
from src.webui.components.agent_settings_tab import create_agent_settings_tab
from src.webui.components.browser_settings_tab import create_browser_settings_tab
from src.webui.components.browser_use_agent_tab import create_browser_use_agent_tab
from src.webui.components.deep_research_agent_tab import create_deep_research_agent_tab
from src.webui.components.skills_tab import create_skills_tab
from src.webui.components.region_config import get_provinces, get_cities, get_region_skills, get_region_name, get_provinces_with_keys, get_cities_with_keys

theme_map = {
    "Default": gr.themes.Default(),
    "Soft": gr.themes.Soft(),
    "Monochrome": gr.themes.Monochrome(),
    "Glass": gr.themes.Glass(),
    "Origin": gr.themes.Origin(),
    "Citrus": gr.themes.Citrus(),
    "Ocean": gr.themes.Ocean(),
    "Base": gr.themes.Base()
}


def get_logo_path():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    candidates = [
        "/app/config/lobster-logo.png",
        "/app/config/lobster-logo.jpg",
        "/app/config/lobster-logo.jpeg",
        "/app/config/lobster-logo.webp",
        "/app/config/logo.png",
        "/app/config/logo.jpg",
        "/app/config/logo.jpeg",
        "/app/config/logo.webp",
        os.path.join(project_root, "assets", "lobster-logo.png"),
        os.path.join(project_root, "assets", "lobster-logo.jpg"),
        os.path.join(project_root, "assets", "lobster-logo.jpeg"),
        os.path.join(project_root, "assets", "lobster-logo.webp"),
        os.path.join(project_root, "assets", "logo.png"),
        os.path.join(project_root, "assets", "logo.jpg"),
        os.path.join(project_root, "assets", "logo.jpeg"),
        os.path.join(project_root, "assets", "logo.webp"),
        os.path.join(project_root, "assets", "web-ui.png"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def get_logo_data_uri():
    logo_path = get_logo_path()
    if not logo_path:
        return None
    mime_type, _ = mimetypes.guess_type(logo_path)
    if not mime_type:
        mime_type = "image/png"
    with open(logo_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def render_brand_html():
    logo_data_uri = get_logo_data_uri()
    if logo_data_uri:
        return f"""
        <div class="app-brand">
            <img src="{logo_data_uri}" alt="公共资源交易龙虾 Logo">
            <div class="app-brand-title">
                <h1>公共资源交易龙虾</h1>
                <p>南通公共资源交易大脑代理智能体</p>
            </div>
        </div>
        """
    return """
    <div class="app-brand">
        <div class="app-brand-title" style="text-align:center;">
            <h1>公共资源交易龙虾</h1>
            <p>南通公共资源交易大脑代理智能体</p>
        </div>
    </div>
    """


def create_ui(theme_name="Ocean"):
    css = """
    .gradio-container {
        width: 95vw !important; 
        max-width: 95% !important; 
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 10px !important;
    }
    #run_button {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    #run_button button {
        pointer-events: auto !important;
        cursor: pointer !important;
        opacity: 1 !important;
    }
    .header-text {
        text-align: center;
        margin-bottom: 20px;
    }
    .tab-header-text {
        text-align: center;
    }
    .app-brand {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 18px;
        margin-bottom: 20px;
    }
    .app-brand img {
        width: 140px;
        height: 140px;
        object-fit: contain;
        border-radius: 24px;
        box-shadow: 0 0 24px rgba(46, 214, 255, 0.35);
    }
    .app-brand-title {
        text-align: left;
    }
    .app-brand-title h1 {
        margin: 0;
        font-size: 2.2rem;
    }
    .app-brand-title p {
        margin: 8px 0 0;
        opacity: 0.9;
        font-size: 1.05rem;
    }
    .theme-section {
        margin-bottom: 10px;
        padding: 15px;
        border-radius: 10px;
    }

    .skills-page {
        width: 100%;
        padding: 6px 0 2px;
    }
    .skills-toolbar {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        margin: 6px 0 14px;
    }
    .skills-title h2 {
        margin: 0;
        font-size: 1.35rem;
        letter-spacing: 0.02em;
    }
    .skills-subtitle {
        margin-top: 6px;
        opacity: 0.75;
        font-size: 0.95rem;
    }
    .skills-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 8px;
    }
    @media (max-width: 960px) {
        .skills-grid { grid-template-columns: 1fr; }
    }
    .skills-card {
        position: relative;
        border-radius: 16px;
        padding: 16px 16px 14px;
        background: linear-gradient(180deg, rgba(22, 28, 38, 0.92), rgba(12, 16, 22, 0.92));
        border: 1px solid rgba(46, 214, 255, 0.22);
        box-shadow: 0 0 30px rgba(46, 214, 255, 0.10);
        overflow: hidden;
    }
    .skills-card:before {
        content: "";
        position: absolute;
        inset: -2px;
        background: radial-gradient(800px 140px at 20% 0%, rgba(46, 214, 255, 0.16), transparent 60%);
        pointer-events: none;
    }
    .skills-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 10px;
        position: relative;
        z-index: 1;
    }
    .skills-card-title {
        font-size: 1.1rem;
        margin: 0;
        line-height: 1.2;
    }
    .skills-card-id {
        font-size: 0.85rem;
        opacity: 0.7;
        margin-top: 6px;
        word-break: break-all;
    }
    .skills-card-desc {
        margin-top: 10px;
        opacity: 0.85;
        line-height: 1.4;
        position: relative;
        z-index: 1;
    }
    .skills-card-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        margin-top: 14px;
        position: relative;
        z-index: 1;
    }
    .skills-btn {
        border: 1px solid rgba(46, 214, 255, 0.22);
        background: rgba(10, 14, 20, 0.55);
        color: rgba(235, 252, 255, 0.94);
        border-radius: 12px;
        padding: 9px 12px;
        cursor: pointer;
        transition: transform 0.08s ease, box-shadow 0.12s ease, border-color 0.12s ease, background 0.12s ease;
        user-select: none;
        white-space: nowrap;
    }
    .skills-btn:hover {
        border-color: rgba(46, 214, 255, 0.55);
        box-shadow: 0 0 24px rgba(46, 214, 255, 0.14);
        transform: translateY(-1px);
    }
    .skills-btn:active { transform: translateY(0px); }
    .skills-btn-primary {
        background: rgba(46, 214, 255, 0.16);
        border-color: rgba(46, 214, 255, 0.65);
    }
    .skills-btn-secondary {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.16);
    }
    .skills-btn-danger {
        background: rgba(255, 72, 72, 0.12);
        border-color: rgba(255, 72, 72, 0.45);
    }
    .skills-btn-ghost {
        background: transparent;
        border-color: rgba(255, 255, 255, 0.14);
        opacity: 0.9;
    }
    .skills-modal-backdrop {
        position: fixed;
        inset: 0;
        display: none;
        align-items: center;
        justify-content: center;
        padding: 20px;
        background: rgba(0, 0, 0, 0.62);
        z-index: 1000;
    }
    .skills-modal-backdrop[aria-hidden="false"] { display: flex; }
    .skills-modal {
        width: min(860px, 92vw);
        border-radius: 18px;
        border: 1px solid rgba(46, 214, 255, 0.24);
        background: linear-gradient(180deg, rgba(16, 20, 28, 0.98), rgba(8, 10, 14, 0.98));
        box-shadow: 0 0 48px rgba(46, 214, 255, 0.16);
        overflow: hidden;
    }
    .skills-modal-sm { width: min(520px, 92vw); }
    .skills-modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 14px;
        border-bottom: 1px solid rgba(46, 214, 255, 0.16);
    }
    .skills-modal-title {
        font-size: 1.05rem;
        font-weight: 600;
    }
    .skills-modal-body {
        padding: 14px 14px 6px;
    }
    .skills-modal-footer {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        padding: 12px 14px 14px;
        border-top: 1px solid rgba(46, 214, 255, 0.12);
    }
    .skills-form-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
    }
    @media (max-width: 720px) {
        .skills-form-row { grid-template-columns: 1fr; }
    }
    .skills-form-field { margin-bottom: 10px; }
    .skills-label {
        display: block;
        margin-bottom: 6px;
        opacity: 0.85;
        font-size: 0.9rem;
    }
    .skills-input, .skills-textarea {
        width: 100%;
        border-radius: 12px;
        border: 1px solid rgba(46, 214, 255, 0.18);
        background: rgba(0, 0, 0, 0.25);
        color: rgba(235, 252, 255, 0.94);
        padding: 10px 12px;
        outline: none;
    }
    .skills-textarea { resize: vertical; }
    .skills-input:focus, .skills-textarea:focus {
        border-color: rgba(46, 214, 255, 0.55);
        box-shadow: 0 0 0 3px rgba(46, 214, 255, 0.10);
    }
    .skills-fields-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 8px;
    }
    .skills-fields-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .skills-field-row {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr auto auto;
        gap: 8px;
        align-items: center;
        padding: 8px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        background: rgba(255, 255, 255, 0.02);
    }
    .skills-field-row .skills-input {
        padding: 8px 10px;
    }
    .skills-field-check {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        opacity: 0.88;
        font-size: 0.86rem;
    }
    .skills-field-empty {
        padding: 10px;
        border-radius: 10px;
        border: 1px dashed rgba(255, 255, 255, 0.16);
        opacity: 0.68;
        font-size: 0.9rem;
    }
    .skills-toast {
        position: fixed;
        top: 18px;
        left: 50%;
        transform: translateX(-50%);
        padding: 10px 14px;
        border-radius: 14px;
        border: 1px solid rgba(46, 214, 255, 0.28);
        background: rgba(10, 14, 20, 0.88);
        color: rgba(235, 252, 255, 0.95);
        box-shadow: 0 0 28px rgba(46, 214, 255, 0.16);
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.18s ease, transform 0.18s ease;
        z-index: 1100;
    }
    .skills-toast[aria-hidden="false"] {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
    }

    .lobster-run-skill-wrap {
        position: relative;
    }
    .lobster-run-skill-btn {
        position: absolute;
        top: 8px;
        right: 10px;
        width: 34px;
        height: 34px;
        border-radius: 12px;
        border: 1px solid rgba(46, 214, 255, 0.28);
        background: rgba(10, 14, 20, 0.55);
        color: rgba(235, 252, 255, 0.94);
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.08s ease, box-shadow 0.12s ease, border-color 0.12s ease, background 0.12s ease;
        z-index: 6;
        user-select: none;
    }
    .lobster-run-skill-btn:hover {
        border-color: rgba(46, 214, 255, 0.60);
        box-shadow: 0 0 20px rgba(46, 214, 255, 0.14);
        transform: translateY(-1px);
    }
    .lobster-run-skill-btn:active { transform: translateY(0px); }

    .lobster-run-skill-panel {
        position: fixed;
        width: min(360px, calc(100vw - 40px));
        max-height: 320px;
        overflow-y: auto;
        overflow-x: hidden;
        border-radius: 14px;
        border: 1px solid rgba(46, 214, 255, 0.22);
        background: rgba(10, 14, 20, 0.92);
        box-shadow: 0 0 34px rgba(46, 214, 255, 0.14);
        padding: 8px;
        z-index: 7;
        scrollbar-width: thin;
        scrollbar-color: rgba(46, 214, 255, 0.55) rgba(255, 255, 255, 0.06);
    }
    .lobster-run-skill-panel::-webkit-scrollbar {
        width: 8px;
    }
    .lobster-run-skill-panel::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.06);
        border-radius: 10px;
    }
    .lobster-run-skill-panel::-webkit-scrollbar-thumb {
        background: rgba(46, 214, 255, 0.45);
        border-radius: 10px;
        border: 2px solid rgba(10, 14, 20, 0.92);
    }
    .lobster-run-skill-panel::-webkit-scrollbar-thumb:hover {
        background: rgba(46, 214, 255, 0.65);
    }
    .lobster-run-skill-panel[aria-hidden="true"] { display: none; }
    .lobster-run-skill-panel-title {
        padding: 6px 8px 8px;
        font-size: 0.88rem;
        opacity: 0.8;
        letter-spacing: 0.02em;
    }
    .lobster-run-skill-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 10px 10px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.10);
        background: rgba(255, 255, 255, 0.03);
        cursor: pointer;
        transition: border-color 0.12s ease, background 0.12s ease, transform 0.08s ease;
        margin-bottom: 8px;
    }
    .lobster-run-skill-item:last-child { margin-bottom: 0; }
    .lobster-run-skill-item:hover {
        border-color: rgba(46, 214, 255, 0.45);
        background: rgba(46, 214, 255, 0.08);
        transform: translateY(-1px);
    }
    .lobster-run-skill-item-name {
        font-size: 0.98rem;
        color: rgba(235, 252, 255, 0.95);
        line-height: 1.2;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .lobster-run-skill-item-id {
        font-size: 0.78rem;
        opacity: 0.65;
        white-space: nowrap;
    }
    .lobster-run-fields {
        margin-top: 10px;
        padding: 10px;
        border: 1px solid rgba(46, 214, 255, 0.22);
        border-radius: 12px;
        background: rgba(10, 14, 20, 0.45);
    }
    .lobster-run-fields-title {
        font-size: 0.92rem;
        opacity: 0.85;
        margin-bottom: 8px;
    }
    .lobster-run-fields-toolbar {
        display: grid;
        grid-template-columns: 140px 120px minmax(160px, 1fr);
        gap: 8px;
        margin-bottom: 8px;
    }
    .lobster-run-fields-filter {
        border-radius: 8px;
        border: 1px solid rgba(46, 214, 255, 0.22);
        background: rgba(0, 0, 0, 0.25);
        color: rgba(235, 252, 255, 0.94);
        padding: 7px 9px;
        width: 100%;
    }
    .lobster-run-fields-required-only {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.82rem;
        opacity: 0.9;
    }
    .lobster-run-fields-meta {
        font-size: 0.8rem;
        opacity: 0.78;
        display: inline-flex;
        align-items: center;
        justify-content: flex-end;
    }
    .lobster-run-fields-empty {
        border: 1px dashed rgba(255, 255, 255, 0.18);
        border-radius: 10px;
        padding: 10px;
        opacity: 0.75;
        font-size: 0.88rem;
    }
    .lobster-run-fields-grid {
        display: flex;
        flex-direction: column;
        gap: 8px;
        max-height: 260px;
        overflow: auto;
    }
    .lobster-run-field-row {
        display: grid;
        grid-template-columns: 180px minmax(120px, 1fr) minmax(180px, 1.8fr) 92px;
        gap: 8px;
        align-items: center;
        padding: 8px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.10);
    }
    .lobster-run-field-row.pending {
        border-color: rgba(255, 124, 124, 0.46);
        background: rgba(255, 80, 80, 0.08);
    }
    .lobster-run-field-row.filled {
        border-color: rgba(46, 214, 255, 0.35);
        background: rgba(46, 214, 255, 0.06);
    }
    .lobster-run-field-name {
        font-size: 0.9rem;
        font-weight: 600;
    }
    .lobster-run-field-key {
        font-size: 0.8rem;
        opacity: 0.72;
    }
    .lobster-run-field-value {
        border-radius: 8px;
        border: 1px solid rgba(46, 214, 255, 0.22);
        background: rgba(0, 0, 0, 0.25);
        color: rgba(235, 252, 255, 0.94);
        padding: 7px 9px;
        width: 100%;
    }
    .lobster-run-field-status {
        text-align: right;
        font-size: 0.8rem;
        opacity: 0.85;
    }
    .lobster-run-field-status.pending { color: rgba(255, 150, 150, 0.95); }
    .lobster-run-field-status.filled { color: rgba(123, 233, 255, 0.95); }
    @media (max-width: 980px) {
        .lobster-run-fields-toolbar {
            grid-template-columns: 1fr;
        }
        .lobster-run-fields-meta {
            justify-content: flex-start;
        }
        .skills-field-row {
            grid-template-columns: 1fr;
        }
        .lobster-run-field-row {
            grid-template-columns: 1fr;
        }
        .lobster-run-field-status {
            text-align: left;
        }
    }
    """

    # dark mode in default
    js_func = """
    () => {
        const url = new URL(window.location);

        if (url.searchParams.get("__theme") !== "dark") {
            url.searchParams.set("__theme", "dark");
            window.location.href = url.href;
            return;
        }

        (function () {
        const STORAGE_KEY = "lobster.skills.v1";
        const DEFAULT_SKILLS = [
            {
                id: "skills-001",
                name: "招标文件发布",
                desc: "协助定位上传模块，解析 PDF 并填表。",
                prompt: `你是“招标文件发布”业务助手。目标：协助用户在系统中完成招标文件发布。

要求：
1) 先询问用户当前处于哪个页面/模块，以及是否已进入上传入口。
2) 指导用户定位上传模块，并提示检查必填项。
3) 若用户提供 PDF（或其关键信息），请提取关键字段并给出表单填报建议（项目名称、招标编号、预算金额、报名时间、开标时间、联系人、联系电话、附件清单等）。
4) 输出结构化步骤清单，并提示用户逐项确认。
`
            , required_fields: [
                { name: "项目名称", key: "project_name", default: "", required: true },
                { name: "招标编号", key: "bid_no", default: "", required: true },
                { name: "预算金额", key: "budget", default: "", required: true },
                { name: "报名时间", key: "register_time", default: "", required: false },
                { name: "开标时间", key: "open_time", default: "", required: false },
                { name: "联系人", key: "contact_name", default: "", required: false },
                { name: "联系电话", key: "contact_phone", default: "", required: false }
            ]},
            {
                id: "skills-002",
                name: "预约开评标场地",
                desc: "查询可用房间并执行预定流程。",
                prompt: `你是“预约开评标场地”业务助手。目标：帮助用户完成开评标场地预约。

要求：
1) 询问预约日期、时间段、人数、是否需要评标室/开标室/候场区等。
2) 给出可用房间查询的步骤，并在得到候选房间后给出对比建议（容量、设备、地点）。
3) 指导用户完成预定/提交审批，并给出注意事项（冲突检查、凭证下载、取消规则）。
4) 输出可复制的预约摘要（日期、时间段、房间、联系人、备注）。
`
            , required_fields: [
                { name: "预约日期", key: "date", default: "", required: true },
                { name: "时间段", key: "time_slot", default: "", required: true },
                { name: "人数", key: "people_count", default: "", required: true },
                { name: "房间类型", key: "room_type", default: "评标室", required: false },
                { name: "联系人", key: "contact_name", default: "", required: false },
                { name: "联系电话", key: "contact_phone", default: "", required: false }
            ]},
            {
                id: "skills-003",
                name: "发布中标候选人公示",
                desc: "提取评标报告数据并生成公示预览。",
                prompt: `你是“发布中标候选人公示”业务助手。目标：从评标报告/评审结果中提取数据，生成候选人公示内容并指导发布。

要求：
1) 询问项目名称、标段、评标日期、候选人数量、是否联合体。
2) 从用户提供的评标报告文本/截图/要点中提取候选人信息（单位名称、报价、得分、排序、项目负责人）。
3) 生成公示预览文案（含监督电话/异议渠道/公示期限），并提示用户核对。
4) 给出发布操作步骤与常见校验点。
`
            , required_fields: [
                { name: "项目名称", key: "project_name", default: "", required: true },
                { name: "标段", key: "section", default: "", required: false },
                { name: "评标日期", key: "review_date", default: "", required: true },
                { name: "候选人数量", key: "candidate_count", default: "3", required: true }
            ]},
            {
                id: "skills-004",
                name: "发布中标结果公告",
                desc: "提取中标人信用代码与金额并同步表单。",
                prompt: `你是“发布中标结果公告”业务助手。目标：帮助用户发布中标结果公告。

要求：
1) 询问项目名称、标段、中标单位、金额、合同工期/服务期、项目负责人等。
2) 如用户提供相关材料，提取中标人统一社会信用代码、金额（大写/小写）、地址/联系人等，并给出表单同步建议。
3) 生成公告预览文案（含公告期限、监督渠道），并提醒核对关键字段。
4) 给出发布前检查清单与附件完整性校验点。
`
            , required_fields: [
                { name: "项目名称", key: "project_name", default: "", required: true },
                { name: "标段", key: "section", default: "", required: false },
                { name: "中标单位", key: "winner_name", default: "", required: true },
                { name: "统一社会信用代码", key: "winner_code", default: "", required: false },
                { name: "中标金额（小写）", key: "winner_amount", default: "", required: true },
                { name: "项目负责人", key: "pm_name", default: "", required: false }
            ]}
        ];

        function safeJsonParse(text) {
            try { return JSON.parse(text); } catch (e) { return null; }
        }

        function loadSkills() {
            const raw = localStorage.getItem(STORAGE_KEY);
            const parsed = raw ? safeJsonParse(raw) : null;
            if (Array.isArray(parsed) && parsed.length > 0) return parsed;
            localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_SKILLS));
            return DEFAULT_SKILLS.slice();
        }

        function saveSkills(skills) {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(skills || []));
            try {
                window.dispatchEvent(new CustomEvent("lobster:skills-updated"));
            } catch (e) { }
        }

        function el(id) { return document.getElementById(id); }

        function showToast(message) {
            const toast = el("lobster-skills-toast");
            if (!toast) return;
            toast.textContent = message || "操作成功";
            toast.setAttribute("aria-hidden", "false");
            clearTimeout(showToast._t);
            showToast._t = setTimeout(() => toast.setAttribute("aria-hidden", "true"), 1400);
        }

        function escapeHtml(s) {
            return String(s ?? "")
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll(String.fromCharCode(34), "&quot;")
                .replaceAll("'", "&#039;");
        }

        function normalizeSkill(skill) {
            const rf = Array.isArray(skill?.required_fields) ? skill.required_fields : [];
            const fields = rf.map((f) => {
                const key = String(f?.key ?? "").trim();
                return {
                    name: String(f?.name ?? key).trim(),
                    key,
                    default: String(f?.default ?? "").trim(),
                    required: !!f?.required
                };
            }).filter(f => f.key);
            return {
                id: String(skill?.id ?? "").trim(),
                name: String(skill?.name ?? "").trim(),
                desc: String(skill?.desc ?? "").trim(),
                prompt: String(skill?.prompt ?? "").trim(),
                required_fields: fields
            };
        }

        function render(skills) {
            const grid = el("lobster-skills-grid");
            if (!grid) return;
            if (!skills || skills.length === 0) {
                grid.innerHTML = "<div class='skills-card'><div class='skills-card-desc'>暂无业务指令。点击右上角“+ 新增业务指令”。</div></div>";
                return;
            }
            grid.innerHTML = skills.map((s, idx) => {
                const id = escapeHtml(s.id);
                const name = escapeHtml(s.name);
                const desc = escapeHtml(s.desc);
                const fieldCount = Array.isArray(s.required_fields) ? s.required_fields.length : 0;
                return `
                  <div class="skills-card" data-index="${idx}">
                    <div class="skills-card-header">
                      <div>
                        <div class="skills-card-title">${name || "未命名业务指令"}</div>
                        <div class="skills-card-id">${id || "未设置 ID"}</div>
                      </div>
                      <button class="skills-btn skills-btn-danger" type="button" data-action="delete">删除</button>
                    </div>
                    <div class="skills-card-desc">${desc || "（无简述）"}</div>
                    <div class="skills-card-id">字段规格：${fieldCount} 项</div>
                    <div class="skills-card-actions">
                      <button class="skills-btn skills-btn-secondary" type="button" data-action="edit">修改</button>
                      <button class="skills-btn skills-btn-primary" type="button" data-action="execute">立即执行</button>
                    </div>
                  </div>
                `;
            }).join("");
        }

        function openModal(mode, skill) {
            const modal = el("lobster-skills-modal");
            if (!modal) return;
            modal.dataset.mode = mode;
            modal.dataset.index = (skill && typeof skill._index === "number") ? String(skill._index) : "";
            el("lobster-skills-modal-title").textContent = mode === "edit" ? "修改业务指令" : "新增业务指令";
            el("lobster-skill-id").value = skill?.id ?? "";
            el("lobster-skill-name").value = skill?.name ?? "";
            el("lobster-skill-desc").value = skill?.desc ?? "";
            el("lobster-skill-prompt").value = skill?.prompt ?? "";
            modal.setAttribute("aria-hidden", "false");
            try { openSkillEditorFields(skill || {}); } catch (e) {}
        }

        function closeModal() {
            const modal = el("lobster-skills-modal");
            if (!modal) return;
            modal.setAttribute("aria-hidden", "true");
        }

        function openConfirm(index, name) {
            const confirm = el("lobster-skills-confirm");
            if (!confirm) return;
            confirm.dataset.index = String(index);
            el("lobster-skills-confirm-text").textContent = `确认删除“${name || "未命名业务指令"}”？此操作不可撤销。`;
            confirm.setAttribute("aria-hidden", "false");
        }

        function closeConfirm() {
            const confirm = el("lobster-skills-confirm");
            if (!confirm) return;
            confirm.setAttribute("aria-hidden", "true");
        }

        function syncRunSkillSpec(skill, extractMap) {
            const specEl = getSpecJsonEl();
            const extEl = getExtractJsonEl();
            const spec = {
                id: String(skill?.id || ""),
                name: String(skill?.name || ""),
                required_fields: Array.isArray(skill?.required_fields) ? skill.required_fields : []
            };
            writeValue(specEl, JSON.stringify(spec));
            writeValue(extEl, JSON.stringify(extractMap || {}));
            renderDynamicForm();
        }

        function setRunAgentPrompt(text, skill) {
            const tabs = Array.from(document.querySelectorAll("[role='tab']"));
            const tabBtn = tabs.find(n => (n?.textContent || "").trim().includes("🤖 运行智能体"));
            if (tabBtn && typeof tabBtn.click === "function") tabBtn.click();
            const ok = fillRunAgentInput(text || "", "replace");
            if (skill) syncRunSkillSpec(skill, {});
            if (!ok) return false;
            return true;
        }

        function getRunAgentRoot() {
            return document.getElementById("user_input");
        }

        function getRunButton() {
            const host = document.getElementById("run_button");
            if (!host) return document.querySelector("#run_button button, button#run_button");
            if (String(host.tagName || "").toLowerCase() === "button") return host;
            return host.querySelector("button");
        }

        function getDynamicFormRoot() {
            return document.getElementById("lobster-run-dynamic-form");
        }

        function getDynamicContextEl() {
            return document.querySelector("#dynamic_context textarea, #dynamic_context input");
        }

        function getFieldsValidEl() {
            return document.querySelector("#fields_valid textarea, #fields_valid input");
        }

        function getSpecJsonEl() {
            return document.querySelector("#skill_spec_json textarea, #skill_spec_json input");
        }

        function getExtractJsonEl() {
            return document.querySelector("#extract_result_json textarea, #extract_result_json input");
        }

        function writeValue(el, v) {
            if (!el) return;
            const val = String(v ?? "");
            el.value = val;
            el.dispatchEvent(new Event("input", { bubbles: true }));
            el.dispatchEvent(new Event("change", { bubbles: true }));
        }

        function mergeExtractWithFields(fields, extractMap) {
            const rows = [];
            const contextPairs = {};
            let allValid = true;
            for (const f of fields) {
                const key = String(f?.key || "").trim();
                const name = String(f?.name || key);
                const required = !!f?.required;
                const defaultVal = String(f?.default || "");
                const aiVal = String(extractMap?.[key] ?? "");
                const value = (aiVal || defaultVal || "");
                const filled = value.trim().length > 0;
                if (required && !filled) allValid = false;
                if (filled) contextPairs[name] = value;
                rows.push({ name, key, value, required, filled });
            }
            return { rows, allValid, contextPairs };
        }

        function renderDynamicForm() {
            try {
                const host = getDynamicFormRoot();
                if (!host) return false;
                const specEl = getSpecJsonEl();
                const extractEl = getExtractJsonEl();
                const ctxEl = getDynamicContextEl();
                const validEl = getFieldsValidEl();
                if (!specEl || !extractEl || !ctxEl || !validEl) return false;
                const spec = safeJsonParse(specEl.value || "{}") || {};
                const fields = Array.isArray(spec.required_fields) ? spec.required_fields : [];
                const extractMap = safeJsonParse(extractEl.value || "{}") || {};
                const { rows, allValid, contextPairs } = mergeExtractWithFields(fields, extractMap);
                const filterStatus = String(host.dataset.filterStatus || "all");
                const requiredOnly = host.dataset.requiredOnly === "1";
                const keyword = String(host.dataset.keyword || "").trim();
                const lowerKeyword = keyword.toLowerCase();
                const filledCount = rows.filter(r => r.filled).length;
                const pendingCount = rows.length - filledCount;
                const requiredMissing = rows.filter(r => r.required && !r.filled).length;
                const filteredRows = rows.filter((r) => {
                    if (filterStatus === "pending" && r.filled) return false;
                    if (filterStatus === "filled" && !r.filled) return false;
                    if (requiredOnly && !r.required) return false;
                    if (!lowerKeyword) return true;
                    const text = `${r.name} ${r.key} ${r.value}`.toLowerCase();
                    return text.includes(lowerKeyword);
                });
                const html = [
                    '<div class="lobster-run-fields">',
                    '<div class="lobster-run-fields-title">动态表单（左对齐规格 + AI 提取 + 可编辑）</div>',
                    `<div class="lobster-run-fields-toolbar">
                        <select class="lobster-run-fields-filter" data-role="status-filter">
                          <option value="all" ${filterStatus === "all" ? "selected" : ""}>全部字段</option>
                          <option value="pending" ${filterStatus === "pending" ? "selected" : ""}>仅待补充</option>
                          <option value="filled" ${filterStatus === "filled" ? "selected" : ""}>仅已填写</option>
                        </select>
                        <label class="lobster-run-fields-required-only">
                          <input type="checkbox" data-role="required-only" ${requiredOnly ? "checked" : ""}/>
                          仅看必填
                        </label>
                        <input class="lobster-run-fields-filter" data-role="keyword" placeholder="搜索字段名/键名/值" value="${escapeHtml(keyword)}"/>
                      </div>`,
                    `<div class="lobster-run-fields-meta">总计 ${rows.length} · 已填 ${filledCount} · 待补 ${pendingCount} · 必填缺失 ${requiredMissing}</div>`,
                    '<div class="lobster-run-fields-grid">'
                ];
                for (let i = 0; i < filteredRows.length; i++) {
                    const r = filteredRows[i];
                    const stClass = r.filled ? "filled" : "pending";
                    const status = r.filled ? "AI已填/已填" : (r.required ? "待补充" : "可选");
                    const escName = escapeHtml(r.name);
                    const escKey = escapeHtml(r.key);
                    const escVal = escapeHtml(r.value);
                    html.push(
                        `<div class="lobster-run-field-row ${stClass}" data-key="${escKey}">
                           <div class="lobster-run-field-name">${escName}</div>
                           <div class="lobster-run-field-key">${escKey}</div>
                           <div><input class="lobster-run-field-value" type="text" value="${escVal}" data-key="${escKey}"></div>
                           <div class="lobster-run-field-status ${stClass}">${status}${r.required ? " · 必填" : ""}</div>
                         </div>`
                    );
                }
                if (filteredRows.length === 0) html.push('<div class="lobster-run-fields-empty">当前筛选条件下无字段，请调整筛选条件。</div>');
                html.push("</div></div>");
                host.innerHTML = html.join("");
                const statusFilterEl = host.querySelector('[data-role="status-filter"]');
                const requiredOnlyEl = host.querySelector('[data-role="required-only"]');
                const keywordEl = host.querySelector('[data-role="keyword"]');
                if (statusFilterEl) {
                    statusFilterEl.addEventListener("change", () => {
                        host.dataset.filterStatus = statusFilterEl.value || "all";
                        renderDynamicForm();
                    });
                }
                if (requiredOnlyEl) {
                    requiredOnlyEl.addEventListener("change", () => {
                        host.dataset.requiredOnly = requiredOnlyEl.checked ? "1" : "0";
                        renderDynamicForm();
                    });
                }
                if (keywordEl) {
                    keywordEl.addEventListener("change", () => {
                        host.dataset.keyword = keywordEl.value || "";
                        renderDynamicForm();
                    });
                }
                const inputs = Array.from(host.querySelectorAll(".lobster-run-field-value"));
                inputs.forEach((inp) => {
                    inp.addEventListener("input", () => {
                        const k = inp.getAttribute("data-key");
                        const v = inp.value;
                        extractMap[k] = v;
                        writeValue(getExtractJsonEl(), JSON.stringify(extractMap));
                        const { rows: r2, allValid: valid2, contextPairs: cp2 } = mergeExtractWithFields(fields, extractMap);
                        writeValue(getDynamicContextEl(), JSON.stringify(cp2, null, 0));
                        writeValue(getFieldsValidEl(), valid2 ? "1" : "0");
                        const rowEl = inp.closest(".lobster-run-field-row");
                        if (rowEl) {
                            const filled = String(v || "").trim().length > 0;
                            rowEl.classList.toggle("filled", filled);
                            rowEl.classList.toggle("pending", !filled);
                            const statusEl = rowEl.querySelector(".lobster-run-field-status");
                            const fieldDef = fields.find(f => String(f.key) === String(k));
                            const isRequired = !!fieldDef?.required;
                            if (statusEl) statusEl.textContent = filled ? "AI已填/已填" + (isRequired ? " · 必填" : "") : (isRequired ? "待补充 · 必填" : "可选");
                        }
                        const btn = getRunButton();
                        const hasRequiredFields2 = fields.some(f => !!f?.required);
                        if (btn) btn.disabled = hasRequiredFields2 && !valid2;
                    });
                    inp.addEventListener("change", () => {
                        const curFilter = String(host.dataset.filterStatus || "all");
                        const requiredOnlyMode = host.dataset.requiredOnly === "1";
                        const hasKeyword = String(host.dataset.keyword || "").trim().length > 0;
                        if (curFilter !== "all" || requiredOnlyMode || hasKeyword) renderDynamicForm();
                    });
                });
                writeValue(ctxEl, JSON.stringify(contextPairs, null, 0));
                writeValue(validEl, allValid ? "1" : "0");
                const btn = getRunButton();
                const hasRequiredFields = fields.some(f => !!f?.required);
                if (btn) btn.disabled = hasRequiredFields && !allValid;
                return true;
            } catch (e) { return false; }
        }

        function bindDynamicFormBridge() {
            const host = getDynamicFormRoot();
            if (!host) return false;
            if (host.dataset.bound === "1") return true;
            host.dataset.bound = "1";
            const sync = () => {
                try {
                    const specEl = getSpecJsonEl();
                    const extEl = getExtractJsonEl();
                    const parsed = safeJsonParse(specEl?.value || "{}") || {};
                    const hasFields = Array.isArray(parsed.required_fields) && parsed.required_fields.length > 0;
                    if (!hasFields) {
                        // 初始化时不自动加载带有必填字段的技能，避免按钮被禁用
                        writeValue(specEl, JSON.stringify({
                            id: "",
                            name: "未选择技能",
                            required_fields: []
                        }));
                        if (!(safeJsonParse(extEl?.value || "{}"))) writeValue(extEl, "{}");
                    }
                    renderDynamicForm();
                } catch (e) {}
            };
            const spec = getSpecJsonEl();
            const ext = getExtractJsonEl();
            if (spec) spec.addEventListener("change", sync);
            if (ext) ext.addEventListener("change", sync);
            setTimeout(sync, 10);
            return true;
        }

        function collectSkillEditorFields() {
            const list = document.getElementById("lobster-skill-fields");
            if (!list) return [];
            const rows = Array.from(list.querySelectorAll(".skills-field-row"));
            const next = rows.map((row) => {
                const get = (sel) => row.querySelector(`[data-field="${sel}"]`);
                return {
                    name: String(get("name")?.value || "").trim(),
                    key: String(get("key")?.value || "").trim(),
                    default: String(get("default")?.value || ""),
                    required: !!get("required")?.checked
                };
            }).filter((r) => r.key);
            return next;
        }

        function openSkillEditorFields(skill) {
            const list = document.getElementById("lobster-skill-fields");
            const addBtn = document.getElementById("lobster-skill-field-add");
            if (!list || !addBtn) return;
            const fields = (Array.isArray(skill?.required_fields) ? skill.required_fields : []).map((f) => ({
                name: String(f?.name || ""),
                key: String(f?.key || ""),
                default: String(f?.default || ""),
                required: !!f?.required
            }));
            const renderList = () => {
                if (!fields.length) {
                    list.innerHTML = '<div class="skills-field-empty">暂无扩展字段。点击右上角“+ 扩展字段”新增。</div>';
                    return;
                }
                list.innerHTML = fields.map((f, i) => {
                    const name = escapeHtml(String(f?.name ?? ""));
                    const key = escapeHtml(String(f?.key ?? ""));
                    const def = escapeHtml(String(f?.default ?? ""));
                    const checked = f?.required ? "checked" : "";
                    return `
                      <div class="skills-field-row" data-index="${i}">
                        <input class="skills-input" placeholder="字段名" value="${name}" data-field="name"/>
                        <input class="skills-input" placeholder="键名(key)" value="${key}" data-field="key"/>
                        <input class="skills-input" placeholder="默认值" value="${def}" data-field="default"/>
                        <label class="skills-field-check"><input type="checkbox" ${checked} data-field="required"/> 必填</label>
                        <button class="skills-btn skills-btn-ghost" data-action="remove" type="button">删除</button>
                      </div>
                    `;
                }).join("");
            };
            addBtn.onclick = () => {
                fields.push({ name: "", key: "", default: "", required: true });
                renderList();
            };
            list.onclick = (e) => {
                const row = e.target?.closest?.(".skills-field-row");
                if (!row) return;
                if (e.target?.getAttribute?.("data-action") === "remove") {
                    const idx = Number(row.getAttribute("data-index"));
                    if (idx >= 0) fields.splice(idx, 1);
                    renderList();
                }
            };
            renderList();
        }

        function getRunAgentInput() {
            const root = getRunAgentRoot();
            if (!root) return null;
            return root.querySelector("textarea, input");
        }

        function focusToEnd(input) {
            try {
                input.focus();
                const len = (input.value || "").length;
                if (typeof input.setSelectionRange === "function") input.setSelectionRange(len, len);
            } catch (e) { }
        }

        function setInputValue(input, nextValue) {
            input.value = nextValue;
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            focusToEnd(input);
        }

        function fillRunAgentInput(text, mode) {
            const input = getRunAgentInput();
            if (!input) return false;
            const nextText = String(text ?? "");
            const cur = String(input.value ?? "");
            if (mode === "smart" && cur.trim().length > 0 && nextText.trim().length > 0) {
                const replace = window.confirm(`任务指令已有内容：确定替换？
点击“取消”则在末尾换行追加。`);
                if (!replace) {
                    const joiner = cur.endsWith("\\n") ? "\\n" : "\\n\\n";
                    setInputValue(input, cur + joiner + nextText);
                    return true;
                }
            }
            setInputValue(input, nextText);
            return true;
        }

        function closeRunSkillPanel() {
            const panel = document.getElementById("lobster-run-skill-panel");
            if (!panel) return;
            panel.setAttribute("aria-hidden", "true");
        }

        function positionRunSkillPanel() {
            const btn = document.getElementById("lobster-run-skill-btn");
            const panel = document.getElementById("lobster-run-skill-panel");
            if (!btn || !panel) return;
            if (panel.getAttribute("aria-hidden") === "true") return;

            const rect = btn.getBoundingClientRect();
            const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
            const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);

            const gap = 10;
            const panelWidth = Math.min(360, vw - 40);

            let left = Math.round(rect.right - panelWidth);
            left = Math.max(12, Math.min(left, vw - panelWidth - 12));

            const downTop = Math.round(rect.bottom + gap);
            const upMax = Math.max(140, Math.round(rect.top - gap - 12));
            const downMax = Math.max(140, Math.round(vh - downTop - 12));
            const useUp = downMax < 220 && upMax > downMax;

            panel.style.width = panelWidth + "px";
            panel.style.left = left + "px";
            panel.style.right = "auto";

            if (useUp) {
                const maxH = Math.min(320, upMax);
                panel.style.maxHeight = maxH + "px";
                panel.style.top = "12px";
                panel.style.bottom = Math.round(vh - rect.top + gap) + "px";
            } else {
                const maxH = Math.min(320, downMax);
                panel.style.maxHeight = maxH + "px";
                panel.style.bottom = "auto";
                panel.style.top = downTop + "px";
            }
        }

        function toggleRunSkillPanel() {
            const panel = document.getElementById("lobster-run-skill-panel");
            if (!panel) return;
            const next = panel.getAttribute("aria-hidden") === "false" ? "true" : "false";
            panel.setAttribute("aria-hidden", next);
            if (next === "false") {
                renderRunSkillList(panel);
                positionRunSkillPanel();
            }
        }

        function renderRunSkillList(panel) {
            const skills = loadSkills().map(normalizeSkill);
            if (!panel) return;
            const items = skills.map((s, idx) => {
                const name = escapeHtml(s.name || "未命名业务指令");
                const id = escapeHtml(s.id || "");
                return `
                  <div class="lobster-run-skill-item" data-index="${idx}">
                    <div class="lobster-run-skill-item-name">${name}</div>
                    <div class="lobster-run-skill-item-id">${id}</div>
                  </div>
                `;
            }).join("");
            panel.innerHTML = `
              <div class="lobster-run-skill-panel-title">调用业务指令</div>
              ${items || "<div class='lobster-run-skill-panel-title' style='padding-top:10px'>暂无业务指令</div>"}
            `;
        }

        function ensureRunSkillPicker() {
            const root = getRunAgentRoot();
            if (!root) return false;

            if (!root.classList.contains("lobster-run-skill-wrap")) root.classList.add("lobster-run-skill-wrap");

            let btn = document.getElementById("lobster-run-skill-btn");
            if (!btn) {
                btn = document.createElement("button");
                btn.type = "button";
                btn.id = "lobster-run-skill-btn";
                btn.className = "lobster-run-skill-btn";
                btn.title = "调用业务指令";
                btn.textContent = "⚡";
                root.appendChild(btn);
            }

            let panel = document.getElementById("lobster-run-skill-panel");
            if (!panel) {
                panel = document.createElement("div");
                panel.id = "lobster-run-skill-panel";
                panel.className = "lobster-run-skill-panel";
                panel.setAttribute("aria-hidden", "true");
                root.appendChild(panel);
            }

            if (btn.dataset.bound !== "1") {
                btn.addEventListener("click", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleRunSkillPanel();
                });
                btn.dataset.bound = "1";
            }

            if (panel.dataset.bound !== "1") {
                panel.addEventListener("click", (e) => {
                    const item = e.target?.closest?.(".lobster-run-skill-item");
                    if (!item) return;
                    const idx = Number(item.getAttribute("data-index"));
                    const skills = loadSkills().map(normalizeSkill);
                    const s = skills[idx];
                    if (!s) return;
                    setRunAgentPrompt(s.prompt || "", s);
                    closeRunSkillPanel();
                });
                panel.dataset.bound = "1";
            }

            if (document.body && document.body.dataset.lobsterRunSkillDoc !== "1") {
                document.addEventListener("click", (e) => {
                    const target = e.target;
                    const p = document.getElementById("lobster-run-skill-panel");
                    const b = document.getElementById("lobster-run-skill-btn");
                    if (!p || !b) return;
                    if (p.getAttribute("aria-hidden") === "true") return;
                    if (p.contains(target) || b.contains(target)) return;
                    closeRunSkillPanel();
                }, true);
                document.addEventListener("keydown", (e) => {
                    if (e.key === "Escape") closeRunSkillPanel();
                }, true);
                window.addEventListener("resize", positionRunSkillPanel, true);
                window.addEventListener("scroll", positionRunSkillPanel, true);
                window.addEventListener("lobster:skills-updated", () => {
                    const p = document.getElementById("lobster-run-skill-panel");
                    if (p && p.getAttribute("aria-hidden") === "false") renderRunSkillList(p);
                });
                document.body.dataset.lobsterRunSkillDoc = "1";
            }

            return true;
        }

        function bindSkills() {
            const root = el("lobster_skills_root");
            if (!root) return false;
            if (root.dataset && root.dataset.bound === "1") return true;

            let skills = loadSkills().map(normalizeSkill);
            saveSkills(skills);
            render(skills);

            el("lobster-skill-create-btn")?.addEventListener("click", () => {
                openModal("create", { id: "", name: "", desc: "", prompt: "" });
            });
            el("lobster-skills-modal-close")?.addEventListener("click", closeModal);
            el("lobster-skills-modal-cancel")?.addEventListener("click", closeModal);

            el("lobster-skills-confirm-close")?.addEventListener("click", closeConfirm);
            el("lobster-skills-confirm-cancel")?.addEventListener("click", closeConfirm);

            el("lobster-skills-modal-save")?.addEventListener("click", () => {
                const modal = el("lobster-skills-modal");
                const mode = modal?.dataset?.mode || "create";
                const idx = modal?.dataset?.index ? Number(modal.dataset.index) : -1;
                const next = normalizeSkill({
                    id: el("lobster-skill-id")?.value,
                    name: el("lobster-skill-name")?.value,
                    desc: el("lobster-skill-desc")?.value,
                    prompt: el("lobster-skill-prompt")?.value,
                    required_fields: collectSkillEditorFields()
                });
                if (!next.id || !next.name || !next.prompt) {
                    showToast("请填写 ID、名称、Prompt");
                    return;
                }
                const dupFieldKey = new Set();
                for (const f of next.required_fields || []) {
                    if (dupFieldKey.has(f.key)) {
                        showToast("字段键名重复，请修改");
                        return;
                    }
                    dupFieldKey.add(f.key);
                }
                skills = loadSkills().map(normalizeSkill);
                const duplicate = skills.find((s, i) => s.id === next.id && (mode !== "edit" || i !== idx));
                if (duplicate) {
                    showToast("ID 已存在，请更换");
                    return;
                }
                if (mode === "edit" && idx >= 0 && idx < skills.length) {
                    skills[idx] = next;
                } else {
                    skills.unshift(next);
                }
                saveSkills(skills);
                render(skills);
                closeModal();
                showToast("操作成功");
            });

            el("lobster-skills-confirm-ok")?.addEventListener("click", () => {
                const confirm = el("lobster-skills-confirm");
                const idx = confirm?.dataset?.index ? Number(confirm.dataset.index) : -1;
                skills = loadSkills().map(normalizeSkill);
                if (idx >= 0 && idx < skills.length) {
                    skills.splice(idx, 1);
                    saveSkills(skills);
                    render(skills);
                }
                closeConfirm();
                showToast("操作成功");
            });

            el("lobster-skills-grid")?.addEventListener("click", (ev) => {
                const btn = ev.target?.closest?.("[data-action]");
                const card = ev.target?.closest?.(".skills-card");
                if (!btn || !card) return;
                const action = btn.getAttribute("data-action");
                const idx = Number(card.getAttribute("data-index"));
                skills = loadSkills().map(normalizeSkill);
                const skill = skills[idx];
                if (!skill) return;

                if (action === "delete") {
                    openConfirm(idx, skill.name);
                    return;
                }
                if (action === "edit") {
                    openModal("edit", { ...skill, _index: idx });
                    return;
                }
                if (action === "execute") {
                    const ok = setRunAgentPrompt(skill.prompt, skill);
                    if (ok) showToast("已填充到“运行智能体”");
                    else showToast("未找到运行输入框");
                }
            });

            if (root.dataset) root.dataset.bound = "1";
            return true;
        }

        function start() {
            let queued = false;
            const tick = () => {
                queued = false;
                try { bindSkills(); } catch (e) { }
                try { ensureRunSkillPicker(); } catch (e) { }
                try { bindDynamicFormBridge(); } catch (e) { }
            };
            const schedule = () => {
                if (queued) return;
                queued = true;
                queueMicrotask(tick);
            };

            const observer = new MutationObserver(schedule);
            if (document.body) observer.observe(document.body, { childList: true, subtree: true });
            schedule();
        }

        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", start);
        } else {
            start();
        }
    })();
    }
    """

    ui_manager = WebuiManager()

    with gr.Blocks(
            title="交易龙虾Pro", theme=theme_map[theme_name], css=css, js=js_func,
    ) as demo:
        with gr.Row():
            brand_html = gr.HTML(render_brand_html())

        with gr.Row():
            with gr.Column(scale=12):
                region_container = gr.HTML()

            with gr.Column(scale=3):
                province_dropdown = gr.Dropdown(
                    choices=get_provinces(),
                    value="江苏省",
                    label="选择省份",
                    interactive=True
                )
                city_dropdown = gr.Dropdown(
                    choices=get_cities("江苏省"),
                    value="南通市",
                    label="选择城市",
                    interactive=True
                )

        def update_cities(province_name):
            cities = get_cities(province_name)
            if cities:
                return gr.update(choices=cities, value=cities[0])
            return gr.update(choices=[], value=None)

        def update_region_display(province_key, city_key):
            region_name = get_region_name(province_key, city_key)
            return f"""
            <div style="display: flex; align-items: center; justify-content: flex-start; gap: 12px; padding: 8px 16px; background: rgba(46, 214, 255, 0.1); border-radius: 12px; border: 1px solid rgba(46, 214, 255, 0.25);">
                <span style="font-size: 1.1rem;">📍</span>
                <span style="font-size: 0.95rem; font-weight: 500;">当前地区：{region_name}</span>
            </div>
            """

        def handle_region_change(province_key, city_key):
            skills = get_region_skills(province_key, city_key)
            skills_json = str(skills).replace("'", "\"").replace('"', '\\"')
            return f"""
            <script>
                const REGION_SKILLS = {skills};
                localStorage.setItem('lobster.skills.v1', JSON.stringify(REGION_SKILLS));
                window.dispatchEvent(new CustomEvent('lobster:skills-updated'));
            </script>
            """

        province_dropdown.change(
            fn=update_cities,
            inputs=province_dropdown,
            outputs=city_dropdown
        )

        region_js = gr.HTML()

        def sync_region_skills(province_key, city_key):
            skills = get_region_skills(province_key, city_key)
            region_name = get_region_name(province_key, city_key)
            
            display_html = f"""
            <div style="display: flex; align-items: center; justify-content: flex-start; gap: 12px; padding: 8px 16px; background: rgba(46, 214, 255, 0.1); border-radius: 12px; border: 1px solid rgba(46, 214, 255, 0.25);">
                <span style="font-size: 1.1rem;">📍</span>
                <span style="font-size: 0.95rem; font-weight: 500;">当前地区：{region_name}</span>
            </div>
            """
            
            js_code = f"""
            <script>
                const REGION_SKILLS = {skills};
                localStorage.setItem('lobster.skills.v1', JSON.stringify(REGION_SKILLS));
                try {{
                    window.dispatchEvent(new CustomEvent('lobster:skills-updated'));
                }} catch(e) {{}}
            </script>
            """
            
            return display_html, js_code

        gr.on(
            triggers=[province_dropdown.change, city_dropdown.change],
            fn=sync_region_skills,
            inputs=[province_dropdown, city_dropdown],
            outputs=[region_container, region_js]
        )

        demo.load(
            fn=sync_region_skills,
            inputs=[province_dropdown, city_dropdown],
            outputs=[region_container, region_js]
        )

        with gr.Tabs() as tabs:
            with gr.TabItem("📚 业务指令集"):
                create_skills_tab(ui_manager)

            with gr.TabItem("⚙️ 智能体设置"):
                create_agent_settings_tab(ui_manager)

            with gr.TabItem("🌐 浏览器配置"):
                create_browser_settings_tab(ui_manager)

            with gr.TabItem("🤖 运行智能体"):
                create_browser_use_agent_tab(ui_manager)
            
            with gr.TabItem("🔎 深度研究"):
                create_deep_research_agent_tab(ui_manager)

        def _auto_load():
            try:
                ui_settings = ui_manager._read_persist()
            except Exception:
                ui_settings = {}
            updates = {}
            for comp_id, comp_val in (ui_settings or {}).items():
                comp = ui_manager.id_to_component.get(comp_id)
                if not comp:
                    continue
                updates[comp] = gr.update(value=comp_val)
            if updates:
                yield updates

        demo.load(fn=render_brand_html, outputs=brand_html)
        demo.load(fn=_auto_load, outputs=list(ui_manager.get_components()))

    return demo
