#!/usr/bin/env python3
"""免费评估版：只生成已暂存变更的路径检查清单；不上传代码。"""
import argparse
import json
import subprocess
from pathlib import Path

VERSION = '0.1.0-trial'

def run_git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Git 执行失败')
    return result.stdout

def report(repo):
    root = run_git(repo, 'rev-parse', '--show-toplevel').strip()
    parts = run_git(root, 'diff', '--cached', '--name-status', '-z', '--no-renames').split('\0')
    entries = []
    for pos in range(0, len(parts)-1, 2):
        status, path = parts[pos:pos+2]
        if not status:
            break
        areas = []
        for area, words in [('鉴权', ('auth', 'permission', 'security', 'session')), ('数据迁移', ('migration', 'schema', '.sql')), ('部署', ('dockerfile', 'deploy', '.github/workflows', '.tf'))]:
            if any(word in path.lower() for word in words):
                areas.append(area)
        entries.append({'status': status, 'path': path, 'checks': areas or ['常规审阅']})
    return {'version': VERSION, 'mode': 'staged-only', 'files': entries}

def markdown(data):
    lines = ['# ChangeGuard 免费版交接清单', '', '仅纳入 Git 暂存区；未暂存/未跟踪文件不在报告内。', '路径匹配可能误报或漏报；不是漏洞扫描、依赖分析、安全保证或测试执行。', '重命名按删除+新增列出。请另行检查真正的调用关系。', '']
    for item in data['files']:
        # JSON 转义换行等字符；不用原始路径作为 Markdown 或 HTML。
        path = json.dumps(item['path'], ensure_ascii=False)
        path = path.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        path = path.replace('`', '&#96;').replace('*', '&#42;').replace('[', '&#91;').replace(']', '&#93;').replace('_', '&#95;')
        lines.append('- [ ] ' + item['status'] + ' ' + path + ' — ' + '、'.join(item['checks']))
    if not data['files']:
        lines.append('暂存区没有变更；请不要为了试用暂存不属于自己的文件。')
    lines.extend(['', '- [ ] 另行审阅未暂存/未跟踪文件', '- [ ] 记录实际执行的测试与未验证项', '- [ ] 合并决定由项目负责人作出', ''])
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='ChangeGuard 免费版：离线暂存区路径检查清单')
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--repo', default='.', help='本人有权使用的 Git 仓库目录')
    args = parser.parse_args()
    try:
        print(markdown(report(Path(args.repo))))
    except (OSError, ValueError) as exc:
        parser.exit(2, '无法生成报告：' + str(exc) + '\n')

if __name__ == '__main__':
    main()
