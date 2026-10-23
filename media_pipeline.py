import os
import logging
from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
from gtts import gTTS
from resilience import retry_with_backoff

logger = logging.getLogger("VIOS-MediaPipeline")

class MediaPipeline:
    def __init__(self, assets_dir="assets"):
        self.assets_dir = assets_dir

    @retry_with_backoff(retries=3)
    def generate_tts(self, text: str, output_path: str):
        """Generates high-quality speech using gTTS."""
        logger.info(f"Generating TTS for text: {text[:30]}...")
        tts = gTTS(text=text, lang='it')
        tts.save(output_path)
        return output_path

    @retry_with_backoff(retries=3)
    def assemble_vertical_video(self, image_path: str, audio_path: str, text_overlay: str, output_path: str):
        """
        Assembles a 9:16 vertical video with kinetic-style subtitles.
        """
        logger.info(f"Assembling video: {output_path}")

        # 1. Load Audio and get duration
        audio = AudioFileClip(audio_path)
        duration = audio.duration

        # 2. Create Background Image (9:16)
        # Standard TikTok/Reels size: 1080x1920
        img_clip = ImageClip(image_path).with_duration(duration)
        img_clip = img_clip.with_position("center").resized(height=1920) # Basic scale

        # 3. Create Dynamic Text Overlay (Kinetic Typography Style)
        # Note: TextClip requires ImageMagick installed on the system
        try:
            txt_clip = TextClip(
                text=text_overlay,
                font_size=70,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(900, None)
            ).with_duration(duration).with_position("center")
        except Exception as e:
            logger.warning(f"TextClip failed (ImageMagick missing?). Using fallback: {e}")
            txt_clip = ColorClip(size=(1,1), color=(0,0,0)).with_duration(0)

        # 4. Composite and Export
        video = CompositeVideoClip([img_clip, txt_clip], size=(1080, 1920))
        video.audio = audio
        video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

        return output_path
