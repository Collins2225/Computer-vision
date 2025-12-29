import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
from scipy import ndimage


class AveragingAndOrderStatsApp:
    """
    Averaging filters + ordinal statistics filters:
      - Mean (Averaging) filter
      - Median filter (order-statistic)
      - Min filter (order-statistic)
      - Max filter (order-statistic)

    GUI structure (3 frames):
      1) Control Frame  - Load / Apply / Reset / Save + filter options
      2) Input Frame    - original image
      3) Output Frame   - filtered image
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Averaging & Ordinal Statistics Filters")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 620)

        self.original_image = None   # PIL RGB
        self.output_image = None     # PIL RGB
        self.tk_in = None
        self.tk_out = None

        self._build_ui()

        # refresh on resize
        self.input_canvas.bind("<Configure>", lambda e: self._refresh())
        self.output_canvas.bind("<Configure>", lambda e: self._refresh())

    # ---------------- UI ----------------
    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # 1) CONTROL FRAME (visually distinct)
        self.control_frame = ttk.LabelFrame(self.root, text="Control Frame")
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        self.control_frame.columnconfigure(99, weight=1)

        ttk.Button(self.control_frame, text="Load Image", command=self.load_image).grid(
            row=0, column=0, padx=8, pady=10, sticky="w"
        )
        ttk.Button(self.control_frame, text="Apply Filter", command=self.apply_filter).grid(
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

        # Filter selection
        ttk.Label(self.control_frame, text="Filter:").grid(row=0, column=5, padx=(0, 6), pady=10, sticky="w")
        self.filter_var = tk.StringVar(value="Mean (Averaging)")

        self.filter_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.filter_var,
            state="readonly",
            values=[
                "Mean (Averaging)",
                "Median (Order-Statistic)",
                "Min (Order-Statistic)",
                "Max (Order-Statistic)",
            ],
            width=26
        )
        self.filter_combo.grid(row=0, column=6, padx=6, pady=10, sticky="w")

        # Kernel size selection
        ttk.Label(self.control_frame, text="Kernel Size:").grid(row=0, column=7, padx=(12, 6), pady=10, sticky="w")
        self.kernel_var = tk.IntVar(value=3)

        self.kernel_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.kernel_var,
            state="readonly",
            values=[3, 5, 7, 9, 11],
            width=5
        )
        self.kernel_combo.grid(row=0, column=8, padx=6, pady=10, sticky="w")

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
        self.input_frame = ttk.LabelFrame(container, text="Input Frame (Original Image)")
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.input_frame.columnconfigure(0, weight=1)
        self.input_frame.rowconfigure(0, weight=1)

        self.input_canvas = tk.Canvas(self.input_frame, bg="white", highlightthickness=1)
        self.input_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 3) OUTPUT FRAME
        self.output_frame = ttk.LabelFrame(container, text="Output Frame (Filtered Image)")
        self.output_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.output_frame.columnconfigure(0, weight=1)
        self.output_frame.rowconfigure(0, weight=1)

        self.output_canvas = tk.Canvas(self.output_frame, bg="white", highlightthickness=1)
        self.output_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self._placeholder(self.input_canvas, "No input image loaded")
        self._placeholder(self.output_canvas, "Output will appear here")

    def _placeholder(self, canvas, text):
        canvas.delete("all")
        w = canvas.winfo_width() or 500
        h = canvas.winfo_height() or 400
        canvas.create_text(w // 2, h // 2, text=text, fill="gray", font=("Segoe UI", 12))

    # ---------------- File actions ----------------
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
            self.status_var.set(f"Loaded: {file_path.split('/')[-1]} | Size: {img.size}")
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image:\n{e}")

    def save_output(self):
        if self.output_image is None:
            messagebox.showwarning("Warning", "No output image to save! Apply a filter first.")
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
            self.status_var.set(f"Saved output: {file_path.split('/')[-1]}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save image:\n{e}")

    def reset(self):
        if self.original_image is None and self.output_image is None:
            self.status_var.set("Nothing to reset.")
            return
        self.output_image = None
        self.status_var.set("Reset done. Output cleared.")
        self._refresh()

    # ---------------- Filtering ----------------
    def apply_filter(self):
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please load an image first!")
            return

        filt = self.filter_var.get()
        k = int(self.kernel_var.get())

        if k % 2 == 0 or k < 3:
            messagebox.showwarning("Warning", "Kernel size must be an odd number >= 3.")
            return

        try:
            img = np.array(self.original_image, dtype=np.float32)

            # Apply per-channel for RGB
            out = np.empty_like(img)

            if filt == "Mean (Averaging)":
                kernel = np.ones((k, k), dtype=np.float32) / (k * k)
                for c in range(3):
                    out[..., c] = ndimage.convolve(img[..., c], kernel, mode="reflect")

            elif filt == "Median (Order-Statistic)":
                for c in range(3):
                    out[..., c] = ndimage.median_filter(img[..., c], size=k, mode="reflect")

            elif filt == "Min (Order-Statistic)":
                # minimum filter
                for c in range(3):
                    out[..., c] = ndimage.minimum_filter(img[..., c], size=k, mode="reflect")

            elif filt == "Max (Order-Statistic)":
                # maximum filter
                for c in range(3):
                    out[..., c] = ndimage.maximum_filter(img[..., c], size=k, mode="reflect")

            else:
                raise ValueError("Unknown filter selected")

            out = np.clip(out, 0, 255).astype(np.uint8)
            self.output_image = Image.fromarray(out, mode="RGB")

            self.status_var.set(f"Applied: {filt} | Kernel: {k}x{k}")
            self._refresh()

        except Exception as e:
            messagebox.showerror("Error", f"Filtering failed:\n{e}")

    # ---------------- Rendering ----------------
    def _refresh(self):
        if self.original_image is None:
            self._placeholder(self.input_canvas, "No input image loaded")
        else:
            self.tk_in = self._render_image(self.input_canvas, self.original_image)

        if self.output_image is None:
            self._placeholder(self.output_canvas, "Output will appear here")
        else:
            self.tk_out = self._render_image(self.output_canvas, self.output_image)

    def _render_image(self, canvas, img):
        canvas.delete("all")
        cw = canvas.winfo_width() or 500
        ch = canvas.winfo_height() or 400

        iw, ih = img.size
        scale = min(cw / iw, ch / ih, 1.0)  # don't upscale
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))

        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)

        x = (cw - nw) // 2
        y = (ch - nh) // 2
        canvas.create_image(x, y, anchor="nw", image=tk_img)

        return tk_img


def main():
    root = tk.Tk()
    app = AveragingAndOrderStatsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()