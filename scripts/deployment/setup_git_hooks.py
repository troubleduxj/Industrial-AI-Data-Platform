#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Hooks 设置工具
自动设置项目的Git钩子，包括提交消息验证、代码检查等
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse


class GitHooksManager:
    """Git钩子管理器"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.hooks_dir = self.repo_path / ".git" / "hooks"
        self.scripts_dir = self.repo_path / "scripts" / "git-hooks"
        
        # 确保hooks目录存在
        self.hooks_dir.mkdir(exist_ok=True)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
    
    def create_commit_msg_hook(self):
        """创建提交消息验证钩子"""
        hook_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git commit-msg hook
验证提交消息格式是否符合 Conventional Commits 规范
"""

import sys
import re
from pathlib import Path

def validate_commit_message(message):
    """验证提交消息格式"""
    # Conventional Commits 格式: type(scope): description
    pattern = r'^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?: .{1,50}'
    
    lines = message.strip().split('\\n')
    if not lines:
        return False, "提交消息不能为空"
    
    subject = lines[0]
    
    # 检查主题行格式
    if not re.match(pattern, subject):
        return False, f"""提交消息格式不正确！

正确格式: <type>[optional scope]: <description>

类型 (type):
  feat:     新功能
  fix:      错误修复
  docs:     文档更新
  style:    代码格式化
  refactor: 代码重构
  perf:     性能优化
  test:     测试相关
  chore:    其他变更
  ci:       CI/CD相关
  build:    构建相关
  revert:   回滚变更

示例:
  feat: 添加用户登录功能
  fix(auth): 修复登录验证问题
  docs: 更新API文档
  
当前提交消息: {subject}"""
    
    # 检查主题行长度
    if len(subject) > 72:
        return False, f"主题行过长 ({len(subject)} 字符)，建议不超过72字符"
    
    # 检查是否以大写字母开头（描述部分）
    description_part = subject.split(': ', 1)[1] if ': ' in subject else ''
    if description_part and description_part[0].isupper():
        return False, "描述部分应以小写字母开头"
    
    # 检查是否以句号结尾
    if description_part.endswith('.'):
        return False, "描述部分不应以句号结尾"
    
    return True, "提交消息格式正确"

