import asyncio
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

import gradio as gr
from json_repair import repair_json

# from browser_use.agent.service import Agent
from browser_use.agent.views import (
    AgentHistoryList,
    AgentOutput,
)
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.browser.views import BrowserState
from gradio.components import Component
from langchain_core.language_models.chat_models import BaseChatModel

from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from src.controller.custom_controller import CustomController
from src.utils import llm_provider
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


# --- Helper Functions --- (Defined at module level)


async def _initialize_llm(
        provider: Optional[str],
        model_name: Optional[str],
        temperature: float,
        base_url: Optional[str],
        api_key: Optional[str],
        num_ctx: Optional[int] = None,
) -> Optional[BaseChatModel]:
    """Initializes the LLM based on settings. Returns None if provider/model is missing."""
    if not provider or not model_name:
        logger.info("LLM Provider or Model Name not specified, LLM will be None.")
        return None
    try:
        # Use your actual LLM provider logic here
        logger.info(
            f"Initializing LLM: Provider={provider}, Model={model_name}, Temp={temperature}"
        )
        # Example using a placeholder function
        llm = llm_provider.get_llm_model(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            base_url=base_url or None,
            api_key=api_key or None,
            # Add other relevant params like num_ctx for ollama
            num_ctx=num_ctx if provider == "ollama" else None,
        )
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}", exc_info=True)
        gr.Warning(
            f"Failed to initialize LLM '{model_name}' for provider '{provider}'. Please check settings. Error: {e}"
        )
        return None


def _get_config_value(
        webui_manager: WebuiManager,
        comp_dict: Dict[gr.components.Component, Any],
        comp_id_suffix: str,
        default: Any = None,
) -> Any:
    """Safely get value from component dictionary using its ID suffix relative to the tab."""
    # Assumes component ID format is "tab_name.comp_name"
    tab_name = "browser_use_agent"  # Hardcode or derive if needed
    comp_id = f"{tab_name}.{comp_id_suffix}"
    # Need to find the component object first using the ID from the manager
    try:
        comp = webui_manager.get_component_by_id(comp_id)
        return comp_dict.get(comp, default)
    except KeyError:
        # Try accessing settings tabs as well
        for prefix in ["agent_settings", "browser_settings"]:
            try:
                comp_id = f"{prefix}.{comp_id_suffix}"
                comp = webui_manager.get_component_by_id(comp_id)
                return comp_dict.get(comp, default)
            except KeyError:
                continue
        logger.warning(
            f"Component with suffix '{comp_id_suffix}' not found in manager for value lookup."
        )
        return default


def _read_uploaded_file_text(file_value: Any) -> str:
    if not file_value:
        return ""
    if isinstance(file_value, dict):
        file_path = file_value.get("name") or file_value.get("path") or ""
    elif isinstance(file_value, str):
        file_path = file_value
    else:
        file_path = getattr(file_value, "name", "") or ""
    if not file_path:
        return ""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return ""
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".md", ".csv", ".json", ".log", ".xml"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".pdf":
            try:
                from pypdf import PdfReader
            except Exception:
                return ""
            reader = PdfReader(str(path))
            chunks = []
            for page in reader.pages[:30]:
                chunks.append(page.extract_text() or "")
            return "\n".join(chunks)
        raw = path.read_bytes()
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _normalize_required_fields(spec_json: str) -> list[dict]:
    if not spec_json:
        return []
    try:
        parsed = json.loads(spec_json)
    except Exception:
        return []
    fields = parsed.get("required_fields") if isinstance(parsed, dict) else None
    if not isinstance(fields, list):
        return []
    normalized = []
    for f in fields:
        if not isinstance(f, dict):
            continue
        key = str(f.get("key") or "").strip()
        name = str(f.get("name") or key).strip()
        default_value = str(f.get("default") or "").strip()
        required = bool(f.get("required", True))
        if not key:
            continue
        normalized.append(
            {
                "name": name or key,
                "key": key,
                "default": default_value,
                "required": required,
            }
        )
    return normalized


async def _extract_by_llm(
        provider: Optional[str],
        model_name: Optional[str],
        temperature: float,
        base_url: Optional[str],
        api_key: Optional[str],
        num_ctx: Optional[int],
        fields: list[dict],
        source_text: str,
) -> dict:
    if not provider or not model_name or not fields or not source_text.strip():
        return {}
    llm = await _initialize_llm(
        provider=provider,
        model_name=model_name,
        temperature=temperature,
        base_url=base_url,
        api_key=api_key,
        num_ctx=num_ctx,
    )
    if llm is None:
        return {}
    fields_text = json.dumps(fields, ensure_ascii=False)
    prompt = (
        "你是业务数据提取助手。请严格只返回 JSON 对象，不要包含 markdown 或解释。\n"
        "目标字段规格如下：\n"
        f"{fields_text}\n"
        "请从材料中抽取对应 key 的值，无法确认请返回空字符串。\n"
        "材料内容如下：\n"
        f"{source_text[:16000]}"
    )
    try:
        msg = await llm.ainvoke(prompt)
        content = msg.content if hasattr(msg, "content") else str(msg)
        repaired = repair_json(str(content), return_objects=True)
        if isinstance(repaired, dict):
            return {str(k): "" if v is None else str(v) for k, v in repaired.items()}
    except Exception as e:
        logger.warning(f"LLM extract failed: {e}")
    return {}


def _format_agent_output(model_output: AgentOutput) -> str:
    """Formats AgentOutput for display in the chatbot using JSON."""
    content = ""
    if model_output:
        try:
            # Directly use model_dump if actions and current_state are Pydantic models
            action_dump = [
                action.model_dump(exclude_none=True) for action in model_output.action
            ]

            state_dump = model_output.current_state.model_dump(exclude_none=True)
            model_output_dump = {
                "current_state": state_dump,
                "action": action_dump,
            }
            # Dump to JSON string with indentation
            json_string = json.dumps(model_output_dump, indent=4, ensure_ascii=False)
            # Wrap in <pre><code> for proper display in HTML
            content = f"<pre><code class='language-json'>{json_string}</code></pre>"

        except AttributeError as ae:
            logger.error(
                f"AttributeError during model dump: {ae}. Check if 'action' or 'current_state' or their items support 'model_dump'."
            )
            content = f"<pre><code>Error: Could not format agent output (AttributeError: {ae}).\nRaw output: {str(model_output)}</code></pre>"
        except Exception as e:
            logger.error(f"Error formatting agent output: {e}", exc_info=True)
            # Fallback to simple string representation on error
            content = f"<pre><code>Error formatting agent output.\nRaw output:\n{str(model_output)}</code></pre>"

    return content.strip()


# --- Updated Callback Implementation ---


