# 📁 Windows 文件夹注释工具

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
<img width="1095" height="896" alt="remark_screenshot" src="https://github.com/user-attachments/assets/f9239975-c20b-4cd2-a783-a2f13e785862" />

一个**带图形界面**的 Windows 小工具，用于给文件夹添加**自定义注释**（鼠标悬停时显示的文字说明），并支持**自定义图标/图片**，还内置了**备注搜索与保存**功能。

> 原理：通过修改文件夹下的隐藏系统文件 `Desktop.ini`，并给文件夹添加系统属性（`attrib +s`）来实现。

---

## ✨ 功能特性

- 🖥️ **图形化界面（GUI）**：无需命令行，双击即可运行，操作直观。
- 🖼️ **支持图片图标**：可以为文件夹设置自定义图片（`.jpg``.png`、`.bmp` 等）。
- 🔍 **备注搜索**：在已有备注的文件夹中快速搜索定位。
- 💾 **搜索记录保存**：自动保存搜索历史，方便重复使用。
- 📦 **双版本提供**：
  - **EXE 版**（推荐）：由 PyInstaller 打包，无需 Python 环境，双击 `remark.exe` 即可使用。
  - **源码版**：需要 Python 3.x 环境，运行 `remark.py`。

---

## 🚀 快速开始

### 方式一：EXE 版（推荐普通用户）

1. 下载本仓库的 `dist/remark/remark.exe` 文件。
2. **双击运行** `remark.exe`，打开图形界面。
3. 点击“浏览”选择目标文件夹，填写注释内容（支持多行）。
4. （可选）点击“选择图片”为文件夹设置自定义图标。
5. 点击“添加备注”完成修改，软件提示稍后可以看到备注。
6. 搜索备注下，指定搜索文件夹路径，可以开启预扫描（自动扫描）或 输入“搜索关键词”后，点击搜索。搜索到的文字和图片在预览器显示。
7. 
### 方式二：源码版（开发者/DIY）

```bash
# 1. 确保 Python 3.x 已安装
# 2. 克隆本仓库或下载 remark.py
# 3. 运行python remark.py


