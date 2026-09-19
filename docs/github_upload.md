# 上传到 GitHub

## 方式一：命令行上传

```powershell
cd D:\Aagent\rag-agent-student-employment
git init
git add .
git commit -m "init rag agent project"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

## 方式二：GitHub 网页上传

1. 在 GitHub 新建仓库。
2. 不要勾选自动生成 README、.gitignore、license，避免冲突。
3. 将本项目文件夹里的内容上传。
4. 确认 `.env` 没有被上传，应该只上传 `.env.example`。

## 注意

- 不要上传 `.env`。
- 不要上传 `frontend/node_modules`。
- 不要上传日志文件和本地上传文件。
