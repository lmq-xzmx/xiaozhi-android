#!/bin/bash

echo "=== 修正Git推送被拒绝问题 ==="
echo ""

cd ..

echo "📂 当前目录: $(pwd)"
echo ""

echo "🔍 检查Git状态..."
git status

echo ""
echo "📋 查看当前分支..."
git branch -v

echo ""
echo "🌐 查看远程仓库..."
git remote -v

echo ""
echo "=== 解决方案选择 ==="
echo "您遇到的错误: remote contains work that you do not have locally"
echo ""
echo "🎯 推荐解决方案:"
echo "1. 先拉取远程更改并合并"
echo "2. 然后推送您的更改"
echo ""

read -p "是否执行自动修复? (y/N): " confirm

if [[ $confirm =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔄 正在拉取远程更改..."
    
    # 尝试拉取并合并
    git pull origin new-main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ 远程更改拉取成功！"
        echo ""
        echo "🚀 重新推送..."
        git push -u origin new-main
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "🎉 推送成功！"
        else
            echo ""
            echo "❌ 推送仍然失败，可能需要手动解决冲突"
        fi
    else
        echo ""
        echo "⚠️ 拉取过程中出现冲突或错误"
        echo "💡 手动解决建议:"
        echo "1. 检查冲突文件: git status"
        echo "2. 编辑冲突文件解决冲突"
        echo "3. 添加解决的文件: git add ."
        echo "4. 完成合并: git commit"
        echo "5. 推送: git push -u origin new-main"
    fi
else
    echo ""
    echo "📝 手动执行步骤:"
    echo "1. git pull origin new-main  # 拉取远程更改"
    echo "2. 解决可能的冲突"
    echo "3. git push -u origin new-main  # 重新推送"
    echo ""
    echo "🔍 如果想查看远程更改:"
    echo "git fetch origin"
    echo "git log --oneline new-main..origin/new-main"
fi

echo ""
echo "📋 其他选择（谨慎使用）:"
echo "- 强制推送（会覆盖远程更改）: git push --force-with-lease origin new-main"
echo "- 重置到远程状态: git reset --hard origin/new-main" 