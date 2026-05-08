import json
import os

import gradio as gr
from gradio.components import Component
from typing import Any, Dict, Optional
from src.webui.webui_manager import WebuiManager
from src.utils import config
import logging
from functools import partial

logger = logging.getLogger(__name__)


def update_model_dropdown(llm_provider):
    """
    Update the model name dropdown with predefined models for the selected provider.
    """
    # Use predefined models for the selected provider
    if llm_provider in config.model_names:
        return gr.Dropdown(choices=config.model_names[llm_provider], value=config.model_names[llm_provider][0],
                           interactive=True)
    else:
        return gr.Dropdown(choices=[], value="", interactive=True, allow_custom_value=True)


async def update_mcp_server(mcp_file: str, webui_manager: WebuiManager):
    """
    Update the MCP server.
    """
    if hasattr(webui_manager, "bu_controller") and webui_manager.bu_controller:
        logger.warning("⚠️ Close controller because mcp file has changed!")
        await webui_manager.bu_controller.close_mcp_client()
        webui_manager.bu_controller = None

    if not mcp_file or not os.path.exists(mcp_file) or not mcp_file.endswith('.json'):
        logger.warning(f"{mcp_file} is not a valid MCP file.")
        return None, gr.update(visible=False)

    with open(mcp_file, 'r') as f:
        mcp_server = json.load(f)

    return json.dumps(mcp_server, indent=2), gr.update(visible=True)


