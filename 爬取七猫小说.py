# 导入 requests 库和 BeautifulSoup 库
import requests
from bs4 import BeautifulSoup
import os

# 目标网页的 URL
url = 'https://www.qimao.com/shuku/1882754-17300808180001/'

# 设置一个 User-Agent，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"正在尝试从 {url} 获取网页内容...")

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    print("网页内容获取成功！")
    response.encoding = response.apparent_encoding

    # 使用 BeautifulSoup 解析 HTML 内容
    soup = BeautifulSoup(response.text, 'html.parser')

    # 提取章节标题
    chapter_title_tag = soup.find('h2', class_='chapter-title')
    if chapter_title_tag:
        chapter_title = chapter_title_tag.get_text(strip=True)
    else:
        chapter_title = "未找到标题"
        print("警告：没有找到章节标题，请检查HTML或选择器。")

    # 提取小说正文
    main_content_area = soup.find('div', class_='article')

    novel_paragraphs_text = []
    if main_content_area:
        paragraphs = main_content_area.find_all('p')
        
        if paragraphs:
            for p_tag in paragraphs:
                novel_paragraphs_text.append(p_tag.get_text(strip=True))
        else:
            print("警告：在指定正文区域内没有找到 <p> 标签。")

    if not novel_paragraphs_text:
        print("警告：未能提取到小说正文内容。请再次检查HTML或选择器。")

    # 打印提取到的内容
    print("\n--- 提取结果 ---")
    print(f"章节标题: {chapter_title}")
    
    print("\n小说正文:")
    if novel_paragraphs_text:
        for paragraph_text in novel_paragraphs_text:
            print(paragraph_text)
    else:
        print("（正文内容为空）")

    # 将提取到的内容保存到桌面
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    filename = f"{chapter_title}.txt" if chapter_title != "未找到标题" else "scraped_novel.txt"
    file_path = os.path.join(desktop, filename)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"章节标题: {chapter_title}\n\n")
            for paragraph_text in novel_paragraphs_text:
                f.write(paragraph_text + "\n")
        print(f"\n小说内容已保存到桌面: {file_path}")
    except OSError as e:
        print(f"\n保存文件失败: {e}. 文件名可能包含非法字符。尝试使用默认文件名。")
        # 如果文件名有问题，使用默认文件名
        default_file_path = os.path.join(desktop, "scraped_novel_content.txt")
        with open(default_file_path, 'w', encoding='utf-8') as f:
            f.write(f"章节标题: {chapter_title}\n\n")
            for paragraph_text in novel_paragraphs_text:
                f.write(paragraph_text + "\n")
        print(f"\n小说内容已保存到桌面: {default_file_path}")

except requests.exceptions.RequestException as e:
    print(f"获取网页失败: {e}")
except Exception as e:
    print(f"发生了其他错误: {e}") 