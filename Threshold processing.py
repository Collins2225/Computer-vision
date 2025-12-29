import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import os


class ThresholdProcessingApp:
    """
    Threshold processing (binary threshold)

    GUI structure (3 frames):
      1) Control Frame  - buttons + threshold slider
      2) Input Frame    - original image + its histogram
      3) Output Frame   - thresholded image + its histogram
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Threshold Processing")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 620)

        self.original_image = None   # PIL RGB
        self.output_image = None     # PIL RGB (thresholded)
        self.tk_in = None
        self.tk_out = None

        self._build_ui()

        # refresh on resize
        self.input_canvas.bind("<Configure>", lambda e: self._refresh_all())
        self.output_canvas.bind("<Configure>", lambda e: self._refresh_all())
        self.input_hist.bind("<Configure>", lambda e: self._refresh_all())
        self.output_hist.bind("<Configure>", lambda e: self._refresh_all())

    # ---------------- UI ----------------
    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # 1) CONTROL FRAME
        self.control_frame = ttk.LabelFrame(self.root, text="Control Frame")
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        self.control_frame.columnconfigure(99, weight=1)

        ttk.Button(self.control_frame, text="Load Image", command=self.load_image).grid(
            row=0, column=0, padx=8, pady=10, sticky="w"
        )
        ttk.Button(self.control_frame, text="Apply Threshold", command=self.apply_threshold).grid(
            row=0, column=1, padx=8, pady=10, sticky="w"
        )
        ttk.Button(self.control_frame, text="Reset", command=self.reset).grid(
            row=0, column=2, padx=8, pady=10, sticky="w"
        )
        ttk.Button(self.control_frame, text="Save Output", command=self.save_output).grid(
            row=0, column=3, padx=8, pady=10, sticky="w"
        )

        ttk.Separator(self.control_frame, orient="vertical").grid(
            row=0, column=4, sticky="ns", padx=10, pady=6
        )

        ttk.Label(self.control_frame, text="Threshold:").grid(row=0, column=5, padx=(0, 6), pady=10, sticky="w")

        self.threshold_var = tk.IntVar(value=128)
        self.threshold_scale = ttk.Scale(
            self.control_frame, from_=0, to=255, orient="horizontal",
            command=self._on_threshold_change
        )
        self.threshold_scale.set(128)
        self.threshold_scale.grid(row=0, column=6, padx=6, pady=10, sticky="ew")
        self.control_frame.columnconfigure(6, weight=1)

        self.threshold_label = ttk.Label(self.control_frame, text="128")
        self.threshold_label.grid(row=0, column=7, padx=(6, 12), pady=10, sticky="w")

        self.status_var = tk.StringVar(value="Ready - Load an image.")
        ttk.Label(self.control_frame, textvariable=self.status_var).grid(
            row=0, column=99, padx=8, pady=10, sticky="e"
        )

        # container for input/output
        container = ttk.Frame(self.root)
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6, 10))
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # 2) INPUT FRAME
        self.input_frame = ttk.LabelFrame(container, text="Input Frame (Original Image + Histogram)")
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.input_frame.columnconfigure(0, weight=1)
        self.input_frame.rowconfigure(0, weight=3)
        self.input_frame.rowconfigure(1, weight=2)

        self.input_canvas = tk.Canvas(self.input_frame, bg="white", highlightthickness=1)
        self.input_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 6))

        self.input_hist = tk.Canvas(self.input_frame, bg="white", highlightthickness=1, height=200)
        self.input_hist.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6, 10))

        # 3) OUTPUT FRAME
        self.output_frame = ttk.LabelFrame(container, text="Output Frame (Thresholded Image + Histogram)")
        self.output_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.output_frame.columnconfigure(0, weight=1)
        self.output_frame.rowconfigure(0, weight=3)
        self.output_frame.rowconfigure(1, weight=2)

        self.output_canvas = tk.Canvas(self.output_frame, bg="white", highlightthickness=1)
        self.output_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 6))

        self.output_hist = tk.Canvas(self.output_frame, bg="white", highlightthickness=1, height=200)
        self.output_hist.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6, 10))

        self._placeholder(self.input_canvas, "No input image loaded")
        self._placeholder(self.output_canvas, "Output will appear here")
        self._placeholder(self.input_hist, "Input histogram will appear here")
        self._placeholder(self.output_hist, "Output histogram will appear here")

    def _placeholder(self, canvas, text):
        canvas.delete("all")
        w = canvas.winfo_width() or 400
        h = canvas.winfo_height() or 200
        canvas.create_text(w // 2, h // 2, text=text, fill="gray", font=("Segoe UI", 12))

    # ---------------- Actions ----------------
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        try:
            img = Image.open(file_path)
            if img.mode != "RGB":
                img = img.convert("RGB")

            self.original_image = img
            self.output_image = None
            self.status_var.set(f"Loaded: {os.path.basename(file_path)} | Size: {img.size}")
            self._refresh_all()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image:\n{e}")

    def save_output(self):
        if self.output_image is None:
            messagebox.showwarning("Warning", "No output image to save! Apply threshold first.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Output Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            self.output_image.save(file_path)
            self.status_var.set(f"Saved output: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save image:\n{e}")

    def reset(self):
        if self.original_image is None and self.output_image is None:
            self.status_var.set("Nothing to reset.")
            return
        self.output_image = None
        self.status_var.set("Reset done. Output cleared.")
        self._refresh_all()

    def _on_threshold_change(self, _):
        t = int(float(self.threshold_scale.get()))
        self.threshold_var.set(t)
        self.threshold_label.config(text=str(t))
        # Optional: live update if output exists
        if self.original_image is not None and self.output_image is not None:
            self.apply_threshold(live=True)

    def apply_threshold(self, live=False):
        if self.original_image is None:
            if not live:
                messagebox.showwarning("Warning", "Please load an image first!")
            return

        t = self.threshold_var.get()

        try:
            gray = np.array(self.original_image.convert("L"), dtype=np.uint8)
            # binary threshold: > t => 255 else 0
            out = np.where(gray > t, 255, 0).astype(np.uint8)

            self.output_image = Image.fromarray(out, mode="L").convert("RGB")
            self.status_var.set(f"Applied: Threshold processing (T={t})")
            self._refresh_all()
        except Exception as e:
            messagebox.showerror("Error", f"Threshold processing failed:\n{e}")

    # ---------------- Rendering ----------------
    def _refresh_all(self):
        if self.original_image is None:
            self._placeholder(self.input_canvas, "No input image loaded")
            self._placeholder(self.input_hist, "Input histogram will appear here")
        else:
            self.tk_in = self._render_image(self.input_canvas, self.original_image)
            self._draw_hist(self.input_hist, self.original_image)

        if self.output_image is None:
            self._placeholder(self.output_canvas, "Output will appear here")
            self._placeholder(self.output_hist, "Output histogram will appear here")
        else:
            self.tk_out = self._render_image(self.output_canvas, self.output_image)
            self._draw_hist(self.output_hist, self.output_image)

    def _render_image(self, canvas, img):
        canvas.delete("all")
        cw = canvas.winfo_width() or 500
        ch = canvas.winfo_height() or 350

        iw, ih = img.size
        scale = min(cw / iw, ch / ih, 1.0)  # don't upscale
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))

        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)

        x = (cw - nw) // 2
        y = (ch - nh) // 2
        canvas.create_image(x, y, anchor="nw", image=tk_img)

        return tk_img

    def _draw_hist(self, canvas, img):
        canvas.delete("all")
        cw = canvas.winfo_width() or 500
        ch = canvas.winfo_height() or 200

        gray = np.array(img.convert("L"), dtype=np.uint8)
        hist = np.bincount(gray.flatten(), minlength=256).astype(np.float64)
        max_h = hist.max() if hist.size else 1.0
        if max_h <= 0:
            max_h = 1.0

        # margins
        pad_l, pad_r, pad_t, pad_b = 35, 10, 10, 25
        w = max(1, cw - pad_l - pad_r)
        h = max(1, ch - pad_t - pad_b)

        # axes
        canvas.create_line(pad_l, pad_t, pad_l, pad_t + h, fill="black")
        canvas.create_line(pad_l, pad_t + h, pad_l + w, pad_t + h, fill="black")

        # labels
        canvas.create_text(pad_l + w // 2, ch - 10, text="Intensity (0..255)", fill="black", font=("Segoe UI", 10))
        canvas.create_text(15, pad_t + h // 2, text="Count", angle=90, fill="black", font=("Segoe UI", 10))

        x_step = w / 256.0
        for i in range(256):
            x = pad_l + i * x_step
            y = pad_t + h - (hist[i] / max_h) * h
            canvas.create_line(x, pad_t + h, x, y, fill="gray")

        # threshold marker (if input loaded)
        t = self.threshold_var.get()
        tx = pad_l + t * x_step
        canvas.create_line(tx, pad_t, tx, pad_t + h, fill="red")
        canvas.create_text(tx, pad_t + 8, text=f"T={t}", anchor="s", fill="red", font=("Segoe UI", 9))

        # ticks
        for tick in [0, 128, 255]:
            x = pad_l + tick * x_step
            canvas.create_line(x, pad_t + h, x, pad_t + h + 5, fill="black")
            canvas.create_text(x, pad_t + h + 12, text=str(tick), fill="black", font=("Segoe UI", 9))

        canvas.create_rectangle(1, 1, cw - 2, ch - 2, outline="#cfcfcf")


def main():
    root = tk.Tk()
    app = ThresholdProcessingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