async def _handle_new_step(
        webui_manager: WebuiManager, state: BrowserState, output: AgentOutput, step_num: int
):
    """Callback for each step taken by the agent, including screenshot display."""

    # Use the correct chat history attribute name from the user's code
    if not hasattr(webui_manager, "bu_chat_history"):
        logger.error(
            "Attribute 'bu_chat_history' not found in webui_manager! Cannot add chat message."
        )
        # Initialize it maybe? Or raise an error? For now, log and potentially skip chat update.
        webui_manager.bu_chat_history = []  # Initialize if missing (consider if this is the right place)
        # return # Or stop if this is critical
    step_num -= 1
    logger.info(f"Step {step_num} completed.")

    # --- Screenshot Handling ---
    screenshot_html = ""
    # Ensure state.screenshot exists and is not empty before proceeding
    # Use getattr for safer access
    screenshot_data = getattr(state, "screenshot", None)
    if screenshot_data:
        try:
            # Basic validation: check if it looks like base64
            if (
                    isinstance(screenshot_data, str) and len(screenshot_data) > 100
            ):  # Arbitrary length check
                # *** UPDATED STYLE: Removed centering, adjusted width ***
                img_tag = f'<img src="data:image/jpeg;base64,{screenshot_data}" alt="Step {step_num} Screenshot" style="max-width: 800px; max-height: 600px; object-fit:contain;" />'
                screenshot_html = (
                        img_tag + "<br/>"
                )  # Use <br/> for line break after inline-block image
            else:
                logger.warning(
                    f"Screenshot for step {step_num} seems invalid (type: {type(screenshot_data)}, len: {len(screenshot_data) if isinstance(screenshot_data, str) else 'N/A'})."
                )
                screenshot_html = "**[Invalid screenshot data]**<br/>"

        except Exception as e:
            logger.error(
                f"Error processing or formatting screenshot for step {step_num}: {e}",
                exc_info=True,
            )
            screenshot_html = "**[Error displaying screenshot]**<br/>"
    else:
        logger.debug(f"No screenshot available for step {step_num}.")

    # --- Format Agent Output ---
    formatted_output = _format_agent_output(output)  # Use the updated function

    # --- Combine and Append to Chat ---
    step_header = f"--- **第 {step_num} 步** ---"
    # Combine header, image (with line break), and JSON block
    final_content = step_header + "<br/>" + screenshot_html + formatted_output

    chat_message = {
        "role": "assistant",
        "content": final_content.strip(),  # Remove leading/trailing whitespace
    }

    # Append to the correct chat history list
    webui_manager.bu_chat_history.append(chat_message)

    await asyncio.sleep(0.05)

def _parse_desired_filename(task_text: str) -> Optional[str]:
    if not task_text:
        return None
    m = re.search(r'filename\s*[:=]\s*["\']?([^"\'\n\r]+?)["\']?(?:\s|$)', task_text, flags=re.IGNORECASE)
    if not m:
        return None
    name = m.group(1).strip()
    name = os.path.basename(name)
    if not name:
        return None
    return name


def _is_incomplete(fname: str) -> bool:
    lower = fname.lower()
    return any(lower.endswith(ext) for ext in ['.crdownload', '.part', '.partial', '.tmp'])


def _inject_login_disambiguation(task_text: str) -> str:
    """Inject robust login-selection rules for pages with multiple CA login tabs."""
    task = str(task_text or "").strip()
    if not task:
        return task
    if "【登录方式精确选择规则】" in task:
        return task
    keywords = ["ca登录", "移动ca", "全国互认", "苏服办", "登录方式", "选择ca"]
    lower = task.lower()
    if not any(k in lower for k in keywords):
        return task
    guard = (
        "\n\n【登录方式精确选择规则】\n"
        "1) 当页面同时出现“CA登录 / 移动CA全国互认 / 苏服办登录”时，必须按文本精确匹配点击，严禁按视觉编号或坐标猜测。\n"
        "2) 若用户要求“选择CA方式登录”，仅可点击文本“CA登录”，不得点击“移动CA全国互认”或“苏服办登录”。\n"
        "3) 点击后必须立即校验是否进入对应模式（例如出现 CA 密码输入框/证书登录区域/激活态样式）。\n"
        "4) 若校验失败，返回并改用文本定位重试一次；仍失败则截图并明确报告“页面文案与目标不一致”。\n"
    )
    return task + guard


def _rename_latest_file(download_dir: str, target_name: str) -> tuple[bool, Optional[str], Optional[str]]:
    if not download_dir or not os.path.isdir(download_dir) or not target_name:
        return False, None, None
    entries = []
    for f in os.listdir(download_dir):
        p = os.path.join(download_dir, f)
        if os.path.isfile(p) and not _is_incomplete(f):
            try:
                entries.append((p, os.path.getmtime(p)))
            except Exception:
                continue
    if not entries:
        return False, None, None
    entries.sort(key=lambda x: x[1], reverse=True)
    latest_path = entries[0][0]
    dest_path = os.path.join(download_dir, target_name)
    try:
        if os.path.abspath(latest_path) == os.path.abspath(dest_path):
            return True, latest_path, dest_path
        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.replace(latest_path, dest_path)
        return True, latest_path, dest_path
    except Exception as e:
        logger.error(f"Rename failed: {e}", exc_info=True)
        return False, latest_path, dest_path


