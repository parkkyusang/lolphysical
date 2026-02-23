import os
import markdown
import glob

# --- 1. 기본 설정 ---
POSTS_DIR = 'posts'
TEMPLATE_POST = 'templates/post_layout.html'
TEMPLATE_BLOG = 'templates/blog_layout.html'

# 템플릿 파일 읽어오기
with open(TEMPLATE_POST, 'r', encoding='utf-8') as f:
    post_template = f.read()
with open(TEMPLATE_BLOG, 'r', encoding='utf-8') as f:
    blog_template = f.read()

articles = []

# --- 2. 글(마크다운) 읽어서 변환하기 ---
# posts 폴더 안의 모든 .md 파일을 찾습니다.
for file_path in glob.glob(f'{POSTS_DIR}/*.md'):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 상단 메타데이터 2줄(제목, 날짜) 추출
    title = lines[0].replace('Title:', '').strip()
    date = lines[1].replace('Date:', '').strip()
    
    # 4번째 줄부터 끝까지 본문으로 인식하고 HTML로 변환
    content_md = ''.join(lines[3:])
    content_html = markdown.markdown(content_md)
    
    # 파일 이름 만들기 (예: 2026-02-24-test.md -> 2026-02-24-test.html)
    output_filename = os.path.basename(file_path).replace('.md', '.html')
    
    # 템플릿의 {{빈칸}} 들을 실제 내용으로 교체
    final_html = post_template.replace('{{title}}', title).replace('{{date}}', date).replace('{{content}}', content_html)
    
    # 변환된 완성본 HTML 저장
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    # 게시판 목록 업데이트를 위해 데이터 모아두기
    articles.append({'title': title, 'date': date, 'link': output_filename})

# --- 3. 게시판(blog.html) 자동 업데이트 ---
# 날짜 최신순으로 정렬
articles.sort(key=lambda x: x['date'], reverse=True)

# <li> 태그로 게시판 리스트 생성
list_html = ""
for article in articles:
    list_html += f"<li><a href='{article['link']}'>{article['title']}</a><span class='post-date' style='color:#666; font-size:0.9rem; margin-left:15px;'>{article['date']}</span></li>\n"

# 블로그 템플릿에 리스트 꽂아넣기
final_blog_html = blog_template.replace('{{article_list}}', list_html)

with open('blog.html', 'w', encoding='utf-8') as f:
    f.write(final_blog_html)

print("✅ 성공! 모든 글이 변환되고 게시판(blog.html)이 최신화되었습니다.")
