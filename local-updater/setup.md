# 本机一键更新器 使用说明（资金流 / 次新股 两页专用）

东方财富把 GitHub 服务器 IP 封了，行业/概念/次新股板块接口在云端抓不到。
你电脑的家庭宽带 IP 东财不封，在本机跑就能抓全量数据并推回 GitHub，让网页每天更新。

## 一、一次性准备（约 5 分钟）

1. **装 Python**
   下载 https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
   安装时**务必勾选 "Add python.exe to PATH"**，一路下一步装完。
   验证：按 Win+R 输 cmd，敲 `python --version` 能显示版本即成功。

2. **拿 GitHub token**
   - 打开 https://github.com/settings/tokens
   - 点 "Generate new token (classic)"，勾选 `repo` 权限，生成
   - 复制那串 `ghp_xxx`（只显示一次，存好）

3. **填 token**
   在本目录把 `config.example.json` 改名为 `config.json`，内容改成：
   ```json
   {"token":"ghp_你的token"}
   ```
   或者设系统环境变量 `GITHUB_TOKEN` = 你的 token（二选一）。

## 二、日常使用

- **手动更新**：双击 `run.bat`，黑框跑完自动关闭（或按任意键关闭）。
- **自动更新**：Windows 任务计划每天 16:30 跑（收盘后）：
  1. 按 Win+R 输 `taskschd.msc` 打开任务计划程序
  2. 右侧"创建基本任务" → 名称" A股看板更新" → 触发器"每天" 16:30
  3. 操作"启动程序" → 程序/脚本填 `run.bat` 的**完整路径**
     （如 `C:\你的路径\ASHARE-SENTIMENT\local-updater\run.bat`）
  4. 完成。以后每天收盘后自动抓这 2 页推 GitHub，网页次日显示最新。

## 三、说明

- 本包只管 **fundflow（资金流）** 和 **ipo（次新股）** 这 2 页——其余 6 页云端已能自动更新。
- 生成的 `data_flow.json` / `data_ipo.json` 在本地，自动推到 GitHub 仓库根目录，网页读取后即更新。
- 若某天抓不到（东财偶发抖动），重跑一次即可；不影响其余页面。
