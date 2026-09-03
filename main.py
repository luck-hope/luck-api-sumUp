"""
应用主入口：同时启动本地网关与 PyQt6 置顶桌面部件
"""
import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from ui.widget import FloatingTrackerWidget
from gateway.proxy import LocalGatewayProxy


async def main():
    app = QApplication(sys.argv)

    # 1. 实例化桌面悬浮部件
    widget = FloatingTrackerWidget(port=8045)
    widget.show()

    # 2. 实例化本地透明中继网关
    gateway = LocalGatewayProxy(
        port=8045,
        upstream_url="https://api.openai.com",
        on_token_update=widget.update_record
    )
    await gateway.start()
    print("[Gateway] Running on http://127.0.0.1:8045")

    # 3. 驱动 Qt 事件循环
    try:
        while True:
            app.processEvents()
            await asyncio.sleep(0.01)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        await gateway.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
