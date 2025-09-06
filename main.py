import cv2
import numpy as np
import threading
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import time

cap = None
running = False
mode = "Normal"
user_text = "⚡ Wizard Mode ⚡"
text_color_name = "Black"
overlay_image = None  # Image to overlay
background = None     # Captured background for invisibility

color_dict = {
    "Black": (0, 0, 0),
    "White": (255, 255, 255),
    "Green": (0, 255, 0),
    "Blue": (255, 0, 0),
    "Yellow": (0, 255, 255)
}

# ----------------- EFFECT FUNCTIONS -----------------
def capture_background(frames=30):
    """Capture background by averaging several frames."""
    global cap, background
    temp_bg = []
    for i in range(frames):
        ret, frame = cap.read()
        if ret:
            temp_bg.append(frame)
        time.sleep(0.05)
    background = np.median(temp_bg, axis=0).astype(np.uint8)

def apply_effect(frame):
    global mode, user_text, text_color_name, overlay_image, background

    if mode == "Normal" or frame is None:
        return frame

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Red color range (cloak detection)
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2

    if mode == "Invisible Cloak":
        if background is None:
            # If background not captured yet, show black
            return cv2.bitwise_and(frame, frame, mask=cv2.bitwise_not(mask))
        # Use captured background where cloak is detected
        res1 = cv2.bitwise_and(background, background, mask=mask)
        res2 = cv2.bitwise_and(frame, frame, mask=cv2.bitwise_not(mask))
        return cv2.addWeighted(res1, 1, res2, 1, 0)

    elif mode == "Glowing Cloak":
        glow = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
        return cv2.addWeighted(frame, 1, glow, 0.7, 0)

    elif mode == "Mirror Cloak":
        flipped = cv2.flip(frame, 1)
        res1 = cv2.bitwise_and(flipped, flipped, mask=mask)
        res2 = cv2.bitwise_and(frame, frame, mask=cv2.bitwise_not(mask))
        return cv2.addWeighted(res1, 1, res2, 1, 0)

    elif mode == "AR Filter" or mode == "Image Overlay":
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1000:
                x, y, w, h = cv2.boundingRect(cnt)

                if mode == "AR Filter":
                    # Text overlay
                    text = user_text
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    scale = 1
                    thickness = 3
                    color = color_dict.get(text_color_name, (0, 0, 0))
                    (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)
                    text_x = x + (w - text_w) // 2
                    text_y = y + (h + text_h) // 2
                    cv2.putText(frame, text, (text_x, text_y), font, scale, color, thickness, cv2.LINE_AA)

                elif mode == "Image Overlay" and overlay_image is not None:
                    # Resize overlay image to bounding box
                    overlay_resized = cv2.resize(overlay_image, (w, h))

                    # Prepare overlay and alpha
                    if overlay_resized.shape[2] == 4:  # PNG with alpha
                        overlay_rgb = overlay_resized[:, :, :3]
                        overlay_alpha = overlay_resized[:, :, 3] / 255.0
                    else:
                        overlay_rgb = overlay_resized
                        overlay_alpha = np.ones((h, w))

                    # Crop red mask to bounding box
                    mask_crop = mask[y:y+h, x:x+w] / 255.0
                    final_alpha = overlay_alpha * mask_crop

                    for c in range(3):
                        frame[y:y+h, x:x+w, c] = (
                            final_alpha * overlay_rgb[:, :, c] +
                            (1 - final_alpha) * frame[y:y+h, x:x+w, c]
                        )
    return frame

# ----------------- CAMERA FUNCTIONS -----------------
def start_camera():
    global cap, running
    if running:
        messagebox.showinfo("Info", "Camera already running")
        return

    cap = cv2.VideoCapture(0)
    running = True

    # Capture background first for invisibility
    capture_background()

    def run():
        global cap, running
        while running:
            ret, frame = cap.read()
            if not ret:
                break
            frame = apply_effect(frame)
            cv2.imshow("ARdrobe", frame)
            if cv2.waitKey(1) == ord('q'):
                stop_camera()
                break
        cap.release()
        cv2.destroyAllWindows()

    threading.Thread(target=run).start()

def stop_camera():
    global running
    running = False

def change_mode(event=None):
    global mode
    mode = effect_var.get()

def update_text(event=None):
    global user_text
    user_text = text_entry.get()

def change_color(event=None):
    global text_color_name
    text_color_name = color_var.get()

def choose_image():
    global overlay_image, mode
    path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg")]
    )
    if path:
        overlay_image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        mode = "Image Overlay"
        effect_var.set("Image Overlay")
        update_widgets()

# ---------------- GUI ----------------
root = tk.Tk()
root.title("ARdrobe - AR Clothing Designer")
root.geometry("360x450")

start_btn = tk.Button(root, text="Start Camera", command=start_camera, width=25)
start_btn.pack(pady=5)

stop_btn = tk.Button(root, text="Stop Camera", command=stop_camera, width=25)
stop_btn.pack(pady=5)

# Dropdown for effects
effect_var = tk.StringVar(value="Normal")
effect_label = tk.Label(root, text="Choose Effect:")
effect_label.pack(pady=5)

effect_dropdown = ttk.Combobox(
    root,
    textvariable=effect_var,
    values=["Normal", "Invisible Cloak", "Glowing Cloak", "Mirror Cloak", "AR Filter", "Image Overlay"],
    state="readonly",
    width=25
)
effect_dropdown.pack(pady=5)

# Text input for AR Filter
text_label = tk.Label(root, text="Type text for your cloth:")
text_entry = tk.Entry(root, width=25)
text_entry.bind("<Return>", update_text)

# Dropdown for text color
color_label = tk.Label(root, text="Choose text color:")
color_var = tk.StringVar(value="Black")  # default black
color_dropdown = ttk.Combobox(
    root,
    textvariable=color_var,
    values=["Black", "White", "Green", "Blue", "Yellow"],
    state="readonly",
    width=25
)
color_dropdown.bind("<<ComboboxSelected>>", change_color)

# Button to choose overlay image
img_btn = tk.Button(root, text="Choose Image Overlay", command=choose_image, width=25)

exit_btn = tk.Button(root, text="Exit", command=root.quit, width=25)
exit_btn.pack(pady=10)

# ---------------- Dynamic widget display ----------------
def update_widgets(event=None):
    choice = effect_var.get()
    if choice == "AR Filter":
        # show text & color
        text_label.pack(pady=5)
        text_entry.pack(pady=5)
        color_label.pack(pady=5)
        color_dropdown.pack(pady=5)
        img_btn.pack_forget()
    elif choice == "Image Overlay":
        # show image button only
        img_btn.pack(pady=10)
        text_label.pack_forget()
        text_entry.pack_forget()
        color_label.pack_forget()
        color_dropdown.pack_forget()
    else:
        # hide everything extra
        text_label.pack_forget()
        text_entry.pack_forget()
        color_label.pack_forget()
        color_dropdown.pack_forget()
        img_btn.pack_forget()

effect_dropdown.bind("<<ComboboxSelected>>", lambda e: [change_mode(), update_widgets()])

# Call once at start to set default visibility
update_widgets()

root.mainloop()
