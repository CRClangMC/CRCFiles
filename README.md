# CRCFiles

## 项目简介
CRCFiles 是一个基于 Django 框架开发的文件管理系统，支持文件上传、分片上传、文件搜索、文件删除等功能。项目还集成了 Microsoft Access 数据库，用于存储文件信息。

## 项目结构
```
collectstatic.bat
data.mdb
db.sqlite3
manage.py
requirements.txt
run_server.bat
CRCFiles/
    __init__.py
    asgi.py
    handler.py
    settings.py
    urls.py
    wsgi.py
index/
    __init__.py
    admin.py
    apps.py
    models.py
    tests.py
    urls.py
    views.py
    migrations/
    templates/
static/
    app.js
    bootstrap.min.css
    jquery-3.6.0.min.js
    admin/
    CSS/
    files/
temp/
```

## 功能概述
1. **文件上传**：支持普通文件上传和分片上传。
2. **文件搜索**：通过关键词搜索文件。
3. **文件删除**：支持批量删除文件及其数据库记录，同时删除文件系统中的实际文件。
4. **文件展示**：支持图片、视频、音频文件的预览。
5. **文件下载**：提供单个文件和批量下载功能。
6. **账户管理**：默认用户名和密码为 `admin`，可通过修改 `data.mdb` 数据库中的 `users` 表添加或修改账户。

## MD5 文件名加密
项目在文件上传时会对文件名进行 MD5 加密处理：
- 原始文件名通过 MD5 算法生成唯一的加密文件名。
- 加密后的文件名用于存储文件，避免文件名冲突。
- 加密文件名存储在数据库的 `md5文件名` 字段中。

## 安装与运行

### 环境要求
- Python 3.11+
- Django 4.x
- Microsoft Access 数据库驱动
- 其他依赖请参考 `requirements.txt`

### 安装步骤
1. 克隆项目到本地：
   ```bash
   git clone https://github.com/CRClangMC/CRCFiles.git
   cd CRCFiles
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置数据库：
   - 确保 `data.mdb` 文件存在于项目根目录。
   - 确保安装了 Microsoft Access 数据库驱动。

4. 运行项目：
   ```bash
   python manage.py runserver
   ```

5. 访问项目：
   在浏览器中打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。

## 配置说明
### 文件上传配置
在 [`CRCFiles/settings.py`](CRCFiles_v4.0/CRCFiles/settings.py) 中：
- 临时文件夹：`FILE_UPLOAD_TEMP_DIR`
- 最大文件大小：`FILE_UPLOAD_MAX_MEMORY_SIZE`
- 自定义上传处理器：`FILE_UPLOAD_HANDLERS`

### 静态文件配置
静态文件存放在 [`static/`](CRCFiles_v4.0/static/) 文件夹中，项目支持通过 `/static/` 路由访问静态资源。

## API 路由
以下是项目的主要 API 路由：
- `/upload/`：文件上传
- `/api/files`：获取文件列表
- `/api/search`：搜索文件
- `/api/delete_files/`：批量删除文件
- `/upload_chunk/`：分片上传
- `/merge_chunks/`：合并分片
- `/api/batch_download/`：批量下载文件

## 数据库说明
项目使用 Microsoft Access 数据库存储文件信息，数据库文件为 [`data.mdb`](CRCFiles_v4.0/data.mdb)。主要表结构如下：
- `files` 表：存储文件信息，包括文件名、文件路径、文件类型等。
- `users` 表：存储用户信息，包括用户名和密码。

## 贡献
欢迎提交 Issue 或 Pull Request 来贡献代码。

## 许可证
本项目使用 MIT 许可证。
