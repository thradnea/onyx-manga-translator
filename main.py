# main.py

import os
import sys
from tkinter import PhotoImage, Toplevel, Label
from app import App


def resource_path(relative_path: str):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


if hasattr(sys, '_MEIPASS'):
    cache_dir = os.path.join(sys._MEIPASS, 'transformers_cache')
    os.environ['HF_HOME'] = cache_dir
    os.environ['TRANSFORMERS_CACHE'] = cache_dir
    os.environ['HF_HUB_CACHE'] = cache_dir

if __name__ == "__main__":
    app = App()
    app.withdraw()

    splash = Toplevel(app)
    splash.overrideredirect(True)  # No title bar

    splash_img = PhotoImage(file=resource_path("splash.png"))

    transparent_color = '#abcdef'
    splash.config(bg=transparent_color)
    splash.wm_attributes('-transparentcolor', transparent_color)

    Label(splash, image=splash_img, bg=transparent_color).pack()

    w, h = splash_img.width(), splash_img.height()
    x = (splash.winfo_screenwidth() - w) // 2
    y = (splash.winfo_screenheight() - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")


    def close_splash():
        """Destroy the splash screen and show the main window."""
        splash.destroy()
        app.deiconify()


    splash.after(2000, close_splash)

    app.mainloop()