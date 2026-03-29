# ChatGPT - csc

**平台**: ChatGPT  
**导出时间**: 2026/03/29 01:24  
**对话数量**: 37

---

## 👤 用户

我之前anki的快速加入卡片的工具，现在我在使用YouTube或者网页的时候要打开桌面，点击start.bat平时的·时候不会特别麻烦，但是在使用YouTube的时候，开启字幕有的单词想要纪录就要暂停视频，我现在想有个功能，能够让我快速把字幕上的一个单词加入anki，怎么制作

## 🤖 AI

我先把方案分成“最低成本能用”和“真正顺手的工程化方案”两类。你这个需求本质不是“再开一个桌面工具”，而是“在浏览器里直接抓取当前选中的字幕词，并一键发到 Anki”。

---

## 👤 用户

(无问题)

## 🤖 AI

我已经确认了最关键的一点：别再走“打开桌面程序 → 点 start.bat”这条路径了。更对的做法是让浏览器扩展直接把你选中的词发给本机 Anki；AnkiConnect 本来就是给这种外部调用准备的，本机默认走 8765 端口。 github.com+1

---

## 👤 用户

(无问题)

## 🤖 AI

能做，而且不该继续用“手动开桌面工具”这种流程。你现在的问题不是 Anki 本身，而是交互链路太长：看到字幕里的词 → 暂停 → 切桌面 → 点 bat → 再录入。这个链路一长，学习动作就断了。

正确方案是：

浏览器扩展 + 快捷键 + AnkiConnect + （可选）本地词典补全

核心思路：

你在 YouTube 或网页里选中一个单词，或者让扩展自动读取当前字幕。

按一个快捷键，比如 Alt+Q。

扩展把这个词通过 HTTP POST 发给本机的 AnkiConnect。

Anki 直接建卡，不再打开你的 start.bat 流程。
AnkiConnect 本来就是给外部程序调用 Anki 用的，本机默认会起一个 HTTP 服务在 127.0.0.1:8765。Chrome 扩展的 Manifest V3 也支持定义快捷键命令、内容脚本和脚本注入。 Chrome for Developers+4GitHub+4GitHub+4

先说结论：你有两个可行级别

方案一：先做能用的 MVP

适合你现在立刻上手。

行为：

网页里选中单词

按快捷键

直接加到 Anki 的某个 deck / note type

字段先只填 word

优点：

最稳

最快做完

不依赖 YouTube 字幕 DOM 结构

缺点：

你得先手动选词

还没有自动带释义、例句、截图

方案二：做真正顺手的版本

行为：

在 YouTube 开字幕

扩展自动识别当前显示字幕文本

你点击某个词，或者按快捷键抓“当前光标附近/当前字幕中的单词”

自动查词典，补全 meaning / sentence / source URL / timestamp

优点：

真正适合视频场景

操作少

缺点：

工程复杂度明显更高

YouTube 页面结构会变，DOM 选择器容易失效

自动分词、自动抓字幕不如“用户选中”稳定

你现在最应该做的是：先做方案一，再迭代到方案二。
别一上来就追求“自动识别字幕里的单词 + 自动查词 + 自动截图 + 自动记录时间戳”。那是典型的功能贪多，最后一个都落不了地。

推荐架构

1）Anki 端

你先装 AnkiConnect。它提供本地 REST 接口，能让外部应用直接创建 note。官方 AnkiWeb 页面最近仍在更新，GitHub 上原仓库已经归档并迁移到新的地址，所以你别把“GitHub 归档”误判成“不能用了”。 ankiweb.net+1

2）浏览器端

做一个 Chrome 扩展，最低需要：

manifest.json

content.js

background.js 或 service_worker

一个可选的 popup.html

Chrome 的 Commands API 支持定义扩展快捷键；MV3 支持 service worker 和 content scripts。 Chrome for Developers+2Chrome for Developers+2

3）数据流

网页选中文字 -> content script -> service worker -> fetch("http://127.0.0.1:8765") -> AnkiConnect addNote

这条链路已经够了。

为什么我不建议你继续用 start.bat

因为这说明你当前工具是“主动打开”的，而不是“常驻等待触发”的。

更合理的是：

要么 Anki 平时开着，AnkiConnect 常驻

要么你自己的本地小服务常驻，浏览器只负责发请求

你现在这种模式，本质上还是“桌面程序思维”，不是“浏览器工作流思维”。

最小可用实现

manifest.json

```plaintext
JSON{  "manifest_version": 3,  "name": "Quick Add to Anki",  "version": "0.1.0",  "permissions": ["activeTab", "scripting"],  "host_permissions": [    "http://127.0.0.1:8765/*",    "https://www.youtube.com/*",    "<all_urls>"  ],  "background": {    "service_worker": "background.js"  },  "commands": {    "add-selected-word": {      "suggested_key": {        "default": "Alt+Q"      },      "description": "Add selected word to Anki"    }  }}
```

这里用到：

commands：注册快捷键 Chrome for Developers

host_permissions：允许访问本地 AnkiConnect 和页面内容 Chrome for Developers

background.js

```plaintext
JavaScriptchrome.commands.onCommand.addListener(async (command) => {  if (command !== "add-selected-word") return;  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });  if (!tab?.id) return;  const results = await chrome.scripting.executeScript({    target: { tabId: tab.id },    func: () => {      const selected = window.getSelection()?.toString().trim() || "";      return {        selected,        url: location.href,        title: document.title      };    }  });  const data = results?.[0]?.result;  if (!data?.selected) {    console.log("No selected text");    return;  }  const word = data.selected;  const payload = {    action: "addNote",    version: 6,    params: {      note: {        deckName: "English",        modelName: "Basic",        fields: {          Front: word,          Back: ""        },        tags: ["quick_add", "youtube"]      }    }  };  try {    const resp = await fetch("http://127.0.0.1:8765", {      method: "POST",      headers: { "Content-Type": "application/json" },      body: JSON.stringify(payload)    });    const json = await resp.json();    console.log("Anki response:", json);  } catch (err) {    console.error("Failed to connect to AnkiConnect:", err);  }});
```

这版已经能工作：

你选中网页中的单词

按 Alt+Q

直接进 Anki

如果你专门要支持 YouTube 字幕

这里你别想简单了。问题不在“能不能做”，而在“做得稳不稳”。

YouTube 视频本质上是网页里的 <video> 播放器，字幕是时间文本轨或其页面渲染层的一部分；HTML 视频和字幕本来就支持 text tracks / WebVTT 这类机制，但具体站点怎么把字幕渲染到页面，是站点自己决定的。也就是说，标准能力存在，不等于 YouTube 页面上给你一个永远稳定可抓的 DOM。 MDN Web Docs

所以你有两条路：

路线 A：仍然以“选中文字”为主

前提：字幕文本能选中
这最稳。

路线 B：扩展直接读当前字幕 DOM

你可以在 content script 里尝试抓 YouTube 当前字幕节点，例如查找页面里的字幕容器文本，然后提取当前显示内容。

伪代码：

```plaintext
JavaScriptfunction getCurrentYoutubeCaption() {  const nodes = document.querySelectorAll(    ".ytp-caption-segment, .ytp-caption-window-container"  );  const text = [...nodes].map(n => n.textContent?.trim() || "").join(" ").trim();  return text;}
```

但我要直接泼冷水：
这个方案会脆。
YouTube 一改类名、一改结构，你就得修。

所以更实用的做法是：

先让扩展支持“选中即加入”

再额外加一个“读取当前字幕整句”的按钮

把整句塞进 Anki 的 example sentence 字段

目标词仍然让你手动选

这才是稳定和效率的平衡点。

更适合你的字段设计

你之前 Anki 卡片字段不是只有一个 word。你有：

word

image

meaning

固定搭配

例句

那你别用 Basic 模型，应该改成你自己的 note type，比如 EnglishMine。

示例：

```plaintext
JavaScriptconst payload = {  action: "addNote",  version: 6,  params: {    note: {      deckName: "English::QuickAdd",      modelName: "EnglishMine",      fields: {        word: word,        image: "",        meaning: "",        固定搭配: "",        例句: currentSentence || ""      },      tags: ["quick_add", "youtube", "browser"]    }  }};
```

你真正该做的版本迭代顺序

第 1 步：做“选词 + 快捷键 + 加入 Anki”

目标：今天就能用

功能：

选中一个词

Alt+Q

加到指定 deck

成功后右下角 toast 提示

第 2 步：加来源信息

把这些也一起写进去：

当前页面 URL

页面标题

如果是 YouTube，再记录视频时间戳

第 3 步：加当前字幕整句

字段写入 例句

第 4 步：接词典 API

自动补：

meaning

搭配

IPA / 音标

词性

第 5 步：做悬浮按钮 / 右键菜单

不用只靠快捷键

你可能忽略的关键问题

1）不是所有字幕都能直接选中

自动字幕、站点自定义渲染、遮罩层，都可能导致 selection 取不到。

2）不是所有“选中的词”都该直接进 Anki

你需要先做清洗：

去标点

去首尾空格

全大写缩写要不要保留

多词短语要不要允许

最少也要有：

```plaintext
JavaScriptfunction normalizeWord(text) {  return text.trim().replace(/^[^\w'-]+|[^\w'-]+$/g, "");}
```

3）你不能把“快速加入”和“完整制卡”混成一个动作

快速加入的重点是不中断视频。
所以第一版只记 word + sentence + source 就够了。
释义、图片、固定搭配，应该留到后面批量补。

这一点很重要。你现在最大的设计风险就是想在“抓词”的那一秒顺手把所有字段都填满，结果操作更慢。

我给你的直接建议

别做桌面程序了。
做一个 Chrome 扩展 MVP：

快捷键：Alt+Q

逻辑：读取当前选中文本

接口：POST 到 127.0.0.1:8765

Anki note fields：先只写 word 和 例句

支持网页通用，YouTube 只是兼容之一，不要先绑死 YouTube

这条路线最对。

你下一步该怎么动手

按这个顺序：

先确认 AnkiConnect 已安装且 Anki 打开时本机 8765 可访问。 github.com+1

建一个 Chrome 扩展目录。

写 manifest.json

写 background.js

在 Chrome 扩展页加载“已解压的扩展程序”

打开任意网页，选中一个单词，按快捷键测试

成功后再接你自己的 Anki note type

你要是继续犹豫方案，就还是停留在想法层。
正确动作是先把 MVP 跑通。

我可以下一条直接给你一套可复制运行的完整 Chrome 扩展代码，包括：

manifest.json

background.js

可选 content.js

可选 toast 提示

针对你 Anki 字段名的版本

---

## 👤 用户

有没有办法连接我的start.bat或者是main.py直接在网页通过快捷键的功能自动输入单词，或者有一个新的，在我的ai-anki-bridge基础上，选取一个单词，自动按照我的哪个模板添加单词

## 🤖 AI

可以连，但你现在要先分清两种架构：
一种是“浏览器快捷键 → 调你现有的 start.bat/main.py”；另一种是“浏览器快捷键 → 直接调你 ai-anki-bridge 的接口/逻辑”。前者能做，但笨；后者才是对的。

---

## 👤 用户

(无问题)

## 🤖 AI

有，但你要选对路线。

结论先说：

网页本身不能直接执行你的 start.bat 或 main.py。 浏览器页面受沙箱限制，不能随便启动本地程序。要想从浏览器侧触发本地脚本，通常要么走 本地 HTTP 服务，要么走 Chrome 扩展 + Native Messaging。 Chrome for Developers+1

对你现在这个场景，最合理的不是“连 bat”，而是：
浏览器快捷键/选词 → 调你 ai-anki-bridge 的本地接口 → 再由它按你的模板写入 Anki。
因为 AnkiConnect 本来就是给外部应用通过本机 localhost:8765 这种 HTTP API 去创建 note 用的，而且 Anki 需要保持运行。 AnkiWeb+2GitHub+2

你提的两个方向，我直接给你判断：

方向 1：连接 start.bat / main.py

能做，但不推荐作为主方案。

为什么不推荐：

网页不能直接启动本地 bat/python。
你必须额外做一层桥接：


要么 Chrome 扩展用 Native Messaging 调本地宿主程序；


要么你先手动开一个本地服务，浏览器再发请求给它。 Chrome for Developers+1

start.bat 更像“启动器”，不是“稳定接口”。
每按一次快捷键都去拉起一个 Python 进程，笨、慢、容易出错。

你真正需要的是“接收一个词并按模板加卡”，这应该是一个常驻服务能力，不是一个“临时双击启动”的动作。

所以，能连，但别连 bat。
如果一定要复用你现有代码，也应该把 main.py 改造成一个本地 API 服务，而不是继续当桌面入口。

方向 2：在 ai-anki-bridge 基础上做“选词即加卡”

这是对的。

你应该把 ai-anki-bridge 分成两层：

第一层：浏览器触发层

负责：

获取当前网页选中的单词

读取当前页面 URL / 标题

绑定快捷键

发请求到本地服务

第二层：本地桥接层（你现有 ai-anki-bridge）

负责：

接收词

按你的模板映射字段

调 AnkiConnect addNote

返回成功/失败

这个架构才干净。
浏览器只负责“抓词”，Python 只负责“制卡”。

你现在最该做的架构

方案 A：最实用

Chrome 扩展 + 本地 Flask/FastAPI 服务 + AnkiConnect

数据流：

网页选中单词 → 按快捷键 → Chrome 扩展 fetch http://127.0.0.1:5001/add-word → 你的 Python 服务处理模板 → 调用 http://127.0.0.1:8765 → Anki

这条路的优点：

不需要 Native Messaging 的注册和宿主清单，开发成本低

能直接复用你现有 ai-anki-bridge

模板逻辑都放在 Python 里，后面好维护

支持 YouTube，也支持任意网页

这是我最推荐的。

方案 B：更原生但更麻烦

Chrome 扩展 + Native Messaging + 本地 Python 程序

这条路也能做，但更重：

你得注册 native host

配置 manifest

Chrome 通过 stdin/stdout 和本地程序通信 Chrome for Developers

这适合做“正式产品”，不适合你现在这种个人效率工具第一版。
你现在别碰这个，纯增加复杂度。

最优改法：把你的 main.py 改成 API 服务

你原来可能是这种思路：

start.bat -> python main.py -> 弹界面/命令行输入 -> 调 Anki

你应该改成：

python server.py 常驻
提供接口：

POST /add-word

POST /add-phrase

POST /add-from-selection

这样浏览器扩展只要发 JSON 给它。

你需要的 Python 服务长这样

用 FastAPI 或 Flask 都行。你如果想简单，Flask 就够了。

server.py

```plaintext
Python运行from flask import Flask, request, jsonifyimport requestsimport reapp = Flask(__name__)ANKI_CONNECT_URL = "http://127.0.0.1:8765"# 你的模板配置TEMPLATE = {    "deckName": "English::QuickAdd",    "modelName": "EnglishMine",   # 改成你的 note type    "fields": ["word", "image", "meaning", "固定搭配", "例句"]}def normalize_word(text: str) -> str:    if not text:        return ""    text = text.strip()    text = re.sub(r"^[^\w'-]+|[^\w'-]+$", "", text)    return textdef add_note_to_anki(word: str, sentence: str = "", source_url: str = "", title: str = ""):    note = {        "deckName": TEMPLATE["deckName"],        "modelName": TEMPLATE["modelName"],        "fields": {            "word": word,            "image": "",            "meaning": "",            "固定搭配": "",            "例句": sentence        },        "tags": ["quick_add", "browser"]    }    payload = {        "action": "addNote",        "version": 6,        "params": {            "note": note        }    }    resp = requests.post(ANKI_CONNECT_URL, json=payload, timeout=10)    resp.raise_for_status()    data = resp.json()    if data.get("error"):        raise RuntimeError(data["error"])    return data.get("result")@app.route("/add-word", methods=["POST"])def add_word():    data = request.get_json(force=True)    selected_text = data.get("word", "")    sentence = data.get("sentence", "")    source_url = data.get("url", "")    title = data.get("title", "")    word = normalize_word(selected_text)    if not word:        return jsonify({"ok": False, "error": "empty word"}), 400    note_id = add_note_to_anki(word, sentence, source_url, title)    return jsonify({"ok": True, "word": word, "note_id": note_id})if __name__ == "__main__":    app.run(host="127.0.0.1", port=5001, debug=True)
```

这才是“桥”。

然后浏览器扩展只干一件事：拿选中的词

manifest.json

```plaintext
JSON{  "manifest_version": 3,  "name": "Quick Add to Anki Bridge",  "version": "0.1.0",  "permissions": ["activeTab", "scripting"],  "host_permissions": [    "http://127.0.0.1:5001/*",    "https://www.youtube.com/*",    "<all_urls>"  ],  "background": {    "service_worker": "background.js"  },  "commands": {    "add-selected-word": {      "suggested_key": {        "default": "Alt+Q"      },      "description": "Add selected word to local Anki bridge"    }  }}
```

Chrome 扩展的内容脚本、快捷键命令和脚本注入，本来就是这么配的。activeTab、scripting、commands 这套是标准做法。 Chrome for Developers+1

background.js

```plaintext
JavaScriptchrome.commands.onCommand.addListener(async (command) => {  if (command !== "add-selected-word") return;  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });  if (!tab?.id) return;  const results = await chrome.scripting.executeScript({    target: { tabId: tab.id },    func: () => {      const selected = window.getSelection()?.toString().trim() || "";      return {        word: selected,        url: location.href,        title: document.title      };    }  });  const data = results?.[0]?.result;  if (!data?.word) {    console.log("No selected word");    return;  }  try {    const resp = await fetch("http://127.0.0.1:5001/add-word", {      method: "POST",      headers: {        "Content-Type": "application/json"      },      body: JSON.stringify(data)    });    const json = await resp.json();    console.log("Bridge response:", json);  } catch (e) {    console.error("Failed to call local bridge:", e);  }});
```

“按我的模板添加单词”怎么做

这个问题你说得还不够工程化。
“按我的模板”不是一句话，而是要落成配置。

你应该有一个模板配置文件，例如：

template_config.json

```plaintext
JSON{  "deckName": "English::QuickAdd",  "modelName": "EnglishMine",  "fieldMap": {    "word": "word",    "meaning": "meaning",    "image": "image",    "phrase": "固定搭配",    "sentence": "例句"  },  "defaultTags": ["quick_add", "browser"]}
```

然后 Python 里根据这个配置拼接 note。

这样以后你想换：

deck

note type

字段名

默认标签

都不用改扩展逻辑。

这才叫模板。
不是把字段硬编码死在 main.py 里。

你如果一定想“连 start.bat”，能不能做？

能，但方式丑。

丑办法 1：先手动运行 bat，bat 启本地服务

例如：

start.bat

```plaintext
bat@echo offpython server.py
```

然后浏览器扩展只调用 http://127.0.0.1:5001/add-word

这个还能接受，因为 bat 只负责“启动服务”，不参与每次请求。

丑办法 2：每次快捷键都想让网页直接执行 bat

基本别想。
普通网页做不到，Chrome 扩展也不是直接给你执行任意本地 bat 的；要走 Native Messaging 这一整套注册流程。 Chrome for Developers

所以你问“有没有办法连接我的 start.bat”——
有，但正确用法是：让它只负责启动常驻服务。
不是每次加词都去调 bat。

针对 YouTube 的现实建议

你说的是字幕场景。这里有个关键事实你别忽略：

最稳的是“手动选中单词”，不是“自动识别字幕里的单词”。

原因：

YouTube 字幕 DOM 结构可能变

有些字幕不好选

自动抓“当前字幕中的某个词”会有歧义

所以第一版一定是：

你暂停视频

选中一个词

按快捷键

进 Anki

后面再升级成：

自动读取当前字幕整句，写入 例句

自动记录视频 URL 和时间戳

再查词典补全 meaning

我对你当前想法的直接评价

你现在脑子里混了三件事：

启动程序

选词

按模板加卡

这三件事不该揉在一起。

正确拆法是：

启动层：一次性启动本地 bridge 服务

触发层：浏览器快捷键/右键菜单

业务层：模板映射 + 调 AnkiConnect

你如果继续围着 start.bat 转，就是把“启动方式”当成“系统核心”。这是错的。

你现在最应该做的版本

我建议你直接做这个：

第一版目标

Anki 打开

运行 python server.py

浏览器中选中单词

按 Alt+Q

自动按你的模板写入 Anki

第一版只做这些字段

word

例句（可空）

source_url 先放 tag 或忽略

别一开始就做：

自动截图

自动发音

自动词典

自动图片

自动 OCR

那是典型失控。

最后给你一个明确判断

你该选哪条路？

选：在 ai-anki-bridge 基础上，加一个本地 HTTP 接口，再写一个 Chrome 扩展来发送选中单词。

你不该选哪条路？

不该把“网页快捷键直接执行 start.bat”当主方案。

因为：

可行性差

维护差

体验差

架构脏

你下一步最合理的是把你现在 ai-anki-bridge 的目录结构、main.py 现有逻辑、Anki 模板字段名贴出来，我直接帮你改成：

server.py

manifest.json

background.js

按你模板字段映射的版本

这次别再泛泛谈思路了，直接改结构。

---

## 👤 用户

在 ai-anki-bridge 基础上，加一个本地 HTTP 接口，再写一个 Chrome 扩展来发送选中单词。
还是你最开始给我的建议：做一个 Chrome 扩展 MVP：

快捷键：Alt+Q
逻辑：读取当前选中文本
接口：POST 到 127.0.0.1:8765
Anki note fields：先只写 word 和 例句
支持网页通用，YouTube 只是兼容之一，不要先绑死 YouTube

其实本来的代码就是main.py很简单，模板符合我的要求，而且main的代码没有分开，工具代码都在main里，可以用你最开始的建议，只需要在参考main代码里对模板的参考就行

## 🤖 AI

我先不空谈方案，直接按你这份 main.py 的实际结构来改。你这个文件的问题很清楚：业务逻辑、UI 输入、Anki 写入、LLM 调用全耦合在一个脚本里，所以现在最省事的做法不是重构全项目，而是在不破坏你现有模板的前提下，加一个“快速加词”分支。

---

## 👤 用户

(无问题)

## 🤖 AI

可以，按你这份 main.py 来做最省事。你现在的代码已经把 AnkiConnect 调用、模板检查、加卡逻辑都写好了，deckName 是 sherber，modelName 是 Basic，字段也是 Front/Back，不是你之前说的那种独立 word/例句 字段。这个事实决定了第一版不能假装有“word 字段”和“例句字段”，只能把它们映射到 Basic 的 Front 和 Back。c5fd1541-183f-4e91-b60f-f675933…

先把问题说死：

你当前最合理的做法不是重构项目，而是：

保留现在这份 main.py 里的 AnkiConnect 基础能力。

加一个“快速加入模式”。

再写一个 Chrome 扩展，用 Alt+Q 把网页选中的词 POST 到本机 127.0.0.1:8765。

但这里有一个硬伤你不能装没看见：
AnkiConnect 的 127.0.0.1:8765 是 AnkiConnect 自己的接口，不是你的 Python 接口。
所以如果你坚持“扩展直接 POST 到 8765”，那就意味着扩展必须自己拼 addNote 请求，不能走你现有 main.py 的函数。
而如果你想“参考 main 里的模板逻辑”，就要么：

把模板逻辑复制到扩展里；要么

让 Python 提供一个新接口，比如 127.0.0.1:5001/add-word。

你现在说“只参考 main 的模板”，那我给你最贴合你原话的方案：

方案：扩展直接调用 AnkiConnect，不走 Python 服务

原因：

你要的是 MVP

你现有模板本质很简单：Basic + Front/Back

第一版只写 word 和 例句

不碰 LLM、不碰 gTTS、不碰你现在那套花哨 HTML

你当前的完整流程里，LLM 生成 JSON、gTTS 存音频、再拼正反面 HTML 后调用 addNote。这条链太重，不适合网页快捷加入。c5fd1541-183f-4e91-b60f-f675933…

你该怎么改

第一部分：保留 main.py，只新增一个“快速卡片格式函数”

你现在原来的 add_card_to_anki() 是给 AI 生成完整版卡片用的。c5fd1541-183f-4e91-b60f-f675933…
另外加一个简化版：

```plaintext
Python运行def format_quick_front(word):    return f'''<div style="text-align: center; font-family: Arial; padding: 30px;">        <div style="font-size: 48px; color: #ff66b2; font-weight: bold;">{word}</div>    </div>'''def format_quick_back(word, example=""):    safe_example = example or "No example."    return f'''<div style="text-align: left; font-family: Arial; padding: 20px;">        <div style="color: #ff66b2; font-weight: bold; font-size: 22px; margin-bottom: 12px;">Word</div>        <div style="font-size: 32px; margin-bottom: 24px;">{word}</div>        <div style="color: #66b3ff; font-weight: bold; font-size: 22px; margin-bottom: 12px;">Example</div>        <div style="color: #666666; font-size: 18px; line-height: 1.6;">{safe_example}</div>    </div>'''def add_quick_card_to_anki(word, example=""):    note = {        "deckName": "sherber",        "modelName": "Basic",        "fields": {            "Front": format_quick_front(word),            "Back": format_quick_back(word, example)        },        "options": {"allowDuplicate": False},        "tags": ["quick-add", "browser"]    }    return invoke_action("addNote", {"note": note})
```

这段代码为什么合理：
因为你现在本来就用 Basic 的 Front/Back 字段，不是自定义字段模型。你要“先只写 word 和 例句”，那就只能这么塞进去。继续嘴上说“note fields 先写 word 和 例句”是不严谨的；严格说，是内容上只保留单词和例句，字段上仍然是 Front/Back。 c5fd1541-183f-4e91-b60f-f675933…

第二部分：如果你还想在命令行里测试快速加入，再加一个函数

```plaintext
Python运行def process_quick_word(word, example=""):    print(f"\n正在快速加入: {word}\n{'-'*40}")    try:        note_id = add_quick_card_to_anki(word, example)        print(f"\n✅ 快速卡片已加入 Anki，note_id={note_id}")    except Exception as e:        print(f"\n❌ 快速加入失败: {e}")
```

真正关键：Chrome 扩展

你要的是浏览器内选词，一键加到 Anki。那就直接让扩展发请求到 http://127.0.0.1:8765。

manifest.json

