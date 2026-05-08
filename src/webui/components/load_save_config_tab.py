import gradio as gr
from gradio.components import Component

from src.webui.webui_manager import WebuiManager
from src.utils import config


def create_load_save_config_tab(webui_manager: WebuiManager):
    """
    Creates a load and save config tab.
    """
    input_components = set(webui_manager.get_components())
    tab_components = {}

    config_file = gr.File(
        label="Load UI Settings from json",
        file_types=[".json"],
        interactive=True
    )
    with gr.Row():
        load_config_button = gr.Button("Load Config", variant="primary")
        save_config_button = gr.Button("Save UI Settings", variant="primary")

    config_status = gr.Textbox(
        label="Status",
        lines=2,
        interactive=False
    )

    tab_components.update(dict(
        load_config_button=load_config_button,
        save_config_button=save_config_button,
        config_status=config_status,
        config_file=config_file,
    ))

    webui_manager.add_components("load_save_config", tab_components)

    all_inputs = list(webui_manager.get_components())
    def save_wrapper(*values):
        components_dict = {comp: val for comp, val in zip(all_inputs, values)}
        return webui_manager.save_config(components_dict)

    save_config_button.click(
        fn=save_wrapper,
        inputs=all_inputs,
        outputs=[config_status]
    )

    load_config_button.click(
        fn=webui_manager.load_config,
        inputs=[config_file],
        outputs=webui_manager.get_components(),
    )
