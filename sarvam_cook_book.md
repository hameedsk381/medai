### **Overview**

This cookbook demonstrates a robust, production-ready call analytics pipeline using Sarvam's SDK. It leverages the Sarvam's Speech-to-Text Translate Batch API with diarization, parses speaker-wise transcripts, and uses Sarvam's LLM for deep analysis. All outputs are saved in structured files for further review.

### Business Value of Call Analytics Module

<ul>
  <li>
    Improve agent effectiveness
  </li>

  <li>
    Understand customer sentiment
  </li>

  <li>
    Detect operational issues early
  </li>

  <li>
    Spot upsell/cross-sell opportunities
  </li>

  <li>
    Generate real-time dashboards
  </li>
</ul>

### Where is it useful

<ul>
  <li>
    <b>E-commerce / D2C:</b>

     Understand refund requests, delivery concerns, or dissatisfaction with product quality.
  </li>

  <li>
    <b>Contact Centers / BPOs:</b>

     Automate call reviews to improve training and ensure compliance at scale.
  </li>

  <li>
    <b>Healthcare & Insurance:</b>

     Analyze patient queries, support delays, and sentiment in sensitive service calls.
  </li>
</ul>

### Why Diarization and Speaker-wise Parsing?

* Diarization assigns speaker labels, linking each line of text to the speaker who said it. This enables:
  * Accurate agent/customer identification
  * Speaker-specific sentiment analysis
  * Monitoring agent talk-time vs. listening time
* Speaker-wise parsing preserves the chronological flow, enabling deeper insights and more accurate LLM analysis.

<Note>
  You can find sample audio files in the <a href="https://github.com/sarvamai/sarvam-ai-cookbook/tree/main/sample_data/call_analytics_audios" target="blank">GitHub cookbook</a>.
</Note>

### 1. Install the SDK and Dependencies

Before you begin, ensure you have the necessary Python libraries installed. Run the following command in your terminal or notebook:

```bash
pip install sarvamai
```

### 2. Authentication

To use the API, you need an API subscription key. Follow these steps to set up your API key:

