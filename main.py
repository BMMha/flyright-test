
#!/usr/bin/env python3
# main.py – Flask + PyGithub – رفع ملف إلى GitHub مباشرة

import os
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory
from github import Github

# ========== إعدادات Flask ==========
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ========== إعدادات GitHub ==========
GITHUB_TOKEN = os.getenv("GH_TOKEN") or "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"
GITHUB_REPO  = os.getenv("GH_REPO")  or "BMMha/flyright-test"  # نموذج: owner/repo
BRANCH       = "main"
# =====================================


# ---------- دفع الملف إلى GitHub ----------
def push_to_github(file_path: Path, gh_path: str) -> str:
    """
    ترفع الملف إلى GitHub وتُعيد رابط الـ Raw
    """
    g    = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    content = file_path.read_bytes()
    try:
        # إذا موجود نحدّثه
        remote = repo.get_contents(gh_path, ref=BRANCH)
        repo.update_file(remote.path, f"Update {file_path.name}", content,
                         remote.sha, branch=BRANCH)
        print("✏️ Updated on GitHub →", gh_path)
    except Exception as e:
        if "404" in str(e):
            repo.create_file(gh_path, f"Add {file_path.name}", content,
                             branch=BRANCH)
            print("✅ Created on GitHub →", gh_path)
        else:
            raise

    # رابط الـ Raw
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{gh_path}"


# ---------- صفحة الرئيسة ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- استقبال الرفع ----------
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        return "لم يتم اختيار ملف", 400

    # المسار المقترح داخل GitHub
    github_path = request.form.get("github_path", "").strip()
    if not github_path:
        github_path = file.filename

    # حفظ محليًا
    save_path = Path(app.config["UPLOAD_FOLDER"]) / github_path
    save_path.parent.mkdir(parents=True, exist_ok=True)
    file.save(save_path)

    # دفع إلى GitHub
    try:
        raw_url = push_to_github(save_path, github_path)
    except Exception as e:
        return f"فشل الرفع إلى GitHub: {e}", 500

    # عرض النتيجة
    return f"""
    ✅ تم رفع الملف بنجاح إلى GitHub!<br>
    المسار داخل الريبو: <b>{github_path}</b><br>
    رابط الـ Raw: 
    <input type="text" value="{raw_url}" readonly style="width:100%"><br>
    <a href="{raw_url}" target="_blank">فتح الملف</a> | 
    <a href="/">رفع ملف آخر</a>
    """


# ---------- سيرف الملفات (اختياري) ----------
@app.route("/uploads/<path:filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


# ---------- تشغيل الخادم ----------
if __name__ == "__main__":
    app.run(debug=True)