import os
import pyodbc
import uuid
import json
from datetime import timedelta
from django.utils.timezone import now
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from .models import FileRecord
from django.db.models import Q
from django.db import connection
from cryptography.fernet import Fernet
from urllib.parse import quote
from django.http import FileResponse
import hashlib
from django.views.decorators.csrf import csrf_exempt
import zipfile

def upload(request):
    user = request.session.get('user', '没有用户')
    DBfile = os.getcwd() + u"""\data.mdb"""
    conn = pyodbc.connect(u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;", autocommit=True)
    cursor = conn.cursor()
    sql = u""" Select * FROM [users] where [用户名]=?"""   
    cursor.execute(sql, user)
    data = cursor.fetchall()
    if data:
        pass
    else:
        return HttpResponseRedirect("http://ftcdstudio.com:520/ls/as.html")

    if request.method == "POST":
        # 获取上传的文件列表
        files = request.FILES.getlist("myfiles")
        if not files:
            return JsonResponse({"status": "error", "message": "No files for upload!"})

        # 文件保存目录（相对于项目根目录）
        upload_dir = os.path.join(os.getcwd(), 'static', 'files')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        uploaded_files = []
        DBfile = os.path.join(os.getcwd(), 'data.mdb')  # 数据库文件路径

        try:
            # 连接数据库
            conn = pyodbc.connect(
                u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;",
                autocommit=True
            )
            cursor = conn.cursor()

            for myFile in files:
                # 使用MD5加密文件名
                file_name, file_extension = os.path.splitext(myFile.name)
                md5_hash = hashlib.md5(file_name.encode()).hexdigest()
                encrypted_name = md5_hash + file_extension

                # 保存文件到指定目录
                file_path = os.path.join(upload_dir, encrypted_name)
                with open(file_path, 'wb+') as f:
                    for chunk in myFile.chunks():
                        f.write(chunk)

                # 获取当前时间戳
                from datetime import datetime
                ID = datetime.now().strftime('%Y%m%d%H%M%S%f')  # 精确到微秒的时间戳

                # 写入数据库，存储原始文件名、时间戳和上传者
                relative_path = os.path.join('static', 'files', myFile.name).replace('\\', '/')
                path_encrypted_name = os.path.join('static', 'files', encrypted_name).replace('\\', '/')

                sql = u"""INSERT INTO [files]([ID],[文件名],[上传者],[md5文件名]) VALUES (?, ?, ?, ?)"""
                cursor.execute(sql, ID, relative_path, user, path_encrypted_name)

                print(f"Uploaded file: {myFile.name}")
                print(f"Operating Users: {user}")
                uploaded_files.append({"id": ID, "path": relative_path})

            # 关闭数据库连接
            cursor.close()
            conn.close()

            return JsonResponse({"status": "success", "files": uploaded_files})

        except Exception as e:
            print("Error:", str(e))  # 打印错误信息
            return JsonResponse({"status": "error", "message": str(e)})

    else:
        return render(request, 'upload.html')

    
def index(request):
    user = request.session.get('user', '没有用户')
    #print(user)
    DBfile = os.getcwd() + u"""\data.mdb"""
    conn = pyodbc.connect(u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;", autocommit=True)
    cursor = conn.cursor()
    sql=u""" Select * FROM [users] where [用户名]=?"""   
    cursor.execute(sql, user)
    data=cursor.fetchall()
    if data:
        pass
    else:
        return HttpResponseRedirect("/login/")
    # 每页显示的文件数量
    files_per_page = 20

    # 获取当前页码，默认为第 1 页
    page = int(request.GET.get('page', 1))

    # 数据库文件路径
    DBfile = os.path.join(os.getcwd(), 'data.mdb')

    try:
        # 连接数据库
        conn = pyodbc.connect(
            u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;",
            autocommit=True
        )
        cursor = conn.cursor()

        # 查询总文件数
        cursor.execute("SELECT COUNT(*) FROM [files]")
        total_files = cursor.fetchone()[0]

        # 计算总页数
        total_pages = (total_files + files_per_page - 1) // files_per_page

        # 计算分页的起始位置
        start_index = (page - 1) * files_per_page + 1
        end_index = page * files_per_page

        # 查询当前页的文件
        cursor.execute(f"""
            SELECT * FROM (
                SELECT [ID], [文件名], [上传者], [md5文件名],
                (SELECT COUNT(*) FROM [files] AS T2 WHERE T2.[ID] <= T1.[ID]) AS RowNum
                FROM [files] AS T1
                ORDER BY [ID] ASC
            ) AS SubQuery
            WHERE RowNum BETWEEN {start_index} AND {end_index}
        """)
        files = cursor.fetchall()

        # 构造文件数据并添加文件类型
        file_data = []
        for row in files:
            file_id = row[0]  # 使用时间戳作为 ID
            file_path = row[1]
            md5_path = row[3]
            uploader = row[2]  # 获取上传者信息
            file_type = "other"
            lower_file_path = md5_path.lower()  # 转为小写以支持大写扩展名
            if lower_file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                file_type = "image"
            elif lower_file_path.endswith(('.mp4', '.mov', '.avi', '.mkv', '.flv')):
                file_type = "video"
            elif lower_file_path.endswith(('.mp3', '.wav', '.flac', '.ogg', '.aac')):
                file_type = "audio"
            file_data.append({"id": file_id, "path": file_path, "md5": md5_path, "type": file_type, "uploader": uploader})

                # 如果是普通请求，渲染 HTML 模板
        return render(request, 'index.html', {
            "files": file_data,
            "total_pages": total_pages,
            "current_page": page
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def file_list_api(request):
    user = request.session.get('user', '没有用户')
    DBfile = os.getcwd() + u"""\data.mdb"""
    conn = pyodbc.connect(u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;", autocommit=True)
    cursor = conn.cursor()
    sql=u""" Select * FROM [users] where [用户名]=?"""   
    cursor.execute(sql, user)
    data=cursor.fetchall()
    if data:
        pass
    else:
        return HttpResponseRedirect("http://ftcdstudio.com:520/ls/as.html")
    # 数据库文件路径
    DBfile = os.path.join(os.getcwd(), 'data.mdb')

    try:
        # 连接数据库
        conn = pyodbc.connect(
            u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;",
            autocommit=True
        )
        cursor = conn.cursor()

        # 获取当前页码，默认为第 1 页
        page = int(request.GET.get('page', 1))
        files_per_page = 20

        # 查询总文件数
        cursor.execute("SELECT COUNT(*) FROM [files]")
        total_files = cursor.fetchone()[0]

        # 计算总页数
        total_pages = (total_files + files_per_page - 1) // files_per_page

        # 计算分页的起始位置
        start_index = (page - 1) * files_per_page + 1
        end_index = page * files_per_page

        # 查询当前页的文件
        cursor.execute(f"""
            SELECT * FROM (
                SELECT [ID], [文件名], [上传者], [md5文件名],
                (SELECT COUNT(*) FROM [files] AS T2 WHERE T2.[ID] <= T1.[ID]) AS RowNum
                FROM [files] AS T1
                ORDER BY [ID] ASC
            ) AS SubQuery
            WHERE RowNum BETWEEN {start_index} AND {end_index}
        """)
        files = cursor.fetchall()

        # 构造文件数据
        file_data = []
        for row in files:
            file_id = row[0]
            file_path = row[1]
            uploader = row[2]  # 获取上传者信息
            md5_path = row[3]  # 获取加密文件名

            # 确定文件类型
            file_type = "other"
            lower_file_path = md5_path.lower()
            if lower_file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                file_type = "image"
            elif lower_file_path.endswith(('.mp4', '.mov', '.avi', '.mkv', '.flv')):
                file_type = "video"
            elif lower_file_path.endswith(('.mp3', '.wav', '.flac', '.ogg', '.aac')):
                file_type = "audio"
            file_data.append({"id": file_id, "path": file_path, "md5": md5_path, "type": file_type, "uploader": uploader})

        return JsonResponse({
            "status": "success",
            "files": file_data,
            "current_page": page,
            "total_pages": total_pages
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

    
def login(request):
    if request.method == 'POST':
        user = request.POST.get('txtuser')
        pwd = request.POST.get('txtpwd')
        warn = ''
        try:
            DBfile = os.path.join(os.getcwd(), 'data.mdb')  # 起始执行目录\数据库文件
            conn = pyodbc.connect(u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;", autocommit=True)  # 用odbc连接DSN为mdb的数据库，修改后自动提交
            cursor = conn.cursor()                            # 用游标方式
            cursor.execute(u""" Select * FROM [users] where [用户名]=?""", user)
            list=cursor.fetchall()                            # 得到查询结果
  
            if list :                                         # 查询结果有内容
                for row in list :                             # 循环遍历                
                    if row[1]==pwd:
                        try:                     # 查询于结果中密码等输入的密码
                            request.session['user']=user  # 设置session
                            request.session.set_expiry(0)  # 设置session过期时间为0，表示浏览器关闭后session失效
                        except Exception as e:
                            print(e)
                            print(request.session['user'])
                        return HttpResponseRedirect("/index/")  # 重定向到index页面
                    else :
                        warn= u"密码错误，请重试！"
            else :
                warn = u"用户不存在！请注册或重试！"

        except Exception as e:
            print("loginerr")
            warn= u"ERROR：请联系服务器管理员！"
            print(e)
        cursor.close()
        conn.close()
        return render(request,'login.html',{'warn':warn,'user':user} )
    else:
        return render(request, 'login.html')

def search_files(request):
    query = request.GET.get('query', '').strip()
    if not query:
        return JsonResponse({"status": "error", "message": "搜索内容不能为空"})

    try:
        DBfile = os.path.join(os.getcwd(), 'data.mdb')
        conn = pyodbc.connect(
            u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;",
            autocommit=True
        )
        cursor = conn.cursor()

        # 模糊搜索文件ID、文件名或上传者
        sql = u"""
            SELECT [ID], [文件名], [md5文件名], [上传者] FROM [files]
            WHERE [ID] LIKE ? OR [文件名] LIKE ? OR [上传者] LIKE ?
        """
        search_pattern = f"%{query}%"
        cursor.execute(sql, search_pattern, search_pattern, search_pattern)
        results = cursor.fetchall()

        files = []
        for row in results:
            file_name = row[1]
            file_path = row[2]
            file_type = "other"
            lower_file_path = file_path.lower()
            if lower_file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                file_type = "image"
            elif lower_file_path.endswith(('.mp4', '.mov', '.avi', '.mkv', '.flv')):
                file_type = "video"
            elif lower_file_path.endswith(('.mp3', '.wav', '.flac', '.ogg', '.aac')):
                file_type = "audio"

            files.append({
                "id": row[0],
                "path": file_path,
                "name": file_name,
                "uploader": row[3],
                "type": file_type
            })

        return JsonResponse({"status": "success", "files": files})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

@csrf_exempt
def upload_chunk(request):
    """
    接收大文件分片上传，每个分片临时保存到 static/files/chunks/<file_id>/chunk_<index>
    """
    if request.method == "POST":
        chunk = request.FILES.get("chunk")
        file_id = request.POST.get("file_id")
        chunk_index = request.POST.get("chunk_index")
        total_chunks = request.POST.get("total_chunks")
        file_name = request.POST.get("file_name")
        is_last = request.POST.get("is_last")
        if not all([chunk, file_id, chunk_index, total_chunks, file_name]):
            return JsonResponse({"status": "error", "message": "参数不完整"})
        chunk_dir = os.path.join(os.getcwd(), 'static', 'files', 'chunks', file_id)
        if not os.path.exists(chunk_dir):
            os.makedirs(chunk_dir)
        chunk_path = os.path.join(chunk_dir, f"chunk_{chunk_index}")
        with open(chunk_path, 'wb+') as f:
            for c in chunk.chunks():
                f.write(c)
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error", "message": "仅支持POST"})

@csrf_exempt
def merge_chunks(request):
    """
    合并分片，保存为最终文件，并写入数据库
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode())
            file_id = data.get("file_id")
            file_name = data.get("file_name")
            file_size = data.get("file_size")
            user = request.session.get('user', '没有用户')
            chunk_dir = os.path.join(os.getcwd(), 'static', 'files', 'chunks', file_id)
            if not os.path.exists(chunk_dir):
                return JsonResponse({"status": "error", "message": "分片目录不存在"})
            chunk_files = sorted([f for f in os.listdir(chunk_dir) if f.startswith('chunk_')], key=lambda x: int(x.split('_')[1]))
            # 生成加密文件名
            file_base, file_ext = os.path.splitext(file_name)
            md5_hash = hashlib.md5(file_base.encode()).hexdigest()
            encrypted_name = md5_hash + file_ext
            upload_dir = os.path.join(os.getcwd(), 'static', 'files')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            final_path = os.path.join(upload_dir, encrypted_name)
            with open(final_path, 'wb+') as outfile:
                for chunk_file in chunk_files:
                    chunk_path = os.path.join(chunk_dir, chunk_file)
                    with open(chunk_path, 'rb') as infile:
                        outfile.write(infile.read())
            # 写入数据库
            from datetime import datetime
            ID = datetime.now().strftime('%Y%m%d%H%M%S%f')
            relative_path = os.path.join('static', 'files', file_name).replace('\\', '/')
            path_encrypted_name = os.path.join('static', 'files', encrypted_name).replace('\\', '/')
            DBfile = os.path.join(os.getcwd(), 'data.mdb')
            conn = pyodbc.connect(u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;", autocommit=True)
            cursor = conn.cursor()
            sql = u"""INSERT INTO [files]([ID],[文件名],[上传者],[md5文件名]) VALUES (?, ?, ?, ?)"""
            cursor.execute(sql, ID, relative_path, user, path_encrypted_name)
            conn.commit()
            cursor.close()
            conn.close()
            # 删除分片目录
            import shutil
            shutil.rmtree(chunk_dir)
            return JsonResponse({"status": "success", "files": [{"id": ID, "path": relative_path}]})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "仅支持POST"})

@csrf_exempt
def batch_download(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        file_ids = data.get('file_ids', [])

        if not file_ids:
            return JsonResponse({"status": "error", "message": "未选择文件"})

        # 数据库文件路径
        DBfile = os.path.join(os.getcwd(), 'data.mdb')

        try:
            conn = pyodbc.connect(
                u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;",
                autocommit=True
            )
            cursor = conn.cursor()

            # 查询文件路径
            placeholders = ','.join(['?'] * len(file_ids))
            cursor.execute(f"SELECT [md5文件名], [文件名] FROM [files] WHERE [ID] IN ({placeholders})", file_ids)
            files = cursor.fetchall()

            if not files:
                return JsonResponse({"status": "error", "message": "未找到文件"})

            # 创建压缩包
            zip_dir = os.path.join(os.getcwd(), 'static', 'files', 'zips')
            if not os.path.exists(zip_dir):
                os.makedirs(zip_dir)

            timestamp = now().strftime('%Y%m%d%H%M%S')
            user = request.session.get('user', 'unknown_user')
            zip_name = f"{timestamp}_{len(files)}_{user}.zip"
            zip_path = os.path.join(zip_dir, zip_name)

            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for md5_file, original_name in files:
                    file_path = os.path.join(os.getcwd(), md5_file)  # 确保文件路径正确
                    if os.path.exists(file_path):
                        # 使用 arcname 确保压缩包内文件名为原始文件名，且不包含文件夹
                        zipf.write(file_path, arcname=os.path.basename(original_name))
                    else:
                        print(f"文件未找到: {file_path}")

            # 返回压缩包路径
            return JsonResponse({"status": "success", "zip_path": f"/static/files/zips/{zip_name}"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

        finally:
            cursor.close()
            conn.close()

    return JsonResponse({"status": "error", "message": "仅支持POST请求"})

@csrf_exempt
def delete_files_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            file_ids = data.get('file_ids', [])

            if not file_ids:
                return JsonResponse({"status": "error", "message": "No files selected for deletion!"})

            DBfile = os.path.join(os.getcwd(), 'data.mdb')
            conn = pyodbc.connect(
                u"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;",
                autocommit=True
            )
            cursor = conn.cursor()

            for file_id in file_ids:
                # 查询文件路径
                cursor.execute("SELECT [md5文件名] FROM [files] WHERE [ID] = ?", file_id)
                result = cursor.fetchone()
                if result:
                    file_path = os.path.join(os.getcwd(), result[0])

                    # 删除文件
                    if os.path.exists(file_path):
                        os.remove(file_path)

                    # 删除数据库记录
                    cursor.execute("DELETE FROM [files] WHERE [ID] = ?", file_id)

            conn.commit()
            cursor.close()
            conn.close()

            return JsonResponse({"status": "success", "message": "Files deleted successfully!"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Only POST requests are allowed!"})
