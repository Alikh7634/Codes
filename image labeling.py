import os
import csv
import glob
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

ROOT_DIR = "Tensorflow\\workspace\\images\\Collectedimages"  # Directory containing the 5 folders of images
OUTPUT_CSV = "Tensorflow\\workspace\\images\\Collectedimages\\annotations.csv"
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp']

# Predefined labels
LABELS = ["hello", "I Love You", "No", "Yes", "Thanks"] # labels for sign language detection

class ImageLabelingApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Labeling Tool")

        # Get all image paths
        self.image_paths = self.get_all_images(ROOT_DIR, IMAGE_EXTENSIONS)
        self.image_paths.sort()
        self.current_image_index = 0
        self.annotations = []

        self.boxes = []  # boxes for the current image
        self.img = None  # PIL image
        self.tk_img = None
        self.canvas_image = None

        # Coordinates for bounding box
        self.start_x = None
        self.start_y = None
        self.rect = None  # Canvas rectangle ID

        # Set up GUI
        self.setup_gui()

        # Load the first image
        if self.image_paths:
            self.load_image(self.image_paths[self.current_image_index])
        else:
            messagebox.showerror("Error", "No images found in the specified directory.")
            self.master.quit()

    def setup_gui(self):
        # Frame for canvas
        self.canvas_frame = tk.Frame(self.master)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Canvas for image
        self.canvas = tk.Canvas(self.canvas_frame, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Frame for buttons
        self.button_frame = tk.Frame(self.master)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.next_button = tk.Button(self.button_frame, text="Next", command=self.next_image)
        self.next_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.quit_button = tk.Button(self.button_frame, text="Quit", command=self.quit_app)
        self.quit_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Instructions label
        self.info_label = tk.Label(self.button_frame, text="Draw bounding boxes with the mouse. After releasing, choose a label.")
        self.info_label.pack(side=tk.LEFT, padx=5, pady=5)

    def get_all_images(self, root_dir, extensions):
        images = []
        for ext in extensions:
            images.extend(glob.glob(os.path.join(root_dir, '**', f'*{ext}'), recursive=True))
        return images

    def load_image(self, image_path):
        self.boxes = []
        self.canvas.delete("all")

        self.img = Image.open(image_path)
        self.original_width, self.original_height = self.img.size

        # Resize image to fit window if needed
        # (For simplicity, we won't implement automatic resizing here. 
        #  You can add code to resize image and maintain aspect ratio if desired.)

        self.tk_img = ImageTk.PhotoImage(self.img)
        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.master.title(f"Image Labeling Tool - {os.path.basename(image_path)}")

        # Adjust canvas size to image size (if desired)
        self.canvas.config(scrollregion=(0,0,self.original_width,self.original_height))
        self.canvas.config(width=self.original_width, height=self.original_height)

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = None

    def on_mouse_drag(self, event):
        if self.start_x is not None and self.start_y is not None:
            # Draw a rectangle on canvas
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline='green', width=2)

    def on_mouse_up(self, event):
        if self.start_x is not None and self.start_y is not None and self.rect is not None:
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y

            x_min, x_max = sorted([x1, x2])
            y_min, y_max = sorted([y1, y2])

            # Show label selection dialog
            label = self.select_label_popup()
            if label is None:
                # User canceled or closed the dialog
                # We can choose to discard the box or mark as unlabeled
                label = "unlabeled"

            # Store the box
            self.boxes.append((x_min, y_min, x_max, y_max, label))

            self.start_x = None
            self.start_y = None
            self.rect = None

    def select_label_popup(self):
        # Popup window for label selection
        popup = tk.Toplevel(self.master)
        popup.title("Select Label")
        popup.geometry("300x120")
        popup.grab_set()  # Make this popup modal

        label_var = tk.StringVar(value=LABELS[0] if LABELS else "")

        tk.Label(popup, text="Choose a label:").pack(pady=5)
        combo = ttk.Combobox(popup, textvariable=label_var, values=LABELS)
        combo.pack(pady=5)
        combo.focus_set()

        chosen_label = [None]  # mutable so inner function can modify

        def on_ok():
            chosen_label[0] = label_var.get().strip()
            popup.destroy()

        def on_cancel():
            chosen_label[0] = None
            popup.destroy()

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)

        popup.wait_window(popup)
        return chosen_label[0]

    def next_image(self):
        # Save current image annotations
        current_image_path = self.image_paths[self.current_image_index]
        for box in self.boxes:
            # box = (x_min, y_min, x_max, y_max, label)
            # Note: Coordinates are relative to the displayed image size (currently same as original)
            self.annotations.append((current_image_path,) + box)

        self.write_annotations()

        # Move to next image if available
        self.current_image_index += 1
        if self.current_image_index < len(self.image_paths):
            self.load_image(self.image_paths[self.current_image_index])
        else:
            messagebox.showinfo("Info", "No more images to label.")
            self.quit_app()

    def quit_app(self):
        # Save final annotations and quit
        self.write_annotations()
        self.master.quit()

    def write_annotations(self):
        with open(OUTPUT_CSV, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["image_path", "x_min", "y_min", "x_max", "y_max", "label"])
            for ann in self.annotations:
                writer.writerow(ann)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageLabelingApp(root)
    root.mainloop()