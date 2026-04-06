# quickly-modifying-GitHub-commit-times
一键快速修改GitHub的commit提交时间脚本，营造你非常努力维护项目的美好品质

## 对比图：
<img width="1601" height="707" alt="image" src="https://github.com/user-attachments/assets/2486f02d-0156-41ca-b67d-bbc50b2e90bd" />

# Git Commit 时间随机重置工具 (commit_reset.py)

这是一个用于重新分配 Git 仓库提交历史时间的 Python 脚本。它的主要作用是将项目中所有的 **commit 日期**，随机且均匀地分布在你指定的 `[begin_time, end_time]` 时间范围内。

## 1. 核心作用与使用场景：设置好 Commit History

**作用原理：**
假设你的项目（例如 `xxx-rag`）有 10 个 commit，全都是在同一天提交的，这会导致 GitHub 的贡献图（Contributions Graph）上只有一个孤零零的绿点。通过使用这个脚本，你可以将这 10 个 commit 的时间“匀开”，分布到不同的日期中，从而让 GitHub 上的绿点看起来更丰富、更连贯。

**前提条件：**
当前项目必须存在**足够多的 commit 信息**。如果当前的 commit 数量太少，达不到你想要的时间跨度效果，可以在执行脚本前多做几次提交（例如通过多次修改 `README.md` 增加 commit 记录）。

---

## 2. 使用说明

在终端中进入你需要操作的项目目录，然后执行该脚本。

**基础命令格式：**
```bash
python xxxx/commit_reset.py "开始时间" "结束时间"
```
*💡 注意：`xxxx/commit_reset.py` 是你存放脚本的实际路径。为了避免脚本被意外提交，**强烈建议不要将此脚本放在你要操作的项目目录内部**。*

### 🌰 操作示例

假设存在以下目录结构：
* **目标项目路径**: `D:\program\forHX\ReAct_Plan-and-solve_Self-Reflection_Agent`
* **脚本存放路径**: `D:\program\forHX\commit_reset.py`

**具体步骤：**
1. 打开终端，进入目标项目目录：
   ```bash
   cd D:\program\forHX\ReAct_Plan-and-solve_Self-Reflection_Agent
   ```
2. 执行脚本，指定时间范围（例如：将项目的 commit 均匀分布到 11.1 - 11.25）：
   ```bash
   python ..\commit_reset.py "2025-11-01 11:00:00" "2025-11-25 23:30:00"
   ```

---

## 3. 收尾处理与完整工作流

调用脚本仅仅是在**本地**修改了项目的 commit 时间，并没有真正更新到 GitHub 上。下面是一个结合 Git 操作的完整闭环示例：

**Step 1. 准备脚本**
将 `commit_reset.py` 放到工作区的父目录，例如 `D:\program\forHX\`。

**Step 2. 进入工作区**
```bash
cd D:\program\forHX\
```

**Step 3. 克隆项目**
将目标项目下载到本地（如果已在本地可跳过此步）：
```bash
git clone [https://github.com/SAYURIqvq/ReAct_Plan-and-solve_Self-Reflection_Agent.git](https://github.com/SAYURIqvq/ReAct_Plan-and-solve_Self-Reflection_Agent.git)
cd ReAct_Plan-and-solve_Self-Reflection_Agent
```

**Step 4. 增加 Commit（可选）**
如果觉得 commit 数量不够，可以按喜好手动增加一些提交：
```bash
# 修改README.md或做一些微调
git add README.md
git commit -m "update README.md"
```

**Step 5. 执行时间重置脚本**
打乱并重新分配 commit 顺序与时间：
```bash
python ..\commit_reset.py "2025-11-01 11:00:00" "2025-11-25 23:30:00"
```

**Step 6. 检查并强制推送到 GitHub**
推送前，请先使用 `git log` 确认 commit 的时间和顺序是否符合预期。确认无误后，强制推送到远程仓库。
```bash
# 查看最终效果
git log

# 强制推送（⚠️ 注意：-f 是危险操作，会覆盖远程历史记录，请确保没有他人在该分支协作）
git push origin main -f
```