def _handle_done(webui_manager: WebuiManager, history: AgentHistoryList, task_text: Optional[str] = None, download_dir: Optional[str] = None):
    """Callback when the agent finishes the task (success or failure)."""
    logger.info(
        f"Agent task finished. Duration: {history.total_duration_seconds():.2f}s, Tokens: {history.total_input_tokens()}"
    )
    def localize_text(text: str) -> str:
        if not text:
            return ""
        out = str(text)
        mapping = {
            "Task Completed": "任务完成",
            "Duration:": "耗时：",
            "seconds": "秒",
            "Total Input Tokens:": "总输入 Tokens：",
            "Final Result:": "最终结果：",
            "Status: Success": "状态：成功",
            "Successfully completed all steps of the task:": "已成功完成任务全部步骤：",
            "Extracted Project Summary Information:": "提取到的项目摘要信息：",
            "Project Name:": "项目名称：",
            "Bid Management Company:": "招标代理机构：",
            "Announcement Date:": "公告日期：",
            "Total Valid Bidders:": "有效投标人数：",
            "Evaluation Method:": "评标办法：",
            "Bid Candidates:": "中标候选人：",
            "First Place Candidate:": "第一中标候选人：",
            "Second Place Candidate:": "第二中标候选人：",
            "Third Place Candidate:": "第三中标候选人：",
            "Company Name:": "单位名称：",
            "Bid Price:": "投标报价：",
            "Project Manager Name:": "项目负责人：",
            "Quality Commitment:": "质量承诺：",
            "Duration Commitment:": "工期承诺：",
            "Additional Key Information:": "其他关键信息：",
            "Proposed Winner:": "拟中标人：",
            "Publication Period:": "公示期限：",
            "Bid Opening Date:": "开标时间：",
            "Disqualified Bidder:": "废标单位：",
            "Contact Person:": "联系人：",
            "Contact Phone:": "联系电话：",
            "Issuing Authority:": "发布单位：",
            "Note:": "备注：",
            "There were no announcements for the current date": "当前日期未查询到公告",
            "most recent announcement": "最近可用公告",
            "Found the latest bid candidate announcement": "已定位最新中标候选人公示",
        }
        for en, zh in mapping.items():
            out = out.replace(en, zh)
        return out

    final_summary = "**任务完成**\n"
    final_summary += f"- 耗时：{history.total_duration_seconds():.2f} 秒\n"
    final_summary += f"- 总输入 Tokens：{history.total_input_tokens()}\n"

    final_result = history.final_result()
    if final_result:
        final_summary += f"- 最终结果：{localize_text(final_result)}\n"

    errors = history.errors()
    if errors and any(errors):
        final_summary += f"- **错误信息：**\n```\n{errors}\n```\n"
    else:
        final_summary += "- 状态：成功\n"

    rename_info = ""
    desired = _parse_desired_filename(task_text or "")
    if desired:
        ok, src, dst = _rename_latest_file(download_dir or "", desired)
        if ok:
            rename_info = f"- 下载文件已重命名：{os.path.basename(src) if src else ''} -> {os.path.basename(dst) if dst else desired}\n- 路径：{download_dir or ''}\n"
        else:
            rename_info = f"- 下载文件重命名尝试：失败，请确认文件已生成且下载完成\n- 路径：{download_dir or ''}\n"
    if rename_info:
        final_summary += rename_info

    webui_manager.bu_chat_history.append(
        {"role": "assistant", "content": final_summary}
    )


async def _ask_assistant_callback(
        webui_manager: WebuiManager, query: str, browser_context: BrowserContext
) -> Dict[str, Any]:
    """Callback triggered by the agent's ask_for_assistant action."""
    logger.info("Agent requires assistance. Waiting for user input.")

    if not hasattr(webui_manager, "_chat_history"):
        logger.error("Chat history not found in webui_manager during ask_assistant!")
        return {"response": "内部错误：无法显示协助请求。"}

    webui_manager.bu_chat_history.append(
        {
            "role": "assistant",
            "content": f"**需要协助：** {query}\n请在浏览器中补充信息或完成必要操作，然后在下方输入你的回复/确认，并点击“提交回复”。",
        }
    )

    # Use state stored in webui_manager
    webui_manager.bu_response_event = asyncio.Event()
    webui_manager.bu_user_help_response = None  # Reset previous response

    try:
        logger.info("Waiting for user response event...")
        await asyncio.wait_for(
            webui_manager.bu_response_event.wait(), timeout=3600.0
        )  # Long timeout
        logger.info("User response event received.")
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for user assistance.")
        webui_manager.bu_chat_history.append(
            {
                "role": "assistant",
                "content": "**超时：** 未收到回复，尝试继续执行。",
            }
        )
        webui_manager.bu_response_event = None  # Clear the event
        return {"response": "超时：用户未回复。"}  # Inform the agent

    response = webui_manager.bu_user_help_response
    webui_manager.bu_chat_history.append(
        {"role": "user", "content": response}
    )  # Show user response in chat
    webui_manager.bu_response_event = (
        None  # Clear the event for the next potential request
    )
    return {"response": response}


# --- Core Agent Execution Logic --- (Needs access to webui_manager)


