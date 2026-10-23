import os
import logging
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from resilience import retry_with_backoff, notify_telegram
from media_pipeline import MediaPipeline

# Import your database models and session
try:
    from database import Engine, Session, ContentItem
except ImportError:
    logging.warning("database.py not found. Using mock models for structural demonstration.")
    class ContentItem:
        id: int
        status: str
        error_log: str
        creator_name: str
        prompt: str
        script: str
        image_path: str
        audio_path: str
        video_path: str

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VIOS-Worker")

class VIOSWorker:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.media_pipeline = MediaPipeline()
        self.scheduler.start()

    def run_pipeline_cycle(self):
        """
        Main loop that processes contents through the lifecycle:
        DRAFT -> SCRIPTING -> RENDERING -> SCHEDULED -> PUBLISHED
        """
        logger.info(f"Cycle started at {datetime.now()}")

        try:
            # 1. Process SCRIPTING (DRAFT -> SCRIPTING)
            self._process_stage("DRAFT", "SCRIPTING", self._generate_script)

            # 2. Process RENDERING (SCRIPTING -> RENDERING)
            self._process_stage("SCRIPTING", "RENDERING", self._generate_assets)

            # 3. Process SCHEDULING (RENDERING -> SCHEDULED)
            self._process_stage("RENDERING", "SCHEDULED", self._schedule_content)

            # 4. Process PUBLISHING (SCHEDULED -> PUBLISHED)
            self._process_stage("SCHEDULED", "PUBLISHED", self._publish_content)

        except Exception as e:
            error_msg = f"Critical failure in Worker Cycle: {str(e)}"
            logger.error(error_msg)
            notify_telegram(error_msg)

    def _process_stage(self, from_status, to_status, process_func):
        """Generic stage processor with error handling."""
        from database import Session, Engine
        with Session(Engine) as session:
            items = session.exec(ContentItem.select().where(ContentItem.status == from_status)).all()

            for item in items:
                try:
                    logger.info(f"Processing Item {item.id} [{from_status} -> {to_status}]")
                    process_func(item, session)
                    item.status = to_status
                    session.add(item)
                    session.commit()
                except Exception as e:
                    item.status = "ERROR"
                    item.error_log = str(e)
                    session.add(item)
                    session.commit()
                    logger.error(f"Item {item.id} failed: {e}")

    @retry_with_backoff(retries=3)
    def _generate_script(self, item, session):
        """Logic to generate script using Growth Engine prompts."""
        logger.info(f"Generating script for {item.id}...")
        # Integration with your script generation logic
        item.script = f"Script for {item.id}: [HOOK] Attention! [BODY] Value content... [CTA] Save this!"
        pass

    @retry_with_backoff(retries=3)
    def _generate_assets(self, item, session):
        """Logic to generate images and assemble video via media_pipeline."""
        logger.info(f"Rendering assets for {item.id}...")

        # 1. Generate Audio
        audio_path = os.path.join("creators", item.creator_name, "assets", f"{item.id}_audio.mp3")
        self.media_pipeline.generate_tts(item.script, audio_path)
        item.audio_path = audio_path

        # 2. Assemble Video (Using image_path from database or default)
        video_path = os.path.join("creators", item.creator_name, "assets", f"{item.id}_video.mp4")
        self.media_pipeline.assemble_vertical_video(
            image_path=item.image_path or "assets/default.png",
            audio_path=audio_path,
            text_overlay=item.script[:100],
            output_path=video_path
        )
        item.video_path = video_path

    @retry_with_backoff(retries=3)
    def _schedule_content(self, item, session):
        """Logic to schedule content on platforms."""
        logger.info(f"Scheduling {item.id}...")
        # Integration with publisher.py
        pass

    @retry_with_backoff(retries=3)
    def _publish_content(self, item, session):
        """Final publishing step."""
        logger.info(f"Publishing {item.id}...")
        # Integration with publisher.py
        pass

    def start(self):
        # Run every 10 minutes
        self.scheduler.add_job(self.run_pipeline_cycle, 'interval', minutes=10)
        logger.info("VIOS Background Worker started. Interval: 10m")

if __name__ == "__main__":
    worker = VIOSWorker()
    worker.start()
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        worker.scheduler.shutdown()
