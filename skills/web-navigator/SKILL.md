---
name: web-navigator
description: |
  使用 Playwright Chromium + CDP 打开网页并提取结构化内容。当用户说"帮我浏览网页"、"打开页面"、"看看这个网站"或给出 URL 时触发。提取页面标题、导航菜单链接、正文链接、标题结构，然后以可选项形式展示给用户供其选择继续深入子页面。必须用于任何 URL 浏览请求。
---

# Web Navigator

使用 Playwright Chromium 的 CDP 接口浏览网页。支持内网地址。

## 工作流

每次用户要求浏览网页，按以下流程执行：

### Step 1: 打开页面

```bash
node /home/wgz/.claude/skills/web-navigator/scripts/browse.mjs open "<url>"
```

输出 JSON：`{ title, text, navLinks, mainLinks, headings }`

- `title` — 页面标题
- `text` — 正文文本（前 5000 字符）
- `headings` — h1/h2/h3 标题结构 `[{level, text}]`
- `navLinks` — 导航区链接（sidebar/header/nav/menu 等），`[{text, href}]`
- `mainLinks` — 正文区链接（已去重，排除导航区链接）

### Step 2: 展示给用户

按以下格式向用户呈现可选路由：

```
**{页面标题}**

{正文摘要前 200 字}

**📌 导航菜单：**
[N] {链接文字}

**📄 页面段落：**
[N] {heading text}

**🔗 快捷入口：**
[N] {链接文字}

说序号继续浏览。
```

规则：
- **导航菜单**放前，标序号 1-9
- **页面段落**（headings）次之，标序号 10+
- **快捷入口**（外部链接/产品链接）最后，标序号 20+
- 去掉无意义链接（空文字、javascript:、纯#、重复的）
- 对外链接标注 `[外部]` 标记
- 碎片链接（以 # 开头定位到本页的锚点）在导航菜单中保留（表示页面内章节），在快捷入口中过滤掉
- 限制展示总数不超过 25 个选项

### Step 3: 用户选择后深入浏览

用户说序号后：

1. 从之前展示的列表中找到对应序号
2. 对 href 做 URL 解析：如果是相对路径（如 `/zhongbo/xxx`），用原始 URL 的 origin + path 拼接成绝对 URL
3. 用 `browse.mjs open "<resolved_url>"` 打开
4. 重复 Step 2

### Step 4: 关闭浏览器

用户明确说结束浏览时，不执行额外操作——脚本会自动关闭创建的 tab。

## 注意事项

- Chromium 支持 headless 模式，不弹出浏览器窗口
- 每轮浏览创建一个新 tab，关闭后销毁
- Chromium 进程在首次被调用时启动，会保持后台运行以加速后续浏览
- 页面 content 最多取 5000 字符，links 最多取 80 条
- SPA 页面（如 Vue/React）需要 3 秒额外等待 JS 渲染
- 遇内网地址不可达时告知用户，不要重试
- 不要展示全部 80 条链接，精选 ≤25 条最重要的展示
