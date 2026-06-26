# bili-whisper

Windows 本地 B站视频 / 本地视频 / 本地音频转文字工具。

功能：

- B站视频转文字
- 本地视频转文字
- 本地音频转文字
- 生成 `txt` / `srt` / `json`
- 默认使用 `faster-whisper`
- 可选使用 `FunASR`
- 默认不读取浏览器 Cookie
- 所有缓存、模型、输出、日志都固定在仓库根目录 `<repo>` 下

## 1. 自动准备运行组件

推荐直接运行：

```powershell
cd <repo>
.\scripts\bootstrap.ps1 -WithDeno -PreloadModels
.\scripts\doctor.ps1
```

bootstrap 会自动下载缺失的本地运行组件到仓库目录：

```text
<repo>\runtime\bin\uv.exe
<repo>\runtime\bin\deno.exe
<repo>\runtime\ffmpeg\bin\ffmpeg.exe
<repo>\runtime\ffmpeg\bin\ffprobe.exe
```

其中 `deno.exe` 只在 `-WithDeno` 时下载，用于部分 YouTube JS challenge 场景。

如果网络环境无法自动下载，也可以手动把这些文件放到上述路径，然后运行：

```powershell
.\scripts\bootstrap.ps1 -NoDownloadTools
```

## 2. 初始化

```powershell
cd <repo>
.\scripts\bootstrap.ps1 -WithDeno -PreloadModels
```

安装 FunASR 可选依赖并预下载 SenseVoiceSmall：

```powershell
.\scripts\bootstrap.ps1 -WithFunASR -WithDeno -PreloadModels
```

## 3. 预下载模型

首次转写时模型也会自动下载。若希望部署后先把默认模型准备好，可运行：

```powershell
.\scripts\run.ps1 preload-models --engine faster-whisper
```

已安装 FunASR 时，也可以一次预下载两套模型：

```powershell
.\scripts\run.ps1 preload-models --engine all
```

## 4. 检查环境

```powershell
.\scripts\doctor.ps1
```

`doctor.ps1` 会检查 Python、pip/uv/Hugging Face/ModelScope/Torch 缓存、ffmpeg、yt-dlp、faster-whisper、FunASR、torch、CUDA、nvidia-smi 和 GPU 信息。

如果输出中发现 `C:\`、`%USERPROFILE%` 或 `AppData` 等路径，会提示路径风险。系统自带的 `nvidia-smi.exe` 路径除外。

## 5. B站链接转文字

```powershell
.\scripts\run.ps1 all "https://www.bilibili.com/video/BVxxxx"
```

处理逻辑：

1. 优先尝试下载 B站已有字幕或自动字幕。
2. 如果有可用字幕，转换为 `txt` / `srt` / `json`。
3. 如果没有字幕，下载音频并转写。

## 5.1 YouTube 链接转文字

YouTube 也通过同一套 `yt-dlp + faster-whisper` 流程处理：

```powershell
.\scripts\run.ps1 all "https://www.youtube.com/watch?v=xxxx"
```

短链接也可以：

```powershell
.\scripts\run.ps1 all "https://youtu.be/xxxx"
```

## 6. 本地视频转文字

```powershell
.\scripts\run.ps1 transcribe "<repo>\data\downloads\test.mp4"
```

本地视频会先用 ffmpeg 提取为 `16kHz`、单声道、`pcm_s16le` WAV，再转写。

## 6.1 只把网页视频或已下载视频转换为音频

如果只想把 B站 / YouTube 链接或本地已下载视频提取成 WAV 音频，不做转写：

```powershell
.\scripts\run.ps1 extract-audio "https://www.bilibili.com/video/BVxxxx"
.\scripts\run.ps1 extract-audio "<repo>\data\downloads\test.mp4"
```

输出文件会写入：

```powershell
<repo>\data\audio
```

## 7. 本地音频转文字

```powershell
.\scripts\run.ps1 transcribe "<repo>\data\audio\test.wav"
```

本地音频会统一转换到适合 ASR 的 WAV 格式，输出仍在项目目录内。

## 8. 使用 faster-whisper

默认参数适合 RTX 3060 Ti：

```powershell
.\scripts\run.ps1 transcribe "<repo>\data\audio\test.wav" --engine faster-whisper --model large-v3-turbo --device cuda --compute-type float16
```

准确率优先可尝试：

```powershell
.\scripts\run.ps1 transcribe "<repo>\data\audio\test.wav" --engine faster-whisper --model large-v3 --compute-type int8_float16
```

CPU 兜底：

```powershell
.\scripts\run.ps1 transcribe "<repo>\data\audio\test.wav" --engine faster-whisper --model small --device cpu --compute-type int8
```

## 9. 使用 FunASR

先安装可选依赖：

```powershell
.\scripts\bootstrap.ps1 -WithFunASR
```

再运行：

```powershell
.\scripts\run.ps1 transcribe "<repo>\data\audio\test.wav" --engine funasr --model "iic/SenseVoiceSmall"
```

FunASR 模型和 ModelScope 缓存会固定在：

```text
<repo>\models\funasr
<repo>\cache\modelscope
```

## 10. 对比两个引擎

```powershell
.\scripts\run.ps1 compare "<repo>\data\audio\test.wav"
```

输出目录结构：

```text
<repo>\data\transcripts\视频名\faster-whisper\transcript.txt
<repo>\data\transcripts\视频名\faster-whisper\transcript.srt
<repo>\data\transcripts\视频名\faster-whisper\transcript.json
<repo>\data\transcripts\视频名\funasr\transcript.txt
<repo>\data\transcripts\视频名\funasr\transcript.srt
<repo>\data\transcripts\视频名\funasr\transcript.json
```

如果 FunASR 未安装，会提示：

```powershell
.\scripts\bootstrap.ps1 -WithFunASR
```

## 10.1 图形界面

启动本地 GUI：

```powershell
.\scripts\gui.ps1
```

GUI 支持粘贴 URL、选择本地音视频、选择 `faster-whisper` / `funasr` / `compare` / `extract-audio`，并可打开输出目录。

## 11. Cookie 使用方式

默认不使用浏览器 Cookie。

如果 B站视频需要登录，请手动导出 cookies 文件，并保存到：

```powershell
<repo>\data\cookies\bilibili.txt
```

如果 YouTube 视频需要登录、年龄验证或字幕权限，请手动导出 cookies 文件，并保存到：

```powershell
<repo>\data\cookies\youtube.txt
```

禁止自动读取 Chrome、Edge、Firefox 等浏览器 Cookie。项目不会使用 `--cookies-from-browser`。

## 12. 输出位置

转写结果：

```powershell
<repo>\data\transcripts
```

音频：

```powershell
<repo>\data\audio
```

字幕：

```powershell
<repo>\data\subtitles
```

日志：

```powershell
<repo>\data\logs
```

模型：

```powershell
<repo>\models
```

缓存：

```powershell
<repo>\cache
```

## 13. 如何确认没有写入 C 盘

运行：

```powershell
.\scripts\doctor.ps1
```

如果发现 C 盘、用户目录或 AppData 路径，doctor 会输出警告。

## 14. 安全说明

- 不绕过 DRM。
- 不破解会员限制。
- 不保存 Cookie 内容到日志。
- 不上传用户音视频。
- 默认全部本地处理。
- 仅处理用户有权下载、分析或转写的内容。
