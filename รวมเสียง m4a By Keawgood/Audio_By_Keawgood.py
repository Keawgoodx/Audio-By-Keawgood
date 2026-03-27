import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import moviepy.editor # pyright: ignore[reportMissingImports]

# --- การตั้งค่าภาษา ---
LANGUAGES = {
    "TH": {
        "app_name": "Audio By Keawgood",
        "menu": "เมนูหลัก",
        "appearance_settings": "ตั้งค่าลักษณะ",
        "font_size": "ขนาดตัวอักษร:",
        "theme": "โหมดสี:",
        "lang_btn": "English",
        
        "select_audio": "1. เลือกไฟล์เสียง (.m4a)",
        "select_image": "2. เลือกรูปภาพ (.jpg/.png)",
        "select_output": "3. เลือกโฟลเดอร์ปลายทาง",
        "merge_settings": "4. ตั้งค่าการรวมและชื่อไฟล์",
        "filename_label": "ตั้งชื่อไฟล์ผลลัพธ์ (ไม่ต้องใส่ .mp4):",
        "chunk_label": "ระบุจำนวนคลิปที่จะรวมเป็น 1 ไฟล์:",
        "start": "เริ่มสร้างวิดีโอ",
        
        "status_idle": "สถานะ: พร้อมทำงาน",
        "status_done": "เสร็จสมบูรณ์!",
        "error_select": "กรุณาเลือกไฟล์และโฟลเดอร์ให้ครบถ้วน",
        "error_number": "กรุณาพิมพ์ตัวเลขจำนวนเต็มที่มากกว่า 0",
        "processing": "กำลังเรนเดอร์ไฟล์ที่ {current}/{total}...",
        "files_selected": "เลือกแล้ว {count} ไฟล์",
        "img_selected": "เลือกรูปภาพแล้ว",
        "output_selected": "บันทึกที่: {path}"
    },
    "EN": {
        "app_name": "Audio By Keawgood",
        "menu": "Main Menu",
        "appearance_settings": "Appearance Settings",
        "font_size": "Font Size:",
        "theme": "Theme Mode:",
        "lang_btn": "ภาษาไทย",
        
        "select_audio": "1. Select Audio (.m4a)",
        "select_image": "2. Select Image (.jpg/.png)",
        "select_output": "3. Select Output Folder",
        "merge_settings": "4. Merge & Naming Settings",
        "filename_label": "Output Filename (no .mp4):",
        "chunk_label": "Enter number of clips to merge into 1 file:",
        "start": "Start Rendering",
        
        "status_idle": "Status: Ready",
        "status_done": "Completed!",
        "error_select": "Please select all required files and folder",
        "error_number": "Please enter a valid number greater than 0",
        "processing": "Rendering file {current}/{total}...",
        "files_selected": "{count} files selected",
        "img_selected": "Image selected",
        "output_selected": "Save to: {path}"
    }
}