```plaintext
JSON{  "manifest_version": 3,  "name": "Quick Add to Anki",  "version": "0.1.0",  "permissions": ["activeTab", "scripting"],  "host_permissions": [    "http://127.0.0.1:8765/*",    "<all_urls>"  ],  "background": {    "service_worker": "background.js"  },  "commands": {    "add-selected-word": {      "suggested_key": {        "default": "Alt+Q"      },      "description": "Add selected word to Anki"    }  }}
```

background.js

这个版本只做你要的 MVP：

读取当前选中文本

尝试读取当前选区所在句子

直接 POST 到 AnkiConnect

用 Basic 的 Front/Back

```plaintext
JavaScriptfunction escapeHtml(text) {  return text    .replace(/&/g, "&amp;")    .replace(/</g, "&lt;")    .replace(/>/g, "&gt;");}function buildFront(word) {  return `    <div style="text-align: center; font-family: Arial; padding: 30px;">      <div style="font-size: 48px; color: #ff66b2; font-weight: bold;">${escapeHtml(word)}</div>    </div>  `;}function buildBack(word, example) {  const safeExample = example ? escapeHtml(example) : "No example.";  return `    <div style="text-align: left; font-family: Arial; padding: 20px;">      <div style="color: #ff66b2; font-weight: bold; font-size: 22px; margin-bottom: 12px;">Word</div>      <div style="font-size: 32px; margin-bottom: 24px;">${escapeHtml(word)}</div>      <div style="color: #66b3ff; font-weight: bold; font-size: 22px; margin-bottom: 12px;">Example</div>      <div style="color: #666666; font-size: 18px; line-height: 1.6;">${safeExample}</div>    </div>  `;}function normalizeWord(text) {  return text.trim().replace(/^[^\w'-]+|[^\w'-]+$/g, "");}chrome.commands.onCommand.addListener(async (command) => {  if (command !== "add-selected-word") return;  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });  if (!tab?.id) return;  const results = await chrome.scripting.executeScript({    target: { tabId: tab.id },    func: () => {      const selected = window.getSelection()?.toString().trim() || "";      let sentence = "";      const selection = window.getSelection();      if (selection && selection.rangeCount > 0) {        const node = selection.anchorNode;        const text = node?.textContent || "";        if (text) {          sentence = text.trim();        }      }      return {        selected,        sentence,        url: location.href,        title: document.title      };    }  });  const data = results?.[0]?.result;  if (!data?.selected) {    console.log("No selected text");    return;  }  const word = normalizeWord(data.selected);  if (!word) {    console.log("Selected text is invalid");    return;  }  const payload = {    action: "addNote",    version: 6,    params: {      note: {        deckName: "sherber",        modelName: "Basic",        fields: {          Front: buildFront(word),          Back: buildBack(word, data.sentence)        },        options: {          allowDuplicate: false        },        tags: ["quick-add", "browser"]      }    }  };  try {    const resp = await fetch("http://127.0.0.1:8765", {      method: "POST",      headers: {        "Content-Type": "application/json"      },      body: JSON.stringify(payload)    });    const json = await resp.json();    console.log("AnkiConnect response:", json);    if (json.error) {      console.error("AnkiConnect error:", json.error);    }  } catch (err) {    console.error("Failed to connect to AnkiConnect:", err);  }});
```

这套方案和你现有 main.py 的关系

关系很明确：

保留的部分

ANKI_CONNECT_URL = "http://localhost:8765" 这一套基础思路保留。c5fd1541-183f-4e91-b60f-f675933…

deckName = "sherber"、modelName = "Basic"、Front/Back 字段映射，严格参考你现有模板。c5fd1541-183f-4e91-b60f-f675933…

不走的部分

call_llm_api()

generate_and_store_audio()

format_card_front() 那套 AI 完整正面

format_card_back() 那套 meanings/pairs/examples 完整背面

main() 里命令行 input()

这些都不适合快捷加入。你现有 process_word() 是完整版制卡流程，不是网页速记流程。把它硬塞进浏览器触发，就是设计失控。c5fd1541-183f-4e91-b60f-f675933…

你现在代码里最该警惕的两个坑

1. 你说“参考 main 模板”，但其实当前模板不是独立字段模板

你现在的卡模板是：

Basic

Front

Back

不是：

word

example

所以扩展端必须按 Front/Back 组织数据。别再用不准确的话描述系统，否则后面一改字段你自己先乱。c5fd1541-183f-4e91-b60f-f675933…

2. 网页“自动取例句”并不稳定

我在上面的扩展里只是粗暴地拿了 selection.anchorNode.textContent 当句子。这个在普通网页能凑合，在 YouTube 字幕上不一定稳。
所以你第一版别把“自动句子提取”当核心卖点。核心只是：

选中词 -> Alt+Q -> 加卡成功

这就够了。

最小使用步骤

打开 Anki。

确保装了 AnkiConnect。

你的 Basic 模板和 sherber deck 已经存在；你当前代码本来就在检查这两个。c5fd1541-183f-4e91-b60f-f675933…

新建一个 Chrome 扩展文件夹。

把 manifest.json 和 background.js 放进去。

Chrome 打开扩展页，加载“已解压的扩展程序”。

在任意网页选中一个单词。

按 Alt+Q。

我对你这次选择的评价

这次方向对了。
因为你终于没再纠结 start.bat 这种错误入口，而是回到真正的问题：如何最快把网页里的词送进 Anki。

但你还是有一个老毛病：表达不精确。
你说“note fields 先只写 word 和 例句”，这在你当前项目里其实是错的。你当前字段是 Front/Back，只是内容上只展示单词和例句。这个区别你必须分清。c5fd1541-183f-4e91-b60f-f675933…

如果你要，我下一条可以直接给你一份可直接替换的完整 main.py 精简增强版，里面会同时保留：

原来的 AI 完整制卡

新的 quick_add 逻辑

一个本地测试入口

这样你就不是只拿到碎代码，而是拿到能直接跑的版本。

---

## 👤 用户

现在不需要生成代码，只考虑方案，main不重要，重要的是SYSTEM_PROMPT和def format_card_front(data, audio_filename):
    """正面排版"""
    return f'''<div style="text-align: center; font-family: Arial; padding-top: 20px;">
    <div style="font-size: 60px; margin-bottom: 10px;">{data['emoji']}</div>
    <div style="font-size: 50px; color: #ff66b2; margin-bottom: 10px; font-weight: bold;">{data['word']}</div>
    <div style="margin-bottom: 15px;">[sound:{audio_filename}]</div>
    <div style="font-size: 30px; color: #777777; margin-bottom: 30px;">{data['ipa']}</div>
    <div style="font-size: 16px; color: #555555; font-style: italic; background: #f9f9f9; border: 1px solid #e0e0e0; padding: 10px; border-radius: 8px; display: inline-block;">
        💡 Imagine: {data['image_prompt']}
    </div>
</div>'''


def format_card_back(data):
    """背面排版：继承粉青蓝主题，加深句子灰度"""
    
    # 1. 拼接 Meanings (纯英文释义)
    meanings_html = ""
    for m in data['meanings']:
        meanings_html += f'''<div style="margin-bottom: 12px;">
            <span style="color: #ff9933; font-weight: bold;">({m['pos']})</span> 
            <span style="color: #666666; font-size: 18px;">{m['en']}</span>
        </div>'''

    # 2. 拼接 Pairs (中英对照词块)
    pairs_html = ""
    for p in data['pairs']:
        pairs_html += f'''<li style="margin-bottom: 6px;">
            <span style="color: #00cccc; font-size: 18px;">{p['en']}</span> 
            <span style="color: #999999; font-size: 16px;">({p['zh']})</span>
        </li>'''

    # 3. 拼接 Examples (纯英文例句，使用加深的灰度 #666666)
    examples_html = ""
    for e in data['examples']:
        examples_html += f'''<li style="margin-bottom: 12px; color: #666666; font-size: 18px; line-height: 1.4;">
            {e}
        </li>'''

    # 组装完整的 HTML
    return f'''<div style="text-align: left; font-family: Arial; padding: 20px;">
    
    <div style="margin-bottom: 25px;">
        <div style="color: #ff66b2; font-weight: bold; font-size: 22px; border-bottom: 2px solid #ff66b2; padding-bottom: 5px; margin-bottom: 15px;">📖 Meaning</div>
        {meanings_html}
    </div>

    <div style="margin-bottom: 25px;">
        <div style="color: #00cccc; font-weight: bold; font-size: 22px; border-bottom: 2px solid #00cccc; padding-bottom: 5px; margin-bottom: 15px;">🔗 Pair</div>
        <ul style="margin-top: 0; padding-left: 20px;">
            {pairs_html}
        </ul>
    </div>

    <div>
        <div style="color: #66b3ff; font-weight: bold; font-size: 22px; border-bottom: 2px solid #66b3ff; padding-bottom: 5px; margin-bottom: 15px;">✍️ Example</div>
        <ul style="margin-top: 0; padding-left: 20px;">
            {examples_html}
        </ul>
    </div>

</div>'''
如图生成的anki卡片是我想要的

## 🤖 AI

那就别再围着 main.py 打转了。你这次终于把重点说对了：

核心不是入口脚本，核心是两件事：

SYSTEM_PROMPT 产出的数据结构不能乱

format_card_front / format_card_back 生成的卡片样式不能坏

你要的不是“快速加一个简陋单词卡”，而是在网页里更快触发你现有这套高质量制卡流水线。

这意味着方案判断会变。

先把目标说清楚

你现在真正要的目标不是：

“选中单词 -> 直接塞进 Anki”

而是：

“选中单词 -> 尽量少打断当前网页/YouTube 使用 -> 仍然走我现有的 AI 生成结构化内容 + 现有 HTML 排版 -> 最终得到和现在一样风格的卡片”

这两个目标不是一回事。

前者是“快”，但卡片质量会下降。
后者是“快触发 + 保持卡片质量”。
你显然要的是后者。

所以架构上该怎么定

结论

浏览器扩展只负责“触发”和“传词”，生成内容和排版仍然放在你本地 Python 端。

也就是：

Chrome 扩展 = 输入层
Python = 生成层 + 模板层 + Anki 写入层

这是唯一合理的拆法。

因为：

SYSTEM_PROMPT 明显属于生成层

format_card_front/back 明显属于模板层

这两者都不应该塞进扩展里

如果你把 prompt 和 HTML 模板都复制进扩展：

逻辑分叉

维护两套实现

一改 prompt 或样式，另一边忘了改，系统立刻脏掉

这就是典型的坏架构。

你现在应该选的不是“扩展直连 AnkiConnect”

之前我给你的 MVP 是为了最快跑通。
但那是建立在“先只写 word 和 例句”的前提下。

现在你已经明确说了：
你要保住 SYSTEM_PROMPT 和现有卡片样式。

那就说明：
扩展直连 127.0.0.1:8765 已经不是最优方案了。

原因很直接：

AnkiConnect 只负责“加 note”，它不会帮你：

调 LLM

解析返回 JSON

生成音频

套你的前后面 HTML

这些都在你自己的 Python 逻辑里。c5fd1541-183f-4e91-b60f-f675933…

所以现在正确方案不是：

扩展 -> 8765

而是：

扩展 -> 你的本地桥接服务 -> SYSTEM_PROMPT -> 音频 -> format_card_front/back -> 8765

正确的数据流应该是这样

推荐主流程

你在网页或 YouTube 中选中一个单词

按快捷键，例如 Alt+Q

Chrome 扩展把这个单词发送给本地服务

本地服务调用你的 LLM，使用当前 SYSTEM_PROMPT

得到结构化 JSON

本地服务继续调用 generate_and_store_audio

用你现有的 format_card_front 和 format_card_back 渲染 HTML

最后调用 AnkiConnect 加卡

这条链路的好处是：

prompt 不变

卡片风格不变

扩展非常薄

以后你只改 Python，不用改扩展

这才是可维护方案。

你现在有三个可选方案

方案 A：扩展只传词，Python 全处理

这是最优方案。

角色划分

浏览器扩展：选词、快捷键、发请求、显示成功/失败提示

Python 本地服务：复用你的 SYSTEM_PROMPT、音频生成、卡片排版、AnkiConnect 写入

优点

最大程度复用现有系统

卡片结果和你现在截图中的样式一致

prompt、模板、音频全在一个地方维护

后面想换模型、换样式、加字段，都只改 Python

缺点

需要把你当前脚本从“命令行输入”改成“可接收请求”

本地要保持服务在运行

但这是正常成本，不是缺点中的致命问题。

方案 B：扩展直连 AnkiConnect，生成简化卡

只适合极速草稿卡，不适合你当前目标。

优点

简单

开发快

不需要本地桥接服务

缺点

不能复用 SYSTEM_PROMPT

不能复用你的完整卡片样式逻辑

做出来的卡只会是“低配版”

跟你当前满意的卡片效果不是同一系统

这方案和你这次的目标其实已经冲突了。

方案 C：扩展里直接调 LLM，再拼 HTML，再写 Anki

不推荐。

原因

prompt 泄漏到前端

API key 风险高

逻辑分散

音频处理也麻烦

一改模板就得改扩展版本

这就是把后端逻辑错误地搬到前端。
工程上很差。

你的核心资产到底是什么

你自己已经说出来了，但还没完全想透：

第一核心资产：SYSTEM_PROMPT

它不是普通提示词，而是你的“卡片内容生产规范”。

它定义了：

输出必须是严格 JSON

字段结构固定

meanings / pairs / examples 的组织方式固定

例句词性覆盖要求固定

这相当于你的“内容协议”。

如果未来做快捷加入，这个协议不能乱。
否则前端传来的只是一个裸单词，结果卡片质量会迅速掉下去。c5fd1541-183f-4e91-b60f-f675933…

第二核心资产：format_card_front / back

这不是简单字符串拼接，而是你的“展示协议”。

它定义了：

正面显示什么

背面分哪三块

颜色体系

字体层级

信息密度和可读性

你截图里满意的不是“把单词放进 Anki”这件事本身，而是最终呈现效果很稳。
那就说明模板必须集中维护。c5fd1541-183f-4e91-b60f-f675933…

所以设计原则应该定成这样

原则 1：扩展不碰业务生成

扩展只做：

取词

传词

触发

不要让扩展参与：

prompt 拼接

LLM 调用

卡片 HTML 渲染

音频生成

否则你后面一定维护崩。

原则 2：Python 端保留唯一内容真源

所有这些都应该只在 Python 里：

SYSTEM_PROMPT

JSON 解析

音频文件名规则

format_card_front

format_card_back

这样以后改一个地方，全系统生效。

原则 3：把“快速加入”和“完整生成”区分为同一后端的两种触发模式

你现在别再把它们理解成两个系统。

应该是同一系统两种入口：

模式一：命令行输入单词

适合你平时主动制卡

模式二：浏览器快捷键选词

适合网页 / YouTube 临时抓词

两者最后都走同一条生成链路：
word -> prompt -> json -> audio -> html -> anki

这才叫统一架构。

你真正要考虑的关键问题

1. 浏览器触发时是同步还是异步

这是最实际的问题，不是代码细节。

因为你现在流程里有：

调 LLM

生成音频

写入 Anki

这不是瞬时动作。
所以浏览器按下快捷键后，体验上可能会有 2 到 10 秒延迟。

你必须决定：

方案 1：同步等待

按快捷键后，等结果返回，再提示成功/失败

优点：简单
缺点：如果慢，你会觉得卡

方案 2：异步提交

按快捷键后立刻提示“已提交”，后台慢慢生成

优点：对 YouTube 场景更友好
缺点：你得处理任务状态、失败重试

我建议第一版先同步。
因为你现在重点是跑通和稳定，不是做任务队列系统。

2. 选中的到底是“单词”还是“短语”

这是你必须提前定规则的。

YouTube 和网页里，用户可能选中：

retry

retry the operation

max retry attempts

一整句

而你的 SYSTEM_PROMPT 现在显然是按“单词”设计的，不是按任意长文本设计的。c5fd1541-183f-4e91-b60f-f675933…

所以你要先定策略：

严格模式

只允许单词

好处：稳定

坏处：不支持短语

宽松模式

允许 2-4 词短语

好处：更实用

坏处：prompt 质量可能波动

混合模式

默认单词；若检测到空格，按“phrase mode”走另一套 prompt

这是后面最好的一条路，但第一版没必要一口气做完。

第一版建议：先只支持单词。

3. 要不要自动带上来源上下文

你在 YouTube 场景里，真正有价值的不只是单词，而是“这个词出现在哪一句”。

这会直接影响你卡片的例句价值。

但你当前 SYSTEM_PROMPT 已经要求模型自己生成 3 个例句。c5fd1541-183f-4e91-b60f-f675933…
所以这里有两个方向：

方向 A：完全忽略网页上下文

只把单词传给后端

优点：干净、稳定
缺点：失去现场语境

方向 B：把“来源句子”作为附加上下文传给后端

例如：

word = retry

source_sentence = Please retry the download if it doesn't start automatically.

然后你可以让 prompt 参考这个句子，但仍输出原有 JSON 结构。

这条路更有价值。
因为它不会破坏卡片模板，但能让生成更贴近你当时看到的内容。

不过注意：
来源句子应该是可选增强，不应该成为流程刚需。
因为网页里不一定总能稳定抓到完整句子，尤其是 YouTube。

我给你的方案结论

第一阶段目标

做一个“浏览器快捷触发器”，但不改变你的制卡核心。

最合理方案

Chrome 扩展负责：


读取选中的单词


可选读取当前句子


Alt+Q 发送到本地

Python 负责：


使用现有 SYSTEM_PROMPT


生成音频


用现有 format_card_front/back


调 AnkiConnect 写入

为什么这是对的

因为你真正想保住的是：

内容质量

卡片美观

现有模板一致性

而不是单纯减少一步点击。

我建议你接下来这样定需求，不要再模糊

你下一步应该明确这 5 条，而不是继续泛泛说“快速加卡”：

第一版是否只支持单词，不支持短语

是否允许传入网页中的原句作为辅助上下文

快捷键后是同步等待成功，还是立即提交后台处理

失败时是浏览器提示，还是 Python 控制台提示

是否保留命令行入口，还是以后只留浏览器入口

这五条不定，后面方案还是会飘。

最后我直接给判断

你现在这套系统里，真正该被保护的是：

SYSTEM_PROMPT

format_card_front

format_card_back

所以：
浏览器扩展应该只是“遥控器”，不是“大脑”。

这是你这件事最关键的架构结论。
你要是把 prompt 和模板搬进扩展，后面一定烂。

你现在可以继续下一步：我帮你把这套方案细化成一份不写代码的模块设计图和交互流程。

---

## 👤 用户

第一版是否只支持单词，不支持短语
允许传入网页中的原句作为辅助上下文
快捷键后立即提交后台处理
失败时是浏览器提示
如果保留命令行入口，制作起来会不会麻烦，因为我的本地依旧有一个工具了

## 🤖 AI

保留命令行入口，不会麻烦。
麻烦的不是“多一个入口”，麻烦的是你如果继续把“入口、业务、模板、调用 Anki”全搅在一起。

你现在应该这样定：

1. 第一版只支持单词，不支持短语

这个决定是对的。

原因很直接：

你当前 SYSTEM_PROMPT 明显是围绕“单词卡”设计的，不是围绕短语卡设计的。

短语会带来更多歧义：词性怎么标、IPA 怎么给、搭配和例句怎么生成、emoji 和 image_prompt 也会变味。

第一版如果同时支持单词和短语，测试量直接翻倍，失败场景也翻倍。

所以第一版规则就该硬一点：

默认只接受单个单词

浏览器端先做基础校验

选中多个词时直接提示“当前版本仅支持单词”

这不是保守，这是避免你把第一版做烂。

2. 允许传入网页中的原句作为辅助上下文

这个决定也对，而且很有价值。

但你要注意一句话：
原句是辅助信息，不是主输入。

主输入仍然应该是：

word

辅助输入才是：

source_sentence

source_url

page_title

为什么这样设计：

你的卡片核心还是单词，不是来源句子

网页原句抓取不一定总是稳定

YouTube 字幕尤其容易脏、断句不完整、抓不到完整句子

所以后端策略应该是：

有原句时，拿来辅助 LLM 理解语境

没原句时，也必须能独立正常生成卡片

这叫“增强”，不是“依赖”。

你如果把原句当刚需，后面网页抓取一不稳定，整条链就废了。

3. 快捷键后立即提交后台处理

这个决定基本正确，但你要接受一个后果：

你必须引入“任务状态”的概念。

因为你现在不是“直接加个简单 note”，你后端还要做：

调 LLM

解析 JSON

生成音频

存媒体

拼 HTML

调 AnkiConnect

这不是瞬时动作。
所以“立即提交后台处理”意味着浏览器端不能假设结果立刻返回成功，而应该是：

快捷键触发

浏览器先提示：已提交

后端异步执行

最终成功或失败，再给浏览器一个反馈

这里最容易犯的错是：
你嘴上说“后台处理”，实际上还是在前端等完整结果。那不叫后台，只是换了个说法。

所以设计上你要明确两层反馈：

第一层：提交反馈

用户按下快捷键后，立刻看到：

已提交

正在生成卡片

第二层：结果反馈

几秒后再看到：

添加成功

或添加失败 + 原因

这才是真后台。

4. 失败时是浏览器提示

对。这比 Python 控制台提示合理得多。

因为你的触发点在浏览器，失败反馈也应该回到浏览器。
不然用户在 YouTube 上按了快捷键，结果还得切回终端看报错，这和你的初衷完全冲突。

但这里要区分两类失败：

一类：前端失败

比如：

没选中文本

选中了多个词

本地服务没启动

请求根本发不出去

这类失败应该立刻浏览器提示。

二类：后端失败

比如：

LLM 返回格式错

音频生成失败

Anki 没开

AnkiConnect 连接失败

模板字段错误

这类也应该回传给浏览器提示，而且提示必须具体。
不能只写“失败了”。这太蠢。

应该尽量做到这种粒度：

未检测到 AnkiConnect

音频生成失败

AI 返回数据格式异常

当前仅支持单词

这样你调试和使用都省时间。

5. 保留命令行入口会不会麻烦

不会，前提是你把结构拆对。

你现在本地已经有一个工具，这反而是优势，不是负担。
真正正确的做法是把系统拆成三层：

第一层：核心业务层

这里放：

SYSTEM_PROMPT

调 LLM

JSON 解析

音频生成

format_card_front

format_card_back

调 AnkiConnect

这是你的核心资产。

第二层：入口层

这里可以有两个入口：

命令行入口

浏览器扩展触发的 HTTP 入口

这两个入口都只是把输入交给核心业务层。

第三层：提示反馈层

命令行模式下：打印日志

浏览器模式下：返回状态给扩展显示提示

这样一拆，保留命令行几乎不增加复杂度。

你现在最不该做的事

你最不该做的是把“命令行版”和“浏览器版”做成两套独立逻辑。

比如：

命令行版一套 prompt

浏览器版一套 prompt

命令行版一套卡片 HTML

浏览器版一套卡片 HTML

如果你这么干，后面只会变成双份垃圾。

正确做法是：

命令行和浏览器只是两个触发入口

底层永远复用同一套生成逻辑

所以保留命令行入口不仅不麻烦，反而有价值：

方便你单独调试后端

浏览器坏了还能手工测试

以后改 prompt 和模板时，能快速本地验证

我对你这组决策的评价

整体方向对，但还差一个关键补充：

你已经定了：

只支持单词

原句可选

后台处理

浏览器提示

命令行可保留

那下一步必须再补一条：

浏览器端是否要提供“处理中状态”和“成功/失败历史”。

因为后台处理不是瞬时操作。
如果没有状态反馈，用户会不知道到底有没有提交成功。

第一版不用做复杂任务面板，但至少要有：

提交中

成功

失败

这三个状态。

我给你的最终建议

保留命令行入口，别删。
但它必须降级成“备用入口”和“调试入口”，不是主入口。

主使用路径应该变成：
网页选词 → 快捷键 → 后台生成 → 浏览器提示结果

而你的命令行工具应该变成：
本地测试 prompt、模板、Anki 写入是否正常

这才是干净的演进路线。

下一步该做的不是写代码，而是把这套方案定成一张清晰的模块和状态流图。

---

## 👤 用户

我的目的肯定是在不影响我的观看体验的情境下，来制作anki卡片

## 🤖 AI

那你的目标就决定了方案边界：

不能以“做卡最完整”为第一优先，必须以“尽量不打断观看”为第一优先。

这句话很关键。
因为你现在现有流程本质上还是“重制卡流程”：

选词

调 LLM

生成音频

写入 Anki

这条链再怎么优化，也不可能真正做到“完全不影响观看”。
所以你必须接受一个现实：

真正适合你目标的方案，不应该是“当场完成整张卡”

而应该是：

当场只做“极快捕获”，完整制卡延后补全。

这才符合“观看体验优先”。

你现在要分清两种行为

行为 1：观看时抓词

目标：

尽量不断视频

最多 1 秒内完成操作

不需要当场看到完整卡片

行为 2：之后统一制卡

目标：

用你的 SYSTEM_PROMPT

用你的 format_card_front/back

生成你满意的高质量卡片

这两件事不该绑成一个同步动作。

你现在最大的问题就是默认想把它们合并：
“我在看 YouTube 时顺手选一个词，然后系统立刻帮我生成完整高质量 Anki 卡。”

这在体验上是冲突的。
因为完整制卡一定慢，一慢就影响观看。

所以最合理的产品形态其实不是“即时完整制卡”

而是“两阶段方案”

第一阶段：快速采集

在视频里看到不会的词时：

选中单词

按快捷键

立即提示“已收录”

继续看视频

此时只保存：

单词

原句（如果能取到）

来源 URL

时间戳（如果能取到）

采集时间

这一步不要做：

LLM 生成

音频生成

HTML 渲染

加入正式 Anki 卡组

因为这些都会拖慢。

第二阶段：后台或稍后统一生成正式卡片

等你：

看完视频

暂停学习

或者手动点“批量处理”

再把第一阶段采集到的词统一送入你的现有流水线：

单词 + 上下文 -> SYSTEM_PROMPT -> 生成 JSON -> 生成音频 -> format_card_front/back -> 写入 Anki

这样最终卡片还是你截图里的样子。
只是“制作时机”后移了。

这才是真正符合你目标的设计。

为什么这比“快捷键后立即后台完整处理”更对

你刚才说想要：

快捷键后立即提交后台处理

