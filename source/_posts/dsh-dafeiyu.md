---
title: "在 DSH 里养一只 QQ 机器人：SnowLuma + Aurabot 全流程"
date: 2026-10-31 18:10:00
tags:
  - DSH
  - QQ机器人
  - SnowLuma
  - OneBot
  - 踩坑
categories:
  - 折腾记录
cover: /img/dsh-dafeiyu/cover.png
---

想给 QQ 里塞一个会说话、有记忆、会发表情的 AI 角色，网上的教程大多长这样：「先装网关，再配 OneBot v11，填好反向 WS 地址和 token」。

然后你就卡住了。

这篇是完整记录：从零到能私聊，中间踩了五个坑，每个都有报错原文和真实原因。**代码和配置都是本机实测的**，不是抄文档。

<!-- more -->

## 最终架构

```text
QQ 小号 ⇄ SnowLuma（OneBot v11 网关） ⇄ Aurabot 插件 ⇄ DSH ⇄ 模型
              :5099 控制台 / :3001 WS
```

三块东西各司其职：

| 组件 | 角色 | 说明 |
|---|---|---|
| DSH | 宿主 | 提供模型、会话、工具运行时 |
| Aurabot 插件 | 角色本体 | 人格、记忆、表情、面板 |
| SnowLuma | 网关 | 把 QQ 协议翻译成 OneBot v11 |

难点全在第三块——它是独立进程，要登录 QQ，还要往 QQ 进程里注入 hook。

## 一、装插件

从 DSH 的插件市场搜 `dsh-aurabot-qq` 安装。

装完**必须彻底重启**（托盘退出，不是关窗口）。插件的宿主半边在进程启动时加载，客户端半边在启动时注入。

重启后侧栏「自动化任务」下面会出现 Aurabot，日志里能看到：

```text
[core] Aurabot v1.1.24 已加载｜总开关 关｜试运行 开
[pet] 桌宠：素材包已下载落位（106 个动画）
```

## 二、装网关

