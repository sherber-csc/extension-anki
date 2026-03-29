# FIELD_EXAMPLES.md

本文件用于补充 `SPEC.md`，通过具体示例说明各字段的真实数据长什么样，避免扩展、后端、Anki note type 在实现时对字段理解不一致。

---

## 1. 示例场景

用户在 YouTube 视频中看到一句话：

> Please retry the download if it doesn't start automatically.

用户实际选中的单词是：

> retry

为说明词形归并规则，系统在其他场景中也可能遇到以下形式：

> retry / retried / retrying / retries

这些形式最终都归并到：

> lemma = retry  
> word_key = retry

---

## 2. 采集阶段示例（扩展 -> 后端）

### 2.1 扩展采集到的原始请求示例

```json
{
  "surface_form": "retry",
  "source_sentence": "Please retry the download if it doesn't start automatically.",
  "source_title": "How to Fix Download Problems",
  "source_url": "https://www.youtube.com/watch?v=example123",
  "source_type": "youtube",
  "source_timestamp": "00:12:35",
  "captured_at": "2026-03-29T14:23:10+09:00"
}
```

### 2.2 字段解释

| 字段名             | 示例值                                                       | 中文含义   | 说明               |
| ------------------ | ------------------------------------------------------------ | ---------- | ------------------ |
| `surface_form`     | `retry`                                                      | 原始词形   | 用户实际选中的词   |
| `source_sentence`  | `Please retry the download if it doesn't start automatically.` | 来源原句   | 选词时所在原句     |
| `source_title`     | `How to Fix Download Problems`                               | 来源标题   | 页面/视频标题      |
| `source_url`       | `https://www.youtube.com/watch?v=example123`                 | 来源链接   | 页面 URL           |
| `source_type`      | `youtube`                                                    | 来源类型   | `web` 或 `youtube` |
| `source_timestamp` | `00:12:35`                                                   | 来源时间点 | 视频中的时间位置   |
| `captured_at`      | `2026-03-29T14:23:10+09:00`                                  | 采集时间   | 选词发生时间       |

---

## 3. 后端标准化与归并示例

后端收到 `surface_form = retry` 后，执行标准化和词形归并。

### 3.1 后端处理中间结果示例

```json
{
  "surface_form": "retry",
  "normalized_form": "retry",
  "lemma": "retry",
  "word_key": "retry"
}
```

### 3.2 词形归并补充示例

```json
[
  { "surface_form": "retry", "lemma": "retry", "word_key": "retry" },
  { "surface_form": "retried", "lemma": "retry", "word_key": "retry" },
  { "surface_form": "retrying", "lemma": "retry", "word_key": "retry" },
  { "surface_form": "retries", "lemma": "retry", "word_key": "retry" }
]
```

### 3.3 字段解释

| 字段名            | 示例值  | 中文含义   | 说明                                          |
| ----------------- | ------- | ---------- | --------------------------------------------- |
| `surface_form`    | `retry` | 原始词形   | 用户实际选中的形式                            |
| `normalized_form` | `retry` | 标准化词形 | 去空格、去首尾标点、统一小写后的结果          |
| `lemma`           | `retry` | 基础词形   | 词形归并后的核心词                            |
| `word_key`        | `retry` | 单词业务键 | 查重使用，第一版等于 `lemma` 的小写标准化结果 |

---

## 4. 队列项示例

### 4.1 待处理队列中的一条记录示例

```json
{
  "record_id": 101,
  "surface_form": "retry",
  "normalized_form": "retry",
  "lemma": "retry",
  "word_key": "retry",
  "source_sentence": "Please retry the download if it doesn't start automatically.",
  "source_title": "How to Fix Download Problems",
  "source_url": "https://www.youtube.com/watch?v=example123",
  "source_type": "youtube",
  "source_timestamp": "00:12:35",
  "captured_at": "2026-03-29T14:23:10+09:00",
  "status": "pending",
  "error_message": "",
  "generator_version": "v1"
}
```

### 4.2 字段解释

| 字段名              | 示例值    | 中文含义   | 说明                         |
| ------------------- | --------- | ---------- | ---------------------------- |
| `record_id`         | `101`     | 记录主键   | 这一条队列记录自己的唯一编号 |
| `word_key`          | `retry`   | 单词业务键 | 用于判断是不是同一个核心词   |
| `status`            | `pending` | 队列状态   | 当前还未生成正式卡           |
| `generator_version` | `v1`      | 生成版本号 | 这条记录对应的生成逻辑版本   |

---

## 5. 后端返回给扩展的状态示例

### 5.1 成功加入待处理

```json
{
  "status": "added_to_queue",
  "message": "Word added to pending queue.",
  "record_id": 101,
  "word_key": "retry",
  "lemma": "retry"
}
```

### 5.2 已在待处理队列中

```json
{
  "status": "already_in_queue",
  "message": "Word already exists in pending queue.",
  "record_id": 101,
  "word_key": "retry",
  "lemma": "retry"
}
```

### 5.3 已存在于 Anki