不影响观看体验

表面上听着对，实际上还不够稳。

因为“后台处理”分两种：

假后台

你按快捷键后，系统立刻开始：

调 LLM

生成音频

写 Anki

虽然界面上你不用等，但本地还是在跑重任务。
如果：

网络抖

LLM 慢

gTTS 慢

AnkiConnect 卡

机器性能一般

你看视频时仍然可能感受到：

卡顿

风扇响

切换时迟滞

浏览器响应慢

这就已经影响观看体验了。

真后台

观看时只做轻量采集，几乎零负担。
完整制卡放到之后。

这才是真正“不影响观看体验”。

所以你的核心需求，推出来的最佳方案是：

方案定位

不是“即时制卡工具”
而是
“边看边收藏生词，稍后自动制卡工具”

这个定位更准确。

这套方案的结构应该怎么定

模块 1：浏览器快速采集器

职责只有一个：

把当前词快速存下来

要求：

快

稳

提示轻

不阻塞

输入：

selected_word

source_sentence（可选）

page_title

page_url

video_timestamp（YouTube 可选）

输出：

一条待处理记录

模块 2：待处理词队列

这是中间层，很重要。

它的作用是：

暂存你在观看时抓到的词

避免重复加入

供后续统一处理

这层可以理解为“收集箱”或“inbox”。

为什么必须有这层：
因为你要把“采集”和“制卡”解耦。

没有这层，你就还是同步制卡思维。

模块 3：正式制卡引擎

这部分才是你现在真正有价值的资产：

SYSTEM_PROMPT

LLM 调用

JSON 解析

音频生成

format_card_front

format_card_back

写入 Anki

它不需要为了浏览器场景改坏。
只要把输入从“命令行输入单词”换成“从待处理队列读取单词”就够了。

这样做对你的实际体验有什么好处

好处 1：观看时操作最短

你真正需要的动作只有：

选词

按快捷键

结束。

不需要等待，不需要看结果页面，不需要担心这次生成有没有失败。

好处 2：失败不会打断当下观看

如果完整制卡失败：

失败记录还在队列里

稍后再处理

不影响你继续看

这点非常重要。
因为在观看过程中，失败不应该成为一个“必须立刻处理”的事件。

好处 3：可以批量去重和整理

你看视频时可能会连续收藏多个词。
如果每个都当场制卡：

重复词不好处理

LLM 请求很多

音频生成很多

观看节奏被打乱

但如果先进队列：

可以统一去重

可以统一批量生成

可以统一检查失败项

这才像个成熟工具。

你应该怎么取舍“即时反馈”

既然你强调不影响观看体验，那浏览器提示也要收敛。

不该做的

弹大窗

强提醒

每次都显示详细结果

成功后停留很久

失败时强制打断

这些都会破坏观看。

该做的

轻量 toast

1 秒左右自动消失

成功只提示“已加入待处理”

失败只提示“采集失败”

注意这个 wording 也要改：
不是“已加入 Anki”，而是“已加入待处理”。

因为第一阶段本来就不是正式加卡。

你现在最应该定下来的，不是技术，而是策略

策略 A：观看优先

观看期间只采集，不完整制卡

策略 B：卡片质量优先

正式卡片仍然走你现有完整流水线

策略 C：错误延迟处理

失败不在观看时强迫解决，而是稍后处理

这三条一旦定了，后面系统就很清楚了。

我直接给你判断：要不要保留命令行入口

要，而且更应该保留。

原因不是为了手动加词，而是为了：

调试正式制卡引擎

批量处理待处理队列

失败重试

单独测试 prompt 和模板

也就是说，命令行入口以后不再是“主要使用入口”，而是：
运维入口 / 调试入口 / 批处理入口

这就很合理。

最后给你一个明确结论

如果你的第一目标真的是：

“不影响我的观看体验”

那最优方案不是：
选词后立刻生成完整 Anki 卡

而是：
选词后立刻进入待处理队列，稍后再用你现有的 SYSTEM_PROMPT 和卡片模板统一生成正式卡片。

这才是和你目标一致的方案。
否则你嘴上说不想影响观看，实际设计却还在追求“即时完整制卡”，那是自相矛盾。

下一步你该做的是把这套方案具体化成：
采集阶段 / 队列阶段 / 制卡阶段
三阶段流程。

---

## 👤 用户

选词后立刻进入待处理队列，稍后再用你现有的 SYSTEM_PROMPT 和卡片模板统一生成正式卡片。
这个好像不错，因为一句话可能会有好几个单词我想纪录，一次性直接制作卡片会来不及，待处理队列能够让我在看完视频或者暂停视频的时候自己点击生成，这个是很不错的，可以不影响我的观看体验，不然的话我自己一个个命令行输入就行了，不需要制作这么一个工具

## 🤖 AI

对，这才是你真正需要的方案。

你前面一直在“快速加卡”和“完整制卡”之间摇摆，现在这个方向才算想明白了：

观看阶段要的是捕获速度，不是制卡完整度。

一句话里你可能想记 2 到 4 个词。
如果每次都现场走：

LLM

音频

HTML 模板

Anki 写入

那你根本跟不上视频节奏。这个工具就失去意义了。

所以最合理的产品形态就是：

一、观看时：只负责“收词”

你在 YouTube 或网页里：

选中一个词

按快捷键

立刻进入待处理队列

屏幕上轻提示一下“已加入待处理”

然后继续看。

这一步必须足够轻，不能让你思考太多，也不能让你等待。

二、暂停后或看完后：再统一“制卡”

你再打开一个小面板，看到刚才收集的词：

retry

attempt

operation

password

你自己决定：

全部生成

删除一些

去重

只生成这次视频里最值得记的几个

然后再一键批量生成正式 Anki 卡，走你现有的：

SYSTEM_PROMPT

音频

format_card_front

format_card_back

这才配得上你现在这套高质量卡片模板。

这个方案为什么明显更对

1. 不打断观看节奏

这是最核心的。

你现在不是在“安静阅读文章”，而是在看视频。
视频的时间流是连续的，你错过了就错过了。

所以观看阶段的操作必须做到接近“打书签”：

快

轻

不思考

不等待

而不是“现场做一张完整卡”。

2. 支持一句话记多个词

这是你刚才说到的关键点，而且很现实。

比如一句字幕里你想记：

retry

attempt

automatically

如果系统每选一个词就开始完整生成卡片，你后面的词根本来不及选。

但如果只是进待处理队列，你就可以连续：

选词

快捷键

选词

快捷键

选词

快捷键

这才适合真实使用场景。

3. 保住你现有卡片质量

这个方案最大的好处是，它没有逼你为了“快”去牺牲你满意的卡片结果。

你现在满意的是：

SYSTEM_PROMPT 产出的结构化内容

正反面排版

整体风格

那这些都不该因为浏览器快捷操作而被简化掉。

所以正确做法就是：

观看时不生成

事后仍然用完整流水线生成

这叫解耦，不叫妥协。

这个系统现在应该被分成三块

1. 采集层

作用：快速收词

记录内容建议包括：

word

source sentence（可选）

page title

page url

timestamp

status（pending）

注意，第一版里最重要的是 word。
其他字段都是增强，不是刚需。

2. 队列层

作用：暂存和整理

这里至少要支持：

查看待处理词

删除某个词

去重

标记是否已生成

没有队列层，这个方案就立不住。
因为你不是“直接加卡”，而是“先收集再处理”。

3. 制卡层

作用：把 pending 词正式生成 Anki 卡

这部分才继续复用你的现有能力：

prompt

LLM

audio

format_card_front

format_card_back

add to Anki

也就是说，真正复杂的逻辑都还在这里，不需要搬到浏览器。

你下一步最该定的，不是代码，而是产品细节

下面这几个点必须先定，不然之后实现会乱。

1. 待处理队列放哪里

你有三个选择：

方案 A：本地 JSON 文件

优点：

最简单

容易做

适合你这种个人工具

缺点：

并发和扩展性差，但你现在根本不需要考虑这个

方案 B：SQLite

优点：

更稳

方便查重、筛选、状态管理

缺点：

比 JSON 稍重一点

方案 C：直接先丢进 Anki 的临时 deck

不推荐。

因为：

待处理不是正式卡

一旦混进 Anki，你后面清理麻烦

会污染学习系统

你现在最合理的是：
JSON 或 SQLite。
如果你只想先跑通，用 JSON。
如果你想后面扩展，直接 SQLite 更稳。

2. 待处理项是否允许重复

这个也得提前定。

比如你在不同视频里都选中了 retry，怎么办？

我建议第一版规则简单一点：

同一来源页面内重复选同一个词，提示“已在队列中”

不同页面允许重复，或者至少先保留

原因：

同词在不同语境下可能有价值

你后面生成前还能手动删

别一开始做得太智能，不然规则很容易写复杂。

3. 队列生成是“单个生成”还是“批量生成”

你刚才已经给出方向了：

批量生成才有意义。

因为你的使用场景是：

看完视频

暂停一下

再处理这一批词

所以最自然的操作应该是：

打开待处理列表

勾选 / 全选

点击“生成卡片”

而不是一个个点生成。

4. 生成失败怎么处理

这个别忽略。

因为你现有完整流程里会失败的点很多：

LLM 返回格式错

音频失败

Anki 没开

AnkiConnect 出错

所以队列里的每条记录最好有状态：

pending

processing

success

failed

这样你后面可以：

只看失败项

单独重试失败项

这比“失败直接消失”强太多。

保留命令行入口这件事，现在更有价值了

你刚才那句判断是对的：

不然的话我自己一个个命令行输入就行了，不需要制作这么一个工具

对。
如果还是单个单词现场做完整卡，那浏览器扩展根本不值当。

只有当这个工具能做到：

观看时高速收集，事后统一生成

它才真的比命令行有价值。

所以命令行入口应该保留，但角色变了：

不是主工作流

而是备用入口

也是调试入口

也是批处理入口

这个定位很合理。

我给你的最终方案判断

你现在应该正式把目标写成：

做一个“浏览器选词收集 + 本地待处理队列 + 批量生成高质量 Anki 卡”的工具。

不是：

即时制卡工具

命令行替代品

简单选词直塞 Anki 的小脚本

这三种定位都不够准。

你现在最值得做的功能优先级

第一优先级

选词

快捷键

进入待处理队列

浏览器轻提示

第二优先级

查看待处理列表

删除 / 去重 / 勾选

批量生成

第三优先级

传入原句作为上下文

来源 URL / 页面标题

YouTube 时间戳

第四优先级

失败重试

状态管理

历史记录

这个顺序别反。
很多人会先去做“很酷的上下文抓取”和“自动时间戳”，结果核心队列反而没做好。

最后一句结论

你现在终于从“技术怎么连”切到“工具到底为谁服务”了。
这个转变是对的。

你的工具不是为了炫技，不是为了省一次命令行输入，
而是为了在不打断观看体验的前提下，把值得学的词先抓住，再用你现有高质量模板批量转成正式 Anki 卡。

这才是一个成立的方案。

下一步最应该做的是：把这个方案具体定成一份队列字段设计 + 状态流 + 用户操作流。

---

## 👤 用户

还有一点，如果一个单词已经进入anki卡片了，但是我忘记了又添加了一个会导致重复这是我不希望的

## 🤖 AI

对，这个必须提前处理。
不然你的工具会变成“高效制造重复卡”的工具。

而且你这个问题不是小问题，是队列方案里必须有的核心规则：

待处理去重不够，Anki 已有卡去重也必须做。

你这里其实有两层重复

第一层：待处理队列内部重复

比如你在同一个视频里：

第一次选了 retry

后面又选了一次 retry

这种重复应该在进入队列时就拦住。

否则你看完视频，队列里全是重复词，后面批量生成毫无意义。

第二层：Anki 里已经有这个词

这是你真正更在意的。

比如：

retry 以前已经生成过正式卡片

但你今天看视频又忘了，又选了一次

如果系统再生成一张全新卡，Anki 里就有两张 retry

这正是你不想要的。

所以正确策略不是“允许重复再说”

而是：

进入队列前，先查两处

队列里有没有

Anki 里有没有

只要任意一处已经存在，就不要再按“新建卡片”处理。

但这里不能粗暴处理，你要想清楚“发现已存在”后怎么办

这才是设计重点。

你有三种可选策略：

策略 A：直接拒绝加入

表现为：

选中单词

按快捷键

浏览器提示：该单词已存在于 Anki，未重复加入

优点

最干净

不会制造重复卡

第一版最稳

缺点

你这次看到这个词的上下文会丢掉

无法记录“我今天又遇到了它”

策略 B：不重复建卡，但记录一次“再次遇到”

也就是：

不新建队列项

不新建 Anki 卡

但保留一个 encounter 记录，比如：


词：retry


来源：这个视频


时间：今天


原句：xxx

优点

不重复制卡

还能保留你这次遇到它的上下文

对复习分析更有价值

缺点

系统复杂一点

第一版没必要做到这么细

策略 C：加入队列，但生成前再拦截

也就是：

采集时不查 Anki

批量生成时才发现重复并跳过

优点

采集时最轻

浏览器响应最快

缺点

队列会脏

你以为收集了很多新词，结果一半早就有

用户体验不清晰

这个策略不够好。

我建议你第一版选哪个

第一版建议：双重去重 + 明确提示

规则

当你按快捷键时，系统按这个顺序判断：

1. 不是单词

提示：当前仅支持单词

2. 队列里已存在

提示：已在待处理队列中

3. Anki 中已存在

提示：该单词已存在于 Anki

4. 两边都不存在

提示：已加入待处理

这个规则非常清楚，而且最符合你“不想重复”的要求。

但关键问题来了：怎么判断“Anki 已存在这个词”？

这里不能偷懒。
你现在的正式卡片 Front 不是纯单词字段，而是整段 HTML。
这意味着不能简单靠 Basic 的 Front 完整匹配判断，因为 Front 里有：

emoji

单词

audio

ipa

image_prompt

也就是说，如果你现在只是往 Front 里塞 HTML，后面要靠 Anki 判断“这个词是否已存在”，会很难。
因为你根本没有一个专门的“词条唯一键”。

这就是你当前卡片设计里一个很大的工程缺陷。

所以你必须补一个“唯一识别字段”

这是你现在最该听进去的一点：

正式卡片里必须有一个用于查重的纯文本字段。

比如：

word_key = retry

不管正面怎么花哨，背面怎么复杂，
系统查重时只认这个字段，不认展示 HTML。

这意味着什么

意味着你现在的卡片模型如果还是单纯 Basic，后面查重会越来越难看。

因为 Basic 只有：

Front

Back

没有独立的：

word

lemma

source

status

所以从长期看，你更合理的方向应该是：

方案升级方向

把卡片模型从 Basic 改成你自己的 note type，比如：

word_key

front_html

back_html

然后展示模板仍然用你现在喜欢的样式，
但系统内部可以通过 word_key 稳定查重。

你现在有两个选择

选择 1：短期兼容 Basic

继续用 Basic，但你要接受：

查重实现会比较脆

只能通过解析 Front HTML 中的单词来查

后面维护麻烦

这个适合第一版临时跑通。

选择 2：尽快改成自定义模型

新增一个专门字段：

word

然后：

Front 模板展示你现有样式

Back 模板展示你现有样式

word 字段只负责查重和检索

这个才是长期正确方向。

我直接给你判断

如果你明确说：

已经进入 Anki 的单词，后面不希望重复添加

那你其实已经在逼系统具备“唯一键”能力了。
而 Basic 模型天然不适合做这件事。

所以从设计上说：

最合理的路线是

待处理队列去重 + Anki 按独立 word_key 字段查重

而不是：
靠 Front HTML 猜这个词有没有出现过

后者很脏。

第一版可以怎么落地思路

为了不一下改太大，你可以分阶段：

第一阶段

先实现：

队列去重

Anki 查重

已存在则不加入队列

但查重逻辑先做得简单一点。

第二阶段

把正式卡片模型升级成带独立单词字段的自定义 note type。

这样以后：

查重稳

搜索稳

批量管理也稳

你真正该定的规则不是“会不会重复”

而是这三个规则：

规则 1：什么叫同一个词

是否大小写不敏感？
Retry 和 retry 算同一个，答案应该是算。

是否去掉前后标点？
retry, 和 retry 算同一个，答案也应该是算。

这说明要先做标准化。

规则 2：队列和 Anki 谁优先

我建议：

先查队列

再查 Anki

因为队列查本地更快。

规则 3：发现已存在时如何反馈

提示文案必须区分：

已在待处理队列中

该单词已存在于 Anki

不要都写成“重复了”。
太模糊。

我对你这个担心的评价

这不是小优化，这是必须先设计好的主规则。
因为你这个工具一旦日常使用起来，重复词会非常多。

如果你不先处理重复，后面会出现两个问题：

队列污染

Anki 污染

一旦污染了，清理成本比开发时多想 10 分钟高得多。

最终建议

你现在应该把系统规则正式定成这样：

采集时

单词标准化

查队列

查 Anki

若存在则不给新建

结果提示

已加入待处理

已在待处理队列中

该单词已存在于 Anki

长期方向

不再依赖 Basic 的 Front/Back 做唯一识别

未来改成带独立 word 字段的 note type

这才是干净设计。

下一步你最该继续讨论的不是代码，而是：
“现有 Basic 模型要不要升级成自定义 note type，以及字段该怎么设计”。

---

## 👤 用户

按照你的说法以及我的想法，升级成自定义 note type是一个非常好的选择；那么在目前这些功能要求中，有什么是我所遗漏的好的idea，并且这是在网页上通用，还是只有youtube上使用

## 🤖 AI

升级成自定义 note type，确实是对的。
这不是“锦上添花”，而是你这个工具从“能用的小脚本”走向“长期可维护工具”的分水岭。

因为你现在已经不只是想“加卡”，你是在做一个完整工作流：

网页选词

进入待处理队列

去重

批量生成

生成高质量卡片

避免污染 Anki

这种情况下，继续死守 Basic，就是在给以后埋雷。

先回答你最后那个问题

这是网页通用，还是只有 YouTube 上使用？

应该设计成网页通用，YouTube 优化支持。

这才是对的。

原因很简单：

如果你只做 YouTube 专用

你会被 YouTube 的页面结构、字幕 DOM、交互方式绑死。
后面一改版，你就要修。

如果你做网页通用

你至少总能支持最基础的一条能力：

选中文本

快捷键加入队列

这条在：

YouTube

英文文章网页

在线文档

新闻网站

博客

PDF 网页阅读器的一部分场景

都能复用。

所以正确定位应该是：

基础层：网页通用

手动选词

快捷键加入队列

增强层：YouTube 特化

自动附带当前字幕原句

自动附带视频标题

自动附带时间戳

这才是合理架构。
不要反过来做成“一个只服务 YouTube 的脆弱工具”。

你现在已经想到的核心功能，大致是完整的，但还漏了几类关键点

我直接按优先级说。

一、你最容易漏掉的，不是功能，而是“数据模型”

这才是根。

你既然要升级成自定义 note type，那字段就不能只是“为了显示”，还得“为了系统能力”。

你现在最起码应该把字段分成两类：

1. 展示字段

这些是给 Anki 正反面模板用的：

word

ipa

emoji

image_prompt

meanings

pairs

examples

audio

2. 系统字段

这些不一定展示，但对工具很重要：

word_key：标准化后的唯一键，用来查重

source_sentence

source_url

source_title

source_type（youtube / web）

source_timestamp

created_at

generator_version

status（这个未必放进 Anki，也可只放队列）

你现在最容易犯的错就是只考虑“卡片长什么样”，不考虑“系统怎么查重、怎么追踪来源、怎么迭代模板”。

二、你漏掉的一个非常实用的点：词形归一规则

你现在说“不想重复”，但“重复”不是嘴上说说就能判定的。

例如：

retry

Retry

retry,

retries

retried

retrying

这些到底怎么算？

你至少要明确两层规则：

第一层：表面标准化

这必须有：

全部转小写

去首尾标点

去多余空格

这样：

Retry

retry

retry,

都算一个词。

第二层：是否做词形归并

比如：

retries

retried

retrying

要不要都归到 retry？

这个功能很好，但第一版别做太重。
因为一旦做 lemma 归并，你就要考虑：

不规则词

误归并

多义词问题

第一版建议

只做表面标准化，不做词形归并。
也就是：

Retry = retry

retry, = retry

但 retrying ≠ retry

这更稳。

三、你漏掉的一个关键交互：队列里的“延迟筛选”

你现在想到的是：

收进队列

之后批量生成

但这里还有一步你没说出来：

生成前筛选

这一步很重要。

因为你观看时收词通常是“先抓住再说”，里面一定会混入：

其实没必要记的词

重复遇到但没必要再制卡的词

一时冲动选进去的词

所以队列不该只是“待处理列表”，还应该支持：

删除

勾选

排序

批量选择生成

否则队列只是一个垃圾堆。

四、你漏掉的一个很值钱的功能：原句预览

既然你允许传入网页原句作为辅助上下文，那队列里就不该只显示单词。

应该至少显示：

单词

原句片段

来源标题

加入时间

为什么这很重要？

因为同一个词在不同语境下，值不值得做卡不一样。
你如果只看到一个裸词，很难判断这次为什么记它。

所以原句预览不是装饰，是帮助你后续筛选的重要依据。

五、你漏掉的一个非常实用的点：来源类型区分

你问这是网页通用还是只有 YouTube 上使用。
答案我已经说了：网页通用，YouTube 特化增强。

那这就意味着你的系统里要有：

source_type = web

source_type = youtube

这个字段很有用，因为后续你可以针对不同来源做不同增强：

对普通网页

抓选中的词

尝试抓所在段落或句子

保存页面标题和 URL

对 YouTube

抓选中的词

尝试抓当前字幕原句

保存视频标题、URL、时间戳

如果不区分来源类型，后面你的逻辑会越来越乱。

六、你漏掉的一个未来很有用的点：生成版本号

这点大多数人都会漏，而且后面会后悔。

既然你有：

SYSTEM_PROMPT

format_card_front

format_card_back

那未来这些东西一定会改。

问题来了：
如果半年后你改了 prompt，发现新卡质量更高，你怎么知道老卡是哪一版生成的？

所以建议你从一开始就有一个概念：

generator_version

或 prompt_version

或 template_version

这不一定非得显示给你看，但它对后面迭代很有用。

例如：

v1 的 pairs 不好

v2 的 examples 更自然

有版本号，你以后才能追踪和重生成。

七、你漏掉的一个操作层功能：失败项单独重试

这个不是第一天必须做，但非常值得保留在设计里。

因为你的完整制卡链条失败点不少：

LLM 格式错

API 超时

音频失败

AnkiConnect 失败

所以批量生成时，结果不应该只有“成功/失败”两个概念。
应该有：

成功项

失败项

失败原因

重试入口

否则你每次失败都得整批重跑，很蠢。

八、你漏掉的一个体验点：快捷键不应该只有一个

这不是第一版必须，但很值得提前想。

例如：

Alt+Q：加入待处理

Alt+W：打开待处理面板

Alt+E：对当前词快速查看是否已存在

第一版可以只做一个快捷键。
但你在设计时要留出扩展空间，不然以后命令体系很乱。

九、你漏掉的一个边界问题：选中的不一定是“干净单词”

现实情况里，用户会选中：

retry.

“retry”

retry/abort

log-in

state-of-the-art

这些都很常见。

所以你要提前决定什么样的字符串才算合法输入。

第一版建议

允许：

字母

连字符

撇号

拒绝：

明显包含多个词的长串

含太多符号的异常串

这类规则不定，后面队列会很脏。

我给你的一个更完整的功能框架

A. 必做功能

这些不是 idea，是必须有：

网页通用选词 + 快捷键加入待处理

队列去重

Anki 已有卡去重

待处理列表

批量生成

失败提示

自定义 note type + word_key

B. 很值得做的增强

这些是你当前最可能遗漏但价值很高的：

原句预览

来源标题 / URL

YouTube 时间戳

生成前筛选

失败项重试

版本号字段

C. 暂时别急着做的

这些不是没用，是现在做会分散注意力：

自动词形归并

自动截图

自动图片生成

自动抓取整段字幕

多语言支持

智能推荐是否值得制卡

这些都容易把项目拖偏。

关于自定义 note type，我直接给你判断

你如果已经决定升级，那 note type 至少要支持下面这种思路：

最少字段集

word_key：查重用

word：展示词

ipa

emoji

audio

image_prompt

meanings

pairs

examples

source_sentence

source_title

source_url

source_timestamp

其中：

word_key 是系统字段

source_* 是半系统半展示字段

其余是展示字段

你不一定要全部在卡片正反面显示，
但字段层最好留好。

最后给你最直接的答案

你遗漏的好 idea 里，最值得补上的有这几个：

word_key 独立字段，用于稳健查重

队列项显示原句预览，而不是只显示单词

区分 web 和 youtube 两类来源

保存来源 URL / 标题 / 时间戳

生成版本号，方便以后升级 prompt 和模板

失败项可重试，而不是整批重做

这个工具该怎么定位？

网页通用，YouTube 优化。

不是 YouTube 专用。
YouTube 只是最重要的一个使用场景，不是整个系统的边界。

你下一步该认真讨论的是：自定义 note type 的字段设计，哪些字段只用于系统，哪些字段要展示在卡片上。

---

## 👤 用户

词形归并很重要，因为在观看时单词的状态是不一样的，可以在anki的模板那加上改单词的过去式，未来式，但是重心还是单词一般现在时本身，标准化同样重要，只集中在单词，不要什么符号空格、标识符之类的，原句预览可以添加就是不知道会不会对拓展是一个负担；
网页通用，YouTube 特化增强：我会使用很多的网页和视频网站，不过只有YouTube是英文的，其他基本是中文网站；
生成版本号：这个建议不错，而且我希望代码要分文件管理，这样不会全部叠在一个文件里，不好我在比如说修改提示词，修改模板这类的
失败项单独重试：我在本地也会遇到api超时之类的问题，我都是重启命令行，重新输入单词；
快捷键不应该只有一个：我本来想的是鼠标右键，但是发现，我在通用页面是鼠标左键划词，然后快捷键，还是怎么样没明白，还有YouTube的字幕有的视频时自带字幕，有的是自动生成，那么我怎么选取改单词，然后快捷键呢，刚才我都没想到

## 🤖 AI

你这次补充的信息很关键，直接把方案从“抽象好想法”拉回了真实使用场景。