async def run_agent_task(
        webui_manager: WebuiManager, components: Dict[gr.components.Component, Any]
) -> AsyncGenerator[Dict[gr.components.Component, Any], None]:
    """Handles the entire lifecycle of initializing and running the agent."""

    # --- Get Components ---
    # Need handles to specific UI components to update them
    user_input_comp = webui_manager.get_component_by_id("browser_use_agent.user_input")
    run_button_comp = webui_manager.get_component_by_id("browser_use_agent.run_button")
    stop_button_comp = webui_manager.get_component_by_id(
        "browser_use_agent.stop_button"
    )
    pause_resume_button_comp = webui_manager.get_component_by_id(
        "browser_use_agent.pause_resume_button"
    )
    clear_button_comp = webui_manager.get_component_by_id(
        "browser_use_agent.clear_button"
    )
    chatbot_comp = webui_manager.get_component_by_id("browser_use_agent.chatbot")
    history_file_comp = webui_manager.get_component_by_id(
        "browser_use_agent.agent_history_file"
    )
    gif_comp = webui_manager.get_component_by_id("browser_use_agent.recording_gif")
    browser_view_comp = webui_manager.get_component_by_id(
        "browser_use_agent.browser_view"
    )

    # --- 1. Get Task and Initial UI Update ---
    task = components.get(user_input_comp, "").strip()
    if not task:
        gr.Warning("请输入任务指令。")
        yield {run_button_comp: gr.update(interactive=True)}
        return

    # Set running state indirectly via _current_task
    webui_manager.bu_chat_history.append({"role": "user", "content": task})

    yield {
        user_input_comp: gr.update(value="", interactive=False, placeholder="智能体运行中..."),
        run_button_comp: gr.update(value="⏳ 运行中...", interactive=False),
        stop_button_comp: gr.update(interactive=True),
        pause_resume_button_comp: gr.update(value="⏸️ 暂停", interactive=True),
        clear_button_comp: gr.update(interactive=False),
        chatbot_comp: gr.update(value=webui_manager.bu_chat_history),
        history_file_comp: gr.update(value=None),
        gif_comp: gr.update(value=None),
    }

    # --- Agent Settings ---
    # Access settings values via components dict, getting IDs from webui_manager
    def get_setting(key, default=None):
        comp = webui_manager.id_to_component.get(f"agent_settings.{key}")
        if not comp:
            return default
        val = components.get(comp, None)
        return default if val is None else val

    override_system_prompt = get_setting("override_system_prompt") or None
    extend_system_prompt = get_setting("extend_system_prompt") or None
    llm_provider_name = get_setting(
        "llm_provider", None
    )  # Default to None if not found
    llm_model_name = get_setting("llm_model_name", None)
    llm_temperature = get_setting("llm_temperature", 0.6)
    use_vision = get_setting("use_vision", False)
    ollama_num_ctx = get_setting("ollama_num_ctx", 16000)
    llm_base_url = get_setting("llm_base_url") or None
    llm_api_key = get_setting("llm_api_key") or None
    max_steps = get_setting("max_steps", 100)
    max_actions = get_setting("max_actions", 10)
    max_input_tokens = get_setting("max_input_tokens", 128000)
    tool_calling_str = get_setting("tool_calling_method", "auto")
    tool_calling_method = tool_calling_str if tool_calling_str != "None" else None
    mcp_server_config_comp = webui_manager.id_to_component.get(
        "agent_settings.mcp_server_config"
    )
    mcp_server_config_str = (
        components.get(mcp_server_config_comp) if mcp_server_config_comp else None
    )
    mcp_server_config = (
        json.loads(mcp_server_config_str) if mcp_server_config_str else None
    )

    # Planner LLM Settings (Optional)
    planner_llm_provider_name = get_setting("planner_llm_provider") or None
    planner_llm = None
    planner_use_vision = False
    if planner_llm_provider_name:
        planner_llm_model_name = get_setting("planner_llm_model_name")
        planner_llm_temperature = get_setting("planner_llm_temperature", 0.6)
        planner_ollama_num_ctx = get_setting("planner_ollama_num_ctx", 16000)
        planner_llm_base_url = get_setting("planner_llm_base_url") or None
        planner_llm_api_key = get_setting("planner_llm_api_key") or None
        planner_use_vision = get_setting("planner_use_vision", False)

        planner_llm = await _initialize_llm(
            planner_llm_provider_name,
            planner_llm_model_name,
            planner_llm_temperature,
            planner_llm_base_url,
            planner_llm_api_key,
            planner_ollama_num_ctx if planner_llm_provider_name == "ollama" else None,
        )

    # --- Browser Settings ---
    def get_browser_setting(key, default=None):
        comp = webui_manager.id_to_component.get(f"browser_settings.{key}")
        if not comp:
            return default
        val = components.get(comp, None)
        return default if val is None else val

    browser_binary_path = get_browser_setting("browser_binary_path") or None
    browser_user_data_dir = get_browser_setting("browser_user_data_dir") or None
    use_own_browser = get_browser_setting(
        "use_own_browser", False
    )  # Logic handled by CDP/WSS presence
    keep_browser_open = get_browser_setting("keep_browser_open", False)
    headless = get_browser_setting("headless", False)
    disable_security = get_browser_setting("disable_security", False)
    window_w = int(get_browser_setting("window_w", 1280))
    window_h = int(get_browser_setting("window_h", 1100))
    cdp_url = get_browser_setting("cdp_url") or None
    wss_url = get_browser_setting("wss_url") or None
    save_recording_path = get_browser_setting("save_recording_path") or None
    save_trace_path = get_browser_setting("save_trace_path") or None
    save_agent_history_path = get_browser_setting(
        "save_agent_history_path", "./tmp/agent_history"
    )
    env_output_path = os.getenv("OUTPUT_PATH", None)
    save_download_path = get_browser_setting("save_download_path", env_output_path if env_output_path else "./tmp/downloads")

    stream_vw = 70
    stream_vh = int(70 * window_h // window_w)

    os.makedirs(save_agent_history_path, exist_ok=True)
    if save_recording_path:
        os.makedirs(save_recording_path, exist_ok=True)
    if save_trace_path:
        os.makedirs(save_trace_path, exist_ok=True)
    if save_download_path:
        os.makedirs(save_download_path, exist_ok=True)

    # --- 2. Initialize LLM ---
    main_llm = await _initialize_llm(
        llm_provider_name,
        llm_model_name,
        llm_temperature,
        llm_base_url,
        llm_api_key,
        ollama_num_ctx if llm_provider_name == "ollama" else None,
    )
    if main_llm is None:
        webui_manager.bu_chat_history.append(
            {
                "role": "assistant",
                "content": "**配置缺失：** 请先在“智能体设置”中选择 LLM Provider 与 Model，并填写对应 API Key / Base URL。",
            }
        )
        yield {
            user_input_comp: gr.update(
                interactive=True, placeholder="请先完成模型配置，然后再提交任务指令..."
            ),
            run_button_comp: gr.update(value="▶️ 提交任务", interactive=True),
            stop_button_comp: gr.update(interactive=False),
            pause_resume_button_comp: gr.update(interactive=False),
            clear_button_comp: gr.update(interactive=True),
            chatbot_comp: gr.update(value=webui_manager.bu_chat_history),
        }
        return

    # Pass the webui_manager instance to the callback when wrapping it
    async def ask_callback_wrapper(
            query: str, browser_context: BrowserContext
    ) -> Dict[str, Any]:
        return await _ask_assistant_callback(webui_manager, query, browser_context)

    if not webui_manager.bu_controller:
        webui_manager.bu_controller = CustomController(
            ask_assistant_callback=ask_callback_wrapper
        )
        await webui_manager.bu_controller.setup_mcp_client(mcp_server_config)

    # --- 4. Initialize Browser and Context ---
    should_close_browser_on_finish = not keep_browser_open

    try:
        # Close existing resources if not keeping open
        if not keep_browser_open:
            if webui_manager.bu_browser_context:
                logger.info("Closing previous browser context.")
                await webui_manager.bu_browser_context.close()
                webui_manager.bu_browser_context = None
            if webui_manager.bu_browser:
                logger.info("Closing previous browser.")
                await webui_manager.bu_browser.close()
                webui_manager.bu_browser = None

        # Create Browser if needed
        if not webui_manager.bu_browser:
            logger.info("Launching new browser instance.")
            extra_args = []
            if use_own_browser:
                browser_binary_path = os.getenv("BROWSER_PATH", None) or browser_binary_path
                if browser_binary_path == "":
                    browser_binary_path = None
                browser_user_data = browser_user_data_dir or os.getenv("BROWSER_USER_DATA", None)
                if browser_user_data:
                    extra_args += [f"--user-data-dir={browser_user_data}"]
            else:
                browser_binary_path = None

            webui_manager.bu_browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=disable_security,
                    browser_binary_path=browser_binary_path,
                    extra_browser_args=extra_args,
                    wss_url=wss_url,
                    cdp_url=cdp_url,
                    new_context_config=BrowserContextConfig(
                        window_width=window_w,
                        window_height=window_h,
                    )
                )
            )

        # Create Context if needed
        if not webui_manager.bu_browser_context:
            logger.info("Creating new browser context.")
            context_config = BrowserContextConfig(
                trace_path=save_trace_path if save_trace_path else None,
                save_recording_path=save_recording_path
                if save_recording_path
                else None,
                save_downloads_path=save_download_path if save_download_path else None,
                window_height=window_h,
                window_width=window_w,
            )
            if not webui_manager.bu_browser:
                raise ValueError("Browser not initialized, cannot create context.")
            webui_manager.bu_browser_context = (
                await webui_manager.bu_browser.new_context(config=context_config)
            )

        # --- 5. Initialize or Update Agent ---
        webui_manager.bu_agent_task_id = str(uuid.uuid4())  # New ID for this task run
        os.makedirs(
            os.path.join(save_agent_history_path, webui_manager.bu_agent_task_id),
            exist_ok=True,
        )
        history_file = os.path.join(
            save_agent_history_path,
            webui_manager.bu_agent_task_id,
            f"{webui_manager.bu_agent_task_id}.json",
        )
        gif_path = os.path.join(
            save_agent_history_path,
            webui_manager.bu_agent_task_id,
            f"{webui_manager.bu_agent_task_id}.gif",
        )

        # Pass the webui_manager to callbacks when wrapping them
        async def step_callback_wrapper(
                state: BrowserState, output: AgentOutput, step_num: int
        ):
            await _handle_new_step(webui_manager, state, output, step_num)

        def done_callback_wrapper(history: AgentHistoryList):
            _handle_done(webui_manager, history, task_text=task, download_dir=save_download_path)

        if not webui_manager.bu_agent:
            logger.info(f"Initializing new agent for task: {task}")
            if not webui_manager.bu_browser or not webui_manager.bu_browser_context:
                raise ValueError(
                    "Browser or Context not initialized, cannot create agent."
                )
            webui_manager.bu_agent = BrowserUseAgent(
                task=task,
                llm=main_llm,
                browser=webui_manager.bu_browser,
                browser_context=webui_manager.bu_browser_context,
                controller=webui_manager.bu_controller,
                register_new_step_callback=step_callback_wrapper,
                register_done_callback=done_callback_wrapper,
                use_vision=use_vision,
                override_system_message=override_system_prompt,
                extend_system_message=extend_system_prompt,
                max_input_tokens=max_input_tokens,
                max_actions_per_step=max_actions,
                tool_calling_method=tool_calling_method,
                planner_llm=planner_llm,
                use_vision_for_planner=planner_use_vision if planner_llm else False,
                source="webui",
            )
            webui_manager.bu_agent.state.agent_id = webui_manager.bu_agent_task_id
            webui_manager.bu_agent.settings.generate_gif = gif_path
        else:
            webui_manager.bu_agent.state.agent_id = webui_manager.bu_agent_task_id
            webui_manager.bu_agent.add_new_task(task)
            webui_manager.bu_agent.settings.generate_gif = gif_path
            webui_manager.bu_agent.browser = webui_manager.bu_browser
            webui_manager.bu_agent.browser_context = webui_manager.bu_browser_context
            webui_manager.bu_agent.controller = webui_manager.bu_controller

        # --- 6. Run Agent Task and Stream Updates ---
        agent_run_coro = webui_manager.bu_agent.run(max_steps=max_steps)
        agent_task = asyncio.create_task(agent_run_coro)
        webui_manager.bu_current_task = agent_task  # Store the task

        last_chat_len = len(webui_manager.bu_chat_history)
        while not agent_task.done():
            is_paused = webui_manager.bu_agent.state.paused
            is_stopped = webui_manager.bu_agent.state.stopped

            # Check for pause state
            if is_paused:
                yield {
                    pause_resume_button_comp: gr.update(
                        value="▶️ 继续", interactive=True
                    ),
                    stop_button_comp: gr.update(interactive=True),
                }
                # Wait until pause is released or task is stopped/done
                while is_paused and not agent_task.done():
                    # Re-check agent state in loop
                    is_paused = webui_manager.bu_agent.state.paused
                    is_stopped = webui_manager.bu_agent.state.stopped
                    if is_stopped:  # Stop signal received while paused
                        break
                    await asyncio.sleep(0.2)

                if (
                        agent_task.done() or is_stopped
                ):  # If stopped or task finished while paused
                    break

                # If resumed, yield UI update
                yield {
                    pause_resume_button_comp: gr.update(
                        value="⏸️ 暂停", interactive=True
                    ),
                    run_button_comp: gr.update(
                        value="⏳ 运行中...", interactive=False
                    ),
                }

            # Check if agent stopped itself or stop button was pressed (which sets agent.state.stopped)
            if is_stopped:
                logger.info("Agent has stopped (internally or via stop button).")
                if not agent_task.done():
                    # Ensure the task coroutine finishes if agent just set flag
                    try:
                        await asyncio.wait_for(
                            agent_task, timeout=1.0
                        )  # Give it a moment to exit run()
                    except asyncio.TimeoutError:
                        logger.warning(
                            "Agent task did not finish quickly after stop signal, cancelling."
                        )
                        agent_task.cancel()
                    except Exception:  # Catch task exceptions if it errors on stop
                        pass
                break  # Exit the streaming loop

            # Check if agent is asking for help (via response_event)
            update_dict = {}
            if webui_manager.bu_response_event is not None:
                update_dict = {
                    user_input_comp: gr.update(
                        placeholder="智能体需要协助，请输入回复并提交。",
                        interactive=True,
                    ),
                    run_button_comp: gr.update(
                        value="✔️ 提交回复", interactive=True
                    ),
                    pause_resume_button_comp: gr.update(interactive=False),
                    stop_button_comp: gr.update(interactive=False),
                    chatbot_comp: gr.update(value=webui_manager.bu_chat_history),
                }
                last_chat_len = len(webui_manager.bu_chat_history)
                yield update_dict
                # Wait until response is submitted or task finishes
                await webui_manager.bu_response_event.wait()

                # Restore UI after response submitted or if task ended unexpectedly
                if not agent_task.done():
                    yield {
                        user_input_comp: gr.update(
                            placeholder="智能体运行中...", interactive=False
                        ),
                        run_button_comp: gr.update(
                            value="⏳ 运行中...", interactive=False
                        ),
                        pause_resume_button_comp: gr.update(interactive=True),
                        stop_button_comp: gr.update(interactive=True),
                    }
                else:
                    break  # Task finished while waiting for response

            # Update Chatbot if new messages arrived via callbacks
            if len(webui_manager.bu_chat_history) > last_chat_len:
                update_dict[chatbot_comp] = gr.update(
                    value=webui_manager.bu_chat_history
                )
                last_chat_len = len(webui_manager.bu_chat_history)

            # Update Browser View
            if headless and webui_manager.bu_browser_context:
                try:
                    screenshot_b64 = (
                        await webui_manager.bu_browser_context.take_screenshot()
                    )
                    if screenshot_b64:
                        html_content = f'<img src="data:image/jpeg;base64,{screenshot_b64}" style="width:{stream_vw}vw; height:{stream_vh}vh ; border:1px solid #ccc;">'
                        update_dict[browser_view_comp] = gr.update(
                            value=html_content, visible=True
                        )
                    else:
                        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>等待浏览器会话...</h1>"
                        update_dict[browser_view_comp] = gr.update(
                            value=html_content, visible=True
                        )
                except Exception as e:
                    logger.debug(f"Failed to capture screenshot: {e}")
                    update_dict[browser_view_comp] = gr.update(
                        value="<div style='...'>加载视图失败...</div>",
                        visible=True,
                    )
            else:
                update_dict[browser_view_comp] = gr.update(visible=False)

            # Yield accumulated updates
            if update_dict:
                yield update_dict

            await asyncio.sleep(0.1)  # Polling interval

        # --- 7. Task Finalization ---
        webui_manager.bu_agent.state.paused = False
        webui_manager.bu_agent.state.stopped = False
        final_update = {}
        try:
            logger.info("Agent task completing...")
            # Await the task ensure completion and catch exceptions if not already caught
            if not agent_task.done():
                await agent_task  # Retrieve result/exception
            elif agent_task.exception():  # Check if task finished with exception
                agent_task.result()  # Raise the exception to be caught below
            logger.info("Agent task completed processing.")

            logger.info(f"Explicitly saving agent history to: {history_file}")
            webui_manager.bu_agent.save_history(history_file)

            if os.path.exists(history_file):
                final_update[history_file_comp] = gr.update(value=history_file)

            if gif_path and os.path.exists(gif_path):
                logger.info(f"GIF found at: {gif_path}")
                final_update[gif_comp] = gr.update(value=gif_path)

        except asyncio.CancelledError:
            logger.info("Agent task was cancelled.")
            if not any(
                    "Cancelled" in msg.get("content", "")
                    for msg in webui_manager.bu_chat_history
                    if msg.get("role") == "assistant"
            ):
                webui_manager.bu_chat_history.append(
                    {"role": "assistant", "content": "**Task Cancelled**."}
                )
            final_update[chatbot_comp] = gr.update(value=webui_manager.bu_chat_history)
        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            error_message = (
                f"**Agent Execution Error:**\n```\n{type(e).__name__}: {e}\n```"
            )
            if not any(
                    error_message in msg.get("content", "")
                    for msg in webui_manager.bu_chat_history
                    if msg.get("role") == "assistant"
            ):
                webui_manager.bu_chat_history.append(
                    {"role": "assistant", "content": error_message}
                )
            final_update[chatbot_comp] = gr.update(value=webui_manager.bu_chat_history)
            gr.Error(f"Agent execution failed: {e}")

        finally:
            webui_manager.bu_current_task = None  # Clear the task reference

            # Close browser/context if requested
            if should_close_browser_on_finish:
                if webui_manager.bu_browser_context:
                    logger.info("Closing browser context after task.")
                    await webui_manager.bu_browser_context.close()
                    webui_manager.bu_browser_context = None
                if webui_manager.bu_browser:
                    logger.info("Closing browser after task.")
                    await webui_manager.bu_browser.close()
                    webui_manager.bu_browser = None

            # --- 8. Final UI Update ---
            final_update.update(
                {
                    user_input_comp: gr.update(
                        value="",
                        interactive=True,
                        placeholder="请输入下一条任务指令...",
                    ),
                    run_button_comp: gr.update(value="▶️ 提交任务", interactive=True),
                    stop_button_comp: gr.update(value="⏹️ 停止", interactive=False),
                    pause_resume_button_comp: gr.update(
                        value="⏸️ 暂停", interactive=False
                    ),
                    clear_button_comp: gr.update(interactive=True),
                    # Ensure final chat history is shown
                    chatbot_comp: gr.update(value=webui_manager.bu_chat_history),
                }
            )
            yield final_update

    except Exception as e:
        # Catch errors during setup (before agent run starts)
        logger.error(f"Error setting up agent task: {e}", exc_info=True)
        webui_manager.bu_current_task = None  # Ensure state is reset
        yield {
            user_input_comp: gr.update(
                interactive=True, placeholder="初始化失败，请重新输入任务指令..."
            ),
            run_button_comp: gr.update(value="▶️ 提交任务", interactive=True),
            stop_button_comp: gr.update(value="⏹️ 停止", interactive=False),
            pause_resume_button_comp: gr.update(value="⏸️ 暂停", interactive=False),
            clear_button_comp: gr.update(interactive=True),
            chatbot_comp: gr.update(
                value=webui_manager.bu_chat_history
                      + [{"role": "assistant", "content": f"**初始化错误：** {e}"}]
            ),
        }


