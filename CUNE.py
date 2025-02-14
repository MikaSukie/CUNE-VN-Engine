import time
import threading
import json
import os
import subprocess
import sys
import math
from enum import Enum

color_setter = None
CUNE_WARN = 0
CUNE_ERR = 0
custom_positions = {}
V = False

def install_pygame():
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pygame'])

try:
    import pygame
except ImportError:
    print("Pygame not found. Installing...")
    install_pygame()
    import pygame

class GameState(Enum):
    RUNNING = 1
    PAUSED = 2
    SETTINGS = 3

class Button:
    def __init__(self, text, command, hover_color=(200, 200, 200), normal_color=(50, 150, 250), size=(80, 30), alpha=255):
        self.text = text
        self.command = command
        self.hover_color = hover_color
        self.normal_color = normal_color
        self.size = size
        self.rect = None
        self.positioned = False
        self.default_position = None
        self.alpha = alpha

    def run_command_in_thread(self):
        command_thread = threading.Thread(target=self.command)
        command_thread.start()

    def set_default_position(self, x, y):
        self.default_position = (x, y)

class DialogBox:
    def __init__(self, size=(1200, 700)):
        self.size = size
        self.texture = pygame.image.load("assets/dialog_texture.png").convert_alpha()
        self.texture = pygame.transform.scale(self.texture, self.size)
        self.y_offset= 375
        self.x_offset= 200
        self.D_offset_x = 0
        self.D_offset_y = -180

    def draw(self, screen, position, text, font):
        global D_offset_x
        global D_offset_y
        D_offset_x = self.D_offset_x
        D_offset_y = self.D_offset_y
        dialog_box_centered = pygame.Rect(position[0], position[1], self.size[0], self.size[1])
        dialog_box_centered.center = (screen.get_width() // 2 + D_offset_x, screen.get_height() + D_offset_y)
        screen.blit(self.texture, dialog_box_centered.topleft)
        global y_offset
        global x_offset
        x_offset = self.x_offset
        y_offset = self.y_offset
        lines = text.split("\n")
        for line in lines:
            text_surf = font.render(line, True, (255, 255, 255))
            screen.blit(text_surf, (dialog_box_centered.x + x_offset, dialog_box_centered.y + y_offset))
            y_offset += font.get_height()

    def modify(self, new_texture_path=None, new_size=None):
        if new_texture_path:
            self.texture = pygame.image.load(new_texture_path).convert_alpha()
        if new_size:
            self.size = new_size
            self.texture = pygame.transform.scale(self.texture, self.size)

    def modify_offset(self, new_x, new_y):
        self.y_offset = new_y
        self.x_offset = new_x

    def modify_dialog_offset(self, new_x, new_y):
        self.D_offset_x = new_x
        self.D_offset_y = new_y

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.text_speed = 0.05
        self.auto_skip_speed = 0.5
        self.volume = 1.0
        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                self.text_speed = settings.get("text_speed", self.text_speed)
                self.auto_skip_speed = settings.get("auto_skip_speed", self.auto_skip_speed)
                self.volume = settings.get("volume", self.volume)

    def save_settings(self):
        settings = {
            "text_speed": self.text_speed,
            "auto_skip_speed": self.auto_skip_speed,
            "volume": self.volume
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)

class CUNE:
    def __init__(self, width=1280, height=720, title="[CUNE Visual Novel Engine]"):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.background = None
        self.characters = {}
        self.dialog_box = DialogBox()
        self.current_dialog = []
        self.dialog_index = 0
        self.dialog_text = ""
        self.is_auto = False
        self.auto_thread = None
        self.settings_manager = SettingsManager()
        self.buttons = []
        self.running = True
        self.button_hovered = None
        self.hover_sound_played = False
        self.last_button_hovered = None
        self.font = pygame.font.SysFont("Arial", 18)
        self.font_button = pygame.font.SysFont("Arial", 18)
        pygame.mouse.set_visible(True)
        self.is_dialog_visible = False
        self.dialog_history = []
        self.load_dialogs("dialogs.json")
        self.hover_sound = pygame.mixer.Sound("assets/hover_sound.wav")
        self.click_sound = pygame.mixer.Sound("assets/select_sound.wav")
        self.static_buttons = []
        self.static_button_x = 0
        self.static_button_y = 0
        self.static_button_hovered = None
        self.last_static_button_hovered = None
        self.static_hover_sound = pygame.mixer.Sound("assets/hover_sound.wav")
        self.static_click_sound = pygame.mixer.Sound("assets/select_sound.wav")
        self.dialogstate = False
        self.dialog_thread = None
        self.dialog_button_size = (80, 30)
        self.dialog_button_spacing = 20

        self.static_button_size = (80, 30)
        self.static_button_spacing = 20

        self.draggable_entities = {}
        self.dragging_entity = None
        self.drag_offset = (0, 0)

        self.tex_offset = 0
        self.tey_offset = 0

        self.button_offset_x = 0
        self.button_offset_y = 0
        self.dialog_constraints = {
            "max_length": 75,
            "allow_overflow": False
        }
    def change_button_sound(self, hover_path, click_path):
        self.hover_sound =        hover_path
        self.static_hover_sound = hover_path
        self.click_sound =        click_path
        self.static_click_sound = click_path

    def wrap_dialog_text(self, text):
        max_length = self.dialog_constraints.get("max_length", 50)
        allow_overflow = self.dialog_constraints.get("allow_overflow", False)

        if allow_overflow and max_length == "overflow":
            return text

        words = text.split()
        wrapped_lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_length:
                current_line += (" " if current_line else "") + word
            else:
                wrapped_lines.append(current_line)
                current_line = word

        if current_line:
            wrapped_lines.append(current_line)

        return "\n".join(wrapped_lines)

    def set_dim(self, width, height):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)

    def set_app_icon(self, icon_path):
        try:
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        except pygame.error as e:
            print(f"Failed to set app icon: {e}")

    def set_background(self, image_path):
        original_background = pygame.image.load(image_path).convert()
        self.background = pygame.transform.scale(original_background, (self.width, self.height))

    def change_entity_texture(self, name, new_image_path, scale_factor_setter=1.0, duration=None):
        if name not in self.characters:
            print(f"Entity '{name}' not found.")
            return
        entity = self.characters[name]

        if "frames" in entity:
            print(f"Cannot change texture of animated entity '{name}'. Use change_anim_folder() instead.")
            return

        new_image = pygame.image.load(new_image_path).convert_alpha()
        scaled_width = int(new_image.get_width() * scale_factor_setter)
        scaled_height = int(new_image.get_height() * scale_factor_setter)
        new_image = pygame.transform.scale(new_image, (scaled_width, scaled_height))

        if duration is None:
            entity["image"] = new_image
            return

        frames = int(duration * 60)
        fade_step = 255 // frames
        original_image = entity["image"]

        def animate():
            for i in range(frames + 1):
                alpha = fade_step * i
                blended_surface = pygame.Surface(original_image.get_size(), pygame.SRCALPHA)
                original_image_with_alpha = original_image.copy()
                original_image_with_alpha.set_alpha(255 - alpha)
                new_image_with_alpha = new_image.copy()
                new_image_with_alpha.set_alpha(alpha)
                blended_surface.blit(original_image_with_alpha, (0, 0))
                blended_surface.blit(new_image_with_alpha, (0, 0))
                entity["image"] = blended_surface

            entity["image"] = new_image

        threading.Thread(target=animate).start()

    def change_anim_folder(self, name, new_folder_path, frame_rate=10, fwdbwd=False):
        if name not in self.characters:
            print(f"Animated entity '{name}' not found.")
            return

        entity = self.characters[name]

        if "frames" not in entity:
            print(f"Entity '{name}' is not animated. Use change_entity_texture() instead.")
            return

        frame_files = sorted(
            [os.path.join(new_folder_path, f) for f in os.listdir(new_folder_path) if f.endswith(('.png', '.jpg'))]
        )

        if not frame_files:
            print(f"No valid frames found in {new_folder_path}.")
            return

        new_frames = [pygame.image.load(frame).convert_alpha() for frame in frame_files]
        first_frame = new_frames[0]
        scale_factor = entity["image"].get_width() / first_frame.get_width()
        scaled_frames = [pygame.transform.scale(frame, (int(frame.get_width() * scale_factor),
                                                        int(frame.get_height() * scale_factor))) for frame in
                         new_frames]


        entity["frames"] = scaled_frames
        entity["current_frame"] = 0
        entity["frame_rate"] = frame_rate
        entity["fwdbwd"] = fwdbwd
        entity["last_update_time"] = pygame.time.get_ticks()

        print(f"Successfully changed animation folder for '{name}'.")

    def set_dialog_font(self, font_path, font_size=18):
        try:
            self.font = pygame.font.Font(font_path, font_size)
        except Exception as e:
            print(f"Failed to set font: {e}")

    def set_button_font(self, font_path, font_size=18):
        try:
            self.font_button = pygame.font.Font(font_path, font_size)
        except Exception as e:
            print(f"Failed to set font: {e}")

    def set_title(self, title):
        pygame.display.set_caption(title)

    def add_entity(self, name, image_path, position=None, z_level=0):
        original_image = pygame.image.load(image_path).convert_alpha()
        screen_height = self.height
        scale_factor = screen_height / original_image.get_height()
        scaled_width = int(original_image.get_width() * scale_factor)
        scaled_image = pygame.transform.scale(original_image, (scaled_width, screen_height))
        if position is None:
            position = ((self.width - scaled_width) // 2, 0)
        self.characters[name] = {"image": scaled_image, "position": position, "z_level": z_level}

    def add_entity_with_scale_factor(self, name, image_path, scale_factor_setter, position=None, z_level=0):
        original_image_cs = pygame.image.load(image_path).convert_alpha()
        scale_factor_cs = scale_factor_setter
        screen_height_cs = int(original_image_cs.get_height() * scale_factor_cs)
        scaled_width_cs = int(original_image_cs.get_width() * scale_factor_cs)
        scaled_image_cs = pygame.transform.scale(original_image_cs, (scaled_width_cs, screen_height_cs))
        if position is None:
            position = ((self.width - scaled_width_cs) // 2, 0)
        self.characters[name] = {"image": scaled_image_cs, "position": position, "z_level": z_level}

    def add_draggable_entity(self, name, image_path=None, position=(0, 0), z_level=0,
                             draggable=True, on_click=None, animated=False, frame_folder=None,
                             frame_rate=24, animate_on="always", loop=True,
                             drag_bounds=None, snap_to_grid=None, fwbwdvar=False, scale_factor=1.0):

        if animated and frame_folder:
            self.add_animated_entity(name, frame_folder, position, z_level, frame_rate, fwdbwd=fwbwdvar)
        elif image_path:
            original_image = pygame.image.load(image_path).convert_alpha()

            scaled_width = int(original_image.get_width() * scale_factor)
            scaled_height = int(original_image.get_height() * scale_factor)
            scaled_image = pygame.transform.scale(original_image, (scaled_width, scaled_height))

            self.characters[name] = {
                "image": scaled_image,
                "position": position,
                "z_level": z_level,
                "scale_factor": scale_factor
            }
        else:
            print(f"Error: No texture or animation provided for '{name}'.")
            return

        self.draggable_entities[name] = {
            "draggable": draggable,
            "on_click": on_click,
            "dragging": False,
            "animated": animated,
            "animate_on": animate_on,
            "loop": loop,
            "drag_bounds": drag_bounds,
            "snap_to_grid": snap_to_grid,
            "scale_factor": scale_factor
        }

        if animated and animate_on == "always":
            self.characters[name]["current_frame"] = 0

    def hide_entity(self, name, effect="slide_back", duration=1.0, target_x="~", target_y="~", initial_alpha=255,
                    final_alpha=0):
        if name not in self.characters:
            print(f"Entity '{name}' not found.")
            return

        entity = self.characters[name]
        frames = int(duration * 60)
        start_x, start_y = entity["position"]
        end_x = start_x if target_x == "~" else target_x
        end_y = start_y if target_y == "~" else target_y

        def animate():
            for i in range(frames + 1):
                progress = i / frames
                ease_progress = (1 - math.cos(progress * math.pi)) / 2
                alpha = initial_alpha + (final_alpha - initial_alpha) * ease_progress
                entity["position"] = (
                    start_x + (end_x - start_x) * ease_progress,
                    start_y + (end_y - start_y) * ease_progress
                )
                entity["alpha"] = int(alpha)
                time.sleep(1 / 60)
            entity["visible"] = False

        threading.Thread(target=animate, daemon=True).start()

    def get_window_width(self):
        return self.width
    def get_window_height(self):
        return self.height

    def show_entity(self, name, effect="slide_in", duration=1.0, start_x="~", start_y="~", initial_alpha=0,
                    final_alpha=255):
        if name not in self.characters:
            print(f"Entity '{name}' not found.")
            return

        entity = self.characters[name]
        frames = int(duration * 60)
        final_x, final_y = entity["position"]
        start_x = final_x if start_x == "~" else start_x
        start_y = final_y if start_y == "~" else start_y
        entity["position"] = (start_x, start_y)
        entity["visible"] = True
        entity["alpha"] = initial_alpha

        def animate():
            for i in range(frames + 1):
                progress = i / frames
                ease_progress = (1 - math.cos(progress * math.pi)) / 2
                alpha = initial_alpha + (final_alpha - initial_alpha) * ease_progress
                entity["position"] = (
                    start_x + (final_x - start_x) * ease_progress,
                    start_y + (final_y - start_y) * ease_progress
                )
                entity["alpha"] = int(alpha)
                time.sleep(1 / 60)
            entity["position"] = (final_x, final_y)
            entity["alpha"] = final_alpha

        threading.Thread(target=animate, daemon=True).start()

    def modify_dialogbox(self, new_texture_path=None, new_size=None):
        self.dialog_box.modify(new_texture_path, new_size)

    def modify_text_offset(self, x, y):
        self.dialog_box.modify_offset(x, y)

    def remove_entity(self, name):
        if name in self.characters:
            del self.characters[name]
            print(f"Entity '{name}' removed.")

        if name in self.draggable_entities:
            del self.draggable_entities[name]
            print(f"Draggable entity '{name}' removed.")
        else:
            print(f"Entity '{name}' not found.")

    def set_dialog_button_offset(self, offset_x, offset_y):
        self.button_offset_x = offset_x
        self.button_offset_y = offset_y

    def add_animated_entity(self, name, folder_path, position=None, z_level=0, frame_rate=10, fwdbwd=False):
        frame_files = sorted(
            [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg'))]
        )

        if not frame_files:
            print(f"No valid frames found in {folder_path}.")
            return

        frames = [pygame.image.load(frame).convert_alpha() for frame in frame_files]
        first_frame = frames[0]
        screen_height = self.height
        scale_factor = screen_height / first_frame.get_height()
        scaled_width = int(first_frame.get_width() * scale_factor)
        scaled_height = int(first_frame.get_height() * scale_factor)

        if position is None:
            position = ((self.width - scaled_width) // 2, 0)

        scaled_frames = [pygame.transform.scale(frame, (scaled_width, scaled_height)) for frame in frames]

        self.characters[name] = {
            "frames": scaled_frames,
            "position": position,
            "z_level": z_level,
            "current_frame": 0,
            "frame_direction": 1,
            "fwdbwd": fwdbwd,
            "frame_rate": frame_rate,
            "last_update_time": pygame.time.get_ticks(),
        }

        print(f"Animated entity '{name}' added successfully with {len(scaled_frames)} frames.")

    def rotate_entity(self, name, degrees, duration=1.0):
        if name not in self.characters:
            print(f"Entity '{name}' not found.")
            return

        entity = self.characters[name]
        frames = int(duration * 60)
        start_angle = entity.get("angle", 0)
        end_angle = start_angle + degrees
        entity["angle"] = start_angle

        def animate():
            for i in range(frames + 1):
                progress = i / frames
                ease_progress = (1 - math.cos(progress * math.pi)) / 2
                current_angle = start_angle + (end_angle - start_angle) * ease_progress
                entity["angle"] = current_angle
                time.sleep(1 / 60)
            entity["angle"] = end_angle

        threading.Thread(target=animate, daemon=True).start()

    def set_dialog(self, dialog_lines):
        self.current_dialog = dialog_lines
        self.dialog_index = 0
        self.dialog_text = ""
        self.is_dialog_visible = True
        self.update_dialog()

    def set_dialog_id_silent(self, dialog_id):
        if 0 <= self.dialog_index < len(self.current_dialog):
            self.current_dialog[self.dialog_index]['id'] = dialog_id
        else:
            print("[CUNE-NOTICE] No active dialog to set ID for.")

    def set_dialog_id(self, dialog_id):
        if 0 <= self.dialog_index < len(self.current_dialog):
            self.current_dialog[self.dialog_index]['id'] = dialog_id
            self.update_dialog()
        else:
            print("[CUNE-NOTICE] No active dialog to set ID for.")

    def entity_set_visible(self, name, visible):
        if name in self.characters:
            self.characters[name]["visible"] = visible
        else:
            print(f"Entity '{name}' not found.")

    def entity_modify_Zlevel(self, name, z_level=None, change=0):
        if name in self.characters:
            if z_level is not None:
                self.characters[name]["z_level"] = z_level
            else:
                self.characters[name]["z_level"] += change
        else:
            print(f"Entity '{name}' not found.")

    def set_dialog_constraints(self, max_length=50, allow_overflow=False):
        self.dialog_constraints["max_length"] = max_length
        self.dialog_constraints["allow_overflow"] = allow_overflow

    def update_dialog(self):
        if self.dialog_index < len(self.current_dialog):
            raw_text = self.current_dialog[self.dialog_index]['dialog']
            formatted_text = self.wrap_dialog_text(raw_text)
            self.display_text(formatted_text)
            self.dialog_history.append(self.current_dialog[self.dialog_index])
            self.dialog_index += 1
        else:
            self.dialog_text = ""
            self.is_dialog_visible = False

    def _print_dialog_text(self, text):
        wrapped_text = self.wrap_dialog_text(text)
        lines = wrapped_text.split("\n")

        def type_effect():
            self.dialog_text = ""
            for line in lines:
                for char in line:
                    self.dialog_text += char
                    time.sleep(self.settings_manager.text_speed)
                self.dialog_text += "\n"
                time.sleep(self.settings_manager.text_speed * 2)

            if self.is_auto:
                self.auto_advance()

        threading.Thread(target=type_effect, daemon=True).start()

    def set_dialog_visible(self):
        self.is_dialog_visible = True

    def set_dialog_not_visible(self):
        self.is_dialog_visible = False

    def dialog_visible_toggle(self):
        global V
        V = not V
        if V:
            CUNE.set_dialog_visible(self)
        else:
            CUNE.set_dialog_not_visible(self)

    def play_audio(self, file_path, volume=1.0, repeat=False):
        try:
            if repeat:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)
            else:
                sound = pygame.mixer.Sound(file_path)
                sound.set_volume(volume)
                sound.play()
        except pygame.error as e:
            global CUNE_ERR
            CUNE_ERR += 1
            print(f"[CUNE-ERR ({CUNE_ERR})] Error: playing sound '{file_path}': {e}")

    def stop_audio(self):
        pygame.mixer.music.stop()

    def get_current_dialog_id(self):
        if self.dialog_index > 0:
            return self.current_dialog[self.dialog_index - 1].get('id', None)
        return None

    def jump_to(self, dialog_id):
        for index, dialog in enumerate(self.current_dialog):
            if dialog.get('id') == dialog_id:
                self.dialog_index = index
                self.update_dialog()
                break
        else:
            print(f"[CUNE-NOTICE] Dialog ID {dialog_id} not found.")

    def modify_dialog_adjustment(self, x, y):
        self.dialog_box.modify_dialog_offset(x, y)

    def auto_advance(self):
        global CUNE_WARN
        if self.dialog_index < len(self.current_dialog):
            if self.auto_thread and self.auto_thread.is_alive():
                if threading.current_thread() is not self.auto_thread:
                    self.auto_thread.join()
                else:
                    CUNE_WARN += 1
                    print(f"[CUNE-WARN ({CUNE_WARN})] Warning: Attempted to join the current thread.")

            self.auto_thread = threading.Timer(self.settings_manager.auto_skip_speed, self.update_dialog)
            self.auto_thread.start()

    def display_text(self, text):
        self.dialog_text = ""
        if self.dialog_thread is not None and self.dialog_thread.is_alive():
            if threading.current_thread() is not self.dialog_thread:
                self.dialog_thread.join()

        self.dialog_thread = threading.Thread(target=self._print_dialog_text, args=(text,))
        self.dialog_thread.start()

    def add_button(self, text, command, hover_color=(200, 200, 200), normal_color=(50, 150, 250), size=(80, 30),
                   alpha=255):
        button = Button(text, command, hover_color, normal_color, size, alpha)
        self.buttons.append(button)

    def add_static_button(self, text, command, hover_color=(200, 200, 200), normal_color=(50, 150, 250), size=(80, 30),
                          alpha=255):
        button = Button(text, command, hover_color, normal_color, size, alpha)
        self.static_buttons.append(button)
        return button

    def layout_static_buttons(self, start_x, start_y, custom_positions=None):
        button_spacing = self.static_button_spacing

        for i, button in enumerate(self.static_buttons):
            if not button.positioned:
                if custom_positions and button.text in custom_positions:
                    button_x, button_y = custom_positions[button.text]
                else:
                    button_x = start_x
                    button_y = start_y + i * (button.size[1] + button_spacing)

                button.set_default_position(button_x, button_y)
                button.positioned = True
            else:
                if custom_positions and button.text in custom_positions:
                    button_x, button_y = custom_positions[button.text]
                    button.set_default_position(button_x, button_y)

            button.rect = self.draw_button(button, button.default_position[0], button.default_position[1],
                                           button.hover_color)

    def draw_button(self, button, x, y, color):
        if button in self.buttons:
            button_width, button_height = self.dialog_button_size
        elif button in self.static_buttons:
            button_width, button_height = self.static_button_size
        else:
            button_width, button_height = self.dialog_button_size
            button.size = (button_width, button_height)
        button.size = (button_width, button_height)

        button_rect = pygame.Rect(x, y, button_width, button_height)
        button_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)

        if button == self.button_hovered or button == self.static_button_hovered:
            button_color = button.hover_color
            if button == self.button_hovered and self.last_button_hovered != button:
                self.hover_sound.play()
                self.last_button_hovered = button
        else:
            button_color = button.normal_color

        button_surface.fill((*button_color, button.alpha))
        self.screen.blit(button_surface, button_rect.topleft)

        button_font = self.font_button
        text_surf = button_font.render(button.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect.topleft)

        button.rect = button_rect
        return button_rect

    def remove_static_button(self, button_text):
        self.static_buttons = [button for button in self.static_buttons if button.text != button_text]

    def next_dialog(self):
        self.update_dialog()

    def toggle_auto(self):
        self.is_auto = not self.is_auto

    def show_dialog_history(self):
        print("Dialog History:")
        for dialog in self.dialog_history:
            print(dialog)

    def add_text_entity(self, name, content, font_path, size, entity_bind=None, position=None, color=(255, 255, 255),
                        z_level=0, tx_offset=50, ty_offset=-10):
        self.tex_offset = tx_offset
        self.tey_offset = ty_offset

        try:
            font = pygame.font.Font(font_path, size)
        except Exception as e:
            print(f"Error loading font '{font_path}': {e}")
            return

        text_surface = font.render(content, True, color)

        if entity_bind and entity_bind in self.characters:
            bound_entity = self.characters[entity_bind]
            bound_x, bound_y = bound_entity["position"]
            text_x = bound_x - text_surface.get_width() // 2 + tx_offset
            text_y = bound_y - text_surface.get_height() // 2 + ty_offset
        elif position:
            text_x, text_y = position
        else:
            print(f"Error: You must provide either an entity to bind to or a manual position.")
            return

        self.characters[name] = {
            "image": text_surface,
            "position": (text_x, text_y),
            "z_level": z_level,
            "font": font,
            "content": content,
            "color": color,
            "entity_bind": entity_bind
        }

    def update_text_entity(self, name, new_content=None, new_font_path=None, new_size=None, new_color=None, tx_offset=50, ty_offset=-10):
        self.tey_offset = ty_offset
        self.tex_offset = tx_offset
        if name not in self.characters:
            print(f"Error: Text entity '{name}' not found.")
            return

        entity = self.characters[name]

        new_font = entity["font"]
        if new_font_path and new_size:
            try:
                new_font = pygame.font.Font(new_font_path, new_size)
            except Exception as e:
                print(f"Error loading new font '{new_font_path}': {e}")
                return

        if new_content:
            entity["content"] = new_content
        if new_color:
            entity["color"] = new_color

        entity["font"] = new_font
        entity["image"] = new_font.render(entity["content"], True, entity["color"])

    def slide_entity(self, name, new_position, duration):
        if name not in self.characters and name not in self.draggable_entities:
            print(f"Entity '{name}' not found.")
            return

        entity = self.characters.get(name, None)

        if not entity:
            print(f"Entity '{name}' could not be retrieved.")
            return

        initial_position = entity["position"]
        frames = int(duration * 60)

        def animate():
            for i in range(frames + 1):
                progress = i / frames
                ease_progress = (1 - math.cos(progress * math.pi)) / 2
                new_x = initial_position[0] + (new_position[0] - initial_position[0]) * ease_progress
                new_y = initial_position[1] + (new_position[1] - initial_position[1]) * ease_progress
                entity["position"] = (new_x, new_y)
                time.sleep(1 / 60)

            entity["position"] = new_position

        threading.Thread(target=animate, daemon=True).start()

    def entity_resize(self, name, scale_factor, duration=1.0):
        if name not in self.characters:
            print(f"Entity '{name}' not found.")
            return

        entity = self.characters[name]
        original_image = entity["image"]
        original_width, original_height = original_image.get_size()

        target_width = int(original_width * scale_factor)
        target_height = int(original_height * scale_factor)

        frames = int(duration * 60)

        def animate():
            for i in range(frames + 1):
                progress = i / frames
                ease_progress = (1 - math.cos(progress * math.pi)) / 2

                current_width = int(original_width + (target_width - original_width) * ease_progress)
                current_height = int(original_height + (target_height - original_height) * ease_progress)

                entity["image"] = pygame.transform.scale(original_image, (current_width, current_height))
                time.sleep(1 / 60)

            entity["image"] = pygame.transform.scale(original_image, (target_width, target_height))

        threading.Thread(target=animate, daemon=True).start()

    def draw_dialog_box(self):
        self.dialog_box.draw(self.screen, (50, self.height - 200), self.dialog_text, self.font)

    def layout_buttons(self):
        button_spacing = self.dialog_button_spacing
        total_button_width = sum(button.size[0] for button in self.buttons) + (len(self.buttons) - 1) * button_spacing
        start_x = (self.dialog_box.size[0] - total_button_width) // 2 + self.button_offset_x
        for i, button in enumerate(self.buttons):
            button_width, button_height = self.dialog_button_size
            button.size = (button_width, button_height)
            button_color = button.hover_color if button == self.button_hovered else (50, 150, 250)

            self.draw_button(button, start_x + i * (button_width + button_spacing),
                             self.height - 218 + self.button_offset_y, button.hover_color)

    def set_dialog_button_size(self, width, height):
        self.dialog_button_size = (width, height)
        for button in self.buttons:
            button.size = (width, height)

    def set_static_button_size(self, width, height):
        self.static_button_size = (width, height)
        for button in self.static_buttons:
            button.size = (width, height)

    def set_dialog_button_spacing(self, spacing):
        self.dialog_button_spacing = spacing

    def set_static_button_spacing(self, spacing):
        self.static_button_spacing = spacing

    def load_dialogs(self, file_path):
        global CUNE_WARN
        global CUNE_ERR
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    self.current_dialog = json.load(f)
                    if not isinstance(self.current_dialog, list):
                        CUNE_WARN += 1
                        print(f"[CUNE-WARN ({CUNE_WARN})] Warning: Loaded dialogs is not a list. Please check the JSON format.")
                        self.current_dialog = []
                except json.JSONDecodeError as e:
                    CUNE_ERR += 1
                    print(f"[CUNE-ERR ({CUNE_ERR})] Error: decoding JSON:", e)
                    self.current_dialog = []

    def draw(self):
        self.screen.fill((0, 0, 0))

        if self.background:
            self.screen.blit(self.background, (0, 0))

        if hasattr(self, 'window_icon') and self.window_icon:
            self.screen.blit(self.window_icon, self.window_icon_position)

        current_time = pygame.time.get_ticks()
        sorted_characters = sorted(self.characters.items(), key=lambda c: c[1]["z_level"])

        for name, character in sorted_characters:
            if not character.get("visible", True):
                continue

            alpha = character.get("alpha", 255)
            angle = character.get("angle", 0)

            if "text" in character:
                font = character["font"]
                text_surface = font.render(character["text"], True, character["color"])
                text_surface.set_alpha(alpha)

                if character["entity_bind"]:
                    bound_entity = self.characters.get(character["entity_bind"])
                    if bound_entity:
                        bound_x, bound_y = bound_entity["position"]
                        character["position"] = (
                            bound_x - text_surface.get_width() // 2,
                            bound_y - text_surface.get_height() // 2
                        )

                rotated_text = pygame.transform.rotate(text_surface, angle)
                text_rect = rotated_text.get_rect(center=character["position"])
                self.screen.blit(rotated_text, text_rect)

            elif "frames" in character:
                if current_time - character["last_update_time"] >= (1000 // character["frame_rate"]):
                    character["last_update_time"] = current_time

                    if character["fwdbwd"]:
                        character["current_frame"] += character["frame_direction"]
                        if character["current_frame"] >= len(character["frames"]):
                            character["current_frame"] = len(character["frames"]) - 2
                            character["frame_direction"] = -1
                        elif character["current_frame"] < 0:
                            character["current_frame"] = 1
                            character["frame_direction"] = 1
                    else:
                        character["current_frame"] = (character["current_frame"] + 1) % len(character["frames"])

                frame = character["frames"][character["current_frame"]].copy()
                frame.set_alpha(alpha)
                rotated_frame = pygame.transform.rotate(frame, angle)
                frame_rect = rotated_frame.get_rect(center=character["position"])
                self.screen.blit(rotated_frame, frame_rect)

            else:
                image = character["image"].copy()
                image.set_alpha(alpha)
                rotated_image = pygame.transform.rotate(image, angle)
                image_rect = rotated_image.get_rect(center=character["position"])
                self.screen.blit(rotated_image, image_rect)

        if self.is_dialog_visible:
            self.draw_dialog_box()
            self.layout_buttons()

        self.layout_static_buttons(self.static_button_x, self.static_button_y, custom_positions)

        pygame.display.flip()

    def run(self):
        global CUNE_ERR
        global CUNE_WARN

        if CUNE_WARN >= 300:
            CUNE_WARN = 0

        if CUNE_ERR >= 300:
            CUNE_ERR = 0

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.settings_manager.save_settings()

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()

                    for button in self.buttons:
                        if button.rect and button.rect.collidepoint(mouse_pos):
                            self.click_sound.play()
                            button.run_command_in_thread()
                            self.auto_thread = None

                    for button in self.static_buttons:
                        if button.rect and button.rect.collidepoint(mouse_pos):
                            self.static_click_sound.play()
                            button.run_command_in_thread()
                            break

                    for name, data in self.draggable_entities.items():
                        entity = self.characters.get(name)

                        if entity:
                            if "frames" in entity:
                                current_frame = entity["frames"][entity["current_frame"]]
                                entity_width, entity_height = current_frame.get_size()
                            else:
                                entity_width, entity_height = entity["image"].get_size()

                            entity_x, entity_y = entity["position"]

                            entity_rect = pygame.Rect(
                                entity_x - entity_width // 2,
                                entity_y - entity_height // 2,
                                entity_width,
                                entity_height
                            )

                            if entity_rect.collidepoint(mouse_pos):
                                if data["on_click"]:
                                    data["on_click"]()

                                if data["animated"] and data["animate_on"] == "mousedown":
                                    entity["current_frame"] = 0

                                if data["draggable"]:
                                    self.dragging_entity = name
                                    self.drag_offset = (
                                        mouse_pos[0] - entity_x,
                                        mouse_pos[1] - entity_y
                                    )

                                break

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.dragging_entity:
                        entity = self.characters.get(self.dragging_entity)
                        data = self.draggable_entities.get(self.dragging_entity)

                        if entity and data and data["animated"] and data["animate_on"] == "mouseup":
                            entity["current_frame"] = 0

                    self.dragging_entity = None

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging_entity:
                        mouse_pos = pygame.mouse.get_pos()
                        entity = self.characters[self.dragging_entity]
                        data = self.draggable_entities[self.dragging_entity]

                        new_x = mouse_pos[0] - self.drag_offset[0]
                        new_y = mouse_pos[1] - self.drag_offset[1]

                        if data["drag_bounds"]:
                            x_min, y_min, x_max, y_max = data["drag_bounds"]
                            new_x = max(x_min, min(new_x, x_max - entity["image"].get_width()))
                            new_y = max(y_min, min(new_y, y_max - entity["image"].get_height()))

                        entity["position"] = (new_x, new_y)

                        for text_name, text_entity in self.characters.items():
                            if text_entity.get("entity_bind") == self.dragging_entity:
                                text_x = new_x - text_entity["image"].get_width() // 2 + self.tex_offset
                                text_y = new_y - text_entity["image"].get_height() // 2 + self.tey_offset
                                text_entity["position"] = (text_x, text_y)

            for name, data in self.draggable_entities.items():
                entity = self.characters.get(name)
                if entity and data["animated"] and data["animate_on"] == "always":
                    entity["current_frame"] = (entity["current_frame"] + 1) % len(entity["frames"]) if data[
                        "loop"] else min(entity["current_frame"] + 1, len(entity["frames"]) - 1)

            mouse_pos = pygame.mouse.get_pos()
            self.button_hovered = None
            for button in self.buttons:
                if button.rect and button.rect.collidepoint(mouse_pos):
                    self.button_hovered = button
                    break

            self.static_button_hovered = None
            for button in self.static_buttons:
                if button.rect and button.rect.collidepoint(mouse_pos):
                    self.static_button_hovered = button
                    break

            if not self.static_button_hovered:
                self.last_static_button_hovered = None

            if not self.button_hovered:
                self.last_button_hovered = None

            if self.static_button_hovered and self.static_button_hovered != self.last_static_button_hovered:
                self.static_hover_sound.play()
                self.last_static_button_hovered = self.static_button_hovered

            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    engine = CUNE()
    engine.run()