def main():
    if len(sys.argv) != 2:
        print("Usage: commit-msg <commit-msg-file>")
        sys.exit(1)
    
    commit_msg_file = Path(sys.argv[1])
    
    try:
        message = commit_msg_file.read_text(encoding='utf-8')
        is_valid, error_msg = validate_commit_message(message)
        
        if not is_valid:
            print(f"❌ {error_msg}")
            sys.exit(1)
        else:
            print("✅ 提交消息格式正确")
            sys.exit(0)
    
    except Exception as e:
        print(f"❌ 验证提交消息时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        hook_path = self.hooks_dir / "commit-msg"
        with open(hook_path, 'w', encoding='utf-8') as f:
            f.write(hook_content)
        
        # 设置执行权限
        hook_path.chmod(0o755)
        print("✅ 创建 commit-msg 钩子")
    
    def create_pre_commit_hook(self):
        """创建预提交钩子"""
        hook_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git pre-commit hook
在提交前执行代码检查和测试
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(command, cwd=None):
    """执行命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_python_files():
    """检查Python文件"""
    print("🔍 检查Python文件...")
    
    # 获取暂存的Python文件
    success, output = run_command("git diff --cached --name-only --diff-filter=ACM | grep '\\.py$'")
    if not success:
        return True  # 没有Python文件变更
    
    python_files = output.strip().split('\\n') if output.strip() else []
    if not python_files:
        return True
    
    print(f"发现 {len(python_files)} 个Python文件变更")
    
    # 检查语法错误
    for file_path in python_files:
        if not Path(file_path).exists():
            continue
        
        success, error = run_command(f"python -m py_compile {file_path}")
        if not success:
            print(f"❌ 语法错误 {file_path}: {error}")
            return False
    
    print("✅ Python文件语法检查通过")
    return True

def check_javascript_files():
    """检查JavaScript文件"""
    print("🔍 检查JavaScript文件...")
    
    # 获取暂存的JS/Vue文件
    success, output = run_command("git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(js|vue|ts)$'")
    if not success:
        return True  # 没有JS文件变更
    
    js_files = output.strip().split('\\n') if output.strip() else []
    if not js_files:
        return True
    
    print(f"发现 {len(js_files)} 个JavaScript/Vue文件变更")
    
    # 检查是否有ESLint
    if Path("web/node_modules/.bin/eslint").exists():
        for file_path in js_files:
            if not Path(file_path).exists():
                continue
            
            success, error = run_command(f"web/node_modules/.bin/eslint {file_path}", cwd=".")
            if not success:
                print(f"❌ ESLint检查失败 {file_path}: {error}")
                return False
        
        print("✅ JavaScript文件ESLint检查通过")
    else:
        print("⚠️ 未找到ESLint，跳过JavaScript文件检查")
    
    return True

def check_large_files():
    """检查大文件"""
    print("🔍 检查大文件...")
    
    success, output = run_command("git diff --cached --name-only --diff-filter=ACM")
    if not success:
        return True
    
    files = output.strip().split('\\n') if output.strip() else []
    large_files = []
    
    for file_path in files:
        if not Path(file_path).exists():
            continue
        
        file_size = Path(file_path).stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            large_files.append((file_path, file_size))
    
    if large_files:
        print("❌ 发现大文件:")
        for file_path, size in large_files:
            print(f"  {file_path}: {size / 1024 / 1024:.2f}MB")
        print("请考虑使用Git LFS或减小文件大小")
        return False
    
    print("✅ 文件大小检查通过")
    return True

def check_secrets():
    """检查敏感信息"""
    print("🔍 检查敏感信息...")
    
    # 敏感信息模式
    secret_patterns = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
        r'-----BEGIN [A-Z ]+-----',
    ]
    
    success, output = run_command("git diff --cached --name-only --diff-filter=ACM")
    if not success:
        return True
    
    files = output.strip().split('\\n') if output.strip() else []
    
    for file_path in files:
        if not Path(file_path).exists():
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern in secret_patterns:
                import re
                if re.search(pattern, content, re.IGNORECASE):
                    print(f"❌ 可能包含敏感信息 {file_path}")
                    print(f"  匹配模式: {pattern}")
                    return False
        
        except (UnicodeDecodeError, PermissionError):
            # 跳过二进制文件或无权限文件
            continue
    
    print("✅ 敏感信息检查通过")
    return True

def main():
    print("🚀 执行预提交检查...")
    
    checks = [
        check_python_files,
        check_javascript_files,
        check_large_files,
        check_secrets,
    ]
    
    for check in checks:
        if not check():
            print("❌ 预提交检查失败")
            sys.exit(1)
    
    print("✅ 所有预提交检查通过")
    sys.exit(0)

if __name__ == "__main__":
    main()
'''
        
        hook_path = self.hooks_dir / "pre-commit"
        with open(hook_path, 'w', encoding='utf-8') as f:
            f.write(hook_content)
        
        # 设置执行权限
        hook_path.chmod(0o755)
        print("✅ 创建 pre-commit 钩子")
    
    def create_pre_push_hook(self):
        """创建预推送钩子"""
        hook_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git pre-push hook
在推送前执行测试和检查
"""

import sys
import subprocess
import os

def run_command(command, cwd=None):
    """执行命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def run_tests():
    """运行测试"""
    print("🧪 运行测试...")
    
    # 检查是否有pytest
    success, _ = run_command("which pytest")
    if success:
        print("运行Python测试...")
        success, output = run_command("python -m pytest tests/ -v --tb=short")
        if not success:
            print(f"❌ Python测试失败: {output}")
            return False
        print("✅ Python测试通过")
    
    # 检查是否有npm test
    if os.path.exists("web/package.json"):
        print("运行前端测试...")
        success, output = run_command("npm test", cwd="web")
        if not success:
            print(f"❌ 前端测试失败: {output}")
            return False
        print("✅ 前端测试通过")
    
    return True

def check_branch_protection():
    """检查分支保护"""
    print("🔒 检查分支保护...")
    
    # 获取当前分支
    success, current_branch = run_command("git branch --show-current")
    if not success:
        return True
    
    current_branch = current_branch.strip()
    
    # 检查是否直接推送到保护分支
    protected_branches = ["main", "master", "develop"]
    if current_branch in protected_branches:
        print(f"❌ 不允许直接推送到保护分支: {current_branch}")
        print("请创建feature分支并通过Pull Request合并")
        return False
    
    print("✅ 分支保护检查通过")
    return True

def main():
    print("🚀 执行预推送检查...")
    
    # 读取推送信息
    remote = sys.argv[1] if len(sys.argv) > 1 else "origin"
    url = sys.argv[2] if len(sys.argv) > 2 else ""
    
    print(f"推送到: {remote} ({url})")
    
    checks = [
        check_branch_protection,
        run_tests,
    ]
    
    for check in checks:
        if not check():
            print("❌ 预推送检查失败")
            sys.exit(1)
    
    print("✅ 所有预推送检查通过")
    sys.exit(0)

if __name__ == "__main__":
    main()
'''
        
        hook_path = self.hooks_dir / "pre-push"
        with open(hook_path, 'w', encoding='utf-8') as f:
            f.write(hook_content)
        
        # 设置执行权限
        hook_path.chmod(0o755)
        print("✅ 创建 pre-push 钩子")
    
    def create_post_commit_hook(self):
        """创建提交后钩子"""
        hook_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git post-commit hook
提交后执行的操作，如通知、统计等
"""

import subprocess
import os
from datetime import datetime

def run_command(command):
    """执行命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def log_commit_info():
    """记录提交信息"""
    # 获取最新提交信息
    success, commit_hash = run_command("git rev-parse HEAD")
    if not success:
        return
    
    success, commit_msg = run_command("git log -1 --pretty=format:'%s'")
    if not success:
        return
    
    success, author = run_command("git log -1 --pretty=format:'%an <%ae>'")
    if not success:
        return
    
    # 记录到日志文件
    log_file = ".git/commit_log.txt"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} | {commit_hash[:8]} | {author} | {commit_msg}\\n")

def update_commit_count():
    """更新提交计数"""
    success, count = run_command("git rev-list --count HEAD")
    if success:
        with open(".git/commit_count.txt", 'w') as f:
            f.write(count)

def main():
    print("📝 记录提交信息...")
    log_commit_info()
    update_commit_count()
    print("✅ 提交后处理完成")

if __name__ == "__main__":
    main()
'''
        
        hook_path = self.hooks_dir / "post-commit"
        with open(hook_path, 'w', encoding='utf-8') as f:
            f.write(hook_content)
        
        # 设置执行权限
        hook_path.chmod(0o755)
        print("✅ 创建 post-commit 钩子")
    
    def setup_all_hooks(self):
        """设置所有钩子"""
        print("🔧 设置Git钩子...")
        
        self.create_commit_msg_hook()
        self.create_pre_commit_hook()
        self.create_pre_push_hook()
        self.create_post_commit_hook()
        
        print("✅ 所有Git钩子设置完成")
    
    def remove_hooks(self):
        """移除所有钩子"""
        hooks = ["commit-msg", "pre-commit", "pre-push", "post-commit"]
        
        for hook in hooks:
            hook_path = self.hooks_dir / hook
            if hook_path.exists():
                hook_path.unlink()
                print(f"🗑️ 移除 {hook} 钩子")
        
        print("✅ 所有Git钩子已移除")
    
    def list_hooks(self):
        """列出已安装的钩子"""
        print("📋 已安装的Git钩子:")
        
        if not self.hooks_dir.exists():
            print("  无")
            return
        
        hooks = ["commit-msg", "pre-commit", "pre-push", "post-commit"]
        installed_hooks = []
        
        for hook in hooks:
            hook_path = self.hooks_dir / hook
            if hook_path.exists() and hook_path.is_file():
                installed_hooks.append(hook)
        
        if installed_hooks:
            for hook in installed_hooks:
                print(f"  ✅ {hook}")
        else:
            print("  无")
    
    def test_hooks(self):
        """测试钩子"""
        print("🧪 测试Git钩子...")
        
        # 测试commit-msg钩子
        commit_msg_hook = self.hooks_dir / "commit-msg"
        if commit_msg_hook.exists():
            print("测试 commit-msg 钩子...")
            
            # 创建临时提交消息文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write("feat: 测试提交消息")
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    [str(commit_msg_hook), temp_file],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("  ✅ commit-msg 钩子测试通过")
                else:
                    print(f"  ❌ commit-msg 钩子测试失败: {result.stderr}")
            finally:
                os.unlink(temp_file)
        
        print("✅ 钩子测试完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Git钩子管理工具")
    parser.add_argument("--repo", default=".", help="仓库路径")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 安装钩子
    subparsers.add_parser("install", help="安装所有Git钩子")
    
    # 移除钩子
    subparsers.add_parser("remove", help="移除所有Git钩子")
    
    # 列出钩子
    subparsers.add_parser("list", help="列出已安装的钩子")
    
    # 测试钩子
    subparsers.add_parser("test", help="测试钩子")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = GitHooksManager(args.repo)
    
    try:
        if args.command == "install":
            manager.setup_all_hooks()
        elif args.command == "remove":
            manager.remove_hooks()
        elif args.command == "list":
            manager.list_hooks()
        elif args.command == "test":
            manager.test_hooks()
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()