# --- Button Click Handlers --- (Need access to webui_manager)


async def handle_submit(
        webui_manager: WebuiManager, components: Dict[gr.components.Component, Any]
):
    """Handles clicks on the main 'Submit' button."""
    user_input_comp = webui_manager.get_component_by_id("browser_use_agent.user_input")
    context_comp = webui_manager.get_component_by_id("browser_use_agent.dynamic_context")
    fields_valid_comp = webui_manager.get_component_by_id("browser_use_agent.fields_valid")
    user_input_value = (components.get(user_input_comp) or "").strip()
    context_value = (components.get(context_comp) or "").strip()
    fields_valid_value = str(components.get(fields_valid_comp) or "1").strip()
    if fields_valid_value == "0":
        gr.Warning("存在必填字段未补全，请先完善业务数据。")
        yield {}
        return
    if context_value:
        user_input_value = (
            f"已知业务数据：{context_value}。\n\n请执行以下指令：\n{user_input_value}"
            if user_input_value
            else f"已知业务数据：{context_value}。"
        )
    user_input_value = _inject_login_disambiguation(user_input_value)
    components[user_input_comp] = user_input_value

    # Check if waiting for user assistance
    if webui_manager.bu_response_event and not webui_manager.bu_response_event.is_set():
        logger.info(f"User submitted assistance: {user_input_value}")
        webui_manager.bu_user_help_response = (
            user_input_value if user_input_value else "User provided no text response."
        )
        webui_manager.bu_response_event.set()
        # UI updates handled by the main loop reacting to the event being set
        yield {
            user_input_comp: gr.update(
                value="",
                interactive=False,
                placeholder="等待智能体继续...",
            ),
            webui_manager.get_component_by_id(
                "browser_use_agent.run_button"
            ): gr.update(value="⏳ 运行中...", interactive=False),
        }
    # Check if a task is currently running (using _current_task)
    elif webui_manager.bu_current_task and not webui_manager.bu_current_task.done():
        logger.warning(
            "Submit button clicked while agent is already running and not asking for help."
        )
        gr.Info("智能体正在运行中，请等待，或使用“停止/暂停”。")
        yield {}  # No change
    else:
        # Handle submission for a new task
        logger.info("Submit button clicked for new task.")
        # Use async generator to stream updates from run_agent_task
        async for update in run_agent_task(webui_manager, components):
            yield update


