import os
import random
import time
import json
import csv
import sys
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns   
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import ast
from collections import Counter

CREDENTIALS_FILE = "credenciais.json"

def is_element_present(driver, xpath):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return True
    except TimeoutException:
        return False
    
def type_like_a_human(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.2, 0.5)) 

def click_not_now(driver):
    try:
        not_now_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//*[text()='Agora não' or text()='Not now']"
            ))
        )
        not_now_button.click()
    except TimeoutException:
        pass
    except Exception as e:
        print(f"Erro inesperado ao tentar clicar em 'Agora não' ou 'Not now': {e}")
        
def check_login_errors(driver):
    if is_element_present(driver, "//p[contains(text(), 'senha incorreta')]"):
        print("Erro de login: Senha incorreta.")
        return False
    
    if is_element_present(driver, "//*[contains(@href, '/explore/')]"):
        return True
    
    print("Erro desconhecido durante o login.")
    return False

def save_credentials(username, password):
    with open(CREDENTIALS_FILE, "w") as file:
        json.dump({"username": username, "password": password}, file)

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as file:
            creds = json.load(file)
            return creds.get("username"), creds.get("password")
    return "", ""

saved_user, saved_pass = load_credentials()

def delete_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        os.remove(CREDENTIALS_FILE)
        messagebox.showinfo("Sucesso", "Credenciais apagadas com sucesso.")
        login_window()
    else:
        messagebox.showwarning("Aviso", "Nenhuma credencial armazenada para ser apagada.")
        
def login(driver, username, password):
    driver.get("https://www.instagram.com")
    
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
    except TimeoutException:
        print("Erro ao carregar a página de login.")
        return False
    except NoSuchElementException:
        print("Erro ao encontrar os campos de login.")
        return False 
    
    type_like_a_human(username_input, username)
    type_like_a_human(password_input, password)
    
    password_input.send_keys("\n")
    
    if not check_login_errors(driver):
        print("Erro durante o login, verifique as credenciais.")
        return False
    else:
        time.sleep(10)
        click_not_now(driver)
        return True

def click_search_icon(driver):
        path = "body > div > div > div > div:nth-child(2) > div > div > div:first-child > div:first-child > div:nth-child(2) > div > div > div > div > div > div:nth-child(2)"
        search_container = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, path))
        )
        
        if search_container: 
            search_container.click()
            time.sleep(2)
            
def type_in_search_field(driver, search_text):
    search_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.XPATH,
            "//input[contains(@placeholder, 'Pesquisar') or contains(@placeholder, 'Search')]"
        ))
    )
    type_like_a_human(search_field, search_text)
    time.sleep(2)

def click_first_search_result(driver, search_text):
    try:
        first_result = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '{search_text}')]"))
        )
        first_result.click()
        
    except Exception as e:
        print(f"Erro ao tentar clicar no primeiro resultado: {e}")

def post_id(driver):
    try:
        url = driver.current_url
        url = url.split("?")[0]
        url_parts = url.rstrip("/").split("/")
        post_id = url_parts[-1]

        #print(f"Post ID: {post_id}")
        return post_id
    except Exception as e:
        print(f"Erro ao obter o Post ID: {e}")
        return None
            
def get_post_details(driver):
    try:
        wait = WebDriverWait(driver, 10)
        
        container = driver.find_element(By.CSS_SELECTOR, "article[role=presentation]")
        
        user_element = container.find_element(By.CSS_SELECTOR, "header a")
        author = user_element.text
        
        post_body = container.find_element(By.CSS_SELECTOR, "& > div > div:nth-child(2) > div > div> div:nth-child(2)")

        comments_body = post_body.find_element(By.CSS_SELECTOR, "& ul")
        
        description_element = comments_body.find_element(By.CSS_SELECTOR, "h1")
        
        description = description_element.get_attribute("innerText")

        date_element = wait.until(EC.presence_of_element_located((By.XPATH, "//time")))
        datetime_str = date_element.get_attribute("datetime")
        
        post_datetime = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))

        try:
            video_element = driver.find_element(By.CSS_SELECTOR, "video")
            post_type = "Vídeo"
            media_url = video_element.get_attribute("src")
        except:
            try:
                image_element = driver.find_element(By.XPATH, "//article//img")
                post_type = "Foto"
                media_url = image_element.get_attribute("src")
            except:
                post_type = "Desconhecido"
                media_url = ""
                
        #print(f"Nome de usuário que realizou postagem: {author}")
        #print(f"Descrição do post: {description}")
        #print(f"Data e Hora da postagem: {post_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        #print(f"Tipo de postagem: {post_type}\n")
        
        return {
            "author": author,
            "description": description,
            "post_datetime": post_datetime,
            "post_type": post_type,
            "media_url": media_url
        }

    except Exception as e:
        print("Erro ao coletar dados do post:", e)