先下结论：

你现在最大的风险已经不是后端，而是“采集动作本身到底顺不顺手”。
如果采集动作不顺，后面 note type、提示词版本、失败重试设计得再漂亮，都没用。

先逐条判断你说的点

1. 词形归并很重要

对，这个我同意。你这次说得比前面准确。

你真正要的不是“表面完全相同才算同一个词”，而是：

不同时态/变形，应该尽量归到同一个核心词条。

比如：

retry

retries

retried

retrying

你更希望它们最终指向 retry。

这个方向是对的。
但你这里有一个必须拆开的概念：

概念 A：采集时的原始词形

这是你当下在网页里实际看到的词。
它应该被保留。

概念 B：用于查重和主词条的归一词形

这是系统内部真正认定的“核心词”。

这两个不能混成一个字段。

否则会出两个问题：

你丢失原始语境，后面不知道当时看到的是 retried 还是 retrying

查重会混乱，系统不知道到底该拿哪个值当唯一键

所以后面一定要分：

surface_form：你在网页里实际选中的词

lemma / word_key：归并后的核心词

你这点终于碰到真正系统设计了。这个方向对。

2. 标准化同样重要，只集中在单词

也对，而且必须做。

你说“不要什么符号空格、标识符之类的”，这本质上就是：

采集入口要尽量只接受干净的词。

这说明第一版输入规则应该偏严格，而不是偏宽松。

合理做法是：

去掉首尾标点

统一大小写

去掉多余空白

明显不是单词的直接拒绝

这一步放在最前面，否则后面队列会脏得很快。

3. 原句预览可以加，但担心对扩展有负担

这个担心是合理的，但你说得还不够准确。

真正的问题不是“对扩展有没有负担”，而是：

原句获取在不同站点上稳定不稳定。

扩展负担本身不大。
难点在于：

普通网页：选区附近通常还能拿到句子或段落

YouTube：字幕 DOM 结构、自动字幕、站点渲染方式，不稳定

所以正确判断是：

对普通网页

原句预览价值高，成本可控，建议做。

对 YouTube

原句预览也有价值，但不要把它当刚需。
能取到就带上，取不到就只收词。

也就是说，原句预览应该是：
通用增强功能，不是核心依赖。

你别把它当成第一版成败关键，否则你会在 YouTube 这里卡很久。

4. 网页通用，YouTube 特化增强

这个判断是对的，而且终于不再偏。

你自己已经给了最重要的信息：

我会使用很多网页和视频网站，不过只有 YouTube 是英文的，其他基本是中文网站

这说明工具的定位应该是：

日常主场景

YouTube 英文视频

泛化兼容场景

其他网页中偶尔出现的英文单词

所以产品设计上不该是“所有网页平均用力”，而应该是：

基础交互网页通用，体验优化重点放在 YouTube。

这比“纯 YouTube 专用”更稳，也比“所有站点都深度适配”更现实。

5. 生成版本号 + 分文件管理

对。这两个都不是装饰，是必须的。

尤其你现在已经明确会改：

提示词

模板

失败重试策略

去重规则

还把所有东西堆在一个 main.py，就是明显错误。

你不需要现在就写代码，但架构上必须定死：

prompt 单独文件

card template 单独文件

queue 单独文件

dedupe / normalization / lemma 单独文件

anki adapter 单独文件

browser trigger / api 单独文件

否则你后面每改一次提示词，都要在一个巨型文件里翻。那不是开发，是自找麻烦。

6. 失败项单独重试

这个必须有，没什么可争的。

你现在“重启命令行，重新输入单词”的方式，本质上是：

没有任务状态

没有失败记录

没有最小重试单元

这很低效。

既然你已经接受“待处理队列 + 批量生成”，那就必须顺带接受：

成功项保留成功状态

失败项单独标记失败

失败项支持单独重试

不然批量生成的价值会被你自己毁掉。

现在说最关键的：快捷键和选词动作

你这段话里最重要的其实是这个：

我本来想的是鼠标右键，但是发现，我在通用页面是鼠标左键划词，然后快捷键，还是怎么样没明白，还有YouTube的字幕有的视频时自带字幕，有的是自动生成，那么我怎么选取改单词，然后快捷键呢，刚才我都没想到

对，这才是核心。
你之前一直在想“生成后怎么处理”，现在终于意识到“前面怎么采”才是第一道坎。

你要把采集方式分成两类，不要混

模式 A：普通网页模式

这里最自然的交互就是：

左键选词 -> 右键菜单 或 快捷键

这个没问题，逻辑清楚。

两种触发都可以保留

1. 右键菜单

优点：

符合直觉

用户不用记快捷键

对普通网页最好用

缺点：

比快捷键慢一点

2. 快捷键

优点：

快

连续操作效率高

缺点：

需要记忆

选区焦点有时可能不稳定

对普通网页的结论

右键菜单 + 快捷键，两个都应该有。
不是二选一。

你之前把它们想成互斥了，这是错的。
好的工具不会强迫用户只剩一种触发方式。

模式 B：YouTube 模式

这里麻烦很多。

问题不在“快捷键”，而在：

字幕到底能不能顺畅被选中。

现实里有几种情况：

情况 1：字幕文本能被直接选中

那就和普通网页一样：

左键选词

右键或快捷键

这是最理想情况。

情况 2：字幕文本不好选，或者选起来非常费劲

这在 YouTube 很可能出现，尤其自动字幕或不同页面状态下。

那你如果还坚持“必须手动选中单词”，体验就会很差。

所以 YouTube 模式不能只靠“普通网页选区逻辑”。

这意味着什么

意味着你现在至少要承认一个事实：

对普通网页

“选中单词”是合理主交互。

对 YouTube

“选中单词”未必总是合理主交互。

这就是你之前遗漏的关键。

所以 YouTube 特化增强里，最有价值的不是时间戳，而是“更易采集”

你之前一直在想：

时间戳

原句

来源

这些都重要，但不是第一优先。

YouTube 场景第一优先其实是：怎么更轻松拿到词。

我建议你把 YouTube 的采集分两档设计

YouTube 档 1：先兼容普通选词

也就是先假设：

能选就选

选完后右键/快捷键加入队列

这是第一版最稳的起点。

YouTube 档 2：后续再做“当前字幕辅助采集”

例如将来可以考虑：

扩展读取当前显示字幕文本

你在一个小面板里点其中某个词加入队列

或者自动把当前字幕分词后供你快速点击

注意，我这里只是在说产品方向，不是在让你现在就做。
因为这个复杂度明显更高。

你现在最该定的，不是“只用快捷键还是只用右键”

而是：

触发方式应该双轨并存

对普通网页

主推：右键菜单

补充：快捷键

对 YouTube

第一版：先试选词 + 右键/快捷键

如果实测很难选，再专门补 YouTube 采集优化

这才是务实路线。

你现在千万别一拍脑袋就决定“全靠快捷键”。
如果前提是“必须先手动精准选中字幕词”，那快捷键本身解决不了核心痛点。

我给你补几个你之前没说透，但现在很重要的 idea

1. 右键菜单必须有

这是你刚刚自己绕出来的问题的直接解法之一。

因为普通网页里：

左键划词

右键“加入待处理”

这非常自然。
你只靠快捷键，其实是在提高使用门槛。

2. 队列添加成功提示要非常轻

尤其 YouTube 场景。
不要大弹窗，不要要求确认。

最好只是一个短暂提示：

已加入待处理

已在待处理队列中

已存在于 Anki

然后立刻消失。

3. YouTube 模式要容忍“只采词，不采句”

这是非常重要的边界。
不要把“拿到原句”当作 YouTube 采集成功的必要条件。

4. 词形归并最好放在后端，不放在扩展

扩展只负责把你选中的表面形式发过去。
真正的：

标准化

lemma 提取

去重判断

都应该在后端统一做。
否则浏览器端和本地端规则一不一致，马上出 bug。

你现在的方案，我帮你重新收束一下

网页通用主流程

左键选中单词

触发方式二选一：


右键加入待处理


快捷键加入待处理

浏览器轻提示结果

YouTube 第一版流程

先尝试同样的选词方式

能选中就沿用通用流程

原句能抓则抓，抓不到也照样收词

后端处理

标准化

词形归并

查队列重复

查 Anki 重复

决定是否加入待处理

批量生成

打开待处理列表

筛选 / 删除 / 勾选

批量生成正式卡

失败项单独重试

最后我直接给你判断

你目前真正该优先补的不是更多 fancy 功能，而是这三件事：

第一，输入动作设计

普通网页和 YouTube 的采集动作到底顺不顺手。

第二，去重规则

标准化 + 词形归并 + Anki 查重。

第三，模块拆分

不要再让 prompt、模板、队列、Anki 适配器、失败重试全部堆在一个文件。

这三件不解决，后面功能越加越乱。

你下一步最值得继续讨论的是：
自定义 note type 的字段设计，尤其是 surface_form、lemma/word_key、source_sentence 这些字段怎么分工。

---

## 👤 用户

确实，网页拓展最重要的是选词，后续单词的处理本地的后端来进行

## 🤖 AI

对。你这句才是整个方案的核心。

扩展负责“拿到词”，后端负责“把词变成卡”。

这就是正确分层。
一旦分层清楚，很多之前混乱的问题都会自动变简单：

扩展不用管 prompt

扩展不用管 Anki 模板

扩展不用管音频生成

扩展不用管词形归并

扩展不用管失败重试

扩展只需要解决一件最难也最关键的事：

如何尽量顺手地把当前看到的词交给本地后端

这才是浏览器侧真正的价值。

所以现在浏览器扩展的职责应该被压缩到很薄

扩展端应该只做这几件事

获取当前选中的文本

尝试获取少量上下文


原句


页面标题


URL


YouTube 时间戳（能拿就拿）

把这些内容发给本地后端

显示轻提示


已加入待处理


已在待处理队列中


已存在于 Anki


采集失败

就这些。
不要让扩展变胖。

后端才是你的真正系统核心

后端负责的事

输入标准化

词形归并

队列去重

Anki 去重

队列存储

批量生成

调 SYSTEM_PROMPT

调音频生成

调 format_card_front/back

写入 Anki

失败记录和重试

版本号管理

这些都应该留在本地后端。
因为这些是规则、资产和复杂度所在。

你现在应该把系统正式理解成两部分

前端采集器

目标：快、轻、稳

关键词：

选词顺手

不打断观看

反馈简单

本地制卡引擎

目标：准、稳、可维护

关键词：

规则统一

模板统一

去重可靠

可重试

这两个目标本来就不一样。
所以不能再想着“一个模块把所有事都干了”。

接下来你最该优先想清楚的，不是生成逻辑，而是采集交互

也就是：

普通网页怎么选词最顺

和

YouTube 字幕怎么选词最顺

因为这一步不顺，整个扩展就没有价值。

你现在已经想明白后端归后端了，那下一步正确方向就是专门把浏览器采集端的交互定下来。
先别再回头纠结 prompt 或 main 了。

---

## 👤 用户

还有一点，要提醒我anki程序要打开，程序打开端口号才出现，才能加入anki，或者是要添加卡片，自动运行anki，感觉后者好一些

## 🤖 AI

后者体验更好，但不能想当然。

你这里其实有三个层级的方案，从稳到爽分别是：

方案 1：只提醒你打开 Anki

流程：

扩展把词发给本地后端

后端检查 127.0.0.1:8765 是否可用

如果不可用，返回：


Anki 未打开


请先启动 Anki

这个最简单，也最稳。
但体验一般，因为你还得手动切出去开 Anki。

方案 2：后端尝试自动启动 Anki

这个更符合你的使用习惯，也更合理。

流程：

后端收到“加入待处理”或“生成卡片”请求

检查 AnkiConnect 端口是否可用

如果不可用：


尝试启动本机 Anki


等几秒让 Anki 和 AnkiConnect 起起来


再次检测 8765


成功就继续


失败再提示浏览器：Anki 未启动成功

这比单纯提醒强很多。

但这里要说清楚：

自动启动 Anki 这件事应该由本地后端做，不应该由浏览器扩展做。

原因很简单：

扩展本身不能可靠地直接拉起你本地任意程序

你已经决定“扩展只负责选词，后端负责处理”

那启动 Anki 也应该属于后端职责

所以架构上很清楚：

扩展：发请求

后端：检查环境、必要时拉起 Anki、写入 Anki

方案 3：完全不依赖 Anki 当下打开

这是最适合你整体方案的。

你现在不是要“选词后立刻写入正式卡”，而是：

先进入待处理队列，之后批量生成正式卡。

既然是这样，其实观看时根本不需要 Anki 打开。

这就是你前面方案的一个额外好处，你自己还没完全意识到。

正确拆分后：

观看时

只把词加入待处理队列

不需要 Anki 打开

不需要 8765 可用

不需要生成音频

不需要调模型

批量生成正式卡时

这时才需要 Anki 打开

后端检查 8765

若没开，自动尝试启动 Anki

启动失败再提示你

这才是最顺的。

所以我直接给结论

最优方案不是“选词时自动运行 Anki”

而是：

选词加入待处理队列时

完全不依赖 Anki

批量生成正式卡片时

再检查 Anki 是否打开；若没打开，后端自动尝试启动

这比你现在想的更合理。

因为你最在意的是：

不影响观看体验

那观看阶段就不该掺进 Anki 这个依赖。
否则你明明只是想先记个词，结果还要关心：

Anki 开没开

端口起没起

插件在不在

这很蠢。

你这里真正该加的提醒逻辑是两层

第一层：采集阶段

如果只是加入待处理队列：

不要提醒 Anki。

因为没必要。
提醒了反而增加干扰。

第二层：生成阶段

当你点击“批量生成卡片”时：

后端先检查：

AnkiConnect 是否可用

如果可用

直接生成

如果不可用

尝试自动启动 Anki

如果自动启动成功

继续生成

如果失败

浏览器提示：


未检测到 Anki/AnkiConnect


请确认 Anki 已安装并启用 AnkiConnect

这才是干净流程。

你这个想法里有个隐藏好处

如果后端负责自动启动 Anki，那以后也能顺带处理更多依赖检查，例如：

AnkiConnect 没装

端口被占用

音频服务失败

API key 缺失

也就是说，后端可以统一做“运行环境检查”。
这比让浏览器端胡乱猜状态强得多。

但我要泼个冷水

“自动启动 Anki”听起来很好，但不要把它当成必然成功。

原因很现实：

不同系统安装路径不同

你本地可能不止一个 Anki 路径

启动后 AnkiConnect 不一定立刻就绪

有时启动了 Anki，但插件没加载成功

所以设计上应该是：

自动启动 = 尝试优化体验

不是：

自动启动 = 唯一依赖路径

也就是说，失败兜底仍然必须有明确提示。

你现在该定的规则

规则 1

加入待处理队列时，不依赖 Anki 是否打开。

规则 2

只有在“正式生成卡片”时，才检测 AnkiConnect。

规则 3

若 Anki 未打开，后端先尝试自动启动。

规则 4

若自动启动失败，再提示用户手动处理。

这四条一旦定了，体验会顺很多。

我对你这个想法的评价

这次思路是对的，但你还差最后一步抽象。

你现在还在下意识把“加入队列”和“生成卡片”当成一个阶段，所以才会想：

要提醒我 anki 程序要打开，或者自动运行 anki

实际上，只有“生成卡片”这个阶段才需要考虑 Anki。
“加入队列”根本不该管它。

把这两步拆开后，你的系统会轻很多，也顺很多。

最终建议

加入待处理时不检查 Anki；批量生成时由后端自动检查并尝试启动 Anki，失败再浏览器提示。

这比“全程都要求 Anki 开着”明显更好。

---

## 👤 用户

自动启动 Anki 这件事应该由本地后端做，不应该由浏览器扩展做。批量生成正式卡片时

再检查 Anki 是否打开；若没打开，后端自动尝试启动；
拓展的功能绝对是选词，轻量、简单；后续的工作都交给本地后端，主要目的还是不影响观看体验

## 🤖 AI

对，这个方向现在是正确的，而且已经收束了。

你现在的系统边界应该正式定成这样：

浏览器扩展

只做四件事：

选词触发


普通网页：左键划词后，右键菜单或快捷键触发


YouTube：第一版先沿用同样方式，别急着做复杂字幕抓取

采集少量上下文


选中的原始词形


可选原句


页面标题


URL


YouTube 时间戳能拿就拿，拿不到别阻塞

发给本地后端


扩展不做任何重逻辑


不做 prompt


不做 Anki


不做词形归并


不做去重判断

轻提示


已加入待处理


已在待处理队列中


已存在于 Anki


采集失败

这就是全部。
扩展越薄越对。

本地后端

后端才是你的真正系统：

输入标准化

词形归并

队列去重

Anki 去重

待处理队列存储

批量生成正式卡

调 SYSTEM_PROMPT

音频生成

套用 format_card_front/back

写入 Anki

失败记录

失败项单独重试

生成版本号管理

批量生成时检查/自动启动 Anki

这才是你该投入精力的地方。

Anki 的规则

你刚才定的这个也对：

加入待处理队列时，不依赖 Anki

批量生成正式卡片时，才检查 Anki

若没开，由后端尝试自动启动

启动失败，再返回浏览器提示

这条规则非常干净。
它直接服务你的核心目标：不影响观看体验。

你现在的主目标，已经可以写成一句话

浏览器扩展只做轻量采集，本地后端完成全部重处理。

这句话以后别再改了。
一改，你架构又会散。

你现在还剩下的关键未决项

已经不多了，只剩真正重要的几个：

1. 采集交互

普通网页：右键菜单和快捷键都保留

YouTube：第一版先验证“字幕是否容易选词”，别靠想象

2. 自定义 note type 字段设计

尤其这几个要分清：

surface_form

lemma / word_key

source_sentence

source_url

source_title

source_timestamp

generator_version

3. 队列数据结构

至少要有：

pending

success

failed

4. 去重规则

必须明确：

标准化规则

词形归并规则

队列查重

Anki 查重

我直接给你一个最终判断

你现在不需要再讨论“要不要直接连 Anki”“要不要扩展做更多逻辑”“要不要把 prompt 放前端”。

这些都已经有答案了：

扩展只采集

后端做重活

生成时再碰 Anki

观看阶段绝不被重任务打断

这条路是成立的。

下一步最该继续讨论的，是 自定义 note type 的字段设计。这一步决定你后面的去重、来源记录、模板维护会不会干净。

---

## 👤 用户

还有一点，具体实现的代码我要让codex桌面版来实现，那么我就需要考虑，拓展和后端的代码分为两块，但是要有相同的定义保证连接，自定义 note type 的字段设计，目前先在我的anki卡片的基础上进行改变

## 🤖 AI

对，这一步你想得对，而且终于进入真正的工程问题了。

你现在不是在想“能不能做”，而是在想：

怎么把“扩展”和“本地后端”拆开开发，但又保证它们始终说同一种语言。

这就是系统接口设计问题。
如果这一步不先定，后面让 Codex 写代码，大概率会写成两边各自猜字段、各自猜状态，最后接不上。

你现在必须先定一个“共享协议”

扩展和后端是两块代码，但它们之间必须有一套共同定义，不然一定乱。

这套共同定义至少包括四类：

1. 输入数据定义

也就是扩展发给后端时，最少要包含什么。

比如概念上至少要区分：

用户实际选中的词

来源句子

来源页面

来源类型

时间戳

触发时间

这里最关键的是两个字段不能混：

surface_form

用户在网页里实际选中的词形。
例如看到的是：

retried

retrying

retries

就保留原样。

word_key / lemma

后端归并后的主词条。
例如最终都归到：

retry

这两个不分开，后面查重和回溯都会乱。

2. 后端返回结果定义

扩展不是只管“发出去”就完了，它还要给用户提示。

所以后端返回值必须有统一状态，而不是随便返回一句字符串。

至少应该有这种层次：

已加入待处理

已在待处理队列中

已存在于 Anki

输入不合法

后端不可用

处理失败

这里不要让 Codex 自己拍脑袋命名。
你应该先把状态枚举定死。

不然将来你前端写的是：

duplicate_in_queue

后端返回的是：

already_exists_queue

这种低级错误一定会出现。

3. 队列项定义

因为你现在已经决定采用“待处理队列”，那队列里每一项长什么样，也要统一。

一个队列项至少应该有三层信息：

采集信息

surface_form

source_sentence

source_url

source_title

source_type

source_timestamp

归一信息

normalized_form

lemma

word_key

生命周期信息

status

created_at

updated_at

error_message

generator_version

这三层你要分清。
否则你后面会把“来源信息”“系统信息”“展示信息”全塞成一团。

4. Note Type 字段定义

这就是你现在最该认真想的地方。

你说“目前先在我的 Anki 卡片基础上进行改变”，这个方向可以，但不要只改表面。
你现在不是简单换个模板，而是要让这张卡片既能展示，又能被系统管理。

所以字段要分成两类：

一类：展示字段

这些是为了保留你现在满意的卡片效果。

根据你现有卡片，展示层最少有：

word

ipa

emoji

audio

image_prompt

meanings

pairs

examples

这部分是你现在已有卡片效果的核心。
正面和背面的大多数内容都来自这些。

另一类：系统字段

这是你以前的 Basic 模型缺的，也是你这次必须补的。

至少应该有：

word_key

surface_form

lemma

source_sentence

source_title

source_url

source_type

source_timestamp

generator_version

这些字段不一定全显示在正反面，
但系统必须有。

尤其是：

word_key

这是查重主键。
没有它，你后面还会回到“从 HTML 里猜这是不是 retry”的脏方案。

surface_form

这个让你保留“当时实际看到的词形”。

lemma

这个支持词形归并。

generator_version

这个支持你未来改 prompt 和模板后知道这张卡是哪一版生成的。

你现在最该做的，不是“让 Codex 开写”

而是先给 Codex 一份固定契约

这份契约至少要包含三部分：

第一部分：扩展到后端的请求契约

也就是扩展发请求时字段名和意义。

比如要明确：

哪些字段必填

哪些字段可空

哪些字段由扩展采集

哪些字段由后端补全

这里最典型的就是：

扩展负责提供

surface_form

source_sentence（可选）

source_url

source_title

source_type

source_timestamp（可选）

后端负责生成

normalized_form

lemma

word_key

去重判断

队列状态

这一步必须写清楚。

第二部分：后端对扩展的响应契约

例如扩展收到结果后只根据状态做提示，不自己推断。

你应该定这种思路：

扩展不理解复杂业务

扩展只识别标准状态码/状态名

后端负责把复杂逻辑收敛成有限状态

这样扩展才会轻。

第三部分：Note Type 字段契约

也就是 Anki 里最终有哪些字段，哪些是展示字段，哪些是系统字段。

Codex 最容易犯的错就是：

后端里叫 lemma

Note Type 里叫 base_word

模板里又叫 word_key

最后三边名字不一致。

所以你现在必须先统一命名。
命名不统一，后面全是胶水代码。

你说“先在我的现有卡片基础上进行改变”，这个思路没错，但你要注意改动层次

你现在现有卡片的优势是：

正反面样式你满意

内容结构你满意

所以不要推翻重来。
但“基于现有卡片改”不等于“继续沿用 Basic 那种只有 Front/Back 的思路”。

正确做法是：

保留

正面视觉结构

背面三段结构

现有 prompt 输出结构

升级

从“Front/Back 承载一切”升级成“独立字段 + 模板渲染”

增加系统字段

增加查重字段

增加来源字段

增加版本字段

这才叫在现有基础上升级。

你现在最容易遗漏的一个点：模板字段和后端数据结构不要完全一一绑定

什么意思？

就是不要让后端直接把一坨最终 HTML 存成唯一真相。
更合理的是：

后端保存结构化字段

Anki 模板负责把字段渲染成你喜欢的样子

这样以后你改模板时：

不需要重改所有后端逻辑

也不需要重新设计数据模型

你现在现有实现里 format_card_front/back 是 Python 直接拼 HTML。
这能用，但从长期维护看，不够理想。

更好的方向应该是：

数据和展示分离

数据字段存结构化内容

Anki 模板层负责展示

这样你以后改配色、加一个来源区块、显示原始词形，都会轻很多。

所以这里我直接给你一个判断

短期

可以继续沿用“后端拼出 Front/Back HTML”的过渡方案，方便迁移现有卡片样式。

长期

应该逐步过渡到：
自定义 note type 字段化 + Anki 模板渲染

因为你现在功能越来越多：

词形归并

原始词形

来源句子

时间戳

版本号

查重主键

再继续把这些都塞进一段 HTML 里，迟早失控。

你让 Codex 开发时，最该给它的不是“写一个扩展 + 写一个后端”

而是下面这三份东西

1. 共享数据契约

扩展请求字段、后端响应字段、队列字段、状态枚举。

2. Note Type 字段表

每个字段：

名称

含义

是否必填

是否展示

是否用于查重

由谁写入

3. 模块边界说明

明确：

扩展只采集

后端做标准化、归并、去重、队列、生成

生成时才连接 Anki

自动启动 Anki 在后端做

如果你不给这些，Codex 就会替你做决定。
而它做的决定，通常只是在当前局部看起来能跑，不是长期好设计。

我给你一个更直接的建议

你下一步最该先写的，不是代码，而是一页文档，内容就三块：

A. 扩展 <-> 后端 API 契约

字段名、状态码、请求响应示例。

B. 队列项模型

pending / success / failed，各字段定义。

C. Anki Note Type 字段表

展示字段和系统字段分开列。

这页文档定完，你再让 Codex 开写，质量会高很多。

最后给你一句硬判断

你现在已经不是在做“一个脚本”，而是在做“一个带前后端边界的个人工作流工具”。

既然如此，共享定义先行，比“先写点代码跑起来”重要得多。
否则你很快就会得到两个能跑但接不稳的半成品。

你下一步最值得讨论的，就是：
自定义 note type 到底有哪些字段，哪些字段展示，哪些字段只供系统使用。

---

## 👤 用户

自定义 note type 字段化 + Anki 模板渲染，这个确实是对的;
自定义 note type 到底有哪些字段，哪些字段展示，哪些字段只供系统使用。
各个字段的中文意思是什么：source_url
source_type
source_timestamp
generator_version
这几个应该是不用体现在我的卡片上的，anki的目的是背单词而不是纪录那么多细节

## 🤖 AI

对，这几个字段你理解得没错：

