import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
import os
import threading # To prevent GUI freezing during network requests

# --- Core Scraping Logic (adapted from your script) ---
def scrape_novel_chapter(url):
    """
    Scrapes the chapter title and content from the given URL.

    Args:
        url (str): The URL of the novel chapter.

    Returns:
        tuple: (chapter_title, novel_paragraphs_text, error_message)
               Returns (None, None, error_message) if an error occurs.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=20) # Increased timeout
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取章节标题 (Extract chapter title)
        chapter_title_tag = soup.find('h2', class_='chapter-title')
        if chapter_title_tag:
            chapter_title = chapter_title_tag.get_text(strip=True)
        else:
            # Try another common selector for titles if the first one fails
            chapter_title_tag = soup.find('h1') # General H1 tag
            if chapter_title_tag:
                chapter_title = chapter_title_tag.get_text(strip=True)
            else:
                chapter_title = "未找到标题" # Title not found

        # 提取小说正文 (Extract novel content)
        # Common selectors for article content. You might need to adjust these based on the website structure.
        content_selectors = [
            {'tag': 'div', 'class_': 'article'},
            {'tag': 'div', 'id': 'content'},
            {'tag': 'article'}, # HTML5 article tag
            {'tag': 'div', 'class_': 'content'},
            {'tag': 'div', 'class_': 'entry-content'}
        ]
        
        main_content_area = None
        for selector in content_selectors:
            if 'class_' in selector:
                main_content_area = soup.find(selector['tag'], class_=selector['class_'])
            elif 'id' in selector:
                main_content_area = soup.find(selector['tag'], id=selector['id'])
            else:
                main_content_area = soup.find(selector['tag'])
            if main_content_area:
                break # Found a content area

        novel_paragraphs_text = []
        if main_content_area:
            paragraphs = main_content_area.find_all('p')
            if paragraphs:
                for p_tag in paragraphs:
                    novel_paragraphs_text.append(p_tag.get_text(strip=True))
            else: # If no <p> tags, try to get all text from the content area
                all_text = main_content_area.get_text(separator='\n', strip=True)
                if all_text:
                    novel_paragraphs_text = [p.strip() for p in all_text.split('\n') if p.strip()]
                else:
                    return chapter_title, [], "在指定正文区域内没有找到 <p> 标签或任何文本内容。" # No <p> tags or any text found in content area
        else:
            return chapter_title, [], "未能找到主要内容区域。请检查HTML结构或尝试不同的选择器。" # Could not find main content area

        if not novel_paragraphs_text:
            return chapter_title, [], "未能提取到小说正文内容。" # Failed to extract novel content

        return chapter_title, novel_paragraphs_text, None

    except requests.exceptions.RequestException as e:
        return None, None, f"获取网页失败 (Failed to fetch webpage): {e}"
    except Exception as e:
        return None, None, f"发生其他错误 (An unexpected error occurred): {e}"

# --- GUI Application ---
class NovelScraperApp:
    def __init__(self, master):
        self.master = master
        master.title("Python小说抓取器 (Novel Scraper)")
        master.geometry("700x550") # Adjusted size for better layout

        # --- Styling ---
        self.label_font = ("Arial", 10)
        self.entry_font = ("Arial", 10)
        self.button_font = ("Arial", 10, "bold")
        self.text_area_font = ("Arial", 9)

        # --- URL Input ---
        tk.Label(master, text="目标网页URL (Target URL):", font=self.label_font).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.url_entry = tk.Entry(master, width=70, font=self.entry_font)
        self.url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.url_entry.insert(0, "https://www.qimao.com/shuku/1882754-17300808180001/") # Default example

        # --- Save Directory ---
        tk.Label(master, text="保存位置 (Save Location):", font=self.label_font).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.save_dir_entry = tk.Entry(master, width=55, font=self.entry_font)
        self.save_dir_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.save_dir_entry.insert(0, os.path.join(os.path.expanduser("~"), "Desktop")) # Default to Desktop
        
        self.browse_button = tk.Button(master, text="浏览 (Browse)", command=self.browse_directory, font=self.button_font)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # --- Scrape Button ---
        self.scrape_button = tk.Button(master, text="开始抓取 (Start Scraping)", command=self.start_scraping_thread, font=self.button_font, bg="#4CAF50", fg="white")
        self.scrape_button.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

        # --- Status/Output Area ---
        tk.Label(master, text="状态/输出 (Status/Output):", font=self.label_font).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.status_text = scrolledtext.ScrolledText(master, width=80, height=20, wrap=tk.WORD, font=self.text_area_font)
        self.status_text.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")
        self.status_text.insert(tk.END, "请填入URL和选择保存位置，然后点击“开始抓取”。\n(Please enter the URL, choose a save location, and click 'Start Scraping'.)\n")

        # --- Configure grid column weights for responsiveness ---
        master.grid_columnconfigure(1, weight=1) # Allow entry fields to expand

    def log_status(self, message):
        """Appends a message to the status text area."""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END) # Auto-scroll to the bottom
        self.master.update_idletasks() # Ensure GUI updates

    def browse_directory(self):
        """Opens a dialog to choose a save directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.save_dir_entry.delete(0, tk.END)
            self.save_dir_entry.insert(0, directory)
            self.log_status(f"保存位置已选择 (Save location selected): {directory}")

    def start_scraping_thread(self):
        """Starts the scraping process in a new thread to avoid freezing the GUI."""
        self.scrape_button.config(state=tk.DISABLED, text="正在抓取... (Scraping...)")
        self.log_status("开始抓取过程... (Starting scraping process...)")
        
        url = self.url_entry.get().strip()
        save_dir = self.save_dir_entry.get().strip()

        if not url:
            messagebox.showerror("错误 (Error)", "请输入目标网页URL。 (Please enter the target URL.)")
            self.log_status("错误：URL不能为空。 (Error: URL cannot be empty.)")
            self.scrape_button.config(state=tk.NORMAL, text="开始抓取 (Start Scraping)")
            return
        if not save_dir:
            messagebox.showerror("错误 (Error)", "请选择保存文件的位置。 (Please select a save location.)")
            self.log_status("错误：保存位置不能为空。 (Error: Save location cannot be empty.)")
            self.scrape_button.config(state=tk.NORMAL, text="开始抓取 (Start Scraping)")
            return
        if not os.path.isdir(save_dir):
            messagebox.showerror("错误 (Error)", "选择的保存位置不是一个有效的文件夹。 (The selected save location is not a valid directory.)")
            self.log_status(f"错误：无效的保存文件夹 (Error: Invalid save directory): {save_dir}")
            self.scrape_button.config(state=tk.NORMAL, text="开始抓取 (Start Scraping)")
            return

        # Run scraping in a separate thread
        thread = threading.Thread(target=self.perform_scraping, args=(url, save_dir))
        thread.daemon = True # Allows main program to exit even if thread is running
        thread.start()

    def perform_scraping(self, url, save_dir):
        """The actual scraping and file saving logic."""
        self.log_status(f"正在尝试从 {url} 获取网页内容... (Attempting to fetch content from {url}...)")
        
        chapter_title, novel_paragraphs, error_msg = scrape_novel_chapter(url)

        if error_msg:
            self.log_status(f"抓取错误 (Scraping error): {error_msg}")
            messagebox.showerror("抓取失败 (Scraping Failed)", error_msg)
            self.scrape_button.config(state=tk.NORMAL, text="开始抓取 (Start Scraping)")
            return

        if not chapter_title or chapter_title == "未找到标题":
            self.log_status("警告：没有找到章节标题，将使用默认文件名。 (Warning: Chapter title not found, using default filename.)")
            filename_base = "scraped_novel_content"
        else:
            # Sanitize filename (remove characters invalid for filenames)
            filename_base = "".join(c for c in chapter_title if c.isalnum() or c in (' ', '.', '_')).rstrip()
            if not filename_base: # If title was all special chars
                filename_base = "scraped_novel_content"
        
        filename = f"{filename_base}.txt"
        file_path = os.path.join(save_dir, filename)
        
        self.log_status("\n--- 提取结果 (Extraction Results) ---")
        self.log_status(f"章节标题 (Chapter Title): {chapter_title}")
        
        if novel_paragraphs:
            self.log_status("\n小说正文 (Novel Content):")
            for i, paragraph_text in enumerate(novel_paragraphs):
                self.log_status(paragraph_text)
                if i < 5: # Log first few paragraphs to GUI for quick check
                    pass 
            if len(novel_paragraphs) > 5:
                self.log_status("... (更多内容已提取但未在状态窗口完全显示) (... more content extracted but not fully shown in status window)")
        else:
            self.log_status("（正文内容为空）((Content is empty))")
            messagebox.showwarning("警告 (Warning)", "未能提取到小说正文内容。文件将只包含标题（如果找到）。 (Failed to extract novel content. File will only contain title if found.)")


        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"章节标题 (Chapter Title): {chapter_title}\n\n")
                if novel_paragraphs:
                    for paragraph_text in novel_paragraphs:
                        f.write(paragraph_text + "\n\n") # Add extra newline for readability
                else:
                    f.write("（未能提取到正文内容）((Failed to extract content))")
            self.log_status(f"\n小说内容已成功保存到 (Novel content successfully saved to): {file_path}")
            messagebox.showinfo("成功 (Success)", f"小说内容已保存到:\n{file_path}")
        except OSError as e:
            self.log_status(f"\n保存文件失败 (Failed to save file): {e}. 文件名可能包含非法字符或路径问题。 (Filename might contain invalid characters or path issues.)")
            # Attempt with a very generic filename if specific one failed
            default_filename = "scraped_novel_default_name.txt"
            default_file_path = os.path.join(save_dir, default_filename)
            try:
                with open(default_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"章节标题 (Chapter Title): {chapter_title}\n\n")
                    if novel_paragraphs:
                        for paragraph_text in novel_paragraphs:
                            f.write(paragraph_text + "\n\n")
                    else:
                        f.write("（未能提取到正文内容）((Failed to extract content))")
                self.log_status(f"由于原始文件名问题，内容已使用默认名称保存到 (Due to original filename issues, content saved with default name to): {default_file_path}")
                messagebox.showinfo("成功 (Success)", f"小说内容已使用默认名称保存到:\n{default_file_path}")
            except Exception as e_default:
                self.log_status(f"使用默认文件名保存也失败了 (Saving with default filename also failed): {e_default}")
                messagebox.showerror("保存失败 (Save Failed)", f"无法保存文件，即使是使用默认文件名。\n错误 (Error): {e_default}")
        except Exception as e_generic:
             self.log_status(f"\n保存文件时发生未知错误 (An unknown error occurred while saving file): {e_generic}")
             messagebox.showerror("保存失败 (Save Failed)", f"保存文件时发生未知错误。\n错误 (Error): {e_generic}")
        finally:
            self.scrape_button.config(state=tk.NORMAL, text="开始抓取 (Start Scraping)")


if __name__ == '__main__':
    root = tk.Tk()
    app = NovelScraperApp(root)
    root.mainloop()