```json
{
  "status": "already_in_anki",
  "message": "Word already exists in Anki.",
  "word_key": "retry",
  "lemma": "retry"
}
```

### 5.4 输入不合法

```json
{
  "status": "invalid_input",
  "message": "Only single English words are supported."
}
```

---

## 6. 正式 Note Type 字段示例

### 6.1 一张正式 Anki 卡的数据示例

```json
{
  "word": "retry",
  "ipa": "/ˌriːˈtraɪ/",
  "emoji": "🔁",
  "audio": "retry_anki_audio.mp3",
  "image_prompt": "A person clicking a retry button on a computer screen.",
  "meanings": "[(verb) to try again after failure, (noun) an act of trying again)]",
  "forms": "retries / retried / retrying",
  "pairs": "[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]",
  "examples": "[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]",
  "record_id": 101,
  "word_key": "retry",
  "lemma": "retry",
  "surface_form": "retry",
  "source_url": "https://www.youtube.com/watch?v=example123",
  "source_type": "youtube",
  "source_timestamp": "00:12:35",
  "generator_version": "v1"
}
```

---

## 7. 展示字段示例

### 7.1 正面展示字段示例

| 字段名         | 示例值                                                   |
| -------------- | -------------------------------------------------------- |
| `word`         | `retry`                                                  |
| `ipa`          | `/ˌriːˈtraɪ/`                                            |
| `emoji`        | `🔁`                                                      |
| `audio`        | `retry_anki_audio.mp3`                                   |
| `image_prompt` | `A person clicking a retry button on a computer screen.` |

### 7.2 背面展示字段示例

| 字段名     | 示例值                                                       |
| ---------- | ------------------------------------------------------------ |
| `meanings` | `[(verb) to try again after failure, (noun) an act of trying again)]` |
| `forms`    | `retries / retried / retrying`                               |
| `pairs`    | `[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]` |
| `examples` | `[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]` |

---

## 8. 不展示字段示例

| 字段名              | 示例值                                       | 中文含义   |
| ------------------- | -------------------------------------------- | ---------- |
| `record_id`         | `101`                                        | 记录主键   |
| `word_key`          | `retry`                                      | 单词业务键 |
| `lemma`             | `retry`                                      | 基础词形   |
| `surface_form`      | `retry`                                      | 原始词形   |
| `source_url`        | `https://www.youtube.com/watch?v=example123` | 来源链接   |
| `source_type`       | `youtube`                                    | 来源类型   |
| `source_timestamp`  | `00:12:35`                                   | 来源时间点 |
| `generator_version` | `v1`                                         | 生成版本号 |

### 8.1 非主示例词形补充

在其他场景中，如果用户实际选中的是其他词形，则可能出现：

| `surface_form` | `lemma` | `word_key` |
| -------------- | ------- | ---------- |
| `retried`      | `retry` | `retry`    |
| `retrying`     | `retry` | `retry`    |
| `retries`      | `retry` | `retry`    |

---

## 9. examples 规则示例

### 9.1 有来源原句时

```json
{
  "examples": [
    "Please retry the download if it doesn't start automatically. (source sentence)",
    "I retried the task after fixing the error. (verb)",
    "You can retry the operation later. (verb)"
  ]
}
```

### 9.2 无来源原句时

```json
{
  "examples": [
    "I retried the task after fixing the error. (verb)",
    "You can retry the operation later. (verb)",
    "She will retry the process tomorrow. (verb)"
  ]
}
```

---

## 10. forms 规则示例

### 10.1 动词示例

| word    | forms                          |
| ------- | ------------------------------ |
| `retry` | `retries / retried / retrying` |
| `study` | `studies / studied / studying` |
| `fix`   | `fixes / fixed / fixing`       |

### 10.2 无明显常见变形时

可为空，或不渲染该字段。

---

## 11. 命名一致性要求

- 所有字段名必须与 `SPEC.md` 一致
- `record_id` 不能替代 `word_key`
- `word_key` 不能使用 `id:12333` 这类记录编号
- `word_key` 必须使用可读、稳定、可归并的业务值
- 第一版默认：`word_key = lemma 的小写标准化结果`

---

## 12. 当前示例中的关键映射关系

| 概念               | 示例值  | 说明              |
| ------------------ | ------- | ----------------- |
| 用户实际选中的词   | `retry` | `surface_form`    |
| 标准化后           | `retry` | `normalized_form` |
| 归并后的基础词形   | `retry` | `lemma`           |
| 查重使用的业务键   | `retry` | `word_key`        |
| 这条记录自己的编号 | `101`   | `record_id`       |

### 12.1 其他词形的映射关系补充

| 概念               | 示例值    | 说明              |
| ------------------ | --------- | ----------------- |
| 用户实际选中的词   | `retried` | `surface_form`    |
| 标准化后           | `retried` | `normalized_form` |
| 归并后的基础词形   | `retry`   | `lemma`           |
| 查重使用的业务键   | `retry`   | `word_key`        |
| 这条记录自己的编号 | `102`     | `record_id`       |