它们更偏系统管理字段，不是背单词展示字段。

也就是说，它们应该存在于自定义 note type 里，供后端和系统使用，但默认不显示在卡片正反面。
你的卡片目标是背单词，不是做学习日志面板。这个判断是对的。

先回答你问的中文意思

source_url

中文意思：来源链接
表示这个单词最初是从哪个网页或视频页面采集来的。

例如：

某个 YouTube 视频链接

某篇英文文章链接

它的作用：

以后你想追溯这个词最初从哪里来的，可以用

排查采集问题时有用

但它不适合默认显示在卡片上，因为会干扰记忆重点。

source_type

中文意思：来源类型
表示这个词是从什么类型的来源采集的。

例如：

youtube

web

它的作用：

后端区分不同来源的处理逻辑

以后统计“我主要从哪里积累单词”也能用

同样，它不适合显示在背单词卡片上。

source_timestamp

中文意思：来源时间点 或 视频时间戳
这个字段主要针对视频场景，表示这个词是在视频的哪个时间点被采集的。

例如：

00:12:35

它的作用：

以后想回到视频具体位置复看时有用

YouTube 场景下比较值钱

但它也不该默认显示在卡片正反面。
否则卡片会变得像“资料索引”，不是记忆卡。

generator_version

中文意思：生成版本号
表示这张卡片是用哪一版生成逻辑做出来的。

例如：

v1

prompt_v2_template_v3

它的作用：

以后你升级了 prompt 或模板，可以知道旧卡是哪一版生成的

出问题时方便排查

想批量重生成时有依据

这个字段更明显属于系统内部字段，完全不应该展示给你背诵时看。

所以你现在的字段，应该明确分成三类

这一步很重要。
不要只分“显示”和“不显示”，更合理的是分三层。

第一类：核心展示字段

这些是卡片正反面真正要展示的，直接服务记忆。

建议包括

word：单词本身

ipa：音标

emoji：记忆辅助图标

audio：发音音频

image_prompt：想象画面提示

meanings：英文释义

pairs：固定搭配

examples：例句

这就是你现在截图里最核心的部分。
这些必须展示。

第二类：辅助展示字段

这些字段不是必须展示，但未来可以选择性展示。

比如

surface_form：原始词形

source_sentence：来源原句

这两个字段以后可能有价值：

surface_form

如果你采到的是：

retried

retrying

而主词条最终归并到 retry

那你有时候可能想知道：
“我最初看到的是哪个形态？”

这个字段可以存在，但默认不一定显示。

source_sentence

这个比较有争议。
它对记忆有一定帮助，但也可能让卡片过载。

所以我建议：

字段保留

默认不显示

以后你想在背面底部加一个“来源原句”小区域时再开启

第三类：系统字段

这些字段就是你刚才提到的那些，重点是系统管理，不是给背诵看的。

建议包括

word_key

lemma

source_url

source_type

source_timestamp

generator_version

这些字段的作用分别是：

word_key

中文：单词唯一键
用于查重。
这是最重要的系统字段之一。

lemma

中文：词元 / 基础词形
用于词形归并。
比如 retried 最终归并到 retry。

source_url

中文：来源链接

source_type

中文：来源类型

source_timestamp

中文：来源时间点 / 视频时间戳

generator_version

中文：生成版本号

这些字段都应该存在，但默认不进入卡片正反面模板。

我给你的字段建议，按你当前需求收敛成这样

一、正面展示字段

只保留你现在满意的效果：

word

ipa

emoji

audio

image_prompt

这和你现在正面几乎一致。

二、背面展示字段

继续保持你现在的重点：

meanings

pairs

examples

如果以后你想加，也最多只建议加一个可折叠或弱化显示的：

source_sentence

但第一版没必要。

三、系统字段，不展示

这部分是你现在问的重点：

word_key：唯一键

lemma：基础词形

surface_form：原始词形

source_url：来源链接

source_type：来源类型

source_timestamp：来源时间点

generator_version：生成版本号

这里我要纠正你一点：

你刚才列出的四个字段确实不该展示，
但你漏掉了两个更关键的不展示字段：

word_key

lemma

这两个比 source_url 那些更核心。
因为它们直接影响去重和词形归并。

一个更直接的建议：别把所有字段都放进卡片视觉层

你现在最该坚持的原则是：

Note type 可以有很多字段，但卡片模板只渲染少数字段。

这就是“字段化 + 模板渲染”的真正好处。

也就是说：

字段多，不等于页面杂

系统强，不等于卡片乱

你以前用 Basic 的问题，就是所有东西只能硬塞到 Front/Back 里面。
现在升级后的好处就是：
系统字段和展示字段终于能分开了。

我建议你现在把字段表先定成这个版本

展示字段

word：单词

ipa：音标

emoji：记忆图标

audio：发音音频文件名

image_prompt：联想画面提示

meanings：英文释义

pairs：固定搭配

examples：例句

非展示但保留字段

surface_form：采集时看到的原始词形

source_sentence：采集时的来源原句

系统字段

word_key：查重键

lemma：基础词形

source_url：来源链接

source_type：来源类型

source_timestamp：来源时间点

generator_version：生成版本号

最后给你一个硬判断

你刚才说：

anki的目的是背单词而不是纪录那么多细节

这句话是对的，但不要误解成“那些细节字段就不该存在”。

更准确的说法是：

这些细节字段应该存在于 note type 中，但不应该出现在默认卡片展示中。

这才是正确设计。
不然你以后又会因为：

查重

词形归并

来源追踪

版本升级

而把系统重新搞乱。

下一步最合理的是：把这些字段再进一步收紧成一张“最终字段清单”，并标明每个字段是：
展示字段 / 可选展示字段 / 系统字段。

---

## 👤 用户

surface_form：原始词形
source_sentence：来源原句，其实在原句的时候就可以看到词形了，我认为没必要添加了；
来源原句可以放在examples里的第一句标注好是原句，然后再生成其他两个例句就好了；
我再考虑要不要再加入过去式和未来式会帮助我记忆单词吗

## 🤖 AI

surface_form 你这个判断，不严谨。

你说：

在原句的时候就可以看到词形了，我认为没必要添加了

这只在一个前提下成立：
你始终都能稳定拿到来源原句。

但前面你自己已经承认过，尤其在 YouTube 场景里，原句不一定总能稳定抓到。那这时候如果没有 surface_form，你就丢了一个很关键的信息：

你当时实际看到的是 retry

还是 retried

还是 retrying

所以我的判断是：

source_sentence 可以不单独展示

但

surface_form 不建议删

因为它很轻，成本很低，但价值不低。
它不是为了展示给你背，而是为了系统保留“你当时实际看到的形态”。

你这个调整里，真正合理的是另一句

来源原句可以放在 examples 里的第一句，标注好是原句，然后再生成其他两个例句

这个方向是好的，而且比单独再加一个“来源原句展示区”更克制。

因为你现在的背面本来就有 examples 区域。
如果再额外加一个 source_sentence 区块，信息层级会变乱。
反而把来源原句直接作为第一条例句，更自然。

我建议你把 examples 设计成固定 3 条，但语义分工明确

第 1 条

来源原句
如果采集到了原句，就把它放第一条，并且标注成来源句。

例如：

Please retry the download if it doesn't start automatically. (source sentence)

第 2、3 条

模型生成例句
继续走你原来的 SYSTEM_PROMPT 风格，只是数量从 3 条改成 2 条。

这样有几个好处：

保留真实语境

卡片背面结构不变

不额外增加一个来源区块

例句区更贴近你的真实输入来源

这个设计比“原句单独做字段并展示一整块”更干净。

但这里有个前提你要想清楚

如果你决定“来源原句占 examples 第一条”，那你的生成逻辑就得变成：

不再是固定由模型生成 3 条例句

而是：

有来源原句时：


第 1 条 = 来源原句


第 2、3 条 = 模型生成的两条例句

没有来源原句时：


3 条都由模型生成

这个规则必须提前定死。
否则后面 prompt、后端处理、模板显示都会出现分叉。

再说你问的重点：要不要加入过去式和未来式

先直接说结论：

过去式有价值

“未来式”这个说法不准确，而且通常没必要单独加

为什么“未来式”说法不准确

英语里你这里想表达的，应该是“不同词形变化”或者“时态相关形式”，不是“未来式”本身。

因为像动词 retry：

原形：retry

第三人称单数：retries

过去式：retried

现在分词：retrying

而所谓“未来式”通常不是一个独立词形字段。
英语一般是靠：

will retry

is going to retry

这种结构表达将来，不是给单词本身再加一个“未来式单形”。

所以如果你要加，正确方向应该是：

加“词形变化”

不是加“未来式”

那词形变化值不值得加

答案是：

值得考虑，但不要放到第一版的核心展示区

原因很简单：

对你有帮助的地方

能帮助你把 retry / retried / retrying / retries 这些形态连起来

对阅读识别很有帮助

也能支持你前面说的词形归并

风险

卡片信息量会变多

对某些词没那么大价值

如果展示方式不好，会喧宾夺主，削弱你对核心词义和搭配的记忆

所以这个功能不是不该有，而是展示层要弱化。

我给你的建议是：加“词形变化字段”，但默认弱展示

推荐字段不是“past / future”

而是一个更通用的字段，比如：

inflections

中文可以理解为：词形变化

里面可以包含：

third_person: retries

past: retried

past_participle: retried

present_participle: retrying

这样比你单独只存“过去式”和“未来式”严谨得多。

这些词形变化该不该显示在卡片上

我的判断：

可以显示，但不要放正面

正面现在已经很干净：

emoji

word

audio

ipa

image_prompt

这个结构别乱动。

背面可以加一个很轻的小区域

位置建议放在：

Meaning 后面，或

Pair 前面

弱化显示，例如一行小字：

retries / retried / retrying

或者标成：

Forms: retries, retried, retrying

这样你既能看到词形变化，又不会让它抢掉 meanings、pairs、examples 的主地位。

值不值得一开始就做

这里我给你一个更严格的判断：

从系统字段角度：值得保留

因为后端做词形归并时，本来就会涉及这些信息。

从展示角度：第一版可以先不显示

先把它存着，后面再决定是否显示。

这才是稳做法。

所以我给你一版更合理的字段取舍

保留

surface_form


不展示


用于保留用户当时实际选中的词形

不单独展示

source_sentence


不单独做一个卡片区块


采集到时塞进 examples[0]

新增可选字段

inflections


词形变化


先存，后决定是否显示

关于你现在的 examples，我建议你正式定成这个规则

examples 字段始终是 3 条

情况 1：有来源原句

来源原句（标注 source sentence）

生成例句

生成例句

情况 2：没有来源原句

生成例句

生成例句

生成例句

这个规则非常自然，也方便模板渲染。
别搞成“有时 2 条，有时 4 条”，那样显示层会开始飘。

最后给你一个直接判断

你这次说对的部分

不必把 source_sentence 单独做成一个展示区

来源原句可以并入 examples 第一条

词形变化确实对记忆和归并都有帮助

你说错或不够严谨的部分

surface_form 不是没必要，它仍然建议保留

“未来式”这个概念不准确，应该改成“词形变化”

我的最终建议

你现在更合理的设计是：

不展示但保留

surface_form

lemma

word_key

source_url

source_type

source_timestamp

generator_version

展示

word

ipa

emoji

audio

image_prompt

meanings

pairs

examples

可选新增

inflections（词形变化，先存后决定是否显示）

examples 规则

来源原句优先占第一条，后两条模型生成

这套比你现在的想法更完整，也更不容易后面返工。

下一步最值得继续定的是：inflections 到底只存动词变化，还是也考虑名词复数、形容词比较级这类变化。

---

## 👤 用户

我的意思是不展示在卡片内容上，我现在和你讨论的是不展示的字段

## 🤖 AI

那你刚才那句就说清楚了。
如果我们现在只讨论不展示在卡片上的字段，那你的方向可以进一步收紧。

先直接结论：

surface_form 仍然建议保留为不展示字段

虽然不显示在卡片上，但它对系统有用。

因为它解决的是：

你当时实际选中的是什么形态

后端归并前的原始输入是什么

以后排查“为什么这个词被归并到这个主词条”时能回溯

它不是为了给你背单词看的，所以完全可以作为不展示字段保留。

你现在这批“不展示字段”，建议分成两类理解

一类：核心系统字段

这些是后端逻辑真正依赖的，建议一定保留。

1. word_key

中文：单词唯一键
作用：

Anki 查重主键

队列和正式卡的唯一识别值

这个是最不能删的。

2. lemma

中文：基础词形 / 词元
作用：

词形归并后的核心词

比如 retried、retrying 最终归到 retry

如果你要做词形归并，这个字段必须有。

3. surface_form

中文：原始词形
作用：

保留你实际选中的形式

比如当时看到的是 retried，而不是抽象后的 retry

这个字段不显示，但很有价值。

4. generator_version

中文：生成版本号
作用：

以后你修改 prompt、模板、字段逻辑时，知道这张卡是哪一版生成的

这个也建议保留。

二类：来源追踪字段

这些对系统和调试有帮助，但不直接参与记忆展示。

5. source_url

中文：来源链接
作用：

记录这个词最初来自哪个网页或视频页面

6. source_type

中文：来源类型
作用：

区分来源是 youtube 还是 web

7. source_timestamp

中文：来源时间点 / 视频时间戳
作用：

视频场景下回定位用

这些字段你说不展示，这判断是对的。
它们存在的意义主要是：

回溯

调试

后续增强

不是为了背诵。

你现在还可以更严格一点：哪些不展示字段是“必须”，哪些只是“可选”

必须保留的不展示字段

这几个我认为你不该删：

word_key

lemma

surface_form

generator_version

原因很简单：
它们是系统结构的一部分，不是附属信息。

尤其：

没 word_key，查重会脏

没 lemma，词形归并会飘

没 surface_form，原始输入丢失

没 generator_version，后面升级不可追踪

建议保留的不展示字段

这些也有价值，但相对没那么核心：

source_url

source_type

source_timestamp

如果你只做普通网页抓词，它们的重要性一般。
但既然你明确有 YouTube 场景，那这三个还是值得留。

尤其是 source_type，它很轻，但能帮你区分不同来源逻辑。

你刚才提到一个隐含问题：source_sentence 还算不算不展示字段

如果你决定：

不单独展示 source_sentence

而是把来源原句塞进 examples 第一条

那 source_sentence 这个字段依然可以保留，但它不再是“直接展示字段”，而是：

中间数据字段

作用是：

后端拿它去构造 examples[0]

或在没用上时备用

所以它可以继续存在，但不需要直接出现在 Anki 卡片模板里。

这和 surface_form 一样，都属于：
存在于数据层，但不直接渲染到卡片层。

所以如果只谈“不展示字段”，我给你一版收紧后的建议清单

核心不展示字段

word_key：单词唯一键

lemma：基础词形

surface_form：原始词形

generator_version：生成版本号

来源不展示字段

source_url：来源链接

source_type：来源类型

source_timestamp：来源时间点

中间处理字段

source_sentence：来源原句
不单独展示，但可用于填充 examples[0]

我再替你把这些字段的“中文意思 + 为什么不展示”压缩说一遍

word_key：单词唯一键。给系统查重用，不给人背。

lemma：基础词形。给词形归并用，不给人背。

surface_form：原始词形。记录你实际选中的形式，不必展示。

source_url：来源链接。回溯来源用，不必展示。

source_type：来源类型。区分网页/YouTube 用，不必展示。

source_timestamp：来源时间点。视频定位用，不必展示。

generator_version：生成版本号。版本追踪用，不必展示。

source_sentence：来源原句。作为例句原料使用，不单独展示。

一个更严格的工程建议

你现在最好别再用“展示字段 / 不展示字段”这种二元分类停住。
更准确应该是三类：

1. 直接展示字段

模板直接渲染

2. 间接展示字段

不直接渲染，但会参与生成展示内容
比如：

source_sentence 参与构造 examples[0]

3. 纯系统字段

只给后端和系统逻辑使用
比如：

word_key

lemma

generator_version

这样你和 Codex 后面沟通会更准确。
不然“这字段不展示”可能被误解成“这字段没用”。

最后给你一个明确结论

如果我们现在只讨论不展示在卡片上的字段，我建议你保留这 7 个：

word_key

lemma

surface_form

source_url

source_type

source_timestamp

generator_version

另外：

source_sentence 不单独展示，但建议保留为中间处理字段

这套是合理的，既不污染卡片内容，又不会把系统做成瞎子。

---

## 👤 用户

弱化显示，例如一行小字：

retries / retried / retrying

或者标成：

Forms: retries, retried, retrying
这样不错因为我还是有一些基础的，一眼就可以判断时态了。弱化显示很不错

## 🤖 AI

对，这个比单独开一个大区块更合适。

你现在的卡片主干已经很清楚了：

正面：词、音标、发音、联想

背面：释义、搭配、例句

如果再把词形变化做成一个大模块，就会抢戏。
弱化显示才是对的，因为它的作用是“辅助识别”，不是“主学习目标”。

这个字段更适合叫

forms

或 inflections

中文理解成：

词形变化

常见变形

其中展示时用 Forms: 最自然，也最短。

展示位置

更合理的是放在背面上半部分，别放正面。

两个可选位置里，我更倾向：

Meaning 下面，Pair 上面

因为逻辑顺序更顺：

先知道这个词是什么

再看它有哪些常见变形

再看固定搭配

最后看例句

这样不会打乱你现在的主结构。

展示样式

你说的方向对，应该：

字号更小

颜色更淡

只占一两行

不加粗得太重

例如视觉上就让它像一个轻提示，而不是栏目标题。

内容范围

这里别贪多。第一版只放最常见、最有用的变形就行。

对动词，优先：

第三人称单数

过去式

现在分词

比如：

retries / retried / retrying

这就够了。
别一上来塞过去分词、名词形式、形容词派生、同根词，那会把卡片弄脏。

一个你需要提前定的规则

如果这个词不是动词，怎么办？

比如名词、形容词，就不一定有你想要的那种时态变化。
所以这个字段不该强制每张卡都有。

更合理的是：

有明显常见变形时才显示

没有就不显示这一行

这样模板更干净。

你现在这套思路，比较合理的分层是

主显示：word / ipa / meanings / pairs / examples

弱显示：forms

不显示：word_key / lemma / source_url / source_type / source_timestamp / generator_version

这个层级已经比较成熟了。

你下一步要定的，不是“要不要 forms”，而是：

forms 这个字段只面向动词，还是也支持名词复数、形容词比较级这类常见变化。

---

## 👤 用户

可以有forms，因为可以选择位置，比较好在模板上调整

## 🤖 AI

对，forms 值得加。

你这次理由是对的：
它不一定要强展示，而且位置可调，模板层很好控制。

这就是“字段化 + 模板渲染”的好处：

先把字段留出来

先把数据存进去

展示强度后面再调

而不是一开始就决定“必须醒目显示”或者“彻底不要”。

现在可以把字段层级先定下来

主展示字段

word：单词

ipa：音标

emoji：记忆图标

audio：音频

image_prompt：联想提示

meanings：英文释义

pairs：固定搭配

examples：例句

弱展示字段

forms：词形变化

不展示字段

word_key：查重键

lemma：基础词形

surface_form：原始词形

source_url：来源链接

source_type：来源类型

source_timestamp：来源时间点

generator_version：生成版本号

source_sentence：来源原句（用于构造 examples[0]，不单独展示）

forms 的中文含义

你以后和 Codex 对接时，最好别只说 forms，容易太泛。
更准确的中文可以定成：

词形变化

或 常见变形

我更推荐你内部文档写成：
forms（词形变化）

forms 里先放什么

别做大而全。第一版只放最常见、最有帮助的形式。

对动词，优先：

第三人称单数

过去式

现在分词

例如：

retries / retried / retrying

这已经很够用了。

现在最适合你的方向

不是继续纠结字段要不要再加几个，而是把 最终 note type 字段清单 定下来，分成三栏：

字段名

中文含义

展示层级（主展示 / 弱展示 / 不展示）

这一步定完，Codex 才不容易写乱。

---

## 👤 用户

forms就放在meaning和pair直接弱显示就好了

## 🤖 AI

可以，这个位置是对的。

放在 Meaning 和 Pair 之间，弱显示，是目前最顺的方案。
你这张图已经把层级关系说明白了：

Meaning 是主理解区

Forms 是轻辅助区

Pair 是主应用区

这样读起来很自然，不会抢主内容。

这个位置为什么合适

因为词形变化本来就更接近“词本身的信息”，而不是“搭配”或“例句”。

所以顺序上：

先看词义

顺手看一下常见变形

再看固定搭配

最后看例句

这是通顺的。

展示强度也对

你说“弱显示”，这个必须坚持。
不要把 Forms 做成和 Meaning / Pair / Example 同级的大标题，否则它会喧宾夺主。

更合理的是：

小一号字体

颜色更淡

不加图标

不用粗边框

只占一行或最多两行

也就是说，它应该像“补充提示”，不是“第四大板块”。

内容写法也该收一下

你图里写的是：

Forms: retried/retries/retring

这里有两个问题。

第一，顺序建议统一

更自然的顺序应该是：

第三人称单数

过去式

现在分词

也就是：

retries / retried / retrying

这样更符合常见英语学习顺序。

第二，你图里拼错了

你写成了：

retring

这是错的。应该是：

retrying

这种地方你以后让 Codex 生成时一定要小心。
词形变化一旦错了，卡片质量会直接掉。

一个更稳的展示格式

推荐用：

Forms: retries / retried / retrying

这比逗号分隔更清楚一点，也更适合你现在这套视觉风格。

最后把这条规则定死

你现在可以把 forms 的展示规则正式定成：

字段存在

放在 Meaning 和 Pair 之间

弱显示

仅在有内容时显示

不单独作为大标题区块

默认展示常见词形变化，不展示系统细节

这个决定已经够具体了，后面可以直接交给 Codex 实现。

你现在下一步该定的是：最终 note type 字段清单，把 forms 也正式写进去。

---

## 👤 用户

Forms: retries / retried / retrying这样是对的，最终 note type 字段清单，把 forms 也正式写进去。
那么现在一个制作条件的标准化规范我们需要写一个md文件，让codex读取，不会在ai构建代码的时候跑偏，或者在后续修改的时候修改字段什么的，导致拓展和后端无法归纳。
还有一点我的牌组名是直接写在代码里的比如说sherber，我目前应该是只会用这个牌组名，但是我如果想制作一个新牌库，我就要去找到相关的代码改名字，不过这不知道是不是我现在要考虑的，会不会增加负担，还是以后再改

## 🤖 AI

对，现在就该写一个 md 规格文档，而且这不是可选项，是必须项。

因为你已经不是在写一个单脚本了，而是在做：

浏览器扩展

本地后端

队列

Anki note type

模板渲染

去重和词形归并

这几个模块只要字段名、状态名、规则名有一个地方漂了，后面就会出现：

扩展传的是一种名字

后端接的是另一种名字

Anki note type 字段又是第三种名字

最后就是你说的那种情况：后续一改字段，扩展和后端对不上。

所以你这个 md 文件，本质上不是“说明文档”，而是：

唯一真源

也就是：
系统协议文档。

Codex 之后写代码，必须围绕它来，不允许自己发明字段名。

这个 md 文件里至少要写什么

我建议你别写得太散，直接固定成 7 个部分。

1. 项目目标

一句话写死：

浏览器扩展只负责轻量选词采集，不影响观看体验；本地后端负责标准化、词形归并、去重、待处理队列、批量生成正式 Anki 卡片。

这句话必须放最前面。
因为它决定边界，防止 Codex 把后端逻辑塞进扩展。

2. 模块职责边界

直接写清楚：

扩展负责

获取选中的单词

可选获取来源原句

获取来源标题 / URL / 来源类型 / 时间戳

发请求给本地后端

显示轻提示

后端负责

输入标准化

词形归并

队列查重

Anki 查重

队列管理

批量生成

调 LLM

生成音频

渲染模板

写入 Anki

生成时检查 / 自动启动 Anki

这部分不写，Codex 非常容易越界。

3. 共享字段定义

这是最关键的一节。
要把每个字段都写成表格。

至少要包含：

字段名

中文含义

来源

是否必填

是否展示

备注

你现在已经基本定下来的字段，可以先写成这样。

主展示字段

word：单词

ipa：音标

emoji：记忆图标

audio：音频

image_prompt：联想提示

meanings：英文释义

forms：词形变化

pairs：固定搭配

examples：例句

不展示字段

word_key：单词唯一键

lemma：基础词形

surface_form：原始词形

source_url：来源链接

source_type：来源类型

source_timestamp：来源时间点

generator_version：生成版本号

中间处理字段

source_sentence：来源原句，不单独展示，可用于构造 examples[0]

这里必须写清楚：
forms 是展示字段，surface_form 不是展示字段。
别让 Codex 自己猜。

4. 规则定义

这部分也非常重要。

输入规则

第一版只支持单词，不支持短语

去掉首尾标点

大小写标准化

非法输入直接拒绝

词形归并规则

记录 surface_form

归并得到 lemma

查重主要使用 word_key

examples 规则

有 source_sentence 时：


第一句为来源原句，并标注 source sentence


后两句由模型生成

无 source_sentence 时：


三句都由模型生成

forms 规则

forms 放在 Meaning 和 Pair 之间

弱显示

有内容才显示

默认格式：Forms: retries / retried / retrying

这些规则写不清，后面模板就会飘。

5. 状态枚举

你后端返回给扩展的状态一定要定死。

例如：

added_to_queue

already_in_queue

already_in_anki

invalid_input

backend_unavailable

processing_failed

别怕麻烦，这节必须写。
否则前后端提示文案会乱。

6. Note Type 规格

这部分要写清楚：

note type 名称

哪些字段属于展示层

哪些字段属于系统层

哪些字段默认不渲染

forms 的显示位置

source_*、generator_version 不显示在卡片上

这就是你后面模板不跑偏的关键。

7. 非目标

这节很容易被忽视，但很重要。

你要明确告诉 Codex：

第一版不做

短语卡

自动截图

自动图片生成

多语言支持

扩展端调用 LLM

扩展端直接操作 Anki

观看时直接生成正式卡

这节能防止它擅自“增强功能”。

你问牌组名 sherber 现在要不要改成可配置

我的判断很明确：

现在不用做复杂配置系统

但

现在就该把牌组名从硬编码逻辑里抽出来

