from dotenv import load_dotenv
load_dotenv()
import argparse
import inspect
from src.webui.interface import theme_map, create_ui, get_logo_path


def main():
    parser = argparse.ArgumentParser(description="Gradio WebUI for Browser Agent")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Theme to use for the UI")
    args = parser.parse_args()

    demo = create_ui(theme_name=args.theme)
    launch_kwargs = {
        "server_name": args.ip,
        "server_port": args.port,
    }
    logo_path = get_logo_path()
    if logo_path and "favicon_path" in inspect.signature(demo.launch).parameters:
        launch_kwargs["favicon_path"] = logo_path
    demo.queue().launch(**launch_kwargs)


if __name__ == '__main__':
    main()
