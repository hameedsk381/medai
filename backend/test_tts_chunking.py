import asyncio
import unittest

from app.services.tts_service import TTSService


class FakeTTSService(TTSService):
    def __init__(self):
        super().__init__()
        self.sarvam_key = "test-key"
        self.groq_key = None
        self.calls = []

    async def _synthesize_sarvam(self, text: str, language: str = "en-IN"):
        self.calls.append((text, language))
        await asyncio.sleep(0)
        return f"audio:{text}".encode("utf-8") * 20


class TTSChunkingTests(unittest.TestCase):
    def test_chunk_size_scales_with_text_length(self):
        service = FakeTTSService()
        service.max_chunk_chars = 220

        self.assertEqual(service.get_chunk_size_for_text("Short confirmation."), 140)
        self.assertEqual(service.get_chunk_size_for_text("x" * 200), 160)
        self.assertEqual(service.get_chunk_size_for_text("x" * 400), 180)
        self.assertEqual(service.get_chunk_size_for_text("x" * 700), 220)

    def test_split_text_prefers_sentence_boundaries(self):
        service = FakeTTSService()

        chunks = service.split_text_for_streaming(
            "Hello there. This is a second sentence. Final short line.",
            max_chars=30
        )

        self.assertEqual(
            chunks,
            ["Hello there.", "This is a second sentence.", "Final short line."]
        )

    def test_split_text_breaks_long_sentences(self):
        service = FakeTTSService()

        chunks = service.split_text_for_streaming(
            "This is a very long sentence without a clean stopping point but it should still break into smaller pieces for playback.",
            max_chars=35
        )

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 35 for chunk in chunks))

    def test_generate_speech_stream_yields_per_chunk(self):
        service = FakeTTSService()

        async def collect():
            outputs = []
            async for audio in service.generate_speech_stream(
                "First sentence. Second sentence. Third sentence.",
                language="en-IN"
            ):
                outputs.append(audio)
            return outputs

        outputs = asyncio.run(collect())

        self.assertEqual(len(outputs), 1)
        self.assertEqual(
            service.calls,
            [("First sentence. Second sentence. Third sentence.", "en-IN")]
        )

    def test_generate_speech_stream_splits_long_text(self):
        service = FakeTTSService()
        service.max_chunk_chars = 20
        long_text = (
            "First sentence. Second sentence. Third sentence. Fourth sentence. "
            "Fifth sentence. Sixth sentence. Seventh sentence. Eighth sentence. "
            "Ninth sentence. Tenth sentence. Eleventh sentence. Twelfth sentence."
        )

        async def collect():
            outputs = []
            async for audio in service.generate_speech_stream(
                long_text,
                language="en-IN"
            ):
                outputs.append(audio)
            return outputs

        outputs = asyncio.run(collect())
        expected_chunks = service.split_text_for_streaming(
            long_text,
            service.get_chunk_size_for_text(long_text)
        )

        self.assertGreater(len(outputs), 3)
        self.assertEqual(
            service.calls,
            [(chunk, "en-IN") for chunk in expected_chunks]
        )


if __name__ == "__main__":
    unittest.main()