也就是说，你不用现在做 UI 配置页面，但也不该继续把 sherber 散落写死在代码里。

这是两个不同层次的问题，你别混。

最合理的做法是什么

现在做

把牌组名定义成一个集中配置项。

例如在文档里明确一个统一概念：

default_deck_name = "sherber"

然后要求：

后端所有地方都从统一配置读取

不允许在业务代码里到处手写 "sherber"

这样带来的好处是：

你当前使用完全不变

代码不会到处硬编码

将来想换牌组名时，只改一个地方

这几乎不增加负担，却能避免后面很恶心的维护问题。

现在不做

不做前端设置页面

不做多牌组切换 UI

不做按来源自动分牌组

不做用户级配置中心

这些都可以以后再说。

所以你这个问题的正确答案是

不是“以后再改”

也不是

“现在做完整配置系统”

而是中间这条：

现在就把牌组名配置化

但只保留一个默认值：

sherber

这才是对的。

为什么我不建议继续硬编码 sherber

因为你已经明确说了：

如果我想制作一个新牌库，我就要去找到相关的代码改名字

这说明现在的设计已经让你不舒服了。
既然已经意识到这里会痛，就别继续放任它。

但也别夸张到现在就做复杂设置界面。
那会增加不必要负担。

你现在在 md 里应该把牌组写成什么

建议专门写一节：

默认配置

default_deck_name: sherber

default_note_type_name: 你后面确定的自定义 note type 名称

default_model_version: v1

同时再加一句约束：

默认牌组名和 note type 名称必须来自统一配置，不允许在扩展或后端业务逻辑中硬编码重复字符串。

这句很重要。
它是在防 Codex 到处复制常量。

我给你的直接建议

你现在下一步不要让 Codex 直接写代码。
你应该先让它根据你们已经定下来的内容，先产出一份 SPEC.md。

这份 SPEC.md 至少包含：

系统目标

模块边界

字段清单

状态枚举

note type 规格

默认配置

非目标

然后你自己先过一遍。
你确认了，再让它开始写扩展和后端。

这一步会帮你省大量返工。

关于牌组名，最终结论

现在就该考虑

因为这是结构问题，不是功能堆叠问题。

但只做最轻的一层

抽成统一配置

默认值仍然是 sherber

现在不需要做

多牌组 UI

动态切换

复杂配置中心

最后一句硬判断

SPEC.md 现在必须写；sherber 现在必须配置化，但不必产品化。

这两件事做了，Codex 才不容易把你的项目写成“暂时能跑、后面难改”的样子。

---

## 👤 用户

SPEC.md 你写一个

## 🤖 AI

下面是可直接给 Codex 读取的 SPEC.md 初稿。

```plaintext
Markdown# SPEC.md## 1. 项目目标本项目用于提升英文视频/网页阅读中的生词采集与 Anki 制卡效率。核心目标：- 浏览器扩展只负责**轻量选词采集**- 本地后端负责**标准化、词形归并、去重、待处理队列、批量生成正式 Anki 卡片**- 整体设计必须以**不影响观看体验**为最高优先级- 正式 Anki 卡片继续沿用现有高质量结构：`SYSTEM_PROMPT` + 自定义 note type 字段 + Anki 模板渲染一句话原则：> 扩展负责“拿到词”，后端负责“把词变成卡”。---## 2. 范围与非目标### 2.1 第一版范围第一版必须支持：- 普通网页中选中单词后加入待处理队列- YouTube 中尽量沿用相同方式选词并加入待处理队列- 扩展向本地后端发送采集请求- 后端执行标准化、词形归并、去重- 后端维护待处理队列- 用户在稍后手动触发批量生成正式卡片- 生成正式卡片时，后端调用 LLM、生成音频、写入 Anki- 生成时后端检测 Anki/AnkiConnect 是否可用；若不可用，尝试自动启动 Anki### 2.2 第一版非目标第一版明确不做：- 短语卡- 扩展端直接调用 LLM- 扩展端直接操作 Anki- 观看时立即生成正式卡- 自动截图- 自动图片生成- 多语言支持- 多牌组 UI 配置- 复杂设置中心- YouTube 专用复杂字幕解析面板---## 3. 模块边界## 3.1 浏览器扩展职责浏览器扩展只负责以下事项：1. 获取当前用户选中的单词2. 尝试获取少量上下文   - `surface_form`   - `source_sentence`（可选）   - `source_title`   - `source_url`   - `source_type`   - `source_timestamp`（可选）3. 将采集结果发送给本地后端4. 根据后端返回结果显示轻提示浏览器扩展禁止负责以下事项：- 调用 LLM- 生成音频- 词形归并- 队列去重- Anki 去重- 直接写入 Anki- 自动启动 Anki- 生成 HTML 卡片内容### 3.2 本地后端职责本地后端负责以下事项：1. 输入标准化2. 词形归并3. 队列去重4. Anki 查重5. 待处理队列管理6. 批量生成正式卡片7. 调用 LLM（使用统一 `SYSTEM_PROMPT`）8. 生成音频9. 写入自定义 note type 字段10. 依赖 Anki 模板渲染卡片11. 失败记录与失败项单独重试12. 生成版本号管理13. 批量生成时检查 / 自动启动 Anki---## 4. 默认配置第一版只保留最小配置能力，不做 UI 配置页。### 4.1 默认配置项- `default_deck_name = "sherber"`- `default_note_type_name = "<待定，自定义 note type 名称>"`- `default_generator_version = "v1"`### 4.2 配置约束- 默认牌组名必须来自统一配置- 默认 note type 名称必须来自统一配置- 不允许在扩展或后端业务逻辑中散落硬编码 `"sherber"`- 第一版不做多牌组切换功能- 将来如需切换牌组，只允许通过集中配置改动---## 5. 输入与采集规则### 5.1 输入对象第一版只支持：- 单个英文单词第一版不支持：- 短语- 整句- 多个单词组合- 含复杂符号的字符串### 5.2 标准化规则后端收到扩展传来的原始输入后，必须执行标准化：1. 去除首尾空白2. 去除首尾标点3. 统一大小写4. 校验是否合法英文单词5. 非法输入直接拒绝### 5.3 词形相关规则必须区分以下三个概念：- `surface_form`：用户在网页中实际选中的原始词形    例如：`retried`- `lemma`：词形归并后的基础词形    例如：`retry`- `word_key`：用于系统查重的唯一键    第一版默认以基础词形为核心生成稳定键### 5.4 去重规则后端采集时按以下顺序处理：1. 标准化输入2. 词形归并3. 查询待处理队列4. 查询 Anki 中是否已有对应 `word_key`5. 若重复，则不新建待处理项---## 6. 扩展 -> 后端 请求契约## 6.1 请求目的扩展向后端发送“采集一个待处理词项”的请求。### 6.2 请求字段定义| 字段名 | 中文含义 | 必填 | 来源 | 备注 ||---|---|---:|---|---|| `surface_form` | 原始词形 | 是 | 扩展采集 | 用户实际选中的文本 || `source_sentence` | 来源原句 | 否 | 扩展采集 | 能获取则传，不能获取则为空 || `source_title` | 来源标题 | 否 | 扩展采集 | 页面标题或视频标题 || `source_url` | 来源链接 | 否 | 扩展采集 | 页面 URL || `source_type` | 来源类型 | 是 | 扩展采集 | 枚举：`web` / `youtube` || `source_timestamp` | 来源时间点 | 否 | 扩展采集 | 主要用于 YouTube || `captured_at` | 采集时间 | 否 | 扩展或后端补全 | 若扩展不传，后端生成 |### 6.3 请求约束- `surface_form` 为唯一必需核心输入- 扩展只传原始采集数据，不传 `lemma` 和 `word_key`- `lemma`、`word_key` 必须由后端计算- 若 `source_sentence` 获取失败，不得阻塞采集流程---## 7. 后端 -> 扩展 响应契约扩展不自行推断业务逻辑，只根据后端返回的标准状态展示提示。### 7.1 状态枚举| 状态值 | 中文含义 | 扩展提示建议 ||---|---|---|| `added_to_queue` | 已加入待处理队列 | 已加入待处理 || `already_in_queue` | 已在待处理队列中 | 已在待处理队列中 || `already_in_anki` | 已存在于 Anki | 该单词已存在于 Anki || `invalid_input` | 输入不合法 | 当前仅支持单词 || `backend_unavailable` | 后端不可用 | 本地后端不可用 || `processing_failed` | 处理失败 | 采集失败 |### 7.2 响应字段建议| 字段名 | 中文含义 | 必填 | 备注 ||---|---|---:|---|| `status` | 状态值 | 是 | 必须来自固定枚举 || `message` | 文本说明 | 否 | 供调试或日志使用 || `word_key` | 单词唯一键 | 否 | 便于调试 || `lemma` | 基础词形 | 否 | 便于调试 |---## 8. 待处理队列模型待处理队列用于承接观看阶段的快速采集，避免即时重制卡打断体验。### 8.1 队列项字段| 字段名 | 中文含义 | 展示层级 | 备注 ||---|---|---|---|| `surface_form` | 原始词形 | 不展示 | 实际选中的词形 || `normalized_form` | 标准化词形 | 不展示 | 标准化后结果 || `lemma` | 基础词形 | 不展示 | 词形归并结果 || `word_key` | 单词唯一键 | 不展示 | 查重主键 || `source_sentence` | 来源原句 | 不展示/中间字段 | 用于构造 `examples[0]` || `source_title` | 来源标题 | 不展示 | 后续队列面板可预留 || `source_url` | 来源链接 | 不展示 | 来源追踪 || `source_type` | 来源类型 | 不展示 | `web` / `youtube` || `source_timestamp` | 来源时间点 | 不展示 | YouTube 场景使用 || `captured_at` | 采集时间 | 不展示 | 创建时间 || `status` | 队列状态 | 不展示 | `pending` / `success` / `failed` || `error_message` | 错误信息 | 不展示 | 失败时保留 || `generator_version` | 生成版本号 | 不展示 | 用于追踪生成逻辑版本 |### 8.2 队列状态- `pending`：待生成- `success`：已生成正式卡片- `failed`：生成失败，可重试### 8.3 队列行为规则- 观看阶段只加入 `pending`- 生成正式卡片成功后更新为 `success`- 生成失败时更新为 `failed`- 失败项必须允许单独重试---## 9. Anki 自定义 Note Type 规格## 9.1 设计原则- 使用自定义 note type- 使用字段化存储数据- 使用 Anki 模板渲染卡片- 不再依赖 `Basic` 的 Front/Back 承载全部信息### 9.2 字段分层字段必须分为三类：1. 主展示字段2. 弱展示字段3. 不展示字段---## 10. 最终字段清单## 10.1 主展示字段| 字段名 | 中文含义 | 是否展示 | 说明 ||---|---|---:|---|| `word` | 单词 | 是 | 正面核心展示 || `ipa` | 音标 | 是 | 正面展示 || `emoji` | 记忆图标 | 是 | 正面展示 || `audio` | 音频 | 是 | 正面播放 || `image_prompt` | 联想提示 | 是 | 正面弱展示 || `meanings` | 英文释义 | 是 | 背面主展示 || `pairs` | 固定搭配 | 是 | 背面主展示 || `examples` | 例句 | 是 | 背面主展示 |## 10.2 弱展示字段| 字段名 | 中文含义 | 是否展示 | 说明 ||---|---|---:|---|| `forms` | 词形变化 | 是（弱显示） | 放在 Meaning 和 Pair 之间 |## 10.3 不展示字段| 字段名 | 中文含义 | 是否展示 | 说明 ||---|---|---:|---|| `word_key` | 单词唯一键 | 否 | 系统查重主键 || `lemma` | 基础词形 | 否 | 词形归并用 || `surface_form` | 原始词形 | 否 | 保留原始采集输入 || `source_url` | 来源链接 | 否 | 来源追踪 || `source_type` | 来源类型 | 否 | 区分 `web` / `youtube` || `source_timestamp` | 来源时间点 | 否 | 视频场景定位 || `generator_version` | 生成版本号 | 否 | 版本追踪 |## 10.4 中间处理字段| 字段名 | 中文含义 | 是否直接展示 | 说明 ||---|---|---:|---|| `source_sentence` | 来源原句 | 否 | 不单独展示，用于构造 `examples[0]` |---## 11. 卡片渲染规则## 11.1 正面渲染规则正面保留当前满意的结构：1. `emoji`2. `word`3. `audio`4. `ipa`5. `image_prompt`### 11.2 背面渲染规则背面保留三大主区块：1. `Meaning`2. `Pair`3. `Example`并新增一个弱显示区块：- `Forms`### 11.3 `forms` 渲染规则- 放置位置：`Meaning` 与 `Pair` 之间- 展示强度：弱显示- 有内容时才显示- 不单独做大标题区块- 推荐展示格式：`Forms: retries / retried / retrying`### 11.4 `examples` 渲染规则#### 有 `source_sentence` 时- `examples[0]` = 来源原句，并标注 `source sentence`- `examples[1]` = 模型生成例句- `examples[2]` = 模型生成例句#### 无 `source_sentence` 时- 三条都由模型生成---## 12. LLM 输出要求后端必须基于统一 `SYSTEM_PROMPT` 请求模型生成结构化结果。### 12.1 输出必须支持以下展示字段- `word`- `ipa`- `emoji`- `image_prompt`- `meanings`- `pairs`- `examples`### 12.2 后端补充字段以下字段不应由扩展生成：- `lemma`- `word_key`- `forms`- `generator_version`其中：- `forms` 可由后端根据词形规则生成- `generator_version` 必须由后端统一写入---## 13. Anki 连接规则### 13.1 观看阶段观看阶段只加入待处理队列，不依赖 Anki 是否打开。### 13.2 批量生成阶段批量生成正式卡片时：1. 检查 AnkiConnect 是否可用2. 若不可用，后端尝试自动启动 Anki3. 启动成功后继续生成4. 启动失败后返回明确错误### 13.3 约束- 自动启动 Anki 的逻辑必须由后端负责- 扩展不负责启动本地程序---## 14. 命名与一致性约束为避免扩展、后端、Anki 模板三方不一致，必须遵守：1. 所有字段名以本 `SPEC.md` 为准2. 扩展不得自定义后端字段名3. 后端不得随意新增未记录字段4. note type 字段名必须与本文件保持一致5. 状态枚举必须与本文件保持一致6. 修改字段前必须先修改 `SPEC.md`---## 15. 开发流程约束（Codex 使用规则）Codex 实现代码前，必须先遵守本文件，不得自行更改以下内容：- 模块边界- 字段命名- 状态枚举- `forms` 显示位置- `examples` 规则- 默认 deck 名称来源方式若实现中发现规格不合理，必须先修改 `SPEC.md`，再改代码。---## 16. 当前已确认决策以下内容已经确认，不得在实现阶段随意更改：- 浏览器扩展只做轻量选词采集- 本地后端负责全部重逻辑- 观看阶段不生成正式卡片- 观看阶段不依赖 Anki 打开- 批量生成阶段才连接 Anki- 若 Anki 未打开，由后端尝试自动启动- 第一版只支持单词，不支持短语- 使用自定义 note type- 使用字段化存储 + Anki 模板渲染- `forms` 为弱展示字段- `forms` 放在 Meaning 和 Pair 之间- `source_sentence` 不单独展示，用于构造 `examples[0]`- 默认 deck 名为 `sherber`
```

你先看这版结构对不对。
如果对，下一步最该做的是把里面两个待定项补死：

default_note_type_name 叫什么

word_key 的生成规则具体怎么定

---

## 👤 用户

default_note_type_name 叫什么
word_key 的生成规则具体怎么定
我不太理解，我目前还是先用sherber，因为是我自己先使用麻，word_key的生成规则是什么不理解

## 🤖 AI

你这里混了两个不同概念，我给你拆开。

1. default_note_type_name 是什么

这不是牌组名。

你现在说的 sherber，对应的是：

deck name

中文就是：牌组名

而 default_note_type_name 指的是：

note type name

中文就是：笔记类型名 / 卡片类型名

这是两层东西。

例子

你可以有：

牌组名：sherber

笔记类型名：SherberVocabNote

意思是：

这些卡都放在 sherber 这个牌组里

这些卡使用 SherberVocabNote 这种字段结构和模板结构

2. 为什么要单独有 note type name

因为你现在已经不想继续用普通 Basic 了。
你要的是自定义字段，比如：

word

ipa

emoji

audio

image_prompt

meanings

forms

pairs

examples

word_key

lemma

surface_form

source_url

source_type

source_timestamp

generator_version

这些字段必须挂在一个自定义 note type 上。
而这个 note type 必须有名字，不然 Anki 不知道你要写进哪种模型。

3. 那这个名字该叫什么

这个名字其实就是你自己定一个稳定名字。
因为你现在自己用，所以不用想太复杂，但也别起得太随便。

我建议你用这种风格：

SherberVocabNote

SherberEnglishNote

SherberWordCard

我最推荐：

SherberVocabNote

原因：

一看就知道是你的

一看就知道是词汇卡

不容易和 Anki 自带 Basic 混淆

后面扩展和后端都容易统一写这个名字

所以你现在可以直接定：

default_deck_name = "sherber"

default_note_type_name = "SherberVocabNote"

4. word_key 是什么

这个也不是给你背单词看的。
它是系统内部用来查重的字段。

你前面不是很在意这个问题吗：

一个单词已经进 Anki 了，我又加一次，不想重复

那系统总得有一个稳定的“唯一识别值”去判断：
这次这个词，和之前那个词，是不是同一个词。

这个稳定识别值，就是 word_key。

5. 为什么不能直接拿 word 当查重字段

因为 word 是展示字段，不够稳。

比如你可能会遇到：

Retry

retry

retry,

retried

retrying

如果直接拿 word 查重：

大小写不同会乱

标点会乱

词形变化会乱

所以系统需要一个更稳定的值：

展示给你看的：

word

系统内部查重用的：

word_key

6. word_key 怎么理解最简单

你可以把它理解成：

“这个词在系统里的身份证号”

比如你看到：

retried

retrying

retries

系统经过标准化和词形归并后，发现它们本质都属于：

retry

那它们的 word_key 就统一用：

retry

这样以后不管你选到的是 retried 还是 retrying，系统都知道：
“你已经有 retry 这张卡了，不要重复建新卡。”

7. 那 word_key 的生成规则怎么定

你现在不用想复杂加密、哈希之类的东西。
你这个项目第一版完全没必要。

最简单、最合理的规则就是：

word_key = lemma 的小写标准化结果

也就是：

用户选中原始词：surface_form

后端标准化：去空格、去首尾标点、转小写

后端做词形归并，得到基础词形：lemma

直接把这个 lemma 当作 word_key

例子

Retry -> lemma = retry -> word_key = retry

retried -> lemma = retry -> word_key = retry

retrying -> lemma = retry -> word_key = retry

这就是第一版最适合你的方案。

8. 这几个字段的关系，你要彻底分清

surface_form

原始词形
你当时选中的词是什么，就是什么。

例如：

retried

lemma

基础词形 / 归并后的主词
后端判断这个词属于哪个核心词。

例如：

retry

word

展示给你看的主单词
通常也会用 retry

word_key

系统内部查重键
第一版直接等于：

retry

9. 所以第一版最简单的规则就是

你可以直接定死：

default_deck_name = "sherber"

default_note_type_name = "SherberVocabNote"

然后再定：

word_key 由后端生成

生成规则：
对 surface_form 做标准化和词形归并后，取其基础词形 lemma 的小写值作为 word_key

这句话已经够写进 SPEC.md 了。

10. 你现在不用纠结的点

你现在不用考虑：

一个牌组里多个 note type 怎么切

word_key 要不要做哈希

多用户怎么隔离

不同语言怎么设计 key

这些都太早了。

你现在只需要一个简单稳定的规则，先服务你自己用。

我帮你把这两个值直接定出来

你现在可以先这样写：

默认配置

default_deck_name = "sherber"

default_note_type_name = "SherberVocabNote"

word_key 规则

word_key 由后端生成，不由扩展提供

后端对 surface_form 做标准化和词形归并

取归并后的基础词形 lemma 作为 word_key

word_key 一律使用小写

11. 最后一句最直接的话

你现在不用把 word_key 想成复杂技术名词。
它就是：

“系统用来判断这是不是同一个词的标准名字”

比如：

你选到 retried

系统认为它属于 retry

那 word_key 就是 retry

就这么简单。

如果你愿意，我下一步可以直接把 SPEC.md 里这两处待定内容补成最终版文本。

---

## 👤 用户

前者听你的，word_key用id：12333这类纪录好一些，还是单词retry好一些

## 🤖 AI

用 retry 这种稳定可读的值更好，不要用 id:12333 当 word_key。

你这里要分清两个不同东西：

1. word_key

这是业务唯一键，用来判断：

这个词是不是已经在队列里

这个词是不是已经在 Anki 里

不同词形是不是归并到同一个主词条

所以它应该是：

稳定

可预测

可读

和词本身强相关

对你这个项目，最合适的就是：

word_key = lemma

例如：

retried -> lemma=retry -> word_key=retry

retrying -> lemma=retry -> word_key=retry

这才符合你“不想重复建卡”的目标。

2. id:12333

这类值更像是记录 ID，不是 word_key。

它的作用通常是：

标识一条队列记录

标识一张生成记录

标识一次采集事件

它适合拿来做：

queue_id

record_id

task_id

但它不适合拿来做单词去重键。

为什么？

因为如果你用：

id:12333

id:12334

哪怕它们都对应 retry，系统也会把它们当成两条不同对象。
那你去重就废了。

直接结论

word_key

用：

retry

不要用：

id:12333

另外再单独保留一个记录 ID

这个反而是对的。

比如你可以同时有：

record_id = "12333"
表示这条采集记录本身的编号

word_key = "retry"
表示这条记录归属于哪个核心词条

这样分工才干净。

你现在最合理的字段理解应该是这样

record_id

中文：记录 ID
作用：

唯一标识一条队列记录或任务记录

纯系统内部编号

例如：

12333

word_key

中文：单词唯一键
作用：

用于单词级别查重

用于判断不同词形是否属于同一个词

例如：

retry

surface_form

中文：原始词形
作用：

记录你当时实际选中的词形

例如：

retried

lemma

中文：基础词形
作用：

词形归并结果

例如：

retry

为什么 word_key=retry 更适合你

因为你以后调试时，一眼就能看懂。

你看到：

surface_form = retried

lemma = retry

word_key = retry

你立刻知道系统在干什么。

但如果你看到：

word_key = 12333

你还得再查一层映射，根本不直观。
这会让后续排错、查重、维护都更麻烦。

唯一需要注意的一点

如果以后你真的扩展到更复杂场景，比如：

同形异义词要严格拆开

多语言

短语

词组和单词混合

那 word_key = lemma 可能不够。
但这是以后，不是现在。

对你当前这个项目，word_key = lemma的小写标准化结果 就是最合理的。

你现在可以直接定

default_note_type_name = "SherberVocabNote"

word_key 使用归并后的基础词形，例如 retry

另外单独增加一个 record_id，用于标识队列记录

这才是干净设计。

---

## 👤 用户

你认为id需要吗，就是我以前学过的代码里好多都有键值，map什么之类的

## 🤖 AI

需要，但不是拿来代替 word_key。

你这里被以前学过的“主键 / id / map 键值”带偏了一点。
在这个项目里，id 和 word_key 不是二选一，而是职责不同。

直接结论

要保留 id

但它的用途是：

标识一条队列记录

标识一次采集事件

标识一次生成任务

不要用 id 代替 word_key

因为 word_key 是：

单词级别去重键

业务语义键

你可以这样理解

id

回答的是：

“这条记录是谁？”

比如：

第 128 条待处理记录

第 5 次采集到的 retry

某个失败任务

它是“记录身份”。

word_key

回答的是：

“这条记录属于哪个核心单词？”

比如：

retried

retrying

retries

都属于：

retry

它是“业务归属”。

为什么两个都保留更合理

因为将来你很可能会遇到这种情况：

你先在一个视频里采到：

retried

后来又在另一个网页里采到：

retrying

如果你的规则是：

已经在 Anki 里有 retry 就不再生成新卡

那它们最终都会归到同一个：

word_key = retry

但这并不代表这两次采集记录没有区别。

它们仍然可能有不同的：

来源原句

来源页面

采集时间

来源时间戳

所以：

word_key 一样

id 不一样

这就很正常。

什么时候 id 很有用

1. 队列管理

你要删除一条待处理项、修改一条失败记录、重试一条任务，
最稳的是用 id 定位。

因为如果你只靠 word_key=retry，那遇到多个 retry 相关记录时会不好操作。

2. 失败重试

比如某条生成失败了，你要重试那一条。
这时候你需要的是：

record_id = xxx

而不是：

word_key = retry

因为 retry 可能对应过多条历史记录。

3. 调试和日志

日志里写：

record_id=129

word_key=retry

会非常清楚。

如果只有 word_key，日志定位不够精确。
如果只有 id，又看不懂业务含义。

你以前学到的 map / key-value，在这里怎么落地

你以前的经验没有错，只是要放对位置。

id

更像：

数据表主键

对象唯一标识

map 里的记录键

word_key

更像：

业务唯一索引

查重索引

单词聚合键

这两个在很多真实系统里本来就是同时存在的。

不是说有了主键 id，业务键就不需要。
也不是说有了业务键，就不需要 id。

我对你这个项目的建议

保留一个 record_id

用于：

队列记录唯一标识

失败重试

删除 / 修改 / 日志定位

这个 record_id 可以是：

自增整数

UUID

时间戳加随机串

第一版你自己用，简单一点就行。
自增整数就够了。

例如：

record_id = 1

record_id = 2

保留一个 word_key

用于：

查重

归并

判断是不是同一个核心词

例如：

retry

所以最终你应该是这样

记录字段

record_id：记录 ID

业务字段

surface_form：原始词形

lemma：基础词形

word_key：查重键

这三个层次就清楚了。

你现在不要犯的错

错误想法 1

“有了 id，就不需要 word_key 了。”

错。
这样你没法做单词级别去重。

错误想法 2

“有了 word_key，就不需要 id 了。”

也不对。
这样你很难管理具体哪条记录。

最后给你一句最短判断

需要 id，但它是记录 ID；word_key 仍然要保留，而且它是单词去重键。

你现在可以把这两个概念正式定成：