def get_likes(driver):
    try:        
        likes_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//section//span[contains(text(), 'curtidas') or contains(text(), 'likes')]/span"))
        )
        likes_text = likes_element.text.replace(',', '').replace('.', '')
        
        if 'K' in likes_text:
            likes = int(float(likes_text.replace('K', '')) * 1000)
        elif 'M' in likes_text:
            likes = int(float(likes_text.replace('M', '')) * 1000000)
        else:
            likes = int(likes_text)
            
        print(f"Número total de curtidas: {likes}")
        return likes
    except Exception as e:
        print(f"Erro ao coletar curtidas: {e}\n")
        return 0

def open_likers_list(driver):
    try:
        likers_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//section//span[contains(text(), 'curtidas') or contains(text(), 'likes')]/span"))
        )
        driver.execute_script("arguments[0].click();", likers_button)

        WebDriverWait(driver, 40).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@role='heading'][contains(text(), 'Curtidas') or contains(text(), 'Likes')]"))
        )
    except Exception as e:
        print(f"Erro ao abrir a lista de curtidores: {e}")
"""
def collect_likers(driver, max_scrolls=10):
    open_likers_list(driver)
    
    scroll_top = 0
    like_list = set()
    error_count = 0
    scroll_count = 0
    
    while scroll_count < max_scrolls:
        if error_count > 3:
            print("Erro ao coletar curtidores.")
            break
        
        try:
            likes_div = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@role='heading'][contains(text(), 'Curtidas') or contains(text(), 'Likes')]"))
            )
            likes_container = likes_div.find_element(By.XPATH, "../../../../..")
            likes_list_element = likes_container.find_element(By.CSS_SELECTOR, "& > div:nth-child(2) > div")
            
            list_item_heigth = likes_list_element.find_element(By.CSS_SELECTOR, "& > div > div").size['height']

            
        except TimeoutException:
            print("Erro: 'Curtidas' não encontrado.")
            open_likers_list(driver)
            error_count += 1
            scroll_count = 0
            scroll_top = 0
            time.sleep(1)
            continue
            
        try:
            current_likes_list = likes_list_element.find_elements(By.CSS_SELECTOR, "& > div > div span>div>a span")
            if len(current_likes_list) != 0:
                for liker in current_likes_list:
                    like_list.add(liker.text.strip())
                
                scroll_top += list_item_heigth * len(current_likes_list)
                driver.execute_script("arguments[0].scrollTop = arguments[1];", likes_list_element, scroll_top)
            
            time.sleep(1)
        except Exception as e:
            print("Erro", e)
            break
        
        scroll_count += 1
        
    return like_list
"""

#Computador 2
def collect_likers(driver, max_scrolls=20):
    open_likers_list(driver)  

    like_list = set()
    scroll_count = 0

    try:
        scroll_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]")
            )
        )
    except Exception as e:
        print(f"Erro ao localizar caixa de curtidores: {e}")
        return like_list

    while scroll_count < max_scrolls:
        try:
           
            users = scroll_box.find_elements(By.XPATH, ".//a[contains(@href, '/')]")

            for user in users:
                username = user.get_attribute("href").split("/")[-2]
                if username and username not in like_list:
                    like_list.add(username)

            
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box
            )
            time.sleep(1)
            scroll_count += 1

        except Exception as e:
            print(f"Erro durante o scroll de curtidores: {e}")
            break

    return list(like_list)

def center_window(window, width=400, height=250):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    window.geometry(f'{width}x{height}+{x}+{y}')

