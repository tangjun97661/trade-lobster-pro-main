import os
from distutils.util import strtobool
import gradio as gr
import logging
from gradio.components import Component

from src.webui.webui_manager import WebuiManager
from src.utils import config

logger = logging.getLogger(__name__)

async def close_browser(webui_manager: WebuiManager):
    """
    Close browser
    """
    if webui_manager.bu_current_task and not webui_manager.bu_current_task.done():
        webui_manager.bu_current_task.cancel()
        webui_manager.bu_current_task = None

    if webui_manager.bu_browser_context:
        logger.info("⚠️ Closing browser context when changing browser config.")
        await webui_manager.bu_browser_context.close()
        webui_manager.bu_browser_context = None

    if webui_manager.bu_browser:
        logger.info("⚠️ Closing browser when changing browser config.")
        await webui_manager.bu_browser.close()
        webui_manager.bu_browser = None

def create_browser_settings_tab(webui_manager: WebuiManager):
    """
    Creates a browser settings tab.
    """
    input_components = set(webui_manager.get_components())
    tab_components = {}

    with gr.Group():
        with gr.Row():
            browser_binary_path = gr.Textbox(
                label="浏览器可执行文件路径",
                lines=1,
                interactive=True,
                placeholder="例如 '/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome'"
            )
            browser_user_data_dir = gr.Textbox(
                label="浏览器用户数据目录",
                lines=1,
                interactive=True,
                placeholder="如使用默认用户数据目录可留空",
            )
    with gr.Group():
        with gr.Row():
            use_own_browser = gr.Checkbox(
                label="使用本地浏览器",
                value=bool(strtobool(os.getenv("USE_OWN_BROWSER", "false"))),
                info="使用你本机现有的浏览器实例",
                interactive=True
            )
            _keep_default = webui_manager.get_persisted("browser_settings.keep_browser_open", bool(strtobool(os.getenv("KEEP_BROWSER_OPEN", "true"))))
            keep_browser_open = gr.Checkbox(
                label="保持浏览器常开",
                value=bool(_keep_default),
                info="在任务之间保持浏览器不关闭",
                interactive=True
            )
            _headless_default = webui_manager.get_persisted("browser_settings.headless", False)
            headless = gr.Checkbox(
                label="无头模式",
                value=bool(_headless_default),
                info="无图形界面运行浏览器",
                interactive=True
            )
            disable_security = gr.Checkbox(
                label="禁用安全策略",
                value=False,
                info="禁用浏览器安全策略",
                interactive=True
            )

    with gr.Group():
        with gr.Row():
            window_w = gr.Number(
                label="窗口宽度",
                value=1280,
                info="浏览器窗口宽度",
                interactive=True
            )
            window_h = gr.Number(
                label="窗口高度",
                value=1100,
                info="浏览器窗口高度",
                interactive=True
            )
    with gr.Group():
        with gr.Row():
            cdp_url = gr.Textbox(
                label="CDP 地址",
                value=os.getenv("BROWSER_CDP", None),
                info="用于浏览器远程调试的 CDP 地址",
                interactive=True,
            )
            wss_url = gr.Textbox(
                label="WSS 地址",
                info="用于浏览器远程调试的 WSS 地址",
                interactive=True,
            )
    with gr.Group():
        with gr.Row():
            save_recording_path = gr.Textbox(
                label="录制保存目录",
                placeholder="例如 ./tmp/record_videos",
                info="浏览器录屏文件保存目录",
                interactive=True,
            )

            save_trace_path = gr.Textbox(
                label="轨迹保存目录",
                placeholder="例如 ./tmp/traces",
                info="智能体运行轨迹保存目录",
                interactive=True,
            )

        with gr.Row():
            save_agent_history_path = gr.Textbox(
                label="智能体历史保存目录",
                value="./tmp/agent_history",
                info="指定智能体历史记录保存目录",
                interactive=True,
            )
            _download_default = webui_manager.get_persisted("browser_settings.save_download_path", os.getenv("OUTPUT_PATH", "./tmp/downloads")),
            save_download_path = gr.Textbox(
                label="浏览器下载保存目录",
                value=_download_default,
                info="指定浏览器下载文件保存目录",
                interactive=True,
            )
    tab_components.update(
        dict(
            browser_binary_path=browser_binary_path,
            browser_user_data_dir=browser_user_data_dir,
            use_own_browser=use_own_browser,
            keep_browser_open=keep_browser_open,
            headless=headless,
            disable_security=disable_security,
            save_recording_path=save_recording_path,
            save_trace_path=save_trace_path,
            save_agent_history_path=save_agent_history_path,
            save_download_path=save_download_path,
            cdp_url=cdp_url,
            wss_url=wss_url,
            window_h=window_h,
            window_w=window_w,
        )
    )
    webui_manager.add_components("browser_settings", tab_components)

    async def close_wrapper():
        """Wrapper for handle_clear."""
        await close_browser(webui_manager)

    headless.change(close_wrapper)
    keep_browser_open.change(close_wrapper)
    disable_security.change(close_wrapper)
    use_own_browser.change(close_wrapper)

    keep_browser_open.change(
        fn=lambda v: webui_manager.set_persisted("browser_settings.keep_browser_open", bool(v)),
        inputs=keep_browser_open,
        outputs=[]
    )
    headless.change(
        fn=lambda v: webui_manager.set_persisted("browser_settings.headless", bool(v)),
        inputs=headless,
        outputs=[]
    )
    save_download_path.change(
        fn=lambda v: webui_manager.set_persisted("browser_settings.save_download_path", v),
        inputs=save_download_path,
        outputs=[]
    )