1. **Obtain your API key**: If you don’t have an API key, sign up on the [Sarvam AI Dashboard](https://dashboard.sarvam.ai/) to get one.
2. **Replace the placeholder key**: In the [Full Workflow](#5-full-workflow-example) below, replace "YOUR\_SARVAM\_AI\_API\_KEY" with your actual API key.

### 3. Set Up Essential Modules and Output Directory

Set up your imports and create an output directory for all generated files (transcripts, analysis, summaries, etc.):

```python
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from pydub import AudioSegment
from sarvamai import SarvamAI
import textwrap

OUTPUT_DIR = "outputs"
Path(OUTPUT_DIR).mkdir(exist_ok=True)
```

### 4. The Call Analytics Class

This class encapsulates the full workflow: splitting audio, batch transcription with diarization, parsing, analysis, Q\&A, and summary generation.

<code>split\_audio</code>
Splits a long audio file into smaller chunks if its duration exceeds 1 hour, since the Batch API can process up to 1 hour per file.

```python
def split_audio(audio_path: str, chunk_duration_ms: int = 60 * 60 * 1000) -> List[AudioSegment]:
    audio = AudioSegment.from_file(audio_path)
    return [audio[i:i + chunk_duration_ms] for i in range(0, len(audio), chunk_duration_ms)] if len(audio) > chunk_duration_ms else [audio]
```

**4.1 Class definition and initialization**

```python
class CallAnalytics:
    def __init__(self, client):
        self.client = client
        self.transcriptions = {}  
```

**4.1.1: process\_audio\_file**
<p>Creates a transcription job using Sarvam's STT Batch API, waits for job completion, downloads and parses transcription output, and calls analysis on the parsed conversation.</p>

<Note>
  For longer audio files, make sure to set the <code>timeout</code> parameter in <code>upload\_files</code> to a sufficiently high value to allow the upload to complete successfully.
</Note>

```python
    def process_audio_files(self, audio_paths: List[str]) -> Dict[str, str]:
        if not audio_paths:
            print("No audio files provided")
            return {}

        print(f"Processing {len(audio_paths)} audio files...")

        try:
            job = client.speech_to_text_translate_job.create_job(
                model="saaras:v3",
                mode="translate",
                with_diarization=True,
            )

            job.upload_files(file_paths=audio_paths, timeout=300)
            job.start()

            print("Waiting for transcription to complete...")
            job.wait_until_complete()

            if job.is_failed():
                print("Transcription failed!")
                return {}

            output_dir = Path(f"{OUTPUT_DIR}/transcriptions_{job.job_id}")
            output_dir.mkdir(parents=True, exist_ok=True)
            job.download_outputs(output_dir=str(output_dir))
            json_files = list(output_dir.glob("*.json"))
            if not json_files:
              raise FileNotFoundError(f"No .json transcription files found in {output_dir}.")

            transcriptions = self._parse_transcriptions(output_dir)
            self.transcriptions.update(transcriptions)

            print(f"Successfully transcribed {len(transcriptions)} files!")

            for file_name, data in transcriptions.items():
                self.analyze_transcription(data["conversation_path"], output_dir, file_name)

            return transcriptions

        except Exception as e:
            print(f"Error processing audio files: {e}")
            return {}
```

**4.1.2: \_parse\_transcriptions**
<p>Reads downloaded JSON transcription files, extracts speaker-wise lines, writes a `.txt` file with clean conversation format, and calculates total speaking time per speaker.</p>

* <code>timing.json</code>: Tracks the total speaking time per speaker in seconds. Beneficial in identifying the dominant speaker and helps in monitoring Agent Talk-Time vs. Listening Time.

```python
    def _parse_transcriptions(self, output_dir: Path) -> Dict[str, dict]:
        transcriptions = {}
        for json_file in output_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                diarized = data.get("diarized_transcript", {}).get("entries")
                speaker_times = {}
                lines = []
                if diarized:
                    for entry in diarized:
                        speaker = entry["speaker_id"]
                        text = entry["transcript"]
                        lines.append(f"{speaker}: {text}")
                        start = entry.get("start_time_seconds")
                        end = entry.get("end_time_seconds")
                        if start is not None and end is not None:
                            duration = end - start
                            speaker_times[speaker] = speaker_times.get(speaker, 0.0) + duration
                else:
                    lines = [f"UNKNOWN: {data.get('transcript', '')}"]
                
                conversation_text = "\n".join(lines)
                txt_path = output_dir / f"{json_file.stem}_conversation.txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(conversation_text)
                
                timing_path = None
                if speaker_times:
                    timing_path = output_dir / f"{json_file.stem}_timing.json"
                    with open(timing_path, "w", encoding="utf-8") as f:
                        json.dump(speaker_times, f, indent=2)
                transcriptions[json_file.stem] = {
                    "entries": diarized or [],
                    "conversation_path": str(txt_path),
                    "timing_path": str(timing_path) if timing_path else None
                }
            except Exception as e:
                print(f"Error parsing {json_file}: {e}")
        return transcriptions
```

**4.1.3: analyze\_transcription**
<p>Reads the conversation file and sends it to Sarvam LLM with a detailed analysis prompt to extract structured insights.</p>

```python
ANALYSIS_PROMPT_TEMPLATE = """
Analyze this call transcription thoroughly from start to finish.

TRANSCRIPTION:
{transcription}

Please answer the following:

1. Identify which speaker is the **customer** and which one is the **agent**.
2. Determine if the customer is a **new/potential customer** or an **existing customer**.
3. What **problem, query, or doubt** did the customer raise at the beginning?
4. What **services/products** was the customer inquiring about or facing issues with?
5. How did the agent respond to and resolve the issue throughout the call?
6. Was the **customer satisfied** at the end of the call?
7. Did the customer express any **emotions or sentiments** (positive, negative, or neutral)?
8. Were there any mentions of **competitors**, or any opportunities for **upselling or cross-selling**?
9. Summarize the **resolution** and whether it was successful.

Provide your answer in a clear, structured format with section headings and bullet points.
"""
```

```python
    def analyze_transcription(self, conversation_path: str, output_dir: Path, file_name: str) -> Dict:
        try:
            with open(conversation_path, "r", encoding="utf-8") as f:
                transcription = f.read()
            analysis_prompt = textwrap.dedent(ANALYSIS_PROMPT_TEMPLATE.format(transcription=transcription))
            messages = [
                {"role": "system", "content": "You are a call analytics expert working for a company's support operations team. Your job is to understand customer calls end-to-end and provide structured insights to improve customer experience and agent effectiveness."},
                {"role": "user", "content": analysis_prompt},
            ]
            response = self.client.chat.completions(messages=messages)
            analysis = response.choices[0].message.content
            analysis_path = output_dir / f"{file_name}_analysis.txt"
            with open(analysis_path, "w", encoding="utf-8") as f:
                f.write(analysis.strip())
            print(f"Analysis saved to {analysis_path}")
            return {"file_name": file_name, "analysis_path": str(analysis_path)}
        except Exception as e:
            error_msg = f"Error analyzing transcription: {str(e)}"
            print(error_msg)
            return {"file_name": file_name, "error": error_msg, "timestamp": datetime.now().isoformat()}
```

**4.1.4: answer\_question**
<p>Answers a user-defined question based on the parsed conversation transcript and saves the answer to a file.</p>

```python
    def answer_question(self, question: str, output_dir: Optional[Path] = None) -> None:
        for file_name, data in self.transcriptions.items():
            try:
                with open(data["conversation_path"], "r", encoding="utf-8") as f:
                    transcription = f.read()
                prompt = f"Based on this call transcription, answer the question below:\n\nTRANSCRIPTION:\n{transcription}\n\nQUESTION: {question}"
                messages = [
                    {"role": "system", "content": ""},
                    {"role": "user", "content": prompt},
                ]
                response = self.client.chat.completions(messages=messages)
                answer = response.choices[0].message.content
                q_hash = hashlib.sha1(question.encode()).hexdigest()[:6]
                path = Path(data["conversation_path"]).parent / f"{file_name}_question_{q_hash}.txt"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"Question: {question}\n\nAnswer:\n{answer}")
                print(f"Answer saved to {path}")
            except Exception as e:
                print(f"Error answering question for {file_name}: {e}")
```

**4.1.5: get\_summary**
<p>Generates a concise summary for each call analysis and saves it to a summary file for easy review.</p>

```python
SUMMARY_PROMPT_TEMPLATE = """
Based on this call analysis, summarize each of the following in 2–3 words:

{analysis_text}

1. Customer & Agent
2. Customer Type
3. Main Issue
4. Service Discussed
5. Agent's Response
6. Customer Satisfaction
7. Sentiment
8. Competitor or Upsell
9. Resolution
"""
```

```python
    def get_summary(self, output_dir: Optional[Path] = None) -> None:
        output_dir = output_dir or Path(OUTPUT_DIR)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = output_dir / f"summary_{timestamp}.txt"
        try:
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write("CALL ANALYTICS SUMMARY REPORT\n")
                f.write("=" * 60 + "\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write(f"Total Calls: {len(self.transcriptions)}\n")
                f.write("=" * 60 + "\n\n")
                for file_name, data in self.transcriptions.items():
                    analysis_file = Path(data["conversation_path"]).parent / f"{file_name}_analysis.txt"
                    if not analysis_file.exists():
                        print(f"Analysis file not found for {file_name}, skipping.")
                        continue
                    with open(analysis_file, "r", encoding="utf-8") as af:
                        analysis_text = af.read()
                    summary_prompt = textwrap.dedent(SUMMARY_PROMPT_TEMPLATE.format(analysis_text=analysis_text))
                    messages = [
                        {"role": "system", "content": "You are a call analytics summarizing expert. Provide concise and clear answers to each point "},
                        {"role": "user", "content": summary_prompt},
                    ]
                    response = self.client.chat.completions(messages=messages)
                    concise_summary = response.choices[0].message.content.strip()
                    f.write(f"Call File: {file_name}\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"{concise_summary}\n\n")
            print(f"Summary saved to {summary_path}")
        except Exception as e:
            print(f"Error writing summary: {e}")
```

### 5. Full Workflow Example

This code block runs the full call analytics workflow: transcribes the audio, analyzes the conversation, answers a specific user question, and generates a concise summary.

```python
client = SarvamAI(api_subscription_key="YOUR_SARVAM_AI_API_KEY")
analytics = CallAnalytics(client=client)

audio_path = "/path/to/your/audio/file.mp3"  
analytics.process_audio_files([audio_path]) 
analytics.answer_question("Add your question here")
analytics.get_summary()

```

<Note>
  For long recordings, the resulting transcription may exceed the maximum token limit of the LLM.
</Note>

### 6. Sample Output

This is the sample output of the analysis you will get if you upload the file [Sample\_product\_refund.mp3](https://github.com/sarvamai/sarvam-ai-cookbook/blob/main/sample_data/call_analytics_audios/Sample_product_refund.mp3).

```
Here's a structured analysis of the call transcription:

### 1. Speaker Identification
* **Customer:** SPEAKER_00 (Adam Wilson)
* **Agent:** SPEAKER_01 (Sam from Coaching Downs)

### 2. Customer Type
* **Existing customer:** The customer has previously made a purchase (order number provided) and is now initiating a return and refund request.

### 3. Initial Problem/Query
* The customer called to:
    * Return an item due to incorrect size.
    * Inquire about the status of their refund, as it hasn't reflected in their account yet.

### 4. Services/Products Involved
* **Product:** Clothing item (implied by the return and size issue).
* **Services:** Return processing and refund issuance.

### 5. Agent's Response and Resolution Process
* **Initial Steps:**
    * Requested the order number, customer name, and contact details (phone number and email).
    * Verified the order details in the system.
* **Issue Identification:**
    * The order wasn't immediately found in the system, leading to further verification.
    * The customer lacked the return tracking number from the courier company.
* **Resolution Steps:**
    * Agent confirmed the return request date (15th of November) and noted it was outside the standard refund processing timeframe.
    * Agent escalated the case to the corporate office for review and promised to send an email update within 2-4 business days.
    * Agent reassured the customer about the refund timeline and confirmed the email address for communication.

### 6. Customer Satisfaction
* **Neutral to slightly positive:** The customer seemed somewhat reassured by the agent's explanation and the promise of a prompt update. However, there was initial frustration about the refund delay.

### 7. Customer Sentiments
* **Initial Frustration:** Expressing concern about the missing refund and the potential delay in processing.
* **Reassurance:** After the agent's explanation, the customer seemed more at ease, though still awaiting confirmation.

### 8. Competitors/Upselling Opportunities
* **No mention of competitors.**
* **No clear upselling/cross-selling opportunities identified during the call.** The focus was solely on resolving the return and refund issue.

### 9. Resolution Summary and Success
* **Resolution:** The agent escalated the case to the corporate office for review and promised an email update within 2-4 business days.
```

### 7. Additional Resources

For more details, refer to our official documentation and join our community for support:

* **Documentation**: [docs.sarvam.ai](https://docs.sarvam.ai)
* **Community**: [Join the Discord Community](https://discord.com/invite/5rAsykttcs)

### 8. Final Notes

* Keep your API key secure.
* Use clear audio for best results.
* All outputs (transcripts, analysis, summaries) are saved in the `outputs/` directory for easy review.

Keep Building!