def collect_comments(driver):
    try:
        comments_container = driver.find_element(By.CSS_SELECTOR, "article[role=presentation] > div > div:nth-child(2) > div > div> div:nth-child(2) > div > ul > div:last-child > div > div")
        
        comments = []

        comment_elements = comments_container.find_elements(By.CSS_SELECTOR, "& > div > ul > div h3 a[role=link]")

        for comment_element in comment_elements:
            try:
                user_name = comment_element.text.strip()
                if user_name:
                    comments.append(user_name)
            except Exception as e:
                print(f"Erro ao processar comentário: {e}")
        
        comments = list(set(comments))
        
        #print(f"\nUsuários que comentaram coletados: {comments}")
        return comments
    except Exception as e:
        print(f"Erro ao coletar comentários: {e}")
    return []

def scroll_like_human_page(driver, scroll_pause_time=2, max_scrolls=10):
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        time.sleep(scroll_pause_time + random.uniform(0, 2))
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            break
        
        last_height = new_height
        
def search_window(username, password):
    def perform_search():
        search_text = entry.get()
        if not search_text:
            messagebox.showerror("Erro", "Por favor, insira o nome do perfil para pesquisar.")
            return

        root.destroy()
        start_bot(username, password, search_text)

    root = tk.Tk()
    root.title("Pesquisar - Instagram Bot")
    root.configure(bg="#f0f2f5")
    root.geometry("400x250")

    font_text = ("Helvetica", 12)
    font_title = ("Helvetica", 12)

    tk.Label(
        root,
        text="Digite o nome do perfil para pesquisar:",
        font=font_title,
        bg="#f0f2f5",
        fg="#333"
    ).pack(pady=(20, 10))

    entry = tk.Entry(root, width=30, font=font_text, justify="center")
    entry.pack(pady=10)
    entry.focus()

    tk.Button(
        root,
        text="Pesquisar",
        command=perform_search,
        bg="#3897f0",
        fg="white",
        font=font_text,
        relief="raised",
        bd=2,
        padx=10,
        pady=5
    ).pack(pady=10)
    
    if os.path.exists(CREDENTIALS_FILE):
        tk.Button(
            root,
            text="Apagar credenciais",
            command=delete_credentials,
            bg="#f44336", 
            fg="white",
            font=font_text,
            relief="raised",
            bd=2,
            width=15,   
            height=1,  
            padx=5,     
        ).pack(pady=(10, 20))

    root.mainloop()
    
def login_window():
    def save_and_continue():
        username = username_entry.get()
        password = password_entry.get()
        save = save_var.get()

        if not username or not password:
            messagebox.showerror("Erro", "Por favor, insira o nome de usuário e a senha.")
            return

        if save:
            save_credentials(username, password)

        root.destroy()
        search_window(username, password)

    def toggle_password_visibility():
        if password_entry.cget('show') == '*':
            password_entry.config(show="")
            toggle_password_button.config(text="Ocultar senha")
        else:
            password_entry.config(show="*")
            toggle_password_button.config(text="Ver senha")

    root = tk.Tk()
    root.title("Login - Instagram Bot")
    root.configure(bg="#f7f7f7")
    root.geometry("400x350")
    root.resizable(False, False)  

    font_text = ("Helvetica", 12)
    entry_font = ("Helvetica", 12)

    # título
    tk.Label(
        root,
        text="Login - Instagram Bot",
        font=("Helvetica", 16, "bold"),
        bg="#f7f7f7",
        fg="#333"
    ).pack(pady=(20, 10))

    frame = tk.Frame(root, bg="#f7f7f7")
    frame.pack(pady=10)

    #nome de usuário
    tk.Label(
        frame,
        text="Nome de usuário ou e-mail:",
        font=font_text,
        bg="#f7f7f7",
        fg="#333",
        anchor="w" 
    ).grid(row=0, column=0, pady=(5, 2), sticky="w")

    username_entry = tk.Entry(frame, width=30, font=entry_font, justify="left", bd=2, relief="solid", fg="#333")
    username_entry.grid(row=1, column=0, pady=(0, 10), sticky="w")
    if saved_user:
        username_entry.insert(0, saved_user)

    #senha
    tk.Label(
        frame,
        text="Senha:",
        font=font_text,
        bg="#f7f7f7",
        fg="#333",
        anchor="w"
    ).grid(row=2, column=0, pady=(10, 2), sticky="w")

    password_frame = tk.Frame(frame, bg="#f7f7f7")
    password_frame.grid(row=3, column=0, pady=(0, 15), sticky="w")

    password_var = tk.StringVar()
    password_entry = tk.Entry(password_frame, textvariable=password_var, width=25, font=entry_font, justify="left", show="*", bd=2, relief="solid", fg="#333")
    password_entry.pack(side=tk.LEFT)

    if saved_pass:
        password_entry.insert(0, saved_pass)

    toggle_password_button = tk.Button(
        password_frame,
        text="Ver senha",
        command=toggle_password_visibility,
        font=font_text,
        bg="#D3D3D3",
        fg="#333",
        relief="solid",
        bd=2,
        padx=10,
        pady=5
    )
    toggle_password_button.pack(side=tk.LEFT)

    save_var = tk.BooleanVar()
    save_checkbox = tk.Checkbutton(
        root,
        text="Salvar credenciais",
        variable=save_var,
        font=font_text,
        bg="#f7f7f7",
        fg="#333",
        anchor="w"
    )
    save_checkbox.pack(pady=(5, 10), anchor="w")

    tk.Button(
        root,
        text="Continuar",
        command=save_and_continue,
        bg="#3897f0",
        fg="white",
        font=font_text,
        relief="raised",
        bd=2,
        padx=10,
        pady=8,
        width=20
    ).pack(pady=10)

    root.mainloop()