下载 [SnowLuma](https://github.com/SnowLuma/SnowLuma/releases) 的 `win-x64.zip`（完整版，自带 Node 运行时），解压到**纯英文路径**，双击 `launcher.bat`。

控制台会打印一次性密码：

```text
★ WebUI 初始登录凭据 ★
initial credentials: user=admin password=xxxxxxxxxxxx
listening http://127.0.0.1:5099
```

浏览器进 `http://127.0.0.1:5099`，同意 EULA，**改掉密码**（不改的话下次启动会重新生成随机密码）。

### 坑 1：不打开 hookAutoLoad，它不会接管 QQ

SnowLuma 默认 `hookAutoLoad: false`。不打开的话，程序在跑、QQ 也在跑，但它就是不注入——**看起来一切正常，实际什么都没发生**。

改 `config/runtime.json`：

```json
{
  "webuiPort": 5099,
  "hookAutoLoad": true
}
```

重启 SnowLuma，然后在控制台看进程列表，三个状态都要是 true：

```text
injected: true    connected: true    loggedIn: true    uin: 你的小号
```

### 坑 2：NapCat 路线会遇到「QQ 文件损坏」

如果你用的是 NapCat 而不是 SnowLuma，第一次启动大概率报这个：

```text
[app]module file name: ...\QQNT.dll
error code v2:-8
[NapCat] [Fork] Worker进程意外退出 (1/3)，正在尝试重新拉起...
```

同时 QQ 弹窗说「文件损坏」。

**你的 QQ 没坏。** 原因是 NapCat 把 QQ 的 `resources/app/package.json` 里 `main` 改成了 `./napcat/napcat.mjs`，QQ 启动时自检发现入口被换，判定损坏并让主进程退出。

同一个安装包，**普通权限启动报错，管理员权限启动立刻出二维码**。

所以根因是权限：注入需要提权。这带来一个连锁麻烦——网关挂在管理员控制台上，窗口一关就死。这也是我最后换 SnowLuma 的原因，它不需要提权，也没有窗口。

## 三、接线

Aurabot 面板的向导分五步，关键是第 2 步：

- 选 **「接我已有的 OneBot 机器人」**（不要选「用 SnowLuma，插件帮你管」——那会把启停也接管过去）
- WebSocket 地址填 `ws://127.0.0.1:3001`
- Token 从 `C:\Aurabot\snowluma\config\onebot_<你的QQ号>.json` 里抄：

```json
"wsServers": [
  {
    "name": "ws-default",
    "accessToken": "这一长串",
    "port": 3001
  }
]
```

点「接入」后它会调 `get_login_info` 核对登录的是不是机器人号，**不是的话主动断开**——这是防止接错到主号。

## 四、模型：能看图的和聪明的，二选一

这一节是我踩得最冤的地方。

### 坑 3：`deepseek-pro` 这个模型不存在

我按名字想当然写了 `deepseek-pro`，每一轮都失败：

```text
The supported API model names are deepseek-flash, deepseek-v4-pro,
but you passed deepseek-pro.
```

正确的是 **`deepseek-v4-pro`**，多一个 `v4-`。

### 坑 4：v4-pro 看不了图

换到 v4-pro 后她说自己看不见图片。查模型元数据：

```text
deepseek-flash               输入: text+image   ✅
deepseek-v4-pro              输入: text         ❌
deepseek-v4-flash            输入: text+image   （当前 key 用不了）
```

**能力是二选一的。** 养角色我建议选 flash——她能看懂你发的截图和表情包，这比「说话更深刻」重要。

## 五、最容易翻车的地方：进程树

### 坑 5：DSH 一重启，网关就掉

现象：日志反复刷这个。

```text
[onebot] QQ 网关：connecting
[onebot] QQ 网关：disconnected（code 1006）
```

`1006` 是异常断开。我先怀疑网络、怀疑 QQ 掉线，都不对。

查 Windows 事件日志：**40 分钟里没有任何 QQ 崩溃记录**，也没有正常退出的日志。不是崩溃，是**被杀**。

再看时间点：

| 网关死的时间 | DSH 重启时间 |
|---|---|
| 11:21:2x | 11:21:36 |
| 11:27:4x | 11:27:20 |

完全吻合。因为网关是从 DSH 的进程树里启动的，**DSH 一重启，整棵子树被回收**。

解决办法是让它脱离 DSH 的进程树。用 WMI 创建进程，父进程是系统服务，重启 DSH 也不影响：

```powershell
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = 'powershell.exe -NoProfile -WindowStyle Hidden -File C:\Aurabot\start-bot.ps1'
}
```

再配一个看门狗，每 30 秒检查并自动补 hook：

```powershell
$list = (Invoke-RestMethod 'http://127.0.0.1:5099/api/processes' -Headers $h).list
$target = $list | Where-Object { $_.name -eq 'QQ.exe' -and -not $_.injected }
if ($target) {
  Invoke-RestMethod -Uri "http://127.0.0.1:5099/api/processes/$($target.pid)/load" `
    -Method Post -Headers $h -ContentType 'application/json' -Body '{}'
}
```

加上这个之前，我一天手动重启了五次；加上之后，再没管过。

## 六、还有两个小坑

### 群里不理人

```text
忽略 group:2161082718（不在群白名单）
```

她默认只认主人私聊。要在面板「权限」页加群号。加完也不是每条都接：被叫必回，没被叫按概率插话，凌晨免打扰。

### 表情发不出来

把 120 张表情导进 QQ 收藏后，日志还是：

```text
没找到「委屈」这张表情，跳过
```

因为挑表情用的是**插件自己的索引**，不是 QQ 收藏：

```text
plugins-data/aurabot/stickers/index.json
  { md5, file, name, tags: ['开心','委屈'], emojiId }
```

QQ 收藏是「手」，这个 index.json 才是「脑子」。只导收藏，她能发但不知道哪张是委屈。

## 验收清单

按这个顺序验，出问题能快速定位：

1. **网关**：`injected / connected / loggedIn` 三个 true
2. **连接**：日志出现 `[onebot] 已连上 QQ 网关（WS）`
3. **消息**：发一句，日志有 `为 private:xxx 新建了 DSH 会话`
4. **模型**：没有 `这一轮没正常结束`
5. **回复**：QQ 里真收到消息

## 一点感想

这套东西真正难的不是装，是**判断问题出在哪一层**。

网关、插件、模型、权限，四层各有各的报错方式，而且经常互相伪装：QQ 说「文件损坏」其实是权限问题，网关「掉线」其实是进程树问题，模型报「不支持」但不说正确的是什么。

给后来者的建议：**别一步到位**。先跑通私聊回一句，再加记忆，再加表情，最后碰群聊。每加一样验一遍，出问题才知道是刚加的那一样。

---

参考：
- [SnowLuma](https://github.com/SnowLuma/SnowLuma) · OneBot v11 网关
- [dsh-aurabot-qq](https://github.com/accomplish07zrh-eng/dsh-aurabot-qq) · Aurabot 插件
- [OneBot v11 协议](https://github.com/botuniverse/onebot-11)
