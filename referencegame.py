from CUNE import CUNE

# Global variable to control dialog visibility
V = False

'''

def main():
    # Create a dict for custom button positions ONLY STATIC BUTTONS

    # engine.set_dim(800, 400)
    #engine.modify_dialogbox("assets/dialog_texture.png",(912, 171))
    #engine.modify_text_offset(100, 200)
    #engine.modify_dialog_adjustment(0, -50)

    custom_positions = {
        "Dialog Test": (50, 50),  # Custom position for "Dialog Test"
        "Dialog State": (50, 100),  # Custom position for "Dialog State"
        "Quit": (50, 150),  # Custom position for "Quit"
        "Start Music": (50, 200),  # Custom position for "Start Music"
        "Stop Music": (50, 250),  # Custom position for "Stop Music"
        #"Remove Me": (600, 300),        # Custom position for "Remove Me"
        "Skip": (50, 300)
    }

    engine = CUNE()
    #engine.set_dim(800, 400)
    engine.set_app_icon("assets/icons/img.png")

    # Center left position for the static button
    center_left_x = 50
    center_left_y = (engine.height - 30) // 2  # Assuming button height is 30

    # Set positions for the static buttons in the engine
    engine.static_button_x = center_left_x
    engine.static_button_y = center_left_y


    # Add static buttons with their respective positions
    dialog_test_button = engine.add_static_button(
        "Dialog Test",
        lambda: retrigger_dialog(engine),
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )
    dialog_test_button.set_default_position(*custom_positions["Dialog Test"])

    dialog_state_button = engine.add_static_button(
        "Dialog State",
        lambda: dialog_toggle(engine),
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )
    dialog_state_button.set_default_position(*custom_positions["Dialog State"])

    quit_button = engine.add_static_button(
        "Quit",
        lambda: exit(engine),
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )
    quit_button.set_default_position(*custom_positions["Quit"])

    # Add a skip button to set the dialog to a specific index

    skip_button = engine.add_static_button(
        "Skip",
        lambda: engine.set_dialog(engine.current_dialog[5:]),  # Set to the dialog from index 5
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )
    skip_button.set_default_position(*custom_positions["Skip"])


    # Adding static buttons with volume control
    engine.add_static_button(
        "Start Music",
        lambda: engine.play_audio("assets/background_music.mp3", volume=0.2, repeat=True),
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )

    engine.add_static_button(
        "Stop Music",
        engine.stop_audio,
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )

    # Button to change Monika's texture
    engine.add_button(
        "chng Texture",
        lambda: (engine.change_entity_texture(
            "Monika",
            "assets/test_entity.png",
            scale_factor_setter=1.2,  # Scale by 1.2x
            duration=1.5  # 1.5 seconds fade duration
        ), engine.slide_entity("Monika", (200, 50), 0.5)),
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )

    # Add the "Remove Me" button with functionality to remove itself
    #remove_button = engine.add_static_button(
    #    "Remove Me",
    #    lambda: remove_self(engine, "Remove Me"),
    #    hover_color=(255, 182, 193),
    #    normal_color=(50, 150, 50)
    #)
    #remove_button.set_default_position(*custom_positions["Remove Me"])

    # Add main control buttons
    engine.add_button(
        "Next",
        lambda: (engine.next_dialog(), remove_self(engine, "Remove Me"), do_dialog_selection()),
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
        #alpha=0  # Set the alpha value for transparency (0-255)
    )

    engine.add_button(
        "Auto",
        lambda: engine.toggle_auto(),
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )

    engine.add_button(
        "History",
        lambda: engine.show_dialog_history(),
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )

    # New "Slide" button to move Monika to (150, 0)
    engine.add_button(
        "Slide",
        lambda: engine.slide_entity("Monika", (-200, 0), 0.5),  # Slide Monika to (150, 0) in 0.5 seconds
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )

    # New "Return" button to move Monika back to (0, 0)
    engine.add_button(
        "Return",
        lambda: engine.slide_entity("Monika", (0, 0), 0.5),  # Return Monika to (0, 0) in 0.5 seconds
        hover_color=(255, 182, 193),
        normal_color=(255, 105, 180)
    )


    # Set the background image
    #engine.set_background("assets/background.png")

    # Add static background with the lowest Z level
    #engine.add_entity("static-background", "assets/white.png", position=(1.5, 0), z_level=0)
    engine.add_entity_with_scale_factor("static-background", "assets/white.png", 2, position=(-500, 0), z_level=0)

    engine.hide_entity("character_name", "shrink_fade", 255, 0, 1.0)
    engine.show_entity("character_name", "grow_fade", 0, 255, 1.0)




    # Add dynamic background above static background
    #engine.add_entity("background", "assets/background.png", position=(1.5, 0), z_level=1)

    # Add Monika above backgrounds
    #engine.add_entity("Monika", "assets/monika.png", position=(0, 0), z_level=2)

    def my_custom_action():
        print("Draggable Box Clicked!")
    
    engine.add_draggable_entity(
        name="draggable_box",
        frame_folder="assets/box_frames",  # Folder with numbered frames (0.png, 1.png, etc.)
        position=(100, 100),
        draggable=True,
        on_click=my_custom_action,
        animated=True,
        animate_on="mousedown",  # Play animation on click
        loop=True,  # Keep looping animation
        snap_to_grid=(50, 50)  # Snap dragging to a 50x50 grid
    )

    # Add an animated entity for bouncing ball/monika
    engine.add_animated_entity(
        name="AnimatedMonika",
        folder_path="assets/entitywithframes/monika",  # Path to the folder containing the frames
        position=(0, 0),  # Position of the animated entity
        z_level=3,  # Z-level for layering
        frame_rate=10,  # Frames per second
        fwdbwd=True  # Enable forward-backward animation
    )


    #ADD ANIMATED DRAGGABLE ENTITIES

        engine.add_draggable_entity(
        name="draggable_box",
        frame_folder="assets/entitywithframes/monika",  # Folder with numbered frames (0.png, 1.png, etc.)
        position=(100, 100),
        draggable=True,
        on_click=pass_this(),
        animated=True,
        animate_on="mousedown",  # Play animation on click
        loop=True,  # Keep looping animation
        snap_to_grid=(50, 50),  # Snap dragging to a 50x50 grid
        z_level=5,
        fwbwdvar=True
    )
        
    #engine.add_text_entity("placeholder", "testboi", "fonts/Aller_Rg.ttf", 18, entity_bind="button", z_level=4, tx_offset=30, ty_offset=10)
    
    engine.add_draggable_entity(
        name="draggable_box1",
        image_path="assets/monika.png",  # Folder with numbered frames (0.png, 1.png, etc.)
        position=(100, 100),
        draggable=True,
        on_click=pass_this(),
        animated=False,
        #animate_on="mousedown",  # Play animation on click
        loop=True,  # Keep looping animation
        snap_to_grid=(50, 50),  # Snap dragging to a 50x50 grid
        z_level=6
    )

    
        if Cur_dialog_ID == 2:
            engine.hide_entity("draggable_box1", "slide_back",  1, "~", 50)
        elif Cur_dialog_ID == 3:
            engine.show_entity("draggable_box1", "", 1, "~", 0)


    #set font or fnt or whatever you call it. for dialog only
    engine.set_dialog_font("fonts/Aller_Rg.ttf", font_size=20)

    #set font or fnt or whatever you call it. but for buttons
    engine.set_button_font("fonts/Vera.ttf", font_size=12)

    # Set the title of the visual novel window
    engine.set_title("Test example game in CUNE Engine")

    # Load the initial dialog from a file
    engine.load_dialogs("dialogs.json")

    # Set the dialog to be displayed
    engine.set_dialog(engine.current_dialog)



    def do_dialog_selection():
        global V
        Cur_dialog_ID = CUNE.get_current_dialog_id(engine)
        #engine.modify_dialogbox("assets/entitywithframes/monika/0.png", (500, 171))



        # implement later this is placeholder!

    # Set initial volume (you can define this in your settings)
    initial_volume = engine.settings_manager.volume if hasattr(engine.settings_manager, 'volume') else 0.5

    # Play background music with looping when the game starts
    engine.play_audio("assets/background_music.mp3", 0.2, repeat=True)

    # Layout static buttons using custom positions
    engine.layout_static_buttons(center_left_x, center_left_y, custom_positions)

    # Run the engine
    engine.run()


def remove_self(engine, button_text):
    """Remove a button from the engine."""
    engine.remove_static_button(button_text)


def retrigger_dialog(engine):
    """Reset and show the current dialog again."""
    engine.set_dialog(engine.current_dialog)


def dialog_toggle(engine):
    """Toggle dialog visibility on or off."""
    engine.dialog_visible_toggle()


def exit(engine):
    """Stop the engine and save settings on exit."""
    engine.running = False
    engine.settings_manager.save_settings()
    engine.stop_audio()  # Stop background music when quitting


if __name__ == "__main__":
    main()
'''
