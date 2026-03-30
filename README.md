# web-anki

一个本地运行的浏览器扩展 + Python 后端工具，用来把网页或 YouTube/Trancy 学习模式中的英文单词采集到待处理队列，再生成并写入 Anki。

## 当前能做什么

- 在普通网页上选中单个英文单词后，用 `Alt+Q` 采集
- 通过浏览器右键菜单 `Capture selected word` 采集
- 在 YouTube + Trancy 学习模式下，优先复用原生选区；原生选区为空时，尝试从 Trancy 字幕 token 做最小 fallback
- 采集后进入本地 pending 队列
- 在扩展 popup 中：
  - 查看 pending 列表
  - 删除单条 pending
  - 生成一条 pending 卡片
  - 一键按顺序生成全部 pending 卡片
- 后端负责：
  - 标准化输入
  - lemma / word_key 归并
  - 队列去重
  - Anki 查重
  - 调用 LLM 生成卡片内容
  - 写入 `SherberVocabNote`

## 目录结构

- [backend](D:/Codex/Project/web-anki/backend)：本地 Python 后端
- [extension](D:/Codex/Project/web-anki/extension)：Chrome/Edge 扩展
- [data](D:/Codex/Project/web-anki/data)：本地数据库和音频文件
- [tests](D:/Codex/Project/web-anki/tests)：测试
- [SPEC.md](D:/Codex/Project/web-anki/SPEC.md)：规格真源
- [FIELD_EXAMPLES.md](D:/Codex/Project/web-anki/FIELD_EXAMPLES.md)：字段示例
- [ARCHITECTURE.md](D:/Codex/Project/web-anki/ARCHITECTURE.md)：架构说明

## 运行前准备

你至少需要：

- Python
- Anki
- AnkiConnect 插件
- Chrome 或 Edge

### 1. 安装 Python 依赖

当前最少要保证 `nltk` 可用，因为 `lemmatizer` 现在会优先走 WordNet。

```bash
pip install nltk
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

### 2. 配置 `.env`

在项目根目录创建或修改 [`.env`](D:/Codex/Project/web-anki/.env)：

```env
LLM_API_KEY=your_minimax_api_key
LLM_BASE_URL=https://api.minimaxi.com/v1/chat/completions
LLM_REQUEST_TIMEOUT_SECONDS=180
```

说明：

- 不要把真实 key 提交到仓库
- `LLM_BASE_URL` 当前默认使用 MiniMax OpenAI 兼容接口

### 3. 启动 Anki 并准备 Note Type

先打开 Anki，并确认 AnkiConnect 已安装可用。

第一次使用时，执行：

```bash
python -m backend.setup_anki
```

它会确保：

- deck：`sherber`
- note type：`SherberVocabNote`

都已经准备好。

## 启动后端

推荐直接双击或执行：

```bat
start_backend.bat
```

等价命令是：

```bash
python -m backend.app
```

成功启动后，你会看到：

```text
Backend listening on http://127.0.0.1:8766
```

## 安装浏览器扩展

### Chrome / Edge 加载方式

1. 打开扩展管理页
   - Chrome：`chrome://extensions`
   - Edge：`edge://extensions`
2. 打开“开发者模式”
3. 选择“加载已解压的扩展程序”
4. 选择目录 [extension](D:/Codex/Project/web-anki/extension)

### 当前扩展权限

扩展当前会使用这些权限：

- `activeTab`
- `notifications`
- `contextMenus`
- `<all_urls>`
- `http://127.0.0.1:8766/*`

## 如何使用

### 方式 1：快捷键采词

在网页上选中一个单词，然后按：

```text
Alt+Q
```

扩展会复用同一条采集链：

- content script 收集 `surface_form / source_sentence / source_url`
- 后端做标准化、lemma、word_key、去重和 Anki 查重
- 返回轻提示

### 方式 2：右键菜单采词

在网页上右键后点击：

```text
Capture selected word
```

这个入口和 `Alt+Q` 复用同一条采集逻辑，不是另一套业务流程。

### 方式 3：扩展 popup 管理 pending

点击扩展图标后，可以看到 popup。

当前有 3 个主要按钮：

- `Generate all pending cards`
- `Generate pending cards`
- `Refresh`

每条 pending 记录还有自己的：

- `Delete`

### popup 当前支持的操作

- 查看 pending 数量
- 查看每条记录的：
  - `surface_form`
  - `lemma`
  - `word_key`
  - `captured_at`
