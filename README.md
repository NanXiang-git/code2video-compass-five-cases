# Code2Video-Compass 五题本地复现包

入口：打开 `index.html`。每题卡片可播放本地参考片段、关键帧和本次会话生成的答案视频；`animation.html?case=...` 可查看带时间轴的源码动画。

## 复现边界

- `answer_codex.mp4` 是 Codex 本次会话按官方题目和 QA 条件编写的本地答案，用于 OmniALE 的可播放复现基线；它不是 Code2Video-Compass 官方发布的模型输出，也没有冒充原作者视频。
- 四个 X 来源通过公开 FxTwitter 元数据解析到原始媒体 CDN 后保存；参考视频版权和使用条件仍以原作者/平台为准。
- C2VC-0035-i2v 首次下载跳转登录；重试公开网页版（普通浏览器 User-Agent，无登录/cookies）取得页面中的媒体地址，完整视频及 52.5 秒关键帧现已下载。失败日志和重试记录保留以便追溯。
- 数据集任务表与题目来源：`research/code2video/hf_preview_*_records.jsonl`；每题原始题目保存在 `cases/<id>/task.json` 和 `prompt.txt`。

## 目录

`index.html` 展示页；`cases/<id>/reference_full.mp4` 是下载的完整参考视频；`reference.mp4` / `reference.png` 是数据集指定片段或关键帧；`answer_codex.mp4` 是答案；`animation.html` 指向共享动画源；`reference_status.json` 记录来源获取状态。

## 答案方法与限制

每题提供一个答案：**Codex（本次会话，工具辅助迭代）**。模型根据官方 prompt、完整 QA、参考帧/片段截图及代码执行反馈编写共享 Canvas 渲染器。未调用第二个模型，也没有对同一题执行独立盲测。模型精确版本、采样参数和 token 消耗在当前会话接口中不可核验，故不作声明。

答案是简化的内容/机制重建：统一为 1280×720、24 fps、无音轨的 H.264 MP4；与原视频的竖屏/方形构图、手绘细节和转场并非逐像素一致。没有运行官方 PF/VQ/TA 等评分器，页面 QA 是待核对要求，并非通过结果。适合作为展示和选题包，不应直接用作论文的模型横评成绩。

- 水循环：包含 16 段因果流程；绘制与镜头运动较简化，部分转场为切换。
- Negroni：完整六步，实际搅拌 20 秒；总时长 52 秒（参考标题的 30 秒配方节奏未严格复刻）。
- Fourier：50 项波形谐波、301 个二维 DFT 系数实际计算；高音谱号与肖像为程序化近似，非原图复刻。
- 斗拱：按参考图修正了昂的方向和受力标注；装配为简化轴测图，十一建筑的比例曲线只表示趋势，不是实测数据；历史与结构不是工程计算结论。
- Verde：模拟 UI 工作流与政策文本、代码 diff；并未实际连接或修改 Claude、ChatGPT、Cursor、Verde 服务。

## 重新运行

依赖 Python 3、`requests`、`playwright`、Chrome 或 Edge、FFmpeg/FFprobe。HTML 直接双击即可浏览，不需要 Python 服务；只有重新生成视频需要上述依赖。

重新导出答案（默认 24 fps，也可 `--case C2VC-0035-i2v` 单独重跑）：

```powershell
E:\anaconda\python.exe render.py
```

重新获取来源：`python download_sources.py`（默认保留已有完整视频）。验证：`python verify.py`。

## 来源与许可

- [官方代码仓库](https://github.com/code2video-compass/Code2Video-Compass)：Apache-2.0（该许可针对上游代码，不自动覆盖媒体）。
- [官方数据集](https://huggingface.co/datasets/code2video-compass/Code2Video-Compass)：CC BY-NC 4.0；本包保留原始任务字段、链接和问答，并添加中文简介及本地答案。
- [官方展示站](https://code2video-compass.github.io/)：当前公开展示条目没有找到这五题的配套受测模型答案代码/成片。本包没有用其他案例冒充它们。
- 五段来源视频的作者与 URL 见每题 `task.json`、`source_metadata.json` / `reference_status.json`。原视频用于本地研究对照，版权与使用条件属于原作者及平台，不因任务表许可而改变。
- `manifest.json` 记录文件摘要、答案生成方式与来源状态。`verification/report.json` 记录视频解码、浏览器播放、离线文件链接和 UI 检查；不代表语义质量评分。
