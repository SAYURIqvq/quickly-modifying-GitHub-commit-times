#!/usr/bin/env python3
"""
python commit_reset.py "2024-01-01 12:00:00" "2024-02-01 12:00:00"
"""

import subprocess
import sys
import os
import re
import time
import random
from datetime import datetime, timedelta

def run_command(cmd, cwd=None, capture_output=True, env=None):
    """执行shell命令并返回结果"""
    print(f"  执行: {cmd}")
    
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=merged_env,
            timeout=120
        )
        if result.returncode != 0 and result.stderr:
            print(f"    警告: {result.stderr.strip()}")
        return result
    except subprocess.TimeoutExpired:
        print("  错误: 命令执行超时")
        return None
    except Exception as e:
        print(f"  错误: {e}")
        return None

def find_git_root(start_path):
    """查找git仓库根目录"""
    current = os.path.abspath(start_path)
    while current:
        if os.path.isdir(os.path.join(current, '.git')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None

def get_commit_count(repo_path):
    """获取当前分支的commit数量"""
    cmd = 'git rev-list --count HEAD'
    result = run_command(cmd, cwd=repo_path)
    if result and result.returncode == 0:
        return int(result.stdout.strip())
    return 0


def get_commit_list(repo_path, num):
    """获取前num个commit的SHA列表(从旧到新)"""
    # 先获取所有commit的SHA (从旧到新),然后取前num个
    cmd = f'git log --format=%H --reverse'
    result = run_command(cmd, cwd=repo_path)
    if result and result.returncode == 0:
        all_commits = [c.strip() for c in result.stdout.strip().split('\n') if c.strip()]
        return all_commits[:num]
    return []


# ==================== generate_random_times.py 的核心逻辑 ====================

def parse_time(time_str):
    """解析时间字符串为datetime对象"""
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        raise ValueError(f"时间格式错误: {time_str}, 应为 'YYYY-MM-DD HH:MM:SS'") from e


def is_hour_valid(dt):
    """检查小时是否在11:00-23:30范围内"""
    hour = dt.hour
    # 小时必须在 11-23 之间
    if hour < 11 or hour > 23:
        return False
    # 如果小时是23,则分钟必须<=30
    if hour == 23 and dt.minute > 30:
        return False
    return True


def generate_random_time(begin_time, end_time):
    """在指定时间范围内生成一个随机时间点,小时限制在11:00-23:30"""
    begin_ts = begin_time.timestamp()
    end_ts = end_time.timestamp()
    
    max_attempts = 1000
    for _ in range(max_attempts):
        # 生成随机时间戳
        random_ts = random.uniform(begin_ts, end_ts)
        random_dt = datetime.fromtimestamp(random_ts)
        
        # 检查小时是否在有效范围内
        if is_hour_valid(random_dt):
            return random_dt
    
    raise ValueError("无法在指定时间范围内找到有效的小时(11:00-23:30)")


def format_time(dt):
    """将datetime对象格式化为字符串"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def generate_random_times(begin_time_str, end_time_str, num):
    """生成num个随机时间点"""
    begin_time = parse_time(begin_time_str)
    end_time = parse_time(end_time_str)
    
    # 验证时间范围
    if begin_time >= end_time:
        raise ValueError("begin_time 必须早于 end_time")
    
    # 检查并调整时间范围
    if not is_hour_valid(begin_time):
        print(f"警告: 起始时间 {format_time(begin_time)} 的小时不在有效范围(11:00-23:30)内")
        print("        将自动调整为11:00:00")
        begin_time = begin_time.replace(hour=11, minute=0, second=0)
    
    if not is_hour_valid(end_time):
        print(f"警告: 结束时间 {format_time(end_time)} 的小时不在有效范围(11:00-23:30)内")
        print("        将自动调整为23:30:00")
        end_time = end_time.replace(hour=23, minute=30, second=0)
    
    # 再次验证调整后的时间范围
    if begin_time >= end_time:
        raise ValueError("调整后的时间范围无效")
    
    # 生成随机时间点
    random.seed()
    
    generated_times = []
    for i in range(num):
        random_time = generate_random_time(begin_time, end_time)
        generated_times.append(random_time)
    
    # 按时间从小到大排序
    generated_times.sort()
    
    return [format_time(dt) for dt in generated_times]

def handle_local_changes(repo_path):
    """检查并处理本地未提交的更改"""
    cmd = 'git status --porcelain'
    result = run_command(cmd, cwd=repo_path)
    
    if not result or result.returncode != 0:
        return True
    
    changes = result.stdout.strip()
    if not changes:
        return True
    
    print(f"检测到本地有未提交的更改:")
    print(f"  {changes}")
    
    # 自动提交这些更改
    cmd = 'git add -A'
    result = run_command(cmd, cwd=repo_path)
    
    if result and result.returncode == 0:
        cmd = 'git commit -m "temp: auto-commit before date reset"'
        result = run_command(cmd, cwd=repo_path)
        
        if result and result.returncode == 0:
            print("  ✓ 已自动提交本地更改")
            return True
        else:
            # 尝试stash
            print("  自动提交失败,尝试stash...")
            cmd = 'git stash push -m "temp: auto-stash before date reset"'
            result = run_command(cmd, cwd=repo_path)
            if result and result.returncode == 0:
                print("  ✓ 已stash本地更改")
                return True
    
    return False


def show_commit_info(commit_sha, repo_path):
    """显示commit详细信息"""
    cmd = f'git show --format=fuller {commit_sha}'
    result = run_command(cmd, cwd=repo_path)
    return result.stdout if result and result.returncode == 0 else None


def modify_commit_date(commit_sha, new_time, repo_path):
    """
    修改指定commit的AuthorDate和CommitDate
    """
    print(f"\n{'='*60}")
    print(f"开始修改commit日期")
    print(f"  目标commit: {commit_sha[:7]}...")
    print(f"  新时间: {new_time}")
    print(f"  仓库: {repo_path}")
    print(f"{'='*60}\n")
    
    # 先处理本地更改
    print("检查本地更改...")
    if not handle_local_changes(repo_path):
        print("错误: 无法处理本地更改")
        return False, None
    
    # 验证commit是否存在
    cmd = f'git cat-file -t {commit_sha}'
    result = run_command(cmd, cwd=repo_path)
    if not result or result.returncode != 0:
        print(f"错误: commit {commit_sha} 不存在")
        return False, None
    
    # 显示原始commit信息
    print("原始commit信息:")
    info = show_commit_info(commit_sha, repo_path)
    if info:
        for line in info.split('\n')[:8]:
            print(f"  {line}")
    
    # 获取当前分支
    cmd = 'git rev-parse --abbrev-ref HEAD'
    result = run_command(cmd, cwd=repo_path)
    current_branch = result.stdout.strip() if result and result.returncode == 0 else "HEAD"
    print(f"\n当前分支: {current_branch}")
    
    # 检查是否为HEAD
    cmd = 'git rev-parse HEAD'
    result = run_command(cmd, cwd=repo_path)
    head_sha = result.stdout.strip() if result and result.returncode == 0 else None
    
    cmd = f'git rev-parse {commit_sha}'
    result = run_command(cmd, cwd=repo_path)
    full_commit_sha = result.stdout.strip() if result and result.returncode == 0 else commit_sha
    
    is_head = (full_commit_sha == head_sha)
    print(f"目标commit是否为HEAD: {is_head}")
    
    # 创建临时分支
    temp_branch = f"temp-fix-{int(time.time())}"
    cmd = f'git checkout -b {temp_branch} {commit_sha}'
    result = run_command(cmd, cwd=repo_path)
    if not result or result.returncode != 0:
        print("错误: 无法创建临时分支")
        return False, None
    
    # 修改日期
    env = {
        'GIT_COMMITTER_DATE': new_time,
        'GIT_AUTHOR_DATE': new_time
    }
    
    cmd = f'git commit --amend --no-edit --date "{new_time}"'
    result = run_command(cmd, cwd=repo_path, env=env)
    
    if not result or result.returncode != 0:
        print("错误: 修改日期失败")
        run_command(f'git checkout {current_branch}', cwd=repo_path)
        run_command(f'git branch -D {temp_branch}', cwd=repo_path)
        return False, None
    
    print("✓ 日期修改成功!")
    
    # 获取新的commit SHA
    cmd = 'git rev-parse HEAD'
    result = run_command(cmd, cwd=repo_path)
    new_commit_sha = result.stdout.strip() if result else None
    print(f"新commit SHA: {new_commit_sha}")
    
    # 回到原分支
    print("\n重放后续commits...")
    cmd = f'git checkout {current_branch}'
    run_command(cmd, cwd=repo_path)
    
    subsequent_commits = []
    if not is_head:
        cmd = f'git log --format=%H --reverse {commit_sha}..HEAD'
        result = run_command(cmd, cwd=repo_path)
        
        if result and result.returncode == 0:
            subsequent_commits = [c.strip() for c in result.stdout.strip().split('\n') if c.strip()]
    
    if subsequent_commits:
        print(f"需要重放 {len(subsequent_commits)} 个后续commit...")
        
        cmd = f'git reset --hard {new_commit_sha}'
        run_command(cmd, cwd=repo_path)
        
        for i, commit in enumerate(subsequent_commits):
            cmd = f'git log -1 --format="%ci" {commit}'
            result = run_command(cmd, cwd=repo_path)
            orig_date = result.stdout.strip() if result and result.returncode == 0 else new_time
            
            cmd = f'git cherry-pick {commit}'
            result = run_command(cmd, cwd=repo_path)
            
            if result and result.returncode == 0:
                env = {'GIT_COMMITTER_DATE': orig_date, 'GIT_AUTHOR_DATE': orig_date}
                cmd = f'git commit --amend --no-edit --date "{orig_date}"'
                run_command(cmd, cwd=repo_path, env=env)
                print(f"  [{i+1}/{len(subsequent_commits)}] 重放commit成功")
    else:
        print("无后续commit,直接更新分支指向")
        cmd = f'git reset --hard {new_commit_sha}'
        run_command(cmd, cwd=repo_path)
    
    # 清理临时分支
    cmd = f'git branch -D {temp_branch}'
    run_command(cmd, cwd=repo_path)
    
    # 获取最终commit SHA
    cmd = 'git rev-parse HEAD'
    result = run_command(cmd, cwd=repo_path)
    final_sha = result.stdout.strip() if result and result.returncode == 0 else new_commit_sha
    
    print(f"\n{'='*60}")
    print("✓ 日期修改完成!")
    print(f"  原始commit: {commit_sha[:7]}...")
    print(f"  新commit:   {final_sha[:7]}...")
    print(f"  设置时间:   {new_time}")
    print(f"{'='*60}")
    
    return True, final_sha

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print(__doc__)
        print("\n使用示例:")
        print('  python batch_commit_date_reset.py "2024-01-01 11:00:00" "2024-12-31 23:30:00"')
        print('  python batch_commit_date_reset.py "2024-01-01 11:00:00" "2024-12-31 23:30:00" 5')
        sys.exit(1)
    
    begin_time = sys.argv[1].strip()
    end_time = sys.argv[2].strip()
    num = None
    if len(sys.argv) == 4:
        try:
            num = int(sys.argv[3].strip())
        except ValueError:
            print("错误: num 必须为整数")
            sys.exit(1)
    
    # 验证时间格式
    try:
        parse_time(begin_time)
        parse_time(end_time)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)
    
    # 查找git仓库
    git_root = find_git_root(os.getcwd())
    if not git_root:
        print("错误: 无法找到git仓库")
        sys.exit(1)
    
    print(f"Git仓库根目录: {git_root}")
    print(f"开始时间: {begin_time}")
    print(f"结束时间: {end_time}")
    
    # 获取commit数量
    if num is None:
        commit_count = get_commit_count(git_root)
        print(f"未指定num参数，将修改当前分支全部 {commit_count} 个commit")
        num = commit_count
    else:
        if num <= 0:
            print("错误: num 必须为正整数")
            sys.exit(1)
        print(f"将修改前 {num} 个commit")
    
    # 获取commit列表 (从旧到新)
    print(f"\n获取前 {num} 个commit...")
    commits = get_commit_list(git_root, num)
    
    if len(commits) == 0:
        print("错误: 无法获取commit列表，请确保当前目录是git仓库且有commit")
        sys.exit(1)
    
    if len(commits) < num:
        print(f"警告: 当前分支只有 {len(commits)} 个commit，将修改所有commit")
        num = len(commits)
    
    print(f"找到 {len(commits)} 个commit")
    for i, commit in enumerate(commits):
        print(f"  {i+1}. {commit[:7]}...")
    
    # 生成随机时间点
    print(f"\n生成 {num} 个随机时间点...")
    try:
        random_times = generate_random_times(begin_time, end_time, num)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)
    
    print("生成的时间点 (已排序):")
    for i, t in enumerate(random_times):
        print(f"  {i+1}. {t}")
    
    # 循环修改每个commit的日期
    print(f"\n{'='*60}")
    print("开始批量修改commit日期")
    print(f"{'='*60}")
    
    success_count = 0
    fail_count = 0
    
    # 按顺序修改每个commit (从旧到新)
    # 由于modify_commit_date会改变commit SHA，每次需要重新获取最新的commit SHA
    for i in range(num):
        # 每次重新获取commit列表，因为之前的修改会改变commit SHA
        current_commits = get_commit_list(git_root, num)
        if i >= len(current_commits):
            print(f"警告: 无法获取第 {i+1} 个commit，跳过")
            continue
        
        commit_sha = current_commits[i]
        new_time = random_times[i]
        
        print(f"\n{'='*60}")
        print(f"[{i+1}/{num}] 修改commit: {commit_sha[:7]}... -> 时间: {new_time}")
        print(f"{'='*60}")
        
        success, new_sha = modify_commit_date(commit_sha, new_time, git_root)
        
        if success:
            success_count += 1
            print(f"✓ 成功修改第 {i+1} 个commit")
        else:
            fail_count += 1
            print(f"✗ 失败修改第 {i+1} 个commit")
    
    # 输出结果
    print(f"\n{'='*60}")
    print("批量修改完成!")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"{'='*60}")
    
    if fail_count > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