def create_agent_settings_tab(webui_manager: WebuiManager):
    """
    Creates an agent settings tab.
    """
    input_components = set(webui_manager.get_components())
    tab_components = {}

    with gr.Group():
        with gr.Column():
            override_system_prompt = gr.Textbox(label="覆盖系统提示词", lines=4, interactive=True, elem_id="override_system_prompt")
            extend_system_prompt = gr.Textbox(label="扩展系统提示词", lines=4, interactive=True, elem_id="extend_system_prompt")

    with gr.Group():
        mcp_json_file = gr.File(label="MCP 配置文件（JSON）", interactive=True, file_types=[".json"])
        mcp_server_config = gr.Textbox(label="MCP 配置内容", lines=6, interactive=True, visible=False)

    with gr.Group():
        with gr.Row():
            _provider_default = webui_manager.get_persisted("agent_settings.llm_provider", os.getenv("DEFAULT_LLM", "openai"))
            llm_provider = gr.Dropdown(
                choices=[provider for provider, model in config.model_names.items()],
                label="模型提供商",
                value=_provider_default,
                info="请选择使用的模型提供商",
                interactive=True
            )
            _model_choices = config.model_names[_provider_default] if _provider_default in config.model_names else []
            _model_default = webui_manager.get_persisted("agent_settings.llm_model_name", (_model_choices[0] if _model_choices else ""))
            llm_model_name = gr.Dropdown(
                label="模型名称",
                choices=_model_choices,
                value=_model_default,
                interactive=True,
                allow_custom_value=True,
                info="可从下拉列表选择，或直接输入自定义模型名称"
            )
        with gr.Row():
            _temp_default = webui_manager.get_persisted("agent_settings.llm_temperature", 0.6)
            try:
                _temp_default = float(_temp_default)
            except Exception:
                _temp_default = 0.6
            llm_temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=_temp_default,
                step=0.1,
                label="温度",
                info="控制模型输出的随机性",
                interactive=True
            )

            use_vision = gr.Checkbox(
                label="使用视觉",
                value=False,
                info="开启视觉（将高亮截图输入给模型）",
                interactive=True
            )

            ollama_num_ctx = gr.Slider(
                minimum=2 ** 8,
                maximum=2 ** 16,
                value=16000,
                step=1,
                label="Ollama 上下文长度",
                info="控制模型可处理的最大上下文长度（越小越快）",
                visible=False,
                interactive=True
            )

        with gr.Row():
            _base_url_default = webui_manager.get_persisted("agent_settings.llm_base_url", "")
            llm_base_url = gr.Textbox(
                label="基础地址",
                value=_base_url_default,
                info="API 基础地址（如需自定义）"
            )
            llm_api_key = gr.Textbox(
                label="API 密钥",
                type="password",
                value="",
                info="你的 API 密钥（留空则使用 .env）"
            )

    with gr.Group():
        with gr.Row():
            planner_llm_provider = gr.Dropdown(
                choices=[provider for provider, model in config.model_names.items()],
                label="规划器 模型提供商",
                info="请选择规划器使用的模型提供商",
                value=None,
                interactive=True
            )
            planner_llm_model_name = gr.Dropdown(
                label="规划器 模型名称",
                interactive=True,
                allow_custom_value=True,
                info="可从下拉列表选择，或直接输入自定义模型名称"
            )
        with gr.Row():
            planner_llm_temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=0.6,
                step=0.1,
                label="规划器 温度",
                info="控制模型输出的随机性",
                interactive=True
            )

            planner_use_vision = gr.Checkbox(
                label="使用视觉（规划器）",
                value=False,
                info="开启视觉（将高亮截图输入给模型）",
                interactive=True
            )

            planner_ollama_num_ctx = gr.Slider(
                minimum=2 ** 8,
                maximum=2 ** 16,
                value=16000,
                step=1,
                label="Ollama 上下文长度",
                info="控制模型可处理的最大上下文长度（越小越快）",
                visible=False,
                interactive=True
            )

        with gr.Row():
            planner_llm_base_url = gr.Textbox(
                label="基础地址",
                value="",
                info="API 基础地址（如需自定义）"
            )
            planner_llm_api_key = gr.Textbox(
                label="API 密钥",
                type="password",
                value="",
                info="你的 API 密钥（留空则使用 .env）"
            )

    with gr.Row():
        max_steps = gr.Slider(
            minimum=1,
            maximum=1000,
            value=100,
            step=1,
            label="最大操作步数",
            info="智能体执行的最大步骤数",
            interactive=True
        )
        max_actions = gr.Slider(
            minimum=1,
            maximum=100,
            value=10,
            step=1,
            label="单步最大动作数",
            info="智能体每一步可执行的最大动作数",
            interactive=True
        )

    with gr.Row():
        max_input_tokens = gr.Number(
            label="输入 Token 上限",
            value=128000,
            precision=0,
            interactive=True
        )
        tool_calling_method = gr.Dropdown(
            label="工具调用方式",
            value="auto",
            interactive=True,
            allow_custom_value=True,
            choices=['function_calling', 'json_mode', 'raw', 'auto', 'tools', "None"],
            visible=True
        )
    tab_components.update(dict(
        override_system_prompt=override_system_prompt,
        extend_system_prompt=extend_system_prompt,
        llm_provider=llm_provider,
        llm_model_name=llm_model_name,
        llm_temperature=llm_temperature,
        use_vision=use_vision,
        ollama_num_ctx=ollama_num_ctx,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        planner_llm_provider=planner_llm_provider,
        planner_llm_model_name=planner_llm_model_name,
        planner_llm_temperature=planner_llm_temperature,
        planner_use_vision=planner_use_vision,
        planner_ollama_num_ctx=planner_ollama_num_ctx,
        planner_llm_base_url=planner_llm_base_url,
        planner_llm_api_key=planner_llm_api_key,
        max_steps=max_steps,
        max_actions=max_actions,
        max_input_tokens=max_input_tokens,
        tool_calling_method=tool_calling_method,
        mcp_json_file=mcp_json_file,
        mcp_server_config=mcp_server_config,
    ))
    webui_manager.add_components("agent_settings", tab_components)

    llm_provider.change(
        fn=lambda x: gr.update(visible=x == "ollama"),
        inputs=llm_provider,
        outputs=ollama_num_ctx
    )
    llm_provider.change(
        lambda provider: update_model_dropdown(provider),
        inputs=[llm_provider],
        outputs=[llm_model_name]
    )
    planner_llm_provider.change(
        fn=lambda x: gr.update(visible=x == "ollama"),
        inputs=[planner_llm_provider],
        outputs=[planner_ollama_num_ctx]
    )
    planner_llm_provider.change(
        lambda provider: update_model_dropdown(provider),
        inputs=[planner_llm_provider],
        outputs=[planner_llm_model_name]
    )

    llm_provider.change(
        fn=lambda v: webui_manager.set_persisted("agent_settings.llm_provider", v),
        inputs=llm_provider,
        outputs=[]
    )
    llm_model_name.change(
        fn=lambda v: webui_manager.set_persisted("agent_settings.llm_model_name", v),
        inputs=llm_model_name,
        outputs=[]
    )
    llm_temperature.change(
        fn=lambda v: webui_manager.set_persisted("agent_settings.llm_temperature", v),
        inputs=llm_temperature,
        outputs=[]
    )
    llm_base_url.change(
        fn=lambda v: webui_manager.set_persisted("agent_settings.llm_base_url", v),
        inputs=llm_base_url,
        outputs=[]
    )

    async def update_wrapper(mcp_file):
        """Wrapper for handle_pause_resume."""
        update_dict = await update_mcp_server(mcp_file, webui_manager)
        yield update_dict

    mcp_json_file.change(
        update_wrapper,
        inputs=[mcp_json_file],
        outputs=[mcp_server_config, mcp_server_config]
    )