record_id：记录主键

word_key：单词业务键

这就不会乱了。

---

## 👤 用户

那么我们现在就输出 SPEC.md的最终版

## 🤖 AI

下面是整理后的 SPEC.md 最终版，可直接交给 Codex 作为实现约束。

```plaintext
Markdown# SPEC.md## 1. 项目目标本项目用于提升英文视频/网页阅读中的生词采集与 Anki 制卡效率。核心目标：- 浏览器扩展只负责**轻量选词采集**- 本地后端负责**标准化、词形归并、去重、待处理队列、批量生成正式 Anki 卡片**- 整体设计必须以**不影响观看体验**为最高优先级- 正式 Anki 卡片继续沿用现有高质量结构：`SYSTEM_PROMPT` + 自定义 note type 字段 + Anki 模板渲染一句话原则：> 扩展负责“拿到词”，后端负责“把词变成卡”。---## 2. 范围与非目标### 2.1 第一版范围第一版必须支持：- 普通网页中选中单词后加入待处理队列- YouTube 中尽量沿用相同方式选词并加入待处理队列- 扩展向本地后端发送采集请求- 后端执行标准化、词形归并、去重- 后端维护待处理队列- 用户在稍后手动触发批量生成正式卡片- 生成正式卡片时，后端调用 LLM、生成音频、写入 Anki- 生成时后端检测 Anki/AnkiConnect 是否可用；若不可用，尝试自动启动 Anki### 2.2 第一版非目标第一版明确不做：- 短语卡- 扩展端直接调用 LLM- 扩展端直接操作 Anki- 观看时立即生成正式卡- 自动截图- 自动图片生成- 多语言支持- 多牌组 UI 配置- 复杂设置中心- YouTube 专用复杂字幕解析面板---## 3. 模块边界### 3.1 浏览器扩展职责浏览器扩展只负责以下事项：1. 获取当前用户选中的单词2. 尝试获取少量上下文   - `surface_form`   - `source_sentence`（可选）   - `source_title`   - `source_url`   - `source_type`   - `source_timestamp`（可选）3. 将采集结果发送给本地后端4. 根据后端返回结果显示轻提示浏览器扩展禁止负责以下事项：- 调用 LLM- 生成音频- 词形归并- 队列去重- Anki 去重- 直接写入 Anki- 自动启动 Anki- 生成 HTML 卡片内容### 3.2 本地后端职责本地后端负责以下事项：1. 输入标准化2. 词形归并3. 队列去重4. Anki 查重5. 待处理队列管理6. 批量生成正式卡片7. 调用 LLM（使用统一 `SYSTEM_PROMPT`）8. 生成音频9. 写入自定义 note type 字段10. 依赖 Anki 模板渲染卡片11. 失败记录与失败项单独重试12. 生成版本号管理13. 批量生成时检查 / 自动启动 Anki---## 4. 默认配置第一版只保留最小配置能力，不做 UI 配置页。### 4.1 默认配置项- `default_deck_name = "sherber"`- `default_note_type_name = "SherberVocabNote"`- `default_generator_version = "v1"`### 4.2 配置约束- 默认牌组名必须来自统一配置- 默认 note type 名称必须来自统一配置- 不允许在扩展或后端业务逻辑中散落硬编码 `"sherber"`- 不允许在扩展或后端业务逻辑中散落硬编码 `"SherberVocabNote"`- 第一版不做多牌组切换功能- 将来如需切换牌组，只允许通过集中配置改动---## 5. 输入与采集规则### 5.1 输入对象第一版只支持：- 单个英文单词第一版不支持：- 短语- 整句- 多个单词组合- 含复杂符号的字符串### 5.2 标准化规则后端收到扩展传来的原始输入后，必须执行标准化：1. 去除首尾空白2. 去除首尾标点3. 统一小写4. 校验是否合法英文单词5. 非法输入直接拒绝### 5.3 词形相关规则必须区分以下四个概念：- `surface_form`：用户在网页中实际选中的原始词形    例如：`retried`- `lemma`：词形归并后的基础词形    例如：`retry`- `word_key`：用于系统查重的单词业务键    第一版默认使用归并后的基础词形- `record_id`：用于标识一条采集/队列记录的记录主键    与 `word_key` 不是同一个概念### 5.4 去重规则后端采集时按以下顺序处理：1. 标准化输入2. 词形归并3. 生成 `word_key`4. 查询待处理队列5. 查询 Anki 中是否已有对应 `word_key`6. 若重复，则不新建待处理项---## 6. 扩展 -> 后端 请求契约### 6.1 请求目的扩展向后端发送“采集一个待处理词项”的请求。### 6.2 请求字段定义| 字段名 | 中文含义 | 必填 | 来源 | 备注 ||---|---|---:|---|---|| `surface_form` | 原始词形 | 是 | 扩展采集 | 用户实际选中的文本 || `source_sentence` | 来源原句 | 否 | 扩展采集 | 能获取则传，不能获取则为空 || `source_title` | 来源标题 | 否 | 扩展采集 | 页面标题或视频标题 || `source_url` | 来源链接 | 否 | 扩展采集 | 页面 URL || `source_type` | 来源类型 | 是 | 扩展采集 | 枚举：`web` / `youtube` || `source_timestamp` | 来源时间点 | 否 | 扩展采集 | 主要用于 YouTube || `captured_at` | 采集时间 | 否 | 扩展或后端补全 | 若扩展不传，后端生成 |### 6.3 请求约束- `surface_form` 为唯一必需核心输入- 扩展只传原始采集数据，不传 `lemma`、`word_key`、`record_id`- `lemma`、`word_key`、`record_id` 必须由后端生成- 若 `source_sentence` 获取失败，不得阻塞采集流程---## 7. 后端 -> 扩展 响应契约扩展不自行推断业务逻辑，只根据后端返回的标准状态展示提示。### 7.1 状态枚举| 状态值 | 中文含义 | 扩展提示建议 ||---|---|---|| `added_to_queue` | 已加入待处理队列 | 已加入待处理 || `already_in_queue` | 已在待处理队列中 | 已在待处理队列中 || `already_in_anki` | 已存在于 Anki | 该单词已存在于 Anki || `invalid_input` | 输入不合法 | 当前仅支持单词 || `backend_unavailable` | 后端不可用 | 本地后端不可用 || `processing_failed` | 处理失败 | 采集失败 |### 7.2 响应字段建议| 字段名 | 中文含义 | 必填 | 备注 ||---|---|---:|---|| `status` | 状态值 | 是 | 必须来自固定枚举 || `message` | 文本说明 | 否 | 供调试或日志使用 || `record_id` | 记录主键 | 否 | 便于调试 || `word_key` | 单词业务键 | 否 | 便于调试 || `lemma` | 基础词形 | 否 | 便于调试 |---## 8. 待处理队列模型待处理队列用于承接观看阶段的快速采集，避免即时重制卡打断体验。### 8.1 队列项字段| 字段名 | 中文含义 | 展示层级 | 备注 ||---|---|---|---|| `record_id` | 记录主键 | 不展示 | 队列记录唯一 ID || `surface_form` | 原始词形 | 不展示 | 实际选中的词形 || `normalized_form` | 标准化词形 | 不展示 | 标准化后结果 || `lemma` | 基础词形 | 不展示 | 词形归并结果 || `word_key` | 单词业务键 | 不展示 | 查重主键 || `source_sentence` | 来源原句 | 不展示/中间字段 | 用于构造 `examples[0]` || `source_title` | 来源标题 | 不展示 | 后续队列面板可预留 || `source_url` | 来源链接 | 不展示 | 来源追踪 || `source_type` | 来源类型 | 不展示 | `web` / `youtube` || `source_timestamp` | 来源时间点 | 不展示 | YouTube 场景使用 || `captured_at` | 采集时间 | 不展示 | 创建时间 || `status` | 队列状态 | 不展示 | `pending` / `success` / `failed` || `error_message` | 错误信息 | 不展示 | 失败时保留 || `generator_version` | 生成版本号 | 不展示 | 用于追踪生成逻辑版本 |### 8.2 队列状态- `pending`：待生成- `success`：已生成正式卡片- `failed`：生成失败，可重试### 8.3 队列行为规则- 观看阶段只加入 `pending`- 生成正式卡片成功后更新为 `success`- 生成失败时更新为 `failed`- 失败项必须允许单独重试---## 9. Anki 自定义 Note Type 规格### 9.1 设计原则- 使用自定义 note type- 使用字段化存储数据- 使用 Anki 模板渲染卡片- 不再依赖 `Basic` 的 Front/Back 承载全部信息### 9.2 字段分层字段必须分为三类：1. 主展示字段2. 弱展示字段3. 不展示字段---## 10. 最终字段清单### 10.1 主展示字段| 字段名 | 中文含义 | 是否展示 | 说明 ||---|---|---:|---|| `word` | 单词 | 是 | 正面核心展示 || `ipa` | 音标 | 是 | 正面展示 || `emoji` | 记忆图标 | 是 | 正面展示 || `audio` | 音频 | 是 | 正面播放 || `image_prompt` | 联想提示 | 是 | 正面弱展示 || `meanings` | 英文释义 | 是 | 背面主展示 || `pairs` | 固定搭配 | 是 | 背面主展示 || `examples` | 例句 | 是 | 背面主展示 |### 10.2 弱展示字段| 字段名 | 中文含义 | 是否展示 | 说明 ||---|---|---:|---|| `forms` | 词形变化 | 是（弱显示） | 放在 Meaning 和 Pair 之间 |### 10.3 不展示字段| 字段名 | 中文含义 | 是否展示 | 说明 ||---|---|---:|---|| `record_id` | 记录主键 | 否 | 队列/日志/重试定位 || `word_key` | 单词业务键 | 否 | 系统查重主键 || `lemma` | 基础词形 | 否 | 词形归并用 || `surface_form` | 原始词形 | 否 | 保留原始采集输入 || `source_url` | 来源链接 | 否 | 来源追踪 || `source_type` | 来源类型 | 否 | 区分 `web` / `youtube` || `source_timestamp` | 来源时间点 | 否 | 视频场景定位 || `generator_version` | 生成版本号 | 否 | 版本追踪 |### 10.4 中间处理字段| 字段名 | 中文含义 | 是否直接展示 | 说明 ||---|---|---:|---|| `source_sentence` | 来源原句 | 否 | 不单独展示，用于构造 `examples[0]` |---## 11. 卡片渲染规则### 11.1 正面渲染规则正面保留当前满意的结构：1. `emoji`2. `word`3. `audio`4. `ipa`5. `image_prompt`### 11.2 背面渲染规则背面保留三大主区块：1. `Meaning`2. `Pair`3. `Example`并新增一个弱显示区块：- `Forms`### 11.3 `forms` 渲染规则- 放置位置：`Meaning` 与 `Pair` 之间- 展示强度：弱显示- 有内容时才显示- 不单独做大标题区块- 推荐展示格式：`Forms: retries / retried / retrying`### 11.4 `examples` 渲染规则#### 有 `source_sentence` 时- `examples[0]` = 来源原句，并标注 `source sentence`- `examples[1]` = 模型生成例句- `examples[2]` = 模型生成例句#### 无 `source_sentence` 时- 三条都由模型生成---## 12. LLM 输出要求后端必须基于统一 `SYSTEM_PROMPT` 请求模型生成结构化结果。### 12.1 输出必须支持以下展示字段- `word`- `ipa`- `emoji`- `image_prompt`- `meanings`- `pairs`- `examples`### 12.2 后端补充字段以下字段不应由扩展生成：- `lemma`- `word_key`- `record_id`- `forms`- `generator_version`其中：- `forms` 可由后端根据词形规则生成- `generator_version` 必须由后端统一写入- `record_id` 必须由后端生成---## 13. word_key 生成规则### 13.1 定义`word_key` 是单词级别查重使用的业务键，不是记录主键。### 13.2 第一版规则第一版固定为：> `word_key = lemma 的小写标准化结果`示例：- `Retry` -> `lemma = retry` -> `word_key = retry`- `retried` -> `lemma = retry` -> `word_key = retry`- `retrying` -> `lemma = retry` -> `word_key = retry`### 13.3 约束- `word_key` 必须可读，不使用随机字符串- `word_key` 不使用 `id:12333` 这类记录编号- `word_key` 仅用于单词去重和归并判断- `record_id` 与 `word_key` 必须分离---## 14. Anki 连接规则### 14.1 观看阶段观看阶段只加入待处理队列，不依赖 Anki 是否打开。### 14.2 批量生成阶段批量生成正式卡片时：1. 检查 AnkiConnect 是否可用2. 若不可用，后端尝试自动启动 Anki3. 启动成功后继续生成4. 启动失败后返回明确错误### 14.3 约束- 自动启动 Anki 的逻辑必须由后端负责- 扩展不负责启动本地程序---## 15. 命名与一致性约束为避免扩展、后端、Anki 模板三方不一致，必须遵守：1. 所有字段名以本 `SPEC.md` 为准2. 扩展不得自定义后端字段名3. 后端不得随意新增未记录字段4. note type 字段名必须与本文件保持一致5. 状态枚举必须与本文件保持一致6. 修改字段前必须先修改 `SPEC.md`---## 16. 开发流程约束（Codex 使用规则）Codex 实现代码前，必须先遵守本文件，不得自行更改以下内容：- 模块边界- 字段命名- 状态枚举- `forms` 显示位置- `examples` 规则- 默认 deck 名称来源方式- `default_note_type_name`- `word_key` 生成规则- `record_id` 与 `word_key` 的职责分离若实现中发现规格不合理，必须先修改 `SPEC.md`，再改代码。---## 17. 当前已确认决策以下内容已经确认，不得在实现阶段随意更改：- 浏览器扩展只做轻量选词采集- 本地后端负责全部重逻辑- 观看阶段不生成正式卡片- 观看阶段不依赖 Anki 打开- 批量生成阶段才连接 Anki- 若 Anki 未打开，由后端尝试自动启动- 第一版只支持单词，不支持短语- 使用自定义 note type- 自定义 note type 名称为 `SherberVocabNote`- 使用字段化存储 + Anki 模板渲染- `forms` 为弱展示字段- `forms` 放在 Meaning 和 Pair 之间- `source_sentence` 不单独展示，用于构造 `examples[0]`- 默认 deck 名为 `sherber`- `word_key = lemma 的小写标准化结果`- `record_id` 为记录主键，不能替代 `word_key`
```

这版已经可以作为实现基线。
下一步最该做的是再补一个配套文档：字段示例表，把每个字段填一个实际例子，Codex 就更不容易跑偏。

---

## 👤 用户

字段示例表，命名成什么，然后输出给我

## 🤖 AI

命名直接一点，别花。

我建议叫：

FIELD_EXAMPLES.md

这个名字最清楚，Codex 一眼就知道这是：

字段

示例

配合 SPEC.md 使用

不要起成：

reference.md

schema.md

notes.md

这些都太泛，后面容易混。

下面是可直接用的内容。