- 删除指定 `record_id` 的 pending
- 生成最早一条 pending
- 按顺序生成全部 pending

## 当前行为说明

### 采集只支持“单个英文单词”

当前第一版仍然只支持：

- 单个英文单词

不支持：

- 短语
- 整句
- 多词批量采集

如果不是单词，常见提示是：

```text
当前仅支持单词
```

### 右键菜单与快捷键行为一致

右键菜单和 `Alt+Q`：

- 走同一条 capture 主链
- 使用同样的后端接口
- 使用同样的轻提示

### Trancy / YouTube 学习模式

在普通网页里，扩展优先依赖浏览器原生选区。

在 YouTube + Trancy 学习模式里，如果 `window.getSelection()` 没有返回可用文本，扩展会在 content script 里做最小 fallback：

- 先尝试读取你刚刚右键点中的字幕 token
- 再从当前英文字幕容器提取整句作为 `source_sentence`

这一步只影响 Trancy/YouTube 页面，不会改普通网页的原生 selection 路径。

## 常见状态提示

采集时常见提示包括：

- `已加入待处理`
- `已在待处理队列中`
- `该单词已存在于 Anki`
- `当前仅支持单词`
- `本地后端不可用`
- `采集失败`

## 建议使用顺序

1. 打开 Anki
2. 启动本地后端
3. 加载扩展
4. 在网页或 YouTube/Trancy 页面采词
5. 打开 popup 查看 pending
6. 先生成一条试跑
7. 没问题后再用 `Generate all pending cards`

## 常见问题

### 1. popup 里一直显示“本地后端不可用”

先确认后端是否启动：

```bash
python -m backend.app
```

并确认扩展 `host_permissions` 里仍然有：

```text
http://127.0.0.1:8766/*
```

### 2. 右键菜单出现了，但点击后还是提示“当前仅支持单词”

这通常说明：

- capture 链已经触发
- 但 content script 最终拿到的 `surface_form` 不是一个合格的单词

普通网页先确认是否真的只选中了一个词。  
Trancy/YouTube 页面则优先检查字幕 token 是否是当前右键目标。

### 3. 生成时失败

建议先分别确认：

- Anki 是否已打开
- AnkiConnect 是否可用
- `.env` 中的 LLM 配置是否正确
- `python -m backend.setup_anki` 是否已成功执行

### 4. `lemmatizer` 看起来不对

当前 `lemmatizer` 已经采用：

- `lemma_overrides.py` 显式修补层
- `WordNetLemmatizer` 作为主路径
- 安全回退原词

如果你要验证它，可以运行：

```bash
python -m unittest tests.test_lemmatizer -v
```

## 调试建议

如果你要排查采词问题，最有用的日志有两组：

### 页面侧日志

在网页 DevTools Console 中看：

```text
[Sherber][content-selection-debug]
```

它会显示：

- `raw_selection`
- `surface_form`
- `source_sentence`
- `fallback_source`

### background 侧日志

在扩展 service worker Console 中看：

```text
[Sherber][background-capture-debug]
```

它会显示最终发给后端前的：

- `surface_form`
- `source_sentence`
- `source_type`
- `source_url`

## 测试

常用测试命令：

```bash
python -m unittest tests.test_lemmatizer -v
python -m unittest tests.test_queue_manager tests.test_app_queue_delete tests.test_contracts -v
python -m unittest tests.test_generation_service tests.test_app_generate_all_pending tests.test_contracts -v
```

## 当前边界

这个项目目前仍然有一些明确边界：

- 采集端优先支持单词，不优先支持短语
- popup 负责触发和展示，不承载生成逻辑
- backend 承担正式生成、查重、状态回写
- 删除功能目前只允许删除 `pending`
- 批量生成目前只支持“按顺序生成全部 pending”
- 不支持并发生成、取消生成、重试失败项、删除 Anki 卡片

## 参考文档

如果你要继续开发，不要只看 README，优先看：

1. [SPEC.md](D:/Codex/Project/web-anki/SPEC.md)
2. [FIELD_EXAMPLES.md](D:/Codex/Project/web-anki/FIELD_EXAMPLES.md)
3. [ARCHITECTURE.md](D:/Codex/Project/web-anki/ARCHITECTURE.md)
4. [PROJECT_HANDOFF.md](D:/Codex/Project/web-anki/PROJECT_HANDOFF.md)
