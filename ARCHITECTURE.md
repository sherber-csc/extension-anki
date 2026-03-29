# ARCHITECTURE.md

本文件在 `SPEC.md` 和 `FIELD_EXAMPLES.md` 之下，用于固定实现层的模块边界、依赖方向和阶段性约束。

若本文件与 `SPEC.md` 冲突，以 `SPEC.md` 为准；若实现需要调整规格，必须先更新规格文档，再修改代码。

## 1. 总体分层

本项目固定拆成两层：

1. 浏览器扩展：只负责轻量采集和轻提示
2. 本地后端：负责标准化、归并、去重、队列、批量生成和 Anki 集成

一句话边界：

> 扩展负责拿到词，后端负责把词变成卡。

## 2. 协议真源

`backend/contracts.py` 是唯一协议真源，统一定义：

- 采集请求字段名
- 响应状态枚举
- 来源类型枚举
- 队列状态枚举
- 扩展提示文案映射

`extension/protocol.js` 必须由 `backend/contracts.py` 单向生成，不允许手工漂移。

同步规则固定如下：

1. 修改协议时，只修改 `backend/contracts.py`
2. 运行 `scripts/sync_extension_protocol.py`
3. 更新生成后的 `extension/protocol.js`
4. 运行 `tests/test_contracts.py`
5. 若 `extension/protocol.js` 未同步，测试必须失败

## 3. 观看阶段与 Anki 依赖

观看阶段采集主流程不依赖 Anki 已打开。

固定行为：

- 采集主流程先做标准化、归并、队列查重
- Anki 查重只在 AnkiConnect 可访问时进行
- 若 AnkiConnect 不可访问，采集仍可返回 `added_to_queue`
- 只有在 Anki 可访问时，才可能返回 `already_in_anki`
- 不能因为 Anki 不可用而返回 `processing_failed`

换言之：

> Anki 是批量生成阶段的强依赖，不是观看阶段采集的强依赖。

## 4. 队列层与正式 Note 层

`record_id` 是队列记录主键，必须存在于队列层。

根据 `SPEC.md` 和 `FIELD_EXAMPLES.md`，最终正式 note 的不展示字段中包含 `record_id`。

因此固定口径如下：

- 队列层必须保存 `record_id`
- 采集响应可返回 `record_id` 便于调试
- 后续正式 note 写入阶段，`record_id` 仍按规格进入正式 note 的不展示字段

当前实现约束：

- 第一阶段仅实现采集与队列，不实现正式 note 写入
- 因此当前阶段还没有真正执行“写入 Anki note 字段”这一步
- 这不是重新打开 `record_id` 的规格决策，而只是说明第一阶段尚未进入正式 note 写入代码

这个约束用于避免把“队列记录主键”和“正式 note 持久字段”混成一个层次。

## 5. forms 生成口径

`forms` 固定由后端生成，不由扩展生成，不依赖扩展传入。

第一版先收紧为：

- 只对可识别为动词的词生成 `forms`
- 非动词默认留空
- 不做名词复数
- 不做形容词比较级/最高级

顺序固定为：

1. third person singular
2. past
3. present participle

示例：

- `retry` -> `retries / retried / retrying`
- `study` -> `studies / studied / studying`

在模块边界上，`forms` 由 `backend/forms_builder.py` 负责；调用方必须提供明确的动词判断信号，若没有可靠动词判断，则返回空字符串。

## 6. generation_service 边界

`backend/generation_service.py` 只能做流程编排，不能膨胀成第二个 `main.py`。

固定调用边界如下：

1. `generation_service.py`：读取待处理项，协调调用，更新状态
2. `llm_client.py`：只负责结构化生成结果
3. `audio_service.py`：只负责音频生成
4. `example_builder.py`：只负责按规则构造 `examples`
5. `forms_builder.py`：只负责生成 `forms`
6. `note_mapper.py`：只负责把各模块结果映射成最终 note 字段
7. `anki_service.py`：只负责 Anki 可用性、启动、查重、写入

## 7. 扩展端 best effort 约束

`content.js` 对以下字段采用 best effort：

- `source_sentence`
- `source_timestamp`

规则固定为：

- 能拿到就传
- 拿不到就传空
- 不能因为取不到而阻塞加入待处理队列
- 第一版不为 YouTube 编写复杂字幕 DOM 解析面板

## 8. 第一阶段实现范围

第一阶段只实现：

- 协议层
- 配置层
- SQLite 队列
- 输入标准化
- 词形归并
- 采集接口
- 扩展到本地后端的最小调用链路

第一阶段不实现：

- 正式 note 写入
- LLM 调用
- 音频生成
- 批量生成正式卡片

但目录和接口会预留扩展位，避免后续返工。
