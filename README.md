# 局域共享 WebDAV（Windows 绿色版）

一个简单的 Windows WebDAV 文件共享工具。运行后选择目录、设置端口和账号密码，局域网设备可通过 WebDAV 客户端访问。

## GitHub Actions 编译

1. 新建 GitHub 仓库，例如 `lan-webdav`。
2. 上传本项目全部文件（包含 `.github/workflows/build.yml`）。
3. 打开仓库的 **Actions** 页面，运行 `Build Windows portable EXE`。
4. 构建成功后，在运行记录的 **Artifacts** 下载 `局域共享WebDAV-Windows-x64`。
5. 解压得到单文件 EXE，复制到任意目录即可运行，无需安装 Python。

## 使用

1. 双击 `局域共享WebDAV.exe`。
2. 选择共享文件夹，设置端口、用户名和强密码。
3. 点击“启动 WebDAV”。
4. 在另一台 Windows 电脑：文件资源管理器 → 此电脑 → 映射网络驱动器。
5. 文件夹地址填写 `http://共享主机IP:8080/`，按提示输入账号密码。

## 注意

- 默认监听 `0.0.0.0`，即所有网络接口；仅建议在可信局域网使用。
- 初次运行可能被 Windows 防火墙拦截，请允许本程序通过“专用网络”。
- Basic Auth 在纯 HTTP 下不加密凭据。只在可信局域网使用；跨公网请使用 HTTPS/VPN。
- WebDAV 文件锁并不等于所有 Office 软件都支持可靠的多人协同编辑。多人同时编辑同一文件时仍可能冲突。
- 只读模式由服务端限制写入。