def download_media(url, folder="imagens", filename="media"):
    if not url:
        return None
    
    if url.startswith("blob:"):
        print("URL é um blob (vídeo), ignorando download.")
        return None
    
    base_folder = os.path.dirname(os.path.abspath(__file__))  
    folder_path = os.path.join(base_folder, folder)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    try:
        ext = url.split("?")[0].split(".")[-1]
        if len(ext) > 5:
            ext = "jpg"

        filepath = os.path.join(folder_path, f"{filename}.{ext}")

        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            #print(f"Arquivo salvo em {filepath}")
            return filepath
        else:
            print(f"Erro ao baixar mídia: Status {r.status_code}")
            return None
    except Exception as e:
        print(f"Erro ao baixar mídia: {e}")
        return None
    
def save_to_csv(file_name, posts_data):
    with open(file_name, mode="w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "Post_ID", "Username", "Description", "Datetime",
            "Type", "Likes", "Likers", "Comments","Media_URL", "Media_File" 
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for post in posts_data:
            likers_str = ";".join(post.get("Likers", []))
            comments_str = json.dumps(post.get("Comments", []), ensure_ascii=False)
            writer.writerow({
                "Post_ID": post.get("Post_ID", ""),
                "Username": post.get("Username", ""),
                "Description": post.get("Description", ""),
                "Datetime": post.get("Datetime", ""),
                "Type": post.get("Type", ""),
                "Likes": post.get("Likes", 0),
                "Likers": likers_str,
                "Comments": comments_str,
                "Media_URL": post.get("Media_URL", ""),
                "Media_File": post.get("Media_File", "")
            })
    #print(f"Dados exportados com sucesso para '{file_name}'.")

def show_dashboard(csv_file):
    sns.set_theme(style="whitegrid")

    df = pd.read_csv(csv_file)

    df["Datetime"] = pd.to_datetime(df["Datetime"], errors='coerce')
    df["Hour"] = df["Datetime"].dt.hour
    df["Likers_List"] = df["Likers"].apply(lambda x: x.split(";") if pd.notna(x) and x != '' else [])
    df["Comments_List"] = df["Comments"].apply(lambda x: ast.literal_eval(x) if pd.notna(x) and x != '' else [])

    window = tk.Tk()
    window.title("Dashboard Instagram")
    window.geometry("1000x700")

    notebook = ttk.Notebook(window)
    notebook.pack(padx=10, pady=10, fill="both", expand=True)

    # Curtidas por Post
    tab1 = tk.Frame(notebook)
    notebook.add(tab1, text="Curtidas por Post")
    
    tab1.grid_rowconfigure(0, weight=1)  
    tab1.grid_rowconfigure(1, weight=2)  
    tab1.grid_columnconfigure(0, weight=1)

    frame_top = tk.Frame(tab1)
    frame_top.grid(row=0, column=0, sticky="nsew")

    frame_bottom = tk.Frame(tab1)
    frame_bottom.grid(row=1, column=0, sticky="nsew")

    frame_bottom.grid_columnconfigure(0, weight=1)
    frame_bottom.grid_columnconfigure(1, weight=2)
    frame_bottom.grid_rowconfigure(0, weight=1)

    frame_image = tk.Frame(frame_bottom, bg="#f0f2f5")
    frame_image.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    frame_text_container = tk.Frame(frame_bottom, bg="#f0f2f5")
    frame_text_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    text_scrollbar = tk.Scrollbar(frame_text_container)
    text_scrollbar.pack(side="right", fill="y")

    details_text = tk.Text(
        frame_text_container,
        yscrollcommand=text_scrollbar.set,
        wrap="word", 
        font=("Arial", 12),
        bg="#f0f2f5",
        relief="flat"
    )
    details_text.pack(fill="both", expand=True)
    
    text_scrollbar.config(command=details_text.yview)
    
    image_label = tk.Label(frame_image, bg="#f0f2f5")
    image_label.pack(padx=10, pady=10, anchor="n")

    # Plot com Seaborn e interação de clique
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    barplot = sns.barplot(x="Post_ID", y="Likes", data=df, ax=ax1, color="#00aaff")
    ax1.set_title("Curtidas por Post")
    ax1.set_xlabel("Post ID")
    ax1.set_ylabel("Curtidas")
    ax1.tick_params(axis='x', rotation=45)
    plt.tight_layout()

    canvas1 = FigureCanvasTkAgg(fig1, master=frame_top)
    canvas1.draw()
    canvas1.get_tk_widget().pack()

    # Habilita clique nas barras
    bars = barplot.patches
    post_bars = {bar: idx for idx, bar in enumerate(bars)}  # mapa de barra → índice

    def resize_image_keep_aspect(img, max_width=540, max_height=675):
        width, height = img.size
        ratio = min(max_width / width, max_height / height)
        new_size = (int(width * ratio), int(height * ratio))
        return img.resize(new_size, Image.LANCZOS)

    def show_post_details(index):
        post = df.iloc[index]

        desc = post["Description"]
        dt = post["Datetime"]
        post_type = post["Type"]
        media_file = post["Media_File"]

        details = f"""Data: {dt}

Descrição: {desc}

Tipo: {post_type}
"""
        details_text.delete("1.0", tk.END)
        details_text.insert(tk.END, details)

        if post_type.lower() == "foto" and pd.notna(media_file) and os.path.exists(media_file):
            try:
                img = Image.open(media_file)
                img = resize_image_keep_aspect(img, max_width=600, max_height=600)
                img_tk = ImageTk.PhotoImage(img)
                image_label.config(image=img_tk, text="")
                image_label.image = img_tk
            except Exception as e:
                image_label.config(image="", text="Erro ao carregar imagem")
                print(f"Erro ao carregar imagem: {e}")
        else:
            image_label.config(image="", text="Este post é um vídeo ou não possui imagem.")
            image_label.image = None

    def on_bar_click(event):
        if event.artist in post_bars:
            index = post_bars[event.artist]
            show_post_details(index)

    canvas1.mpl_connect("pick_event", on_bar_click)
    for bar in bars:
        bar.set_picker(True)

    # Usuário mais Engajado
    tab2 = tk.Frame(notebook)
    notebook.add(tab2, text="Usuário mais Engajado")

    likers_counter = Counter()
    for likers in df["Likers_List"]:
        likers_counter.update(likers)

    comments_counter = Counter()
    for comments in df["Comments_List"]:
        for comment in comments:
            if ":" in comment:
                username = comment.split(":")[0].strip()
                comments_counter[username] += 1
            else:
                comments_counter[comment.strip()] += 1

    total_interactions = likers_counter + comments_counter
    most_active = total_interactions.most_common(10)
    users, counts = zip(*most_active) if most_active else ([], [])

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    sns.barplot(x=counts, y=users, ax=ax2, color="#ffa500")
    ax2.set_title("Top 10 Usuários Mais Engajados")
    ax2.set_xlabel("Interações (Curtidas + Comentários)")
    ax2.set_ylabel("Usuário")
    plt.tight_layout()

    canvas2 = FigureCanvasTkAgg(fig2, master=tab2)
    canvas2.draw()
    canvas2.get_tk_widget().pack()

    # Melhor Horário
    tab3 = tk.Frame(notebook)
    notebook.add(tab3, text="Melhor Horário")

    hourly_likes = df.groupby("Hour")["Likes"].mean().fillna(0)

    fig3, ax3 = plt.subplots(figsize=(6, 4))
    sns.lineplot(x=hourly_likes.index, y=hourly_likes.values, marker='o', ax=ax3, color="#4CAF50")
    ax3.set_title("Média de Curtidas por Hora")
    ax3.set_xlabel("Hora do Dia")
    ax3.set_ylabel("Média de Curtidas")
    ax3.set_xticks(range(0, 24))
    plt.grid(True)
    plt.tight_layout()

    canvas3 = FigureCanvasTkAgg(fig3, master=tab3)
    canvas3.draw()
    canvas3.get_tk_widget().pack()

    # Tipos de Post 
    tab4 = tk.Frame(notebook)
    notebook.add(tab4, text="Tipos de Post")

    type_likes = df.groupby("Type")["Likes"].sum()

    fig4, ax4 = plt.subplots(figsize=(5, 5))
    ax4.pie(type_likes, labels=type_likes.index, autopct='%1.1f%%', startangle=90)
    ax4.set_title("Distribuição de Curtidas por Tipo de Post")
    plt.tight_layout()

    canvas4 = FigureCanvasTkAgg(fig4, master=tab4)
    canvas4.draw()
    canvas4.get_tk_widget().pack()

    def on_close():
        if messagebox.askokcancel("Sair", "Deseja encerrar o programa?"):
            window.destroy()
            sys.exit()

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()
    
def start_bot(username, password, search_text):
    progress_window = tk.Tk()
    progress_window.title("Progresso da Coleta")
    progress_window.geometry("400x150")
    progress_window.configure(bg="#f0f2f5")
    progress_window.lift()
    progress_window.attributes('-topmost', True)

    tk.Label(
        progress_window,
        text="Coletando dados...",
        font=("Helvetica", 12),
        bg="#f0f2f5",
        fg="#333"
    ).pack(pady=10)
    
    progressbar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
    progressbar.pack(pady=20)

    progress_window.update()
    
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    login(driver, username, password)
    #print("Login realizado com sucesso.")
    
    click_search_icon(driver)
    type_in_search_field(driver, search_text)
    click_first_search_result(driver, search_text)

    scroll_like_human_page(driver, scroll_pause_time=2, max_scrolls=10)
    
    elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "main > div > div:nth-child(3) a"))
    ) 
    
    posts_data = []
    total_posts = len(elements)
    progressbar['maximum'] = total_posts  

    for index in range(total_posts):
        time.sleep(1)
        print(f"Clicando no post {index + 1} de {total_posts}")
        elements[index].click()
        time.sleep(2)
        
        print(f"Coletando dados do post {index + 1}...")
        post_details = get_post_details(driver)
        time.sleep(2)
        
        post_id_value = post_id(driver)
        time.sleep(2)
                
        likes = get_likes(driver)
        time.sleep(1)
    
        open_likers_list(driver)
        time.sleep(2)
        likers = collect_likers(driver, max_scrolls=5)
        print(f"\nUsuários que curtiram coletados: {likers}")
        print(f"Total de curtidores coletados: {len(likers)}")
        time.sleep(1)
    
        comments = collect_comments(driver)
        time.sleep(2)
        
        media_path = download_media(
        post_details["media_url"],
        folder="./imagens",   
        filename=post_id_value
        )
        
        post_data = {
        "Post_ID": post_id_value,
        "Username": post_details["author"],
        "Description": post_details["description"],
        "Datetime": post_details["post_datetime"].strftime("%Y-%m-%d %H:%M:%S"),  
        "Type": post_details["post_type"],
        "Likes": likes,
        "Likers": likers,
        "Comments": comments,
        "Media_URL": post_details["media_url"],
        "Media_File": media_path
        }
        posts_data.append(post_data)
            
        driver.back()
        time.sleep(2)
        
        progressbar['value'] = index + 1
        progress_window.update()
    
    file_name = f"{search_text}_posts_data.csv"
 
    save_to_csv(file_name, posts_data)

    driver.quit()   
    progress_window.destroy()  
    print("Coleta concluída!")

    df = pd.read_csv(file_name)
    show_dashboard(file_name)

username, password = load_credentials()

if username and password:
    search_window(username, password)
else:
    login_window()