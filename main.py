import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from cheroot.wsgi import Server
from wsgidav.wsgidav_app import WsgiDAVApp

APP_NAME = "局域共享 WebDAV"

def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

class WebDAVGui:
    def __init__(self, root):
        self.root = root
        root.title(APP_NAME)
        root.geometry("650x440")
        root.minsize(590, 400)
        self.server = None
        self.server_thread = None

        self.folder = tk.StringVar(value=str(Path.home() / "共享文件"))
        self.port = tk.StringVar(value="8080")
        self.username = tk.StringVar(value="webdav")
        self.password = tk.StringVar(value="")
        self.readonly = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="已停止")

        frame = ttk.Frame(root, padding=14)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="共享文件夹").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.folder).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(frame, text="选择…", command=self.choose_folder).grid(row=0, column=2)

        ttk.Label(frame, text="端口").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.port, width=12).grid(row=1, column=1, sticky="w", padx=8)

        ttk.Label(frame, text="用户名").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.username, width=24).grid(row=2, column=1, sticky="w", padx=8)

        ttk.Label(frame, text="密码").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.password, show="*", width=24).grid(row=3, column=1, sticky="w", padx=8)

        ttk.Checkbutton(frame, text="只读共享（禁止上传、修改和删除）",
                        variable=self.readonly).grid(row=4, column=1, sticky="w", padx=8, pady=6)

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=3, sticky="w", pady=10)
        self.start_btn = ttk.Button(buttons, text="启动 WebDAV", command=self.start_server)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(buttons, text="停止服务", command=self.stop_server, state="disabled")
        self.stop_btn.pack(side="left", padx=8)
        ttk.Label(buttons, textvariable=self.status).pack(side="left", padx=12)

        ttk.Label(frame, text="访问地址（在同一局域网的设备上使用）").grid(
            row=6, column=0, columnspan=3, sticky="w", pady=(8, 3))
        self.address = tk.Text(frame, height=3, wrap="word")
        self.address.grid(row=7, column=0, columnspan=3, sticky="nsew")
        self.address.insert("1.0", "启动后显示地址。Windows 可在资源管理器中选择“映射网络驱动器”。")
        self.address.configure(state="disabled")

        ttk.Label(frame, text="提示：请在 Windows 防火墙中允许本程序通过专用网络。").grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(8, 0))

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def choose_folder(self):
        selected = filedialog.askdirectory()
        if selected:
            self.folder.set(selected)

    def set_address(self, text):
        self.address.configure(state="normal")
        self.address.delete("1.0", "end")
        self.address.insert("1.0", text)
        self.address.configure(state="disabled")

    def start_server(self):
        folder = Path(self.folder.get()).expanduser()
        username = self.username.get().strip()
        password = self.password.get()
        try:
            port = int(self.port.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("端口错误", "端口必须是 1–65535 之间的整数。")
            return
        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("目录错误", "请选择一个存在的文件夹。")
            return
        if not username or not password:
            messagebox.showerror("账号错误", "请填写用户名和密码。")
            return
        if len(password) < 8:
            if not messagebox.askyesno("密码较短", "建议使用至少 8 位密码。仍要启动吗？"):
                return

        # WsgiDAV filesystem provider + Basic authentication
        config = {
            "host": "0.0.0.0",
            "port": port,
            "provider_mapping": {
                "/": {
                    "root": str(folder),
                    "readonly": self.readonly.get(),
                }
            },
            "http_authenticator": {
                "domain_controller": "wsgidav.dc.simple_dc.SimpleDomainController",
                "accept_basic": True,
                "accept_digest": False,
                "default_to_digest": False,
            },
            "simple_dc": {
                "user_mapping": {
                    "*": {
                        username: {
                            "password": password,
                            "roles": ["reader"] if self.readonly.get() else ["reader", "writer"],
                        }
                    }
                }
            },
            "verbose": 1,
            "logging": {"enable": False},
            "dir_browser": {"enable": True, "davmount": True},
            "lock_storage": True,
        }
        try:
            wsgi_app = WsgiDAVApp(config)
            self.server = Server(("0.0.0.0", port), wsgi_app)
            self.server_thread = threading.Thread(target=self.server.start, daemon=True)
            self.server_thread.start()
        except Exception as exc:
            self.server = None
            messagebox.showerror("启动失败", str(exc))
            return

        self.status.set("运行中")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        addresses = [f"http://本机局域网IP:{port}/"]
        try:
            import socket
            host = socket.gethostname()
            for info in socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM):
                ip = info[4][0]
                if not ip.startswith("127."):
                    addresses.append(f"http://{ip}:{port}/")
        except Exception:
            pass
        self.set_address("\n".join(dict.fromkeys(addresses)) +
                         f"\n账号：{username}    密码：启动时设置的密码")

    def stop_server(self):
        if self.server:
            try:
                self.server.stop()
            except Exception:
                pass
            self.server = None
        self.status.set("已停止")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.set_address("服务已停止。")

    def on_close(self):
        self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    WebDAVGui(root)
    root.mainloop()
