import tkinter as tk
from tkinter import messagebox, Listbox
import os
import glob
import subprocess
from datetime import datetime
import markdown  # nl2br 확장을 사용해 메모장처럼 엔터치면 자동 줄바꿈 적용


# --- 1. 사이트 자동 생성 엔진 (build.py 통합) ---
def rebuild_site():
    POSTS_DIR = 'posts'
    TEMPLATE_POST = 'templates/post_layout.html'
    TEMPLATE_BLOG = 'templates/blog_layout.html'

    with open(TEMPLATE_POST, 'r', encoding='utf-8') as f:
        post_template = f.read()
    with open(TEMPLATE_BLOG, 'r', encoding='utf-8') as f:
        blog_template = f.read()

    articles = []
    # 모든 글 변환
    for file_path in glob.glob(f'{POSTS_DIR}/*.md'):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        title = lines[0].replace('Title:', '').strip()
        date = lines[1].replace('Date:', '').strip()
        content_md = ''.join(lines[3:])

        # extensions=['nl2br'] 덕분에 마크다운을 몰라도 엔터만 치면 줄바꿈이 완벽히 적용됩니다.
        content_html = markdown.markdown(content_md, extensions=['nl2br'])
        output_filename = os.path.basename(file_path).replace('.md', '.html')

        final_html = post_template.replace('{{title}}', title).replace('{{date}}', date).replace('{{content}}',
                                                                                                 content_html)
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_html)

        articles.append({'title': title, 'date': date, 'link': output_filename})

    # 게시판 업데이트
    articles.sort(key=lambda x: x['date'], reverse=True)
    list_html = ""
    for article in articles:
        list_html += f"<li><a href='{article['link']}'>{article['title']}</a><span style='color:#666; font-size:0.9rem; margin-left:15px;'>{article['date']}</span></li>\n"

    final_blog_html = blog_template.replace('{{article_list}}', list_html)
    with open('blog.html', 'w', encoding='utf-8') as f:
        f.write(final_blog_html)


# --- 2. 깃허브 자동 발행 함수 ---
def git_push(commit_msg):
    try:
        subprocess.run(["git", "add", "."], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(["git", "push"], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception as e:
        messagebox.showerror("깃허브 연결 오류", "GitHub Desktop으로 폴더가 연동되어 있는지 확인하세요!")
        return False


# --- 3. GUI 동작 로직 ---
current_file_path = None  # 현재 수정 중인 파일 경로


def load_post_list():
    listbox.delete(0, tk.END)
    for file_path in sorted(glob.glob('posts/*.md'), reverse=True):
        filename = os.path.basename(file_path)
        listbox.insert(tk.END, filename)


def on_select_post(event):
    global current_file_path
    selection = listbox.curselection()
    if not selection: return

    filename = listbox.get(selection[0])
    current_file_path = f"posts/{filename}"

    with open(current_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entry_title.delete(0, tk.END)
    entry_title.insert(0, lines[0].replace('Title:', '').strip())

    text_content.delete("1.0", tk.END)
    text_content.insert(tk.END, ''.join(lines[3:]))

    btn_publish.config(text="🔄 수정 후 발행하기", bg="#00ffcc", fg="black")


def clear_editor():
    global current_file_path
    current_file_path = None
    entry_title.delete(0, tk.END)
    text_content.delete("1.0", tk.END)
    btn_publish.config(text="🚀 새 글 저장 및 깃허브 발행", bg="#ff3366", fg="white")


def save_and_publish():
    global current_file_path
    title = entry_title.get().strip()
    content = text_content.get("1.0", tk.END).strip()

    if not title or not content:
        messagebox.showwarning("오류", "제목과 본문을 입력하세요.")
        return

    # 새 글일 경우 파일명 생성
    if not current_file_path:
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = title.replace(" ", "_").replace("/", "-")
        current_file_path = f"posts/{date_str}_{safe_title}.md"
    else:
        # 기존 파일 수정 시 날짜 유지
        with open(current_file_path, 'r', encoding='utf-8') as f:
            date_str = f.readlines()[1].replace('Date:', '').strip()

    # 마크다운 파일 저장 (일반 메모장처럼 적어도 알아서 줄바꿈됨)
    with open(current_file_path, 'w', encoding='utf-8') as f:
        f.write(f"Title: {title}\n")
        f.write(f"Date: {date_str}\n\n")
        f.write(content)

    rebuild_site()
    if git_push(f"Update post: {title}"):
        messagebox.showinfo("성공", "🎉 사이트 업데이트 및 깃허브 발행이 완료되었습니다!")
        load_post_list()
        clear_editor()


def delete_post():
    global current_file_path
    if not current_file_path: return

    if messagebox.askyesno("삭제 확인", "정말로 이 글을 삭제하시겠습니까?"):
        # 마크다운 및 연결된 HTML 파일 동시 삭제
        os.remove(current_file_path)
        html_file = current_file_path.replace('posts/', '').replace('.md', '.html')
        if os.path.exists(html_file):
            os.remove(html_file)

        rebuild_site()
        if git_push(f"Delete post: {html_file}"):
            messagebox.showinfo("삭제 완료", "글이 완전히 삭제되었습니다.")
            load_post_list()
            clear_editor()


# --- 4. 화면 구성 (GUI) ---
root = tk.Tk()
root.title("LOLPhysical 블로그 매니저")
root.geometry("850x600")
root.configure(bg="#0a0a0c")

# 왼쪽 프레임 (글 목록)
frame_left = tk.Frame(root, bg="#0a0a0c")
frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)

tk.Label(frame_left, text="📋 내 칼럼 목록", fg="#00ffcc", bg="#0a0a0c", font=("Pretendard", 12, "bold")).pack(pady=5)
listbox = Listbox(frame_left, width=25, height=25, bg="#111", fg="#fff", font=("Pretendard", 10))
listbox.pack()
listbox.bind('<<ListboxSelect>>', on_select_post)

tk.Button(frame_left, text="✨ 새 글 쓰기", command=clear_editor, bg="#333", fg="#fff").pack(pady=10, fill=tk.X)
tk.Button(frame_left, text="🗑️ 글 삭제하기", command=delete_post, bg="#cc0000", fg="#fff").pack(fill=tk.X)

# 오른쪽 프레임 (에디터)
frame_right = tk.Frame(root, bg="#0a0a0c")
frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

tk.Label(frame_right, text="칼럼 제목", fg="#00ffcc", bg="#0a0a0c", font=("Pretendard", 12, "bold")).pack(anchor="w")
entry_title = tk.Entry(frame_right, font=("Pretendard", 12))
entry_title.pack(fill=tk.X, pady=5)

tk.Label(frame_right, text="본문 (메모장처럼 그냥 엔터 치며 쓰세요)", fg="#00ffcc", bg="#0a0a0c", font=("Pretendard", 12, "bold")).pack(
    anchor="w", pady=(10, 0))
text_content = tk.Text(frame_right, height=20, font=("Pretendard", 11))
text_content.pack(fill=tk.BOTH, expand=True, pady=5)

btn_publish = tk.Button(frame_right, text="🚀 새 글 저장 및 깃허브 발행", command=save_and_publish, bg="#ff3366", fg="white",
                        font=("Pretendard", 14, "bold"))
btn_publish.pack(fill=tk.X, pady=10)

load_post_list()
root.mainloop()