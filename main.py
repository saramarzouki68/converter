from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.dropdown import DropDown
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from moviepy.editor import VideoFileClip
from proglog import TqdmProgressBarLogger
from threading import Thread
import os

class VideoConverterApp(App):
    def build(self):
        self.file_path = None
        self.output_format = "mp4"
        self.converted_video_path = None

        # Main layout
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # File chooser
        self.file_chooser = FileChooserIconView(filters=['*.mp4', '*.avi'])
        self.file_chooser.bind(on_selection=self.on_file_selected)
        self.layout.add_widget(self.file_chooser)

        # Label for selected file path
        self.file_label = Label(text="No file selected")
        self.layout.add_widget(self.file_label)

        # Format dropdown
        self.format_dropdown = DropDown()
        formats = ["MP4", "AVI", "GIF"]
        for fmt in formats:
            btn = Button(text=fmt, size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.format_dropdown.select(btn.text))
            self.format_dropdown.add_widget(btn)
        self.format_button = Button(text="Select Output Format (Default: MP4)", size_hint=(1, None), height=40)
        self.format_button.bind(on_release=self.format_dropdown.open)
        self.format_dropdown.bind(on_select=lambda instance, x: setattr(self.format_button, 'text', f"Selected Format: {x}") or setattr(self, 'output_format', x.lower()))
        self.layout.add_widget(self.format_button)

        # Convert button
        self.convert_button = Button(text="Convert", size_hint=(1, None), height=40, on_release=self.start_conversion_thread)
        self.layout.add_widget(self.convert_button)

        # Download button
        self.download_button = Button(text="Download", size_hint=(1, None), height=40, disabled=True, on_release=self.download_converted_file)
        self.layout.add_widget(self.download_button)

        # Status label
        self.status_label = Label(text="Status: Waiting for input")
        self.layout.add_widget(self.status_label)

        # Progress bar
        self.progress_bar = ProgressBar(max=1.0, value=0, size_hint=(1, None), height=20)
        self.layout.add_widget(self.progress_bar)

        return self.layout

    def on_file_selected(self, instance, value):
        if value:
            self.file_path = value[0]
            self.file_label.text = f"Selected file: {os.path.basename(self.file_path)}"

    def start_conversion_thread(self, instance):
        if not self.file_path or not self.output_format:
            self.status_label.text = "Please select a video file and output format."
            return

        # Disable buttons during conversion
        self.convert_button.disabled = True
        self.download_button.disabled = True
        self.status_label.text = "Converting, please wait..."
        self.progress_bar.value = 0

        # Start the conversion in a separate thread
        thread = Thread(target=self.convert_video)
        thread.start()

    def convert_video(self):
        output_file = os.path.splitext(self.file_path)[0] + f"_converted.{self.output_format}"
        self.converted_video_path = output_file

        # Custom progress logger
        class KivyProgressLogger(TqdmProgressBarLogger):
            def bars_callback(self, bar, attr, value, total=None):
                self.total_progress = total if total else 1
                progress = max(0.0, min(value / self.total_progress, 1.0))
                self.progress_bar.value = progress
                self.layout.canvas.ask_update()

        try:
            clip = VideoFileClip(self.file_path)
            logger = KivyProgressLogger()
            if self.output_format == "gif":
                clip.write_gif(output_file, logger=logger)
            elif self.output_format == "mp4":
                clip.write_videofile(output_file, codec="libx264", logger=logger)
            elif self.output_format == "avi":
                clip.write_videofile(output_file, codec="png", logger=logger)

            clip.close()
            self.status_label.text = "Conversion successful! Click Download."
            self.download_button.disabled = False
        except Exception as ex:
            self.status_label.text = f"Error: {str(ex)}"

        # Re-enable buttons
        self.convert_button.disabled = False

    def download_converted_file(self, instance):
        if self.converted_video_path:
            popup = Popup(title="Download Completed", content=Label(text="Download successful!"), size_hint=(0.6, 0.4))
            popup.open()

if __name__ == '__main__':
    VideoConverterApp().run()