async def handle_extract_business_data(
        webui_manager: WebuiManager, components: Dict[gr.components.Component, Any]
):
    upload_comp = webui_manager.get_component_by_id("browser_use_agent.upload_file")
    spec_comp = webui_manager.get_component_by_id("browser_use_agent.skill_spec_json")
    result_comp = webui_manager.get_component_by_id("browser_use_agent.extract_result_json")
    context_comp = webui_manager.get_component_by_id("browser_use_agent.dynamic_context")
    file_value = components.get(upload_comp)
    spec_json = str(components.get(spec_comp) or "")
    fields = _normalize_required_fields(spec_json)
    if not fields:
        gr.Warning("当前技能未配置字段，请先在业务指令集中扩展字段。")
        return {
            result_comp: gr.update(value="{}"),
            context_comp: gr.update(value=""),
        }
    source_text = _read_uploaded_file_text(file_value)
    if not source_text.strip():
        gr.Warning("未检测到可解析的上传内容，请重新上传文本或 PDF 文件。")
        prefill = {f["key"]: str(f.get("default", "") or "") for f in fields}
        return {
            result_comp: gr.update(value=json.dumps(prefill, ensure_ascii=False)),
            context_comp: gr.update(value=""),
        }

    def get_setting(key, default=None):
        comp = webui_manager.id_to_component.get(f"agent_settings.{key}")
        if not comp:
            return default
        val = components.get(comp, None)
        return default if val is None else val

    extracted = await _extract_by_llm(
        provider=get_setting("llm_provider", None),
        model_name=get_setting("llm_model_name", None),
        temperature=get_setting("llm_temperature", 0.3),
        base_url=get_setting("llm_base_url") or None,
        api_key=get_setting("llm_api_key") or None,
        num_ctx=get_setting("ollama_num_ctx", 16000),
        fields=fields,
        source_text=source_text,
    )
    context_pairs = {}
    extract_map = {}
    for f in fields:
        key = f["key"]
        value = str(extracted.get(key, "") or f.get("default", "") or "")
        extract_map[key] = value
        if value.strip():
            context_pairs[f["name"]] = value
    context_text = json.dumps(context_pairs, ensure_ascii=False)
    gr.Info("AI 提取完成，可在动态表单中继续补全。")
    return {
        result_comp: gr.update(value=json.dumps(extract_map, ensure_ascii=False)),
        context_comp: gr.update(value=context_text),
    }


