import tkinter as tk
from tkinter import messagebox
import sqlite3
import random
import string
import datetime
import webbrowser

# Database setup
conn = sqlite3.connect('url_shortener.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_url TEXT NOT NULL UNIQUE,
                clicks INTEGER DEFAULT 0,
                date_created TEXT DEFAULT CURRENT_TIMESTAMP
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                referrer TEXT,
                ip_address TEXT,
                FOREIGN KEY(url_id) REFERENCES urls(id)
            )''')

conn.commit()


# Function to generate a random short URL
def generate_short_url():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))


# Function to shorten the URL
def shorten_url(original_url):
    short_url = generate_short_url()
    try:
        c.execute("INSERT INTO urls (original_url, short_url) VALUES (?, ?)", (original_url, short_url))
        conn.commit()
        return short_url
    except sqlite3.IntegrityError:
        return shorten_url(original_url)


# Function to record a click
def record_click(short_url, referrer=None, ip_address=None):
    c.execute("SELECT id FROM urls WHERE short_url = ?", (short_url,))
    url_id = c.fetchone()[0]
    c.execute("INSERT INTO clicks (url_id, referrer, ip_address) VALUES (?, ?, ?)", (url_id, referrer, ip_address))
    c.execute("UPDATE urls SET clicks = clicks + 1 WHERE id = ?", (url_id,))
    conn.commit()


# Function to get the original URL from the short URL
def get_original_url(short_url):
    c.execute("SELECT original_url FROM urls WHERE short_url = ?", (short_url,))
    result = c.fetchone()
    return result[0] if result else None


# Function to get analytics for a specific short URL
def get_analytics(short_url):
    c.execute("SELECT clicks FROM urls WHERE short_url = ?", (short_url,))
    clicks = c.fetchone()[0]

    c.execute(
        "SELECT timestamp, referrer, ip_address FROM clicks WHERE url_id = (SELECT id FROM urls WHERE short_url = ?)",
        (short_url,))
    click_data = c.fetchall()

    return clicks, click_data


# GUI Application
class URLShortenerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Shortener with Analytics")
        self.root.geometry("400x300")

        self.url_label = tk.Label(root, text="Enter URL:")
        self.url_label.pack(pady=5)

        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack(pady=5)

        self.shorten_button = tk.Button(root, text="Shorten URL", command=self.shorten_url)
        self.shorten_button.pack(pady=5)

        self.result_label = tk.Label(root, text="")
        self.result_label.pack(pady=5)

        self.analytics_button = tk.Button(root, text="View Analytics", command=self.view_analytics)
        self.analytics_button.pack(pady=5)

        self.open_url_button = tk.Button(root, text="Open Short URL", command=self.open_short_url)
        self.open_url_button.pack(pady=5)

    def shorten_url(self):
        original_url = self.url_entry.get()
        if original_url:
            short_url = shorten_url(original_url)
            self.result_label.config(text=f"Short URL: {short_url}")
        else:
            messagebox.showwarning("Warning", "Please enter a URL")

    def view_analytics(self):
        short_url = self.result_label.cget("text").split("Short URL: ")[-1]
        if short_url:
            clicks, click_data = get_analytics(short_url)
            analytics_text = f"Total Clicks: {clicks}\n\n"
            analytics_text += "Timestamp, Referrer, IP Address\n"
            analytics_text += "-" * 40 + "\n"
            for data in click_data:
                analytics_text += f"{data[0]}, {data[1]}, {data[2]}\n"
            messagebox.showinfo("Analytics", analytics_text)
        else:
            messagebox.showwarning("Warning", "No URL to analyze")

    def open_short_url(self):
        short_url = self.result_label.cget("text").split("Short URL: ")[-1]
        if short_url:
            original_url = get_original_url(short_url)
            if original_url:
                record_click(short_url)
                webbrowser.open(original_url)
            else:
                messagebox.showerror("Error", "Invalid Short URL")
        else:
            messagebox.showwarning("Warning", "No URL to open")


if __name__ == "__main__":
    root = tk.Tk()
    app = URLShortenerApp(root)
    root.mainloop()

    # Close the database connection when the app closes
    conn.close()