```plaintext
Markdown# FIELD_EXAMPLES.md本文件用于补充 `SPEC.md`，通过具体示例说明各字段的真实数据长什么样，避免扩展、后端、Anki note type 在实现时对字段理解不一致。---## 1. 示例场景用户在 YouTube 视频中看到一句话：> Please retry the download if it doesn't start automatically.用户实际选中的单词是：> retried / retry / retrying / retries为方便说明，这里以用户选中 `retried` 为主示例。---## 2. 采集阶段示例（扩展 -> 后端）### 2.1 扩展采集到的原始请求示例```json{  "surface_form": "retried",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00"}
```

2.2 字段解释

字段名示例值中文含义说明surface_formretried原始词形用户实际选中的词source_sentencePlease retry the download if it doesn't start automatically.来源原句选词时所在原句source_titleHow to Fix Download Problems来源标题页面/视频标题source_urlhttps://www.youtube.com/watch?v=example123来源链接页面 URLsource_typeyoutube来源类型web 或 youtubesource_timestamp00:12:35来源时间点视频中的时间位置captured_at2026-03-29T14:23:10+09:00采集时间选词发生时间

3. 后端标准化与归并示例

后端收到 surface_form = retried 后，执行标准化和词形归并。

3.1 后端处理中间结果示例

```plaintext
JSON{  "surface_form": "retried",  "normalized_form": "retried",  "lemma": "retry",  "word_key": "retry"}
```

3.2 字段解释

字段名示例值中文含义说明surface_formretried原始词形用户实际选中的形式normalized_formretried标准化词形去空格、去首尾标点、统一小写后的结果lemmaretry基础词形词形归并后的核心词word_keyretry单词业务键查重使用，第一版等于 lemma 的小写标准化结果

4. 队列项示例

4.1 待处理队列中的一条记录示例

```plaintext
JSON{  "record_id": 101,  "surface_form": "retried",  "normalized_form": "retried",  "lemma": "retry",  "word_key": "retry",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00",  "status": "pending",  "error_message": "",  "generator_version": "v1"}
```

4.2 字段解释

字段名示例值中文含义说明record_id101记录主键这一条队列记录自己的唯一编号word_keyretry单词业务键用于判断是不是同一个核心词statuspending队列状态当前还未生成正式卡generator_versionv1生成版本号这条记录对应的生成逻辑版本

5. 后端返回给扩展的状态示例

5.1 成功加入待处理

```plaintext
JSON{  "status": "added_to_queue",  "message": "Word added to pending queue.",  "record_id": 101,  "word_key": "retry",  "lemma": "retry"}
```

5.2 已在待处理队列中

```plaintext
JSON{  "status": "already_in_queue",  "message": "Word already exists in pending queue.",  "record_id": 101,  "word_key": "retry",  "lemma": "retry"}
```

5.3 已存在于 Anki

```plaintext
JSON{  "status": "already_in_anki",  "message": "Word already exists in Anki.",  "word_key": "retry",  "lemma": "retry"}
```

5.4 输入不合法

```plaintext
JSON{  "status": "invalid_input",  "message": "Only single English words are supported."}
```

6. 正式 Note Type 字段示例

6.1 一张正式 Anki 卡的数据示例

```plaintext
JSON{  "word": "retry",  "ipa": "/ˌriːˈtraɪ/",  "emoji": "🔁",  "audio": "retry_anki_audio.mp3",  "image_prompt": "A person clicking a retry button on a computer screen.",  "meanings": "[(verb) to try again after failure]",  "forms": "retries / retried / retrying",  "pairs": "[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]",  "examples": "[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]",  "record_id": 101,  "word_key": "retry",  "lemma": "retry",  "surface_form": "retried",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "generator_version": "v1"}
```

7. 展示字段示例

7.1 正面展示字段示例

字段名示例值wordretryipa/ˌriːˈtraɪ/emoji🔁audioretry_anki_audio.mp3image_promptA person clicking a retry button on a computer screen.

7.2 背面展示字段示例

字段名示例值meanings[(verb) to try again after failure]formsretries / retried / retryingpairs[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]examples[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]

8. 不展示字段示例

字段名示例值中文含义record_id101记录主键word_keyretry单词业务键lemmaretry基础词形surface_formretried原始词形source_urlhttps://www.youtube.com/watch?v=example123来源链接source_typeyoutube来源类型source_timestamp00:12:35来源时间点generator_versionv1生成版本号

9. examples 规则示例

9.1 有来源原句时

```plaintext
JSON{  "examples": [    "Please retry the download if it doesn't start automatically. (source sentence)",    "I retried the task after fixing the error. (verb)",    "You can retry the operation later. (verb)"  ]}
```

9.2 无来源原句时

```plaintext
JSON{  "examples": [    "I retried the task after fixing the error. (verb)",    "You can retry the operation later. (verb)",    "She will retry the process tomorrow. (verb)"  ]}
```

10. forms 规则示例

10.1 动词示例

wordformsretryretries / retried / retryingstudystudies / studied / studyingfixfixes / fixed / fixing

10.2 无明显常见变形时

可为空，或不渲染该字段。

11. 命名一致性要求

所有字段名必须与 SPEC.md 一致

record_id 不能替代 word_key

word_key 不能使用 id:12333 这类记录编号

word_key 必须使用可读、稳定、可归并的业务值

第一版默认：word_key = lemma 的小写标准化结果

12. 当前示例中的关键映射关系

概念示例值说明用户实际选中的词retriedsurface_form标准化后retriednormalized_form归并后的基础词形retrylemma查重使用的业务键retryword_key这条记录自己的编号101record_id

```plaintext
你现在文件就定成这两个：- `SPEC.md`- `FIELD_EXAMPLES.md`这套命名最稳。  如果你愿意，我下一步可以继续给你补第三个：**`ARCHITECTURE.md`**，专门写扩展、后端、队列、Anki 模板之间的模块关系。
```

---

## 👤 用户

> Please retry the download if it doesn't start automatically.

用户实际选中的单词是：

> retried / retry / retrying / retries

为方便说明，这里以用户选中 retried 为主示例。
这句话里只有retry没有retried吧

## 🤖 AI

对，这里写错了。
你抓得对，而且这是低级错误。

原句是：

Please retry the download if it doesn't start automatically.

这句话里实际出现的只有：

retry

没有：

retried

retrying

retries

我前面把“同一词的不同词形示例”混进了“原句实际选中示例”，这会误导实现。这个必须改。

应该怎么改才严谨

这里要拆成两个不同示例，不要混写。

示例 A：原句实际选中示例

如果沿用这句：

Please retry the download if it doesn't start automatically.

那用户实际选中的单词就应该写成：

retry

示例 B：词形归并说明示例

如果是为了说明不同词形会归并到同一个 lemma / word_key，就应该单独写：

例如，系统还可能在其他场景中遇到以下词形：

retry

retried

retrying

retries

它们最终都归并到：

lemma = retry

word_key = retry

这样才不混乱。

你应该把 FIELD_EXAMPLES.md 那一段改成这样

把原来这段：

```plaintext
Markdown用户实际选中的单词是：> retried / retry / retrying / retries为方便说明，这里以用户选中 `retried` 为主示例。
```

改成：

```plaintext
Markdown用户实际选中的单词是：> retry为说明词形归并规则，系统在其他场景中也可能遇到以下形式：> retry / retried / retrying / retries这些形式最终都归并到：> lemma = retry> word_key = retry
```

更进一步，后面的 JSON 示例也要一起改

因为你当前主示例句子里选中的是 retry，
那采集示例里更一致的写法应该是：

```plaintext
JSON{  "surface_form": "retry",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00"}
```

然后再单独加一个“词形归并补充示例”：

```plaintext
JSON[  { "surface_form": "retry", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retried", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retrying", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retries", "lemma": "retry", "word_key": "retry" }]
```

你这个纠正很重要

因为如果示例文档自己就不严谨，Codex 很容易照着错误示例实现，后面你会白白多一轮返工。

你现在最对的做法是把这两个文档继续压实，别让示例和规则打架。

我建议下一步直接把 修正后的 FIELD_EXAMPLES.md 完整终版 重新输出一版。

---

## 👤 用户

修正后的 FIELD_EXAMPLES.md 完整终版 重新输出一版。都输出在黑框里好复制

## 🤖 AI

```plaintext
Markdown# FIELD_EXAMPLES.md本文件用于补充 `SPEC.md`，通过具体示例说明各字段的真实数据长什么样，避免扩展、后端、Anki note type 在实现时对字段理解不一致。---## 1. 示例场景用户在 YouTube 视频中看到一句话：> Please retry the download if it doesn't start automatically.用户实际选中的单词是：> retry为说明词形归并规则，系统在其他场景中也可能遇到以下形式：> retry / retried / retrying / retries这些形式最终都归并到：> lemma = retry  > word_key = retry---## 2. 采集阶段示例（扩展 -> 后端）### 2.1 扩展采集到的原始请求示例```json{  "surface_form": "retry",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00"}
```

2.2 字段解释

字段名示例值中文含义说明surface_formretry原始词形用户实际选中的词source_sentencePlease retry the download if it doesn't start automatically.来源原句选词时所在原句source_titleHow to Fix Download Problems来源标题页面/视频标题source_urlhttps://www.youtube.com/watch?v=example123来源链接页面 URLsource_typeyoutube来源类型web 或 youtubesource_timestamp00:12:35来源时间点视频中的时间位置captured_at2026-03-29T14:23:10+09:00采集时间选词发生时间

3. 后端标准化与归并示例

后端收到 surface_form = retry 后，执行标准化和词形归并。

3.1 后端处理中间结果示例

```plaintext
JSON{  "surface_form": "retry",  "normalized_form": "retry",  "lemma": "retry",  "word_key": "retry"}
```

3.2 词形归并补充示例

```plaintext
JSON[  { "surface_form": "retry", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retried", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retrying", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retries", "lemma": "retry", "word_key": "retry" }]
```

3.3 字段解释

字段名示例值中文含义说明surface_formretry原始词形用户实际选中的形式normalized_formretry标准化词形去空格、去首尾标点、统一小写后的结果lemmaretry基础词形词形归并后的核心词word_keyretry单词业务键查重使用，第一版等于 lemma 的小写标准化结果

4. 队列项示例

4.1 待处理队列中的一条记录示例

```plaintext
JSON{  "record_id": 101,  "surface_form": "retry",  "normalized_form": "retry",  "lemma": "retry",  "word_key": "retry",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00",  "status": "pending",  "error_message": "",  "generator_version": "v1"}
```

4.2 字段解释

字段名示例值中文含义说明record_id101记录主键这一条队列记录自己的唯一编号word_keyretry单词业务键用于判断是不是同一个核心词statuspending队列状态当前还未生成正式卡generator_versionv1生成版本号这条记录对应的生成逻辑版本

5. 后端返回给扩展的状态示例

5.1 成功加入待处理

```plaintext
JSON{  "status": "added_to_queue",  "message": "Word added to pending queue.",  "record_id": 101,  "word_key": "retry",  "lemma": "retry"}
```

5.2 已在待处理队列中

```plaintext
JSON{  "status": "already_in_queue",  "message": "Word already exists in pending queue.",  "record_id": 101,  "word_key": "retry",  "lemma": "retry"}
```

5.3 已存在于 Anki

```plaintext
JSON{  "status": "already_in_anki",  "message": "Word already exists in Anki.",  "word_key": "retry",  "lemma": "retry"}
```

5.4 输入不合法

```plaintext
JSON{  "status": "invalid_input",  "message": "Only single English words are supported."}
```

6. 正式 Note Type 字段示例

6.1 一张正式 Anki 卡的数据示例

```plaintext
JSON{  "word": "retry",  "ipa": "/ˌriːˈtraɪ/",  "emoji": "🔁",  "audio": "retry_anki_audio.mp3",  "image_prompt": "A person clicking a retry button on a computer screen.",  "meanings": "[(verb) to try again after failure, (noun) an act of trying again)]",  "forms": "retries / retried / retrying",  "pairs": "[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]",  "examples": "[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]",  "record_id": 101,  "word_key": "retry",  "lemma": "retry",  "surface_form": "retry",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "generator_version": "v1"}
```

7. 展示字段示例

7.1 正面展示字段示例

字段名示例值wordretryipa/ˌriːˈtraɪ/emoji🔁audioretry_anki_audio.mp3image_promptA person clicking a retry button on a computer screen.

7.2 背面展示字段示例

字段名示例值meanings[(verb) to try again after failure, (noun) an act of trying again)]formsretries / retried / retryingpairs[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]examples[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]

8. 不展示字段示例

字段名示例值中文含义record_id101记录主键word_keyretry单词业务键lemmaretry基础词形surface_formretry原始词形source_urlhttps://www.youtube.com/watch?v=example123来源链接source_typeyoutube来源类型source_timestamp00:12:35来源时间点generator_versionv1生成版本号

8.1 非主示例词形补充

在其他场景中，如果用户实际选中的是其他词形，则可能出现：

surface_formlemmaword_keyretriedretryretryretryingretryretryretriesretryretry

9. examples 规则示例

9.1 有来源原句时

```plaintext
JSON{  "examples": [    "Please retry the download if it doesn't start automatically. (source sentence)",    "I retried the task after fixing the error. (verb)",    "You can retry the operation later. (verb)"  ]}
```

9.2 无来源原句时

```plaintext
JSON{  "examples": [    "I retried the task after fixing the error. (verb)",    "You can retry the operation later. (verb)",    "She will retry the process tomorrow. (verb)"  ]}
```

10. forms 规则示例

10.1 动词示例

wordformsretryretries / retried / retryingstudystudies / studied / studyingfixfixes / fixed / fixing

10.2 无明显常见变形时

可为空，或不渲染该字段。

11. 命名一致性要求

所有字段名必须与 SPEC.md 一致

record_id 不能替代 word_key

word_key 不能使用 id:12333 这类记录编号

word_key 必须使用可读、稳定、可归并的业务值

第一版默认：word_key = lemma 的小写标准化结果

12. 当前示例中的关键映射关系

概念示例值说明用户实际选中的词retrysurface_form标准化后retrynormalized_form归并后的基础词形retrylemma查重使用的业务键retryword_key这条记录自己的编号101record_id

12.1 其他词形的映射关系补充

概念示例值说明用户实际选中的词retriedsurface_form标准化后retriednormalized_form归并后的基础词形retrylemma查重使用的业务键retryword_key这条记录自己的编号102record_id

---

## 👤 用户

你这样发给我是只要上面那一点，还是后续内容都要啊，不希望都在一起容易复制

## 🤖 AI

都要，但不要挤在一个黑框里。你这个担心是对的。

黑框太长有两个问题：

不好复制，容易漏头漏尾

你后面检查时也容易看乱

更合理的发法是：

一个文件，一个黑框

也就是分别给你：

SPEC.md

FIELD_EXAMPLES.md

如果内容还是太长，再继续拆成：

FIELD_EXAMPLES.md 分段输出

第 1 部分：示例场景 + 采集阶段

第 2 部分：后端归并 + 队列项 + 状态示例

第 3 部分：正式 Note Type 字段 + examples/forms 规则 + 命名要求

这样你复制最稳。

最适合你的方式

我建议后面统一按这个格式发：

先给文件名

SPEC.md

然后单独一个黑框

内容只放这个文件

再下一条：

文件名

FIELD_EXAMPLES.md

再单独一个黑框

内容只放这个文件

不要把解释、说明、正文、代码、补充全塞进同一个黑框。

你这次这个截图里的情况

你看到的应该是：

上面有 JSON 示例

下面又接表格和说明

这种“整篇连续塞一起”的形式，确实不适合你复制到本地文件里。

后面我会怎么发

我会按下面这种方式给你：

文件名：FIELD_EXAMPLES.md（第 1 部分）

```plaintext
Markdown...
```

文件名：FIELD_EXAMPLES.md（第 2 部分）

```plaintext
Markdown...
```

这样你直接分段复制，再合并成一个文件就行。

你现在要的话，我下一条就按这个方式，把 FIELD_EXAMPLES.md 拆成 3 个独立黑框 重新发。

---

## 👤 用户

把 FIELD_EXAMPLES.md 拆成 3 个独立黑框 重新发

## 🤖 AI

文件名：FIELD_EXAMPLES.md（第 1 部分）

```plaintext
Markdown# FIELD_EXAMPLES.md本文件用于补充 `SPEC.md`，通过具体示例说明各字段的真实数据长什么样，避免扩展、后端、Anki note type 在实现时对字段理解不一致。---## 1. 示例场景用户在 YouTube 视频中看到一句话：> Please retry the download if it doesn't start automatically.用户实际选中的单词是：> retry为说明词形归并规则，系统在其他场景中也可能遇到以下形式：> retry / retried / retrying / retries这些形式最终都归并到：> lemma = retry  > word_key = retry---## 2. 采集阶段示例（扩展 -> 后端）### 2.1 扩展采集到的原始请求示例```json{  "surface_form": "retry",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00"}
```

2.2 字段解释

字段名示例值中文含义说明surface_formretry原始词形用户实际选中的词source_sentencePlease retry the download if it doesn't start automatically.来源原句选词时所在原句source_titleHow to Fix Download Problems来源标题页面/视频标题source_urlhttps://www.youtube.com/watch?v=example123来源链接页面 URLsource_typeyoutube来源类型web 或 youtubesource_timestamp00:12:35来源时间点视频中的时间位置captured_at2026-03-29T14:23:10+09:00采集时间选词发生时间

3. 后端标准化与归并示例

后端收到 surface_form = retry 后，执行标准化和词形归并。

3.1 后端处理中间结果示例

```plaintext
JSON{  "surface_form": "retry",  "normalized_form": "retry",  "lemma": "retry",  "word_key": "retry"}
```

3.2 词形归并补充示例

```plaintext
JSON[  { "surface_form": "retry", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retried", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retrying", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retries", "lemma": "retry", "word_key": "retry" }]
```

3.3 字段解释

字段名示例值中文含义说明surface_formretry原始词形用户实际选中的形式normalized_formretry标准化词形去空格、去首尾标点、统一小写后的结果lemmaretry基础词形词形归并后的核心词word_keyretry单词业务键查重使用，第一版等于 lemma 的小写标准化结果

```plaintext
**文件名：`FIELD_EXAMPLES.md`（第 2 部分）**```md## 4. 队列项示例### 4.1 待处理队列中的一条记录示例```json{  "record_id": 101,  "surface_form": "retry",  "normalized_form": "retry",  "lemma": "retry",  "word_key": "retry",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00",  "status": "pending",  "error_message": "",  "generator_version": "v1"}
```

4.2 字段解释

字段名示例值中文含义说明record_id101记录主键这一条队列记录自己的唯一编号word_keyretry单词业务键用于判断是不是同一个核心词statuspending队列状态当前还未生成正式卡generator_versionv1生成版本号这条记录对应的生成逻辑版本

5. 后端返回给扩展的状态示例

5.1 成功加入待处理

```plaintext
JSON{  "status": "added_to_queue",  "message": "Word added to pending queue.",  "record_id": 101,  "word_key": "retry",  "lemma": "retry"}
```

5.2 已在待处理队列中

```plaintext
JSON{  "status": "already_in_queue",  "message": "Word already exists in pending queue.",  "record_id": 101,  "word_key": "retry",  "lemma": "retry"}
```

5.3 已存在于 Anki

```plaintext
JSON{  "status": "already_in_anki",  "message": "Word already exists in Anki.",  "word_key": "retry",  "lemma": "retry"}
```

5.4 输入不合法

```plaintext
JSON{  "status": "invalid_input",  "message": "Only single English words are supported."}
```

6. 正式 Note Type 字段示例

6.1 一张正式 Anki 卡的数据示例

```plaintext
JSON{  "word": "retry",  "ipa": "/ˌriːˈtraɪ/",  "emoji": "🔁",  "audio": "retry_anki_audio.mp3",  "image_prompt": "A person clicking a retry button on a computer screen.",  "meanings": "[(verb) to try again after failure, (noun) an act of trying again)]",  "forms": "retries / retried / retrying",  "pairs": "[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]",  "examples": "[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]",  "record_id": 101,  "word_key": "retry",  "lemma": "retry",  "surface_form": "retry",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "generator_version": "v1"}
```

7. 展示字段示例

7.1 正面展示字段示例

字段名示例值wordretryipa/ˌriːˈtraɪ/emoji🔁audioretry_anki_audio.mp3image_promptA person clicking a retry button on a computer screen.

7.2 背面展示字段示例

字段名示例值meanings[(verb) to try again after failure, (noun) an act of trying again)]formsretries / retried / retryingpairs[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]examples[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]

```plaintext
**文件名：`FIELD_EXAMPLES.md`（第 3 部分）**```md## 8. 不展示字段示例| 字段名 | 示例值 | 中文含义 ||---|---|---|| `record_id` | `101` | 记录主键 || `word_key` | `retry` | 单词业务键 || `lemma` | `retry` | 基础词形 || `surface_form` | `retry` | 原始词形 || `source_url` | `https://www.youtube.com/watch?v=example123` | 来源链接 || `source_type` | `youtube` | 来源类型 || `source_timestamp` | `00:12:35` | 来源时间点 || `generator_version` | `v1` | 生成版本号 |### 8.1 非主示例词形补充在其他场景中，如果用户实际选中的是其他词形，则可能出现：| `surface_form` | `lemma` | `word_key` ||---|---|---|| `retried` | `retry` | `retry` || `retrying` | `retry` | `retry` || `retries` | `retry` | `retry` |---## 9. examples 规则示例### 9.1 有来源原句时```json{  "examples": [    "Please retry the download if it doesn't start automatically. (source sentence)",    "I retried the task after fixing the error. (verb)",    "You can retry the operation later. (verb)"  ]}
```

9.2 无来源原句时

```plaintext
JSON{  "examples": [    "I retried the task after fixing the error. (verb)",    "You can retry the operation later. (verb)",    "She will retry the process tomorrow. (verb)"  ]}
```

10. forms 规则示例

10.1 动词示例

wordformsretryretries / retried / retryingstudystudies / studied / studyingfixfixes / fixed / fixing

10.2 无明显常见变形时

可为空，或不渲染该字段。

11. 命名一致性要求

所有字段名必须与 SPEC.md 一致

record_id 不能替代 word_key

word_key 不能使用 id:12333 这类记录编号

word_key 必须使用可读、稳定、可归并的业务值

第一版默认：word_key = lemma 的小写标准化结果

12. 当前示例中的关键映射关系

概念示例值说明用户实际选中的词retrysurface_form标准化后retrynormalized_form归并后的基础词形retrylemma查重使用的业务键retryword_key这条记录自己的编号101record_id

12.1 其他词形的映射关系补充

概念示例值说明用户实际选中的词retriedsurface_form标准化后retriednormalized_form归并后的基础词形retrylemma查重使用的业务键retryword_key这条记录自己的编号102record_id

---

## 👤 用户

你是这样发给我的，很奇怪，应该是一次性发给我

## 🤖 AI

对，这次是我发法不对。
你要的是一次性完整复制，不是分段拼接。

下面我直接一次性给你完整的 FIELD_EXAMPLES.md，只放一个黑框里，不再拆。

```plaintext
Markdown# FIELD_EXAMPLES.md本文件用于补充 `SPEC.md`，通过具体示例说明各字段的真实数据长什么样，避免扩展、后端、Anki note type 在实现时对字段理解不一致。---## 1. 示例场景用户在 YouTube 视频中看到一句话：> Please retry the download if it doesn't start automatically.用户实际选中的单词是：> retry为说明词形归并规则，系统在其他场景中也可能遇到以下形式：> retry / retried / retrying / retries这些形式最终都归并到：> lemma = retry  > word_key = retry---## 2. 采集阶段示例（扩展 -> 后端）### 2.1 扩展采集到的原始请求示例```json{  "surface_form": "retry",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00"}
```

2.2 字段解释

字段名示例值中文含义说明surface_formretry原始词形用户实际选中的词source_sentencePlease retry the download if it doesn't start automatically.来源原句选词时所在原句source_titleHow to Fix Download Problems来源标题页面/视频标题source_urlhttps://www.youtube.com/watch?v=example123来源链接页面 URLsource_typeyoutube来源类型web 或 youtubesource_timestamp00:12:35来源时间点视频中的时间位置captured_at2026-03-29T14:23:10+09:00采集时间选词发生时间

3. 后端标准化与归并示例

后端收到 surface_form = retry 后，执行标准化和词形归并。

3.1 后端处理中间结果示例

```plaintext
JSON{  "surface_form": "retry",  "normalized_form": "retry",  "lemma": "retry",  "word_key": "retry"}
```

3.2 词形归并补充示例

```plaintext
JSON[  { "surface_form": "retry", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retried", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retrying", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retries", "lemma": "retry", "word_key": "retry" }]
```

3.3 字段解释

字段名示例值中文含义说明surface_formretry原始词形用户实际选中的形式normalized_formretry标准化词形去空格、去首尾标点、统一小写后的结果lemmaretry基础词形词形归并后的核心词word_keyretry单词业务键查重使用，第一版等于 lemma 的小写标准化结果

4. 队列项示例

4.1 待处理队列中的一条记录示例

```plaintext
JSON{  "record_id": 101,  "surface_form": "retry",  "normalized_form": "retry",  "lemma": "retry",  "word_key": "retry",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00",  "status": "pending",  "error_message": "",  "generator_version": "v1"}
```

4.2 字段解释

字段名示例值中文含义说明record_id101记录主键这一条队列记录自己的唯一编号word_keyretry单词业务键用于判断是不是同一个核心词statuspending队列状态当前还未生成正式卡generator_versionv1生成版本号这条记录对应的生成逻辑版本

5. 后端返回给扩展的状态示例

5.1 成功加入待处理

```plaintext
JSON{  "status": "added_to_queue",  "message": "Word added to pending queue.",  "record_id": 101,  "word_key": "retry",  "lemma": "retry"}
```

5.2 已在待处理队列中

```plaintext
JSON{  "status": "already_in_queue",  "message": "Word already exists in pending queue.",  "record_id": 101,  "word_key": "retry",  "lemma": "retry"}
```

5.3 已存在于 Anki

```plaintext
JSON{  "status": "already_in_anki",  "message": "Word already exists in Anki.",  "word_key": "retry",  "lemma": "retry"}
```

5.4 输入不合法

```plaintext
JSON{  "status": "invalid_input",  "message": "Only single English words are supported."}
```

6. 正式 Note Type 字段示例

6.1 一张正式 Anki 卡的数据示例

```plaintext
JSON{  "word": "retry",  "ipa": "/ˌriːˈtraɪ/",  "emoji": "🔁",  "audio": "retry_anki_audio.mp3",  "image_prompt": "A person clicking a retry button on a computer screen.",  "meanings": "[(verb) to try again after failure, (noun) an act of trying again)]",  "forms": "retries / retried / retrying",  "pairs": "[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]",  "examples": "[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]",  "record_id": 101,  "word_key": "retry",  "lemma": "retry",  "surface_form": "retry",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "generator_version": "v1"}
```

7. 展示字段示例

7.1 正面展示字段示例

字段名示例值wordretryipa/ˌriːˈtraɪ/emoji🔁audioretry_anki_audio.mp3image_promptA person clicking a retry button on a computer screen.

7.2 背面展示字段示例

字段名示例值meanings[(verb) to try again after failure, (noun) an act of trying again)]formsretries / retried / retryingpairs[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]examples[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]

8. 不展示字段示例

字段名示例值中文含义record_id101记录主键word_keyretry单词业务键lemmaretry基础词形surface_formretry原始词形source_urlhttps://www.youtube.com/watch?v=example123来源链接source_typeyoutube来源类型source_timestamp00:12:35来源时间点generator_versionv1生成版本号

8.1 非主示例词形补充

在其他场景中，如果用户实际选中的是其他词形，则可能出现：

surface_formlemmaword_keyretriedretryretryretryingretryretryretriesretryretry

9. examples 规则示例

9.1 有来源原句时

```plaintext
JSON{  "examples": [    "Please retry the download if it doesn't start automatically. (source sentence)",    "I retried the task after fixing the error. (verb)",    "You can retry the operation later. (verb)"  ]}
```

9.2 无来源原句时

```plaintext
JSON{  "examples": [    "I retried the task after fixing the error. (verb)",    "You can retry the operation later. (verb)",    "She will retry the process tomorrow. (verb)"  ]}
```

10. forms 规则示例

10.1 动词示例

wordformsretryretries / retried / retryingstudystudies / studied / studyingfixfixes / fixed / fixing

10.2 无明显常见变形时

可为空，或不渲染该字段。

11. 命名一致性要求

所有字段名必须与 SPEC.md 一致

record_id 不能替代 word_key

word_key 不能使用 id:12333 这类记录编号

word_key 必须使用可读、稳定、可归并的业务值

第一版默认：word_key = lemma 的小写标准化结果

12. 当前示例中的关键映射关系

概念示例值说明用户实际选中的词retrysurface_form标准化后retrynormalized_form归并后的基础词形retrylemma查重使用的业务键retryword_key这条记录自己的编号101record_id

12.1 其他词形的映射关系补充

概念示例值说明用户实际选中的词retriedsurface_form标准化后retriednormalized_form归并后的基础词形retrylemma查重使用的业务键retryword_key这条记录自己的编号102record_id

---

## 👤 用户

并没有，我直接一次性给你完整的 FIELD_EXAMPLES.md，只放一个黑框里，不再拆。

## 🤖 AI

对，前一版还是被渲染坏了。问题就在于：外层黑框里又套了很多内层三引号代码块，界面会折叠和截断。

这次我直接用 外层四个反引号 包住整个文件，这样你可以一次性整块复制。

```plaintext
Markdown# FIELD_EXAMPLES.md本文件用于补充 `SPEC.md`，通过具体示例说明各字段的真实数据长什么样，避免扩展、后端、Anki note type 在实现时对字段理解不一致。---## 1. 示例场景用户在 YouTube 视频中看到一句话：> Please retry the download if it doesn't start automatically.用户实际选中的单词是：> retry为说明词形归并规则，系统在其他场景中也可能遇到以下形式：> retry / retried / retrying / retries这些形式最终都归并到：> lemma = retry  > word_key = retry---## 2. 采集阶段示例（扩展 -> 后端）### 2.1 扩展采集到的原始请求示例```json{  "surface_form": "retry",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00"}```### 2.2 字段解释| 字段名 | 示例值 | 中文含义 | 说明 ||---|---|---|---|| `surface_form` | `retry` | 原始词形 | 用户实际选中的词 || `source_sentence` | `Please retry the download if it doesn't start automatically.` | 来源原句 | 选词时所在原句 || `source_title` | `How to Fix Download Problems` | 来源标题 | 页面/视频标题 || `source_url` | `https://www.youtube.com/watch?v=example123` | 来源链接 | 页面 URL || `source_type` | `youtube` | 来源类型 | `web` 或 `youtube` || `source_timestamp` | `00:12:35` | 来源时间点 | 视频中的时间位置 || `captured_at` | `2026-03-29T14:23:10+09:00` | 采集时间 | 选词发生时间 |---## 3. 后端标准化与归并示例后端收到 `surface_form = retry` 后，执行标准化和词形归并。### 3.1 后端处理中间结果示例```json{  "surface_form": "retry",  "normalized_form": "retry",  "lemma": "retry",  "word_key": "retry"}```### 3.2 词形归并补充示例```json[  { "surface_form": "retry", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retried", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retrying", "lemma": "retry", "word_key": "retry" },  { "surface_form": "retries", "lemma": "retry", "word_key": "retry" }]```### 3.3 字段解释| 字段名 | 示例值 | 中文含义 | 说明 ||---|---|---|---|| `surface_form` | `retry` | 原始词形 | 用户实际选中的形式 || `normalized_form` | `retry` | 标准化词形 | 去空格、去首尾标点、统一小写后的结果 || `lemma` | `retry` | 基础词形 | 词形归并后的核心词 || `word_key` | `retry` | 单词业务键 | 查重使用，第一版等于 `lemma` 的小写标准化结果 |---## 4. 队列项示例### 4.1 待处理队列中的一条记录示例```json{  "record_id": 101,  "surface_form": "retry",  "normalized_form": "retry",  "lemma": "retry",  "word_key": "retry",  "source_sentence": "Please retry the download if it doesn't start automatically.",  "source_title": "How to Fix Download Problems",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "captured_at": "2026-03-29T14:23:10+09:00",  "status": "pending",  "error_message": "",  "generator_version": "v1"}```### 4.2 字段解释| 字段名 | 示例值 | 中文含义 | 说明 ||---|---|---|---|| `record_id` | `101` | 记录主键 | 这一条队列记录自己的唯一编号 || `word_key` | `retry` | 单词业务键 | 用于判断是不是同一个核心词 || `status` | `pending` | 队列状态 | 当前还未生成正式卡 || `generator_version` | `v1` | 生成版本号 | 这条记录对应的生成逻辑版本 |---## 5. 后端返回给扩展的状态示例### 5.1 成功加入待处理```json{  "status": "added_to_queue",  "message": "Word added to pending queue.",  "record_id": 101,  "word_key": "retry",  "lemma": "retry"}```### 5.2 已在待处理队列中```json{  "status": "already_in_queue",  "message": "Word already exists in pending queue.",  "record_id": 101,  "word_key": "retry",  "lemma": "retry"}```### 5.3 已存在于 Anki```json{  "status": "already_in_anki",  "message": "Word already exists in Anki.",  "word_key": "retry",  "lemma": "retry"}```### 5.4 输入不合法```json{  "status": "invalid_input",  "message": "Only single English words are supported."}```---## 6. 正式 Note Type 字段示例### 6.1 一张正式 Anki 卡的数据示例```json{  "word": "retry",  "ipa": "/ˌriːˈtraɪ/",  "emoji": "🔁",  "audio": "retry_anki_audio.mp3",  "image_prompt": "A person clicking a retry button on a computer screen.",  "meanings": "[(verb) to try again after failure, (noun) an act of trying again)]",  "forms": "retries / retried / retrying",  "pairs": "[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]",  "examples": "[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]",  "record_id": 101,  "word_key": "retry",  "lemma": "retry",  "surface_form": "retry",  "source_url": "https://www.youtube.com/watch?v=example123",  "source_type": "youtube",  "source_timestamp": "00:12:35",  "generator_version": "v1"}```---## 7. 展示字段示例### 7.1 正面展示字段示例| 字段名 | 示例值 ||---|---|| `word` | `retry` || `ipa` | `/ˌriːˈtraɪ/` || `emoji` | `🔁` || `audio` | `retry_anki_audio.mp3` || `image_prompt` | `A person clicking a retry button on a computer screen.` |### 7.2 背面展示字段示例| 字段名 | 示例值 ||---|---|| `meanings` | `[(verb) to try again after failure, (noun) an act of trying again)]` || `forms` | `retries / retried / retrying` || `pairs` | `[retry the download（重新下载）, retry the request（重新请求）, retry later（稍后重试）]` || `examples` | `[Please retry the download if it doesn't start automatically. (source sentence), I retried the task after fixing the error. (verb), You can retry the operation later. (verb)]` |---## 8. 不展示字段示例| 字段名 | 示例值 | 中文含义 ||---|---|---|| `record_id` | `101` | 记录主键 || `word_key` | `retry` | 单词业务键 || `lemma` | `retry` | 基础词形 || `surface_form` | `retry` | 原始词形 || `source_url` | `https://www.youtube.com/watch?v=example123` | 来源链接 || `source_type` | `youtube` | 来源类型 || `source_timestamp` | `00:12:35` | 来源时间点 || `generator_version` | `v1` | 生成版本号 |### 8.1 非主示例词形补充在其他场景中，如果用户实际选中的是其他词形，则可能出现：| `surface_form` | `lemma` | `word_key` ||---|---|---|| `retried` | `retry` | `retry` || `retrying` | `retry` | `retry` || `retries` | `retry` | `retry` |---## 9. examples 规则示例### 9.1 有来源原句时```json{  "examples": [    "Please retry the download if it doesn't start automatically. (source sentence)",    "I retried the task after fixing the error. (verb)",    "You can retry the operation later. (verb)"  ]}```### 9.2 无来源原句时```json{  "examples": [    "I retried the task after fixing the error. (verb)",    "You can retry the operation later. (verb)",    "She will retry the process tomorrow. (verb)"  ]}```---## 10. forms 规则示例### 10.1 动词示例| word | forms ||---|---|| `retry` | `retries / retried / retrying` || `study` | `studies / studied / studying` || `fix` | `fixes / fixed / fixing` |### 10.2 无明显常见变形时可为空，或不渲染该字段。---## 11. 命名一致性要求- 所有字段名必须与 `SPEC.md` 一致- `record_id` 不能替代 `word_key`- `word_key` 不能使用 `id:12333` 这类记录编号- `word_key` 必须使用可读、稳定、可归并的业务值- 第一版默认：`word_key = lemma 的小写标准化结果`---## 12. 当前示例中的关键映射关系| 概念 | 示例值 | 说明 ||---|---|---|| 用户实际选中的词 | `retry` | `surface_form` || 标准化后 | `retry` | `normalized_form` || 归并后的基础词形 | `retry` | `lemma` || 查重使用的业务键 | `retry` | `word_key` || 这条记录自己的编号 | `101` | `record_id` |### 12.1 其他词形的映射关系补充| 概念 | 示例值 | 说明 ||---|---|---|| 用户实际选中的词 | `retried` | `surface_form` || 标准化后 | `retried` | `normalized_form` || 归并后的基础词形 | `retry` | `lemma` || 查重使用的业务键 | `retry` | `word_key` || 这条记录自己的编号 | `102` | `record_id` |
```

接下来如果你要，我会用同样的方式把 SPEC.md 也重新发成这种真正可整块复制的版本。