async def handle_stop(webui_manager: WebuiManager):
    """Handles clicks on the 'Stop' button."""
    logger.info("Stop button clicked.")
    agent = webui_manager.bu_agent
    task = webui_manager.bu_current_task

    if agent and task and not task.done():
        # Signal the agent to stop by setting its internal flag
        agent.state.stopped = True
        agent.state.paused = False  # Ensure not paused if stopped
        return {
            webui_manager.get_component_by_id(
                "browser_use_agent.stop_button"
            ): gr.update(interactive=False, value="⏹️ 正在停止..."),
            webui_manager.get_component_by_id(
                "browser_use_agent.pause_resume_button"
            ): gr.update(interactive=False),
            webui_manager.get_component_by_id(
                "browser_use_agent.run_button"
            ): gr.update(interactive=False),
        }
    else:
        logger.warning("Stop clicked but agent is not running or task is already done.")
        # Reset UI just in case it's stuck
        return {
            webui_manager.get_component_by_id(
                "browser_use_agent.run_button"
            ): gr.update(interactive=True),
            webui_manager.get_component_by_id(
                "browser_use_agent.stop_button"
            ): gr.update(interactive=False),
            webui_manager.get_component_by_id(
                "browser_use_agent.pause_resume_button"
            ): gr.update(interactive=False),
            webui_manager.get_component_by_id(
                "browser_use_agent.clear_button"
            ): gr.update(interactive=True),
        }


async def handle_pause_resume(webui_manager: WebuiManager):
    """Handles clicks on the 'Pause/Resume' button."""
    agent = webui_manager.bu_agent
    task = webui_manager.bu_current_task

    if agent and task and not task.done():
        if agent.state.paused:
            logger.info("Resume button clicked.")
            agent.resume()
            # UI update happens in main loop
            return {
                webui_manager.get_component_by_id(
                    "browser_use_agent.pause_resume_button"
                ): gr.update(value="⏸️ 暂停", interactive=True)
            }  # Optimistic update
        else:
            logger.info("Pause button clicked.")
            agent.pause()
            return {
                webui_manager.get_component_by_id(
                    "browser_use_agent.pause_resume_button"
                ): gr.update(value="▶️ 继续", interactive=True)
            }  # Optimistic update
    else:
        logger.warning(
            "Pause/Resume clicked but agent is not running or doesn't support state."
        )
        return {}  # No change


async def handle_clear(webui_manager: WebuiManager):
    """Handles clicks on the 'Clear' button."""
    logger.info("Clear button clicked.")

    # Stop any running task first
    task = webui_manager.bu_current_task
    if task and not task.done():
        logger.info("Clearing requires stopping the current task.")
        webui_manager.bu_agent.stop()
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=2.0)  # Wait briefly
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        except Exception as e:
            logger.warning(f"Error stopping task on clear: {e}")
    webui_manager.bu_current_task = None

    if webui_manager.bu_controller:
        await webui_manager.bu_controller.close_mcp_client()
        webui_manager.bu_controller = None
    webui_manager.bu_agent = None

    # Reset state stored in manager
    webui_manager.bu_chat_history = []
    webui_manager.bu_response_event = None
    webui_manager.bu_user_help_response = None
    webui_manager.bu_agent_task_id = None

    logger.info("Agent state and browser resources cleared.")

    # Reset UI components
    return {
        webui_manager.get_component_by_id("browser_use_agent.chatbot"): gr.update(
            value=[]
        ),
        webui_manager.get_component_by_id("browser_use_agent.user_input"): gr.update(
            value="", placeholder="在此输入任务指令..."
        ),
        webui_manager.get_component_by_id(
            "browser_use_agent.agent_history_file"
        ): gr.update(value=None),
        webui_manager.get_component_by_id("browser_use_agent.recording_gif"): gr.update(
            value=None
        ),
        webui_manager.get_component_by_id("browser_use_agent.browser_view"): gr.update(
            value="<div style='...'>浏览器已清空</div>"
        ),
        webui_manager.get_component_by_id("browser_use_agent.run_button"): gr.update(
            value="▶️ 提交任务", interactive=True
        ),
        webui_manager.get_component_by_id("browser_use_agent.stop_button"): gr.update(
            interactive=False
        ),
        webui_manager.get_component_by_id(
            "browser_use_agent.pause_resume_button"
        ): gr.update(value="⏸️ 暂停", interactive=False),
        webui_manager.get_component_by_id("browser_use_agent.clear_button"): gr.update(
            interactive=True
        ),
    }


