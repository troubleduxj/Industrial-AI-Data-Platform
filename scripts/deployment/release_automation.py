#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布自动化工具
自动化版本发布流程，包括版本更新、变更日志生成、标签创建等
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import argparse
from typing import List, Dict, Optional

# 导入其他脚本（从 development 目录）
sys.path.append(str(Path(__file__).parent.parent / "development"))
from version_manager import VersionManager, VersionInfo
from generate_changelog import ChangelogGenerator


class ReleaseAutomation:
    """发布自动化管理器"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.version_manager = VersionManager(repo_path)
        self.changelog_generator = ChangelogGenerator(repo_path)
    
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> tuple[bool, str]:
        """执行命令"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr
    
    def check_working_directory_clean(self) -> bool:
        """检查工作目录是否干净"""
        success, output = self.run_command(["git", "status", "--porcelain"])
        if not success:
            return False
        
        return len(output.strip()) == 0
    
    def check_current_branch(self) -> str:
        """获取当前分支"""
        success, branch = self.run_command(["git", "branch", "--show-current"])
        if not success:
            raise RuntimeError("无法获取当前分支")
        return branch
    
    def create_release_branch(self, version: str) -> bool:
        """创建发布分支"""
        branch_name = f"release/v{version}"
        
        print(f"🌿 创建发布分支: {branch_name}")
        
        # 检查分支是否已存在
        success, _ = self.run_command(["git", "branch", "--list", branch_name])
        if success:
            print(f"⚠️ 分支 {branch_name} 已存在")
            return False
        
        # 创建并切换到发布分支
        success, _ = self.run_command(["git", "checkout", "-b", branch_name])
        if not success:
            print(f"❌ 创建发布分支失败")
            return False
        
        print(f"✅ 成功创建发布分支: {branch_name}")
        return True
    
    def update_version_in_files(self, version: str) -> bool:
        """更新文件中的版本号"""
        print(f"📝 更新版本号到 {version}")
        
        try:
            self.version_manager.update_version_files(version)
            return True
        except Exception as e:
            print(f"❌ 更新版本文件失败: {e}")
            return False
    
    def generate_changelog(self, version: str) -> bool:
        """生成变更日志"""
        print("📋 生成变更日志...")
        
        try:
            # 获取自上次标签以来的提交
            tags = self.version_manager.git.get_tag_list()
            last_tag = tags[0] if tags else None
            
            commits = self.changelog_generator.get_commits_between_tags(last_tag, "HEAD")
            
            if not commits:
                print("⚠️ 没有新的提交，跳过变更日志生成")
                return True
            
            # 生成变更日志部分
            changelog_section = self.changelog_generator.generate_section_for_version(
                version, commits
            )
            
            # 更新变更日志文件
            changelog_path = self.repo_path / "CHANGELOG.md"
            if changelog_path.exists():
                with open(changelog_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # 在第一个 ## 之前插入新内容
                if "## [" in existing_content:
                    parts = existing_content.split("## [", 1)
                    new_content = parts[0] + changelog_section + "## [" + parts[1]
                else:
                    new_content = existing_content + changelog_section
            else:
                header = """# 变更日志

本文档记录了项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

"""
                new_content = header + changelog_section
            
            with open(changelog_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ 变更日志生成完成")
            return True
            
        except Exception as e:
            print(f"❌ 生成变更日志失败: {e}")
            return False
    
    def run_tests(self) -> bool:
        """运行测试"""
        print("🧪 运行测试...")
        
        # Python测试
        if (self.repo_path / "tests").exists():
            print("运行Python测试...")
            success, output = self.run_command(["python", "-m", "pytest", "tests/", "-v"])
            if not success:
                print(f"❌ Python测试失败: {output}")
                return False
            print("✅ Python测试通过")
        
        # 前端测试
        if (self.repo_path / "web" / "package.json").exists():
            print("运行前端测试...")
            success, output = self.run_command(["npm", "test"], cwd=self.repo_path / "web")
            if not success:
                print(f"❌ 前端测试失败: {output}")
                return False
            print("✅ 前端测试通过")
        
        return True
    
    def build_project(self) -> bool:
        """构建项目"""
        print("🔨 构建项目...")
        
        # 前端构建
        if (self.repo_path / "web" / "package.json").exists():
            print("构建前端...")
            success, output = self.run_command(["npm", "run", "build"], cwd=self.repo_path / "web")
            if not success:
                print(f"❌ 前端构建失败: {output}")
                return False
            print("✅ 前端构建完成")
        
        # Docker构建
        if (self.repo_path / "Dockerfile").exists():
            print("构建Docker镜像...")
            success, output = self.run_command([
                "docker", "build", "-t", f"device-monitor:latest", "."
            ])
            if not success:
                print(f"❌ Docker构建失败: {output}")
                return False
            print("✅ Docker镜像构建完成")
        
        return True
    
    def commit_release_changes(self, version: str) -> bool:
        """提交发布变更"""
        print("💾 提交发布变更...")
        
        # 添加所有变更
        success, _ = self.run_command(["git", "add", "."])
        if not success:
            print("❌ 添加文件失败")
            return False
        
        # 提交变更
        commit_message = f"chore(release): 准备发布 v{version}"
        success, _ = self.run_command(["git", "commit", "-m", commit_message])
        if not success:
            print("❌ 提交变更失败")
            return False
        
        print("✅ 发布变更已提交")
        return True
    
    def create_tag(self, version: str) -> bool:
        """创建版本标签"""
        print(f"🏷️ 创建版本标签 v{version}")
        
        tag_message = f"Release version {version}"
        success, _ = self.run_command(["git", "tag", "-a", f"v{version}", "-m", tag_message])
        if not success:
            print("❌ 创建标签失败")
            return False
        
        print(f"✅ 成功创建标签 v{version}")
        return True
    
    def push_release(self, version: str) -> bool:
        """推送发布"""
        print("📤 推送发布...")
        
        # 推送分支
        branch_name = f"release/v{version}"
        success, _ = self.run_command(["git", "push", "origin", branch_name])
        if not success:
            print("❌ 推送分支失败")
            return False
        
        # 推送标签
        success, _ = self.run_command(["git", "push", "origin", f"v{version}"])
        if not success:
            print("❌ 推送标签失败")
            return False
        
        print("✅ 发布推送完成")
        return True
    
    def merge_to_main(self, version: str) -> bool:
        """合并到主分支"""
        print("🔀 合并到主分支...")
        
        # 切换到main分支
        success, _ = self.run_command(["git", "checkout", "main"])
        if not success:
            print("❌ 切换到main分支失败")
            return False
        
        # 拉取最新代码
        success, _ = self.run_command(["git", "pull", "origin", "main"])
        if not success:
            print("❌ 拉取main分支失败")
            return False
        
        # 合并发布分支
        branch_name = f"release/v{version}"
        success, _ = self.run_command(["git", "merge", "--no-ff", branch_name])
        if not success:
            print("❌ 合并发布分支失败")
            return False
        
        # 推送main分支
        success, _ = self.run_command(["git", "push", "origin", "main"])
        if not success:
            print("❌ 推送main分支失败")
            return False
        
        print("✅ 成功合并到main分支")
        return True
    
    def merge_to_develop(self, version: str) -> bool:
        """合并到开发分支"""
        print("🔀 合并到开发分支...")
        
        # 切换到develop分支
        success, _ = self.run_command(["git", "checkout", "develop"])
        if not success:
            print("⚠️ develop分支不存在，跳过合并")
            return True
        
        # 拉取最新代码
        success, _ = self.run_command(["git", "pull", "origin", "develop"])
        if not success:
            print("❌ 拉取develop分支失败")
            return False
        
        # 合并发布分支
        branch_name = f"release/v{version}"
        success, _ = self.run_command(["git", "merge", "--no-ff", branch_name])
        if not success:
            print("❌ 合并到develop分支失败")
            return False
        
        # 推送develop分支
        success, _ = self.run_command(["git", "push", "origin", "develop"])
        if not success:
            print("❌ 推送develop分支失败")
            return False
        
        print("✅ 成功合并到develop分支")
        return True
    
    def cleanup_release_branch(self, version: str) -> bool:
        """清理发布分支"""
        print("🧹 清理发布分支...")
        
        branch_name = f"release/v{version}"
        
        # 删除本地分支
        success, _ = self.run_command(["git", "branch", "-d", branch_name])
        if not success:
            print("⚠️ 删除本地发布分支失败")
        
        # 删除远程分支
        success, _ = self.run_command(["git", "push", "origin", "--delete", branch_name])
        if not success:
            print("⚠️ 删除远程发布分支失败")
        
        print("✅ 发布分支清理完成")
        return True
    
    def generate_release_notes(self, version: str) -> bool:
        """生成发布说明"""
        print("📄 生成发布说明...")
        
        try:
            tags = self.version_manager.git.get_tag_list()
            last_tag = tags[1] if len(tags) > 1 else None  # 获取上一个标签
            
            release_notes = self.changelog_generator.generate_release_notes(version, last_tag)
            
            # 保存发布说明
            release_notes_path = self.repo_path / f"RELEASE_NOTES_v{version}.md"
            with open(release_notes_path, 'w', encoding='utf-8') as f:
                f.write(release_notes)
            
            print(f"✅ 发布说明已保存到: {release_notes_path}")
            return True
            
        except Exception as e:
            print(f"❌ 生成发布说明失败: {e}")
            return False
    
    def create_release(
        self,
        version_type: str = "auto",
        prerelease: Optional[str] = None,
        skip_tests: bool = False,
        skip_build: bool = False,
        dry_run: bool = False
    ) -> bool:
        """创建完整发布"""
        print("🚀 开始自动化发布流程...")
        print(f"发布类型: {version_type}")
        if prerelease:
            print(f"预发布标识: {prerelease}")
        if dry_run:
            print("🔍 预览模式（不会实际执行）")
        
        try:
            # 1. 检查工作目录
            if not self.check_working_directory_clean():
                print("❌ 工作目录不干净，请先提交或暂存变更")
                return False
            
            # 2. 检查当前分支
            current_branch = self.check_current_branch()
            if current_branch not in ["develop", "main", "master"]:
                print(f"❌ 当前分支 '{current_branch}' 不适合发布，请切换到 develop 或 main 分支")
                return False
            
            # 3. 计算版本号
            current_version = self.version_manager.get_current_version()
            print(f"当前版本: v{current_version}")
            
            # 获取提交信息来计算版本
            latest_tag = self.version_manager.git.get_latest_tag()
            commit_lines = self.version_manager.git.get_commits_since_tag(latest_tag)
            commits = [self.version_manager.git.parse_commit(line) for line in commit_lines]
            commits = [c for c in commits if c is not None]
            
            if not commits:
                print("❌ 没有新的提交，无需发布")
                return False
            
            if version_type == "auto":
                next_version = self.version_manager.calculate_next_version(current_version, commits)
            elif version_type == "major":
                next_version = VersionInfo(current_version.major + 1, 0, 0)
            elif version_type == "minor":
                next_version = VersionInfo(current_version.major, current_version.minor + 1, 0)
            elif version_type == "patch":
                next_version = VersionInfo(current_version.major, current_version.minor, current_version.patch + 1)
            else:
                raise ValueError(f"不支持的版本类型: {version_type}")
            
            if prerelease:
                next_version.prerelease = prerelease
            
            version_str = str(next_version)
            print(f"下一个版本: v{version_str}")
            
            if dry_run:
                print("🔍 预览模式，显示将要执行的操作:")
                print(f"  - 创建发布分支: release/v{version_str}")
                print(f"  - 更新版本文件到: {version_str}")
                print(f"  - 生成变更日志")
                if not skip_tests:
                    print(f"  - 运行测试")
                if not skip_build:
                    print(f"  - 构建项目")
                print(f"  - 创建标签: v{version_str}")
                print(f"  - 推送到远程仓库")
                return True
            
            # 4. 创建发布分支
            if not self.create_release_branch(version_str):
                return False
            
            # 5. 更新版本文件
            if not self.update_version_in_files(version_str):
                return False
            
            # 6. 生成变更日志
            if not self.generate_changelog(version_str):
                return False
            
            # 7. 运行测试
            if not skip_tests:
                if not self.run_tests():
                    print("❌ 测试失败，发布中止")
                    return False
            
            # 8. 构建项目
            if not skip_build:
                if not self.build_project():
                    print("❌ 构建失败，发布中止")
                    return False
            
            # 9. 提交发布变更
            if not self.commit_release_changes(version_str):
                return False
            
            # 10. 创建标签
            if not self.create_tag(version_str):
                return False
            
            # 11. 推送发布
            if not self.push_release(version_str):
                return False
            
            # 12. 合并到主分支
            if not self.merge_to_main(version_str):
                return False
            
            # 13. 合并到开发分支
            if not self.merge_to_develop(version_str):
                return False
            
            # 14. 生成发布说明
            if not self.generate_release_notes(version_str):
                return False
            
            # 15. 清理发布分支
            if not self.cleanup_release_branch(version_str):
                return False
            
            print("🎉 发布流程完成！")
            print(f"✅ 版本 v{version_str} 已成功发布")
            print(f"📋 发布说明: RELEASE_NOTES_v{version_str}.md")
            print(f"🏷️ Git标签: v{version_str}")
            
            return True
            
        except Exception as e:
            print(f"❌ 发布过程中出现错误: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="发布自动化工具")
    parser.add_argument("--repo", default=".", help="仓库路径")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 创建发布命令
    release_parser = subparsers.add_parser("release", help="创建自动化发布")
    release_parser.add_argument(
        "--type",
        choices=["auto", "major", "minor", "patch"],
        default="auto",
        help="版本类型"
    )
    release_parser.add_argument("--prerelease", help="预发布标识 (alpha, beta, rc)")
    release_parser.add_argument("--skip-tests", action="store_true", help="跳过测试")
    release_parser.add_argument("--skip-build", action="store_true", help="跳过构建")
    release_parser.add_argument("--dry-run", action="store_true", help="预览模式")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    automation = ReleaseAutomation(args.repo)
    
    try:
        if args.command == "release":
            success = automation.create_release(
                version_type=args.type,
                prerelease=args.prerelease,
                skip_tests=args.skip_tests,
                skip_build=args.skip_build,
                dry_run=args.dry_run
            )
            
            if not success:
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()