class AudioByKeawgood(ctk.CTk):
    def __init__(self):
        super().__init__()

        # การตั้งค่าพื้นฐานของ Window
        self.title("Audio By Keawgood - Batch Audio to Video")
        self.geometry("850x650")
        self.current_lang = "TH"
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # --- การตั้งค่า Font (TH Sarabun PSK) ---
        # Fallback fonts: If Sarabun is not present, use Sarabun New or Arial.
        font_families = ["TH Sarabun PSK", "Sarabun New", "Arial"]
        self.current_font_size = 14
        
        self.font = ctk.CTkFont(family=font_families[0], size=self.current_font_size)
        self.font_bold = ctk.CTkFont(family=font_families[0], size=self.current_font_size, weight="bold")
        
        # Check if the primary font exists, otherwise try fallbacks
        try:
            temp_font = ctk.CTkFont(family=font_families[0])
            self.font.configure(family=font_families[0])
            self.font_bold.configure(family=font_families[0])
        except Exception:
            try:
                self.font.configure(family=font_families[1])
                self.font_bold.configure(family=font_families[1])
            except Exception:
                self.font.configure(family=font_families[2])
                self.font_bold.configure(family=font_families[2])
        
        # ตัวแปรเก็บข้อมูลอื่น
        self.audio_paths = []
        self.image_path = ""
        self.output_dir = ""
        self.chunk_size = 1

        self.setup_ui()

    def update_font_size(self, value):
        # Update current size and configure the fonts
        self.current_font_size = int(value)
        self.font.configure(size=self.current_font_size)
        self.font_bold.configure(size=self.current_font_size)
        
        # Update the display label next to the slider
        self.lbl_font_size_display.configure(text=f"{self.current_font_size} pt")

    def setup_ui(self):
        L = LANGUAGES[self.current_lang]
        
        # ================= Sidebar (แถบด้านข้าง) =================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")

        # Static Title (Use a slightly larger non-dynamic bold font)
        title_font = ("TH Sarabun PSK", 22, "bold")
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text=L["app_name"], font=title_font)
        self.logo_label.pack(pady=(30, 10), padx=20)

        # Main Menu Label
        self.lbl_menu = ctk.CTkLabel(self.sidebar_frame, text=L["menu"], text_color="gray", font=self.font)
        self.lbl_menu.pack(pady=(10, 5))

        # Language Button
        self.lang_btn = ctk.CTkButton(self.sidebar_frame, text=L["lang_btn"], 
                                      command=self.toggle_language, fg_color="transparent", 
                                      border_width=1, text_color=("gray10", "#DCE4EE"), font=self.font)
        self.lang_btn.pack(pady=10, padx=20)
        
        # --- Appearance Settings Group (Font & Theme) ---
        self.frame_appearance = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.frame_appearance.pack(pady=(20, 10), fill="x", padx=10)
        
        self.lbl_appearance = ctk.CTkLabel(self.frame_appearance, text=L["appearance_settings"], text_color="gray", font=self.font_bold)
        self.lbl_appearance.pack(pady=(10, 5))

        # Font Size Slider
        self.lbl_font_size = ctk.CTkLabel(self.frame_appearance, text=L["font_size"], font=self.font)
        self.lbl_font_size.pack(pady=(5, 0))
        
        self.lbl_font_size_display = ctk.CTkLabel(self.frame_appearance, text=f"{self.current_font_size} pt", text_color="#3498db", font=self.font_bold)
        self.lbl_font_size_display.pack(pady=(0, 5))

        self.slider_font_size = ctk.CTkSlider(self.frame_appearance, from_=10, to=30, number_of_steps=20, command=self.update_font_size)
        self.slider_font_size.set(self.current_font_size)
        self.slider_font_size.pack(pady=(0, 15), padx=20)

        # Theme Mode Menu
        self.lbl_theme = ctk.CTkLabel(self.frame_appearance, text=L["theme"], font=self.font)
        self.lbl_theme.pack(pady=(5, 0))
        self.appearance_mode_menu = ctk.CTkOptionMenu(self.frame_appearance, values=["Dark", "Light"], 
                                                       command=self.change_appearance_mode, font=self.font)
        self.appearance_mode_menu.pack(pady=10, padx=20)

        # ================= Main Content (พื้นที่หลัก) =================
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=15)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # 1. ส่วนเลือกไฟล์เสียง
        self.frame_audio = ctk.CTkFrame(self.main_frame, fg_color=("gray90", "gray15"))
        self.frame_audio.pack(fill="x", pady=10, padx=10)
        self.btn_audio = ctk.CTkButton(self.frame_audio, text=L["select_audio"], command=self.select_audio, font=self.font)
        self.btn_audio.pack(side="left", pady=15, padx=20)
        self.lbl_audio_status = ctk.CTkLabel(self.frame_audio, text="0 files", font=self.font)
        self.lbl_audio_status.pack(side="left", padx=10)

        # 2. ส่วนเลือกรุปภาพ
        self.frame_image = ctk.CTkFrame(self.main_frame, fg_color=("gray90", "gray15"))
        self.frame_image.pack(fill="x", pady=10, padx=10)
        self.btn_image = ctk.CTkButton(self.frame_image, text=L["select_image"], 
                                       fg_color="#2ecc71", hover_color="#27ae60", command=self.select_image, font=self.font)
        self.btn_image.pack(side="left", pady=15, padx=20)
        self.lbl_image_status = ctk.CTkLabel(self.frame_image, text="", font=self.font)
        self.lbl_image_status.pack(side="left", padx=10)

        # 3. ส่วนเลือกปลายทาง
        self.frame_output = ctk.CTkFrame(self.main_frame, fg_color=("gray90", "gray15"))
        self.frame_output.pack(fill="x", pady=10, padx=10)
        self.btn_output = ctk.CTkButton(self.frame_output, text=L["select_output"], 
                                        fg_color="#e67e22", hover_color="#d35400", command=self.select_output, font=self.font)
        self.btn_output.pack(side="left", pady=15, padx=20)
        self.lbl_output_status = ctk.CTkLabel(self.frame_output, text="", wraplength=400, justify="left", font=self.font)
        self.lbl_output_status.pack(side="left", padx=10, pady=10)

        # 4. ตั้งค่าจำนวนไฟล์และชื่อ (Settings)
        self.frame_settings = ctk.CTkFrame(self.main_frame, fg_color=("gray90", "gray15"))
        self.frame_settings.pack(fill="x", pady=10, padx=10)
        
        self.lbl_settings = ctk.CTkLabel(self.frame_settings, text=L["merge_settings"], font=self.font_bold)
        self.lbl_settings.pack(pady=(10, 5))
        
        # 4.1 กล่องตั้งชื่อไฟล์
        self.lbl_filename = ctk.CTkLabel(self.frame_settings, text=L["filename_label"], font=self.font)
        self.lbl_filename.pack(pady=(5, 0))
        self.entry_filename = ctk.CTkEntry(self.frame_settings, placeholder_text="เช่น นิยายเรื่อง...", width=300, justify="center", font=self.font)
        self.entry_filename.insert(0, "Audio_Output")
        self.entry_filename.pack(pady=(0, 15))

        # 4.2 กล่องระบุจำนวนคลิป
        self.lbl_chunk = ctk.CTkLabel(self.frame_settings, text=L["chunk_label"], font=self.font)
        self.lbl_chunk.pack(pady=(0, 0))
        self.entry_chunk = ctk.CTkEntry(self.frame_settings, placeholder_text="เช่น 10, 50 หรือจำนวนทั้งหมด", width=300, justify="center", font=self.font)
        self.entry_chunk.insert(0, "1") 
        self.entry_chunk.pack(pady=(0, 15))

        # --- Progress & Action ---
        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(20, 10), fill="x", padx=20)

        self.lbl_status = ctk.CTkLabel(self.main_frame, text=L["status_idle"], text_color="#3498db", font=self.font)
        self.lbl_status.pack()

        # Start button uses the dynamic bold font
        self.btn_start = ctk.CTkButton(self.main_frame, text=L["start"], 
                                       height=50, fg_color="#e74c3c", hover_color="#c0392b",
                                       command=self.start_process_thread, font=self.font_bold)
        self.btn_start.pack(pady=20, padx=20, fill="x")

    # ================= ฟังก์ชันการทำงาน =================

    def toggle_language(self):
        self.current_lang = "EN" if self.current_lang == "TH" else "TH"
        self.update_ui_texts()

    def update_ui_texts(self):
        L = LANGUAGES[self.current_lang]
        self.logo_label.configure(text=L["app_name"])
        self.lbl_menu.configure(text=L["menu"])
        self.lbl_appearance.configure(text=L["appearance_settings"])
        self.lbl_font_size.configure(text=L["font_size"])
        self.lbl_font_size_display.configure(text=f"{self.current_font_size} pt")
        self.lbl_theme.configure(text=L["theme"])
        self.appearance_mode_menu.configure(values=["Dark", "Light"])
        
        self.btn_audio.configure(text=L["select_audio"])
        self.btn_image.configure(text=L["select_image"])
        self.btn_output.configure(text=L["select_output"])
        self.lbl_settings.configure(text=L["merge_settings"])
        self.lbl_filename.configure(text=L["filename_label"])
        self.lbl_chunk.configure(text=L["chunk_label"])
        self.btn_start.configure(text=L["start"])
        self.lang_btn.configure(text=L["lang_btn"])
        self.lbl_status.configure(text=L["status_idle"])
        
        if self.audio_paths:
            self.lbl_audio_status.configure(text=L["files_selected"].format(count=len(self.audio_paths)))
        if self.image_path:
            self.lbl_image_status.configure(text=L["img_selected"])
        if self.output_dir:
            self.lbl_output_status.configure(text=L["output_selected"].format(path=self.output_dir))

    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)

    def select_audio(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio files", "*.m4a *.mp3 *.wav")])
        if files:
            self.audio_paths = sorted(list(files)) 
            total_files = len(self.audio_paths)
            self.lbl_audio_status.configure(text=LANGUAGES[self.current_lang]["files_selected"].format(count=total_files))
            
            # อัปเดตตัวเลขในช่องกรอกให้อัตโนมัติ เพื่อรวมทุกไฟล์เป็น 1 ไฟล์เสมอ
            self.entry_chunk.delete(0, 'end')
            self.entry_chunk.insert(0, str(total_files))

    def select_image(self):
        file = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file:
            self.image_path = file
            self.lbl_image_status.configure(text=LANGUAGES[self.current_lang]["img_selected"])

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir = path
            self.lbl_output_status.configure(text=LANGUAGES[self.current_lang]["output_selected"].format(path=path))

    def start_process_thread(self):
        if not self.audio_paths or not self.image_path or not self.output_dir:
            messagebox.showwarning("Error", LANGUAGES[self.current_lang]["error_select"])
            return
        
        try:
            val = int(self.entry_chunk.get())
            if val <= 0:
                raise ValueError
            self.chunk_size = val
        except ValueError:
            messagebox.showwarning("Error", LANGUAGES[self.current_lang]["error_number"])
            return

        # ล็อค UI ชั่วคราว
        self.btn_start.configure(state="disabled")
        self.entry_chunk.configure(state="disabled")
        self.entry_filename.configure(state="disabled")
        self.slider_font_size.configure(state="disabled") # ล็อค SliderFont ด้วย
        
        threading.Thread(target=self.process_files, daemon=True).start()

    def process_files(self):
        L = LANGUAGES[self.current_lang]
        files = self.audio_paths
        chunk_size = self.chunk_size
        
        base_filename = self.entry_filename.get().strip()
        if not base_filename:
            base_filename = "Audio_Output"
        
        total_chunks = (len(files) + chunk_size - 1) // chunk_size

        for i in range(0, len(files), chunk_size):
            current_chunk_index = (i // chunk_size) + 1
            chunk_files = files[i:i + chunk_size]
            
            self.lbl_status.configure(text=L["processing"].format(current=current_chunk_index, total=total_chunks))
            self.progress_bar.set(current_chunk_index / total_chunks)

            try:
                # 1. รวมเสียง
                audio_clips = [moviepy.editor.AudioFileClip(f) for f in chunk_files]
                final_audio = moviepy.editor.concatenate_audioclips(audio_clips)

                # 2. ทำภาพประกอบเสียง
                img_clip = moviepy.editor.ImageClip(self.image_path)
                img_clip = img_clip.set_duration(final_audio.duration)
                img_clip = img_clip.set_audio(final_audio)

                # 3. ตั้งชื่อไฟล์ Output 
                if total_chunks == 1:
                    output_filename = f"{base_filename}.mp4"
                else:
                    output_filename = f"{base_filename}_Part_{current_chunk_index}.mp4"
                
                output_path = os.path.join(self.output_dir, output_filename)

                # 4. สั่งเรนเดอร์
                img_clip.write_videofile(output_path, fps=1, codec="libx264", audio_codec="aac", logger=None)

                # เคลียร์หน่วยความจำ
                for clip in audio_clips:
                    clip.close()
                final_audio.close()
                img_clip.close()

            except Exception as e:
                print(f"Error processing chunk {current_chunk_index}: {e}")

        # ปลดล็อค UI เมื่อเสร็จสิ้น
        self.lbl_status.configure(text=L["status_done"])
        self.btn_start.configure(state="normal")
        self.entry_chunk.configure(state="normal")
        self.entry_filename.configure(state="normal")
        self.slider_font_size.configure(state="normal") # ปลดล็อค SliderFont
        
        messagebox.showinfo("Success", L["status_done"])

if __name__ == "__main__":
    app = AudioByKeawgood()
    app.mainloop()