# --- Tab Creation Function ---


def create_browser_use_agent_tab(webui_manager: WebuiManager):
    """
    Create the run agent tab, defining UI, state, and handlers.
    """
    webui_manager.init_browser_use_agent()

    # --- Define UI Components ---
    tab_components = {}
    with gr.Column():
        chatbot = gr.Chatbot(
            lambda: webui_manager.bu_chat_history,  # Load history dynamically
            elem_id="browser_use_chatbot",
            label="智能体交互",
            type="messages",
            height=600,
            show_copy_button=True,
        )
        with gr.Group():
            gr.Markdown("### 业务数据（AI提取+动态补全增强版）")
            with gr.Row():
                skill_spec_json = gr.Textbox(
                    label="当前技能规格（由前端注入 JSON，仅包含 required_fields）",
                    value="",
                    lines=1,
                    interactive=False,
                    elem_id="skill_spec_json",
                    visible=False,
                )
                fields_valid = gr.Textbox(
                    label="字段有效性",
                    value="1",
                    interactive=False,
                    elem_id="fields_valid",
                    visible=False,
                )
                extract_result_json = gr.Textbox(
                    label="AI 提取结果 JSON",
                    value="{}",
                    interactive=False,
                    elem_id="extract_result_json",
                    visible=False,
                )
            with gr.Row():
                upload_file = gr.File(label="上传材料（可选）", file_count="single", interactive=True)
                extract_button = gr.Button("🧠 AI 提取", variant="secondary")
            dynamic_form_view = gr.HTML(value="<div id='lobster-run-dynamic-form'></div>", visible=True)
            dynamic_context = gr.Textbox(
                label="合成上下文（自动生成，可编辑）",
                lines=2,
                interactive=True,
                elem_id="dynamic_context",
            )
        user_input = gr.Textbox(
            label="任务指令",
            placeholder="在此输入任务指令，或在需要时提供回复。",
            lines=3,
            interactive=True,
            elem_id="user_input",
        )
        with gr.Row():
            stop_button = gr.Button(
                "⏹️ 停止", interactive=False, variant="stop", scale=2
            )
            pause_resume_button = gr.Button(
                "⏸️ 暂停", interactive=False, variant="secondary", scale=2, visible=True
            )
            clear_button = gr.Button(
                "🗑️ 清空", interactive=True, variant="secondary", scale=2
            )
            run_button = gr.Button("▶️ 提交任务", variant="primary", scale=3, elem_id="run_button")

        browser_view = gr.HTML(
            value="<div style='width:100%; height:50vh; display:flex; justify-content:center; align-items:center; border:1px solid #ccc; background-color:#f0f0f0;'><p>浏览器视图（需要启用无头模式）</p></div>",
            label="浏览器实时视图",
            elem_id="browser_view",
            visible=False,
        )
        with gr.Column():
            gr.Markdown("### 任务输出")
            agent_history_file = gr.File(label="智能体历史 JSON", interactive=False)
            recording_gif = gr.Image(
                label="任务录制 GIF",
                format="gif",
                interactive=False,
                type="filepath",
            )

    # --- Store Components in Manager ---
    tab_components.update(
        dict(
            chatbot=chatbot,
            upload_file=upload_file,
            extract_button=extract_button,
            dynamic_form_view=dynamic_form_view,
            dynamic_context=dynamic_context,
            skill_spec_json=skill_spec_json,
            fields_valid=fields_valid,
            extract_result_json=extract_result_json,
            user_input=user_input,
            clear_button=clear_button,
            run_button=run_button,
            stop_button=stop_button,
            pause_resume_button=pause_resume_button,
            agent_history_file=agent_history_file,
            recording_gif=recording_gif,
            browser_view=browser_view,
        )
    )
    webui_manager.add_components(
        "browser_use_agent", tab_components
    )  # Use "browser_use_agent" as tab_name prefix

    submit_inputs: list[Component] = []
    submit_inputs.append(webui_manager.get_component_by_id("browser_use_agent.user_input"))
    submit_inputs.append(webui_manager.get_component_by_id("browser_use_agent.dynamic_context"))
    submit_inputs.append(webui_manager.get_component_by_id("browser_use_agent.fields_valid"))
    submit_inputs.extend(
        [comp for comp_id, comp in webui_manager.id_to_component.items() if comp_id.startswith("agent_settings.")]
    )
    submit_inputs.extend(
        [comp for comp_id, comp in webui_manager.id_to_component.items() if comp_id.startswith("browser_settings.")]
    )
    run_tab_outputs = list(tab_components.values())

    async def submit_wrapper(*values) -> AsyncGenerator[Dict[Component, Any], None]:
        components_dict = {comp: val for comp, val in zip(submit_inputs, values)}
        async for update in handle_submit(webui_manager, components_dict):
            yield update

    async def stop_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        """Wrapper for handle_stop."""
        update_dict = await handle_stop(webui_manager)
        yield update_dict

    async def pause_resume_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        """Wrapper for handle_pause_resume."""
        update_dict = await handle_pause_resume(webui_manager)
        yield update_dict

    async def clear_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        """Wrapper for handle_clear."""
        update_dict = await handle_clear(webui_manager)
        yield update_dict

    async def extract_wrapper(*values) -> Dict[Component, Any]:
        extract_inputs = [webui_manager.get_component_by_id("browser_use_agent.upload_file"),
                          webui_manager.get_component_by_id("browser_use_agent.skill_spec_json")]
        extract_inputs.extend(
            [comp for comp_id, comp in webui_manager.id_to_component.items() if comp_id.startswith("agent_settings.")]
        )
        components_dict = {comp: val for comp, val in zip(extract_inputs, values)}
        return await handle_extract_business_data(webui_manager, components_dict)

    # --- Connect Event Handlers using the Wrappers --
    run_button.click(
        fn=submit_wrapper, inputs=submit_inputs, outputs=run_tab_outputs, trigger_mode="multiple"
    )
    user_input.submit(
        fn=submit_wrapper, inputs=submit_inputs, outputs=run_tab_outputs
    )
    extract_button.click(
        fn=extract_wrapper,
        inputs=[webui_manager.get_component_by_id("browser_use_agent.upload_file"),
                webui_manager.get_component_by_id("browser_use_agent.skill_spec_json")]
               + [comp for comp_id, comp in webui_manager.id_to_component.items() if comp_id.startswith("agent_settings.")],
        outputs=run_tab_outputs,
    )
    stop_button.click(fn=stop_wrapper, inputs=None, outputs=run_tab_outputs)
    pause_resume_button.click(
        fn=pause_resume_wrapper, inputs=None, outputs=run_tab_outputs
    )
    clear_button.click(fn=clear_wrapper, inputs=None, outputs=run_tab_outputs)
