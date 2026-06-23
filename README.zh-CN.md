# Video-Audio-to-Text-Transcription 中文介绍

这是一个面向 Windows 本地使用的音视频转文字工具。它可以处理 B站链接、YouTube 链接、本地视频和本地音频，输出 `txt`、`srt`、`json` 三种格式。

本仓库只发布源码和部署脚本，不包含本机成品环境。也就是说，仓库里不会提交 `.venv`、ffmpeg、uv、模型文件、缓存、Cookie、下载的视频音频、转写结果和日志。别人 clone 后按说明准备本地工具和依赖即可部署。

## 主要功能

- 支持 B站视频转文字。
- 支持 YouTube 视频转文字。
- 支持本地视频和本地音频转文字。
- 默认使用 `faster-whisper`，适合有 NVIDIA 显卡的本地机器。
- 可选安装 `FunASR / SenseVoiceSmall`，用于中文口语识别对比。
- 可生成纯文本、字幕和结构化 JSON。
- 提供 PowerShell 命令行脚本和 Tkinter 本地 GUI。
- 缓存、模型、输出、日志都放在当前仓库目录下，方便迁移和清理。

## 适合谁用

这个工具适合想在本机离线或半离线处理音视频转写的人，比如：

- 把 B站或 YouTube 视频整理成文字稿。
- 给本地课程、访谈、会议录音生成字幕。
- 对比 `faster-whisper` 和 `FunASR` 的中文识别效果。
- 不想把音视频上传到第三方云服务。

## 部署方式

克隆仓库：

```powershell
git clone https://github.com/rbigo/Video-Audio-to-Text-Transcription.git
cd Video-Audio-to-Text-Transcription
```

手动准备以下本地工具：

```text
runtime\bin\uv.exe
runtime\ffmpeg\bin\ffmpeg.exe
runtime\ffmpeg\bin\ffprobe.exe
```

如果需要处理部分 YouTube JS challenge，可以额外放置：

```text
runtime\bin\deno.exe
```

初始化环境：

```powershell
.\scripts\bootstrap.ps1
.\scripts\doctor.ps1
```

如需 FunASR：

```powershell
.\scripts\bootstrap.ps1 -WithFunASR
```

## 常用命令

处理 B站链接：

```powershell
.\scripts\run.ps1 all "https://www.bilibili.com/video/BVxxxx"
```

处理 YouTube 链接：

```powershell
.\scripts\run.ps1 all "https://www.youtube.com/watch?v=xxxx"
```

处理本地音视频：

```powershell
.\scripts\run.ps1 transcribe "D:\path\to\video-or-audio.mp4"
```

对比两个识别引擎：

```powershell
.\scripts\run.ps1 compare "D:\path\to\audio.wav"
```

打开图形界面：

```powershell
.\scripts\gui.ps1
```

## Cookie 说明

项目默认不会自动读取 Chrome、Edge、Firefox 等浏览器 Cookie，也不会使用 `--cookies-from-browser`。

如果视频需要登录、年龄验证或权限校验，请手动导出 Netscape `cookies.txt` 格式的 Cookie，并放到：

```text
data\cookies\bilibili.txt
data\cookies\youtube.txt
```

这些 Cookie 文件已被 `.gitignore` 忽略，不能提交到仓库。

## 输出位置

运行产生的文件会放在当前仓库目录下：

```text
data\audio
data\subtitles
data\transcripts
data\logs
cache
models
```

这些目录都是本机运行状态，不会提交到 Git。

## 推荐配置

如果使用 RTX 3060 Ti 这类 8GB 显存显卡，日常建议：

```powershell
--engine faster-whisper --model large-v3-turbo --device cuda --compute-type float16 --language zh --vad
```

如果中文口语识别效果不满意，可以用 `compare` 跑一次 FunASR 对照；如果更看重字幕时间轴，通常优先使用 `faster-whisper` 的 SRT。

## 安全边界

- 不绕过 DRM。
- 不破解会员限制。
- 不上传用户音视频。
- 不把 Cookie 内容写入日志。
- 只处理用户有权下载、分析或转写的内容。
