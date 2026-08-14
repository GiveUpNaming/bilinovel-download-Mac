

## 项目来源

本项目基于 [ShqWW/bilinovel-download](https://github.com/ShqWW/bilinovel-download) 修改。

Windows 版本、Chromium 下载流程、图形界面、漫画下载和 EPUB 生成功能均来自原项目。本仓库主要维护 macOS 与 Safari 的适配，不再重复介绍原项目已有功能；完整的 Windows 使用说明请查看原项目。

## 本仓库添加的内容

* 增加 macOS 支持，并通过 Selenium 调用系统 Safari 下载哔哩轻小说。
* 抽象 Safari 与 Chromium 浏览器后端：macOS 默认选择 Safari，其他系统默认选择 Chromium。
* 命令行增加 `--browser` 和 `--browser-path` 参数，可手动选择浏览器或指定 Chromium 可执行文件。
* 图形界面的设置页增加“自动 / Safari / Chromium”浏览器选项，并兼容已有配置。
* 针对 Safari 增加正文隐藏段落清理、缓存规避、旧页面检测重试和网页弹窗处理。
* 每个下载任务结束后关闭浏览器与线程池，便于在同一次命令行会话中继续下载其他书籍。
* 调整 EPUB 打包方式，使 `mimetype` 位于压缩包首项并保持不压缩，提高阅读器兼容性。
* 增加浏览器选择、Safari 页面处理、配置迁移和线程池关闭的测试。

## 安装

下载过慢换清华源
```bash
pip install -r requirements.txt
```

### Safari 首次设置

1. 打开 Safari，在“设置 > 高级”中启用网页开发者功能。
2. 打开“开发 > 开发者设置”，勾选“允许远程自动化”。
3. 在终端执行：

```bash
safaridriver --enable
```

## 执行示例

如果使用safari，使用前将safeguard（防弹窗插件）打开。使用其他浏览器的也打开各自的防弹窗插件。

下面的例子使用 Safari，将文件保存到 `./out`，请求间隔为 4500 毫秒，并使用 4 个插图下载线程：

```bash
python bilinovel.py \
  --browser safari \
  --out_path ./out \
  --interval 4500 \
  --num_thread 4
```

程序启动后按提示输入书号和卷号。例如：

```text
请输入书籍号：2704
请输入卷号(查看目录信息不输入直接按回车，下载多卷请使用逗号分隔或者连字符-)：1-3
```

卷号留空可先查看目录；输入 `1,3,5` 或 `1-3` 可下载多卷。一次任务完成后可以继续输入下一本书，按 `Ctrl+D` 退出。

图形界面仍可通过以下命令启动：

```bash
python main.py
```
