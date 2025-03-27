from flask import Flask, request, render_template, send_file
from youtube_transcript_api import YouTubeTranscriptApi
import io
import re
import os
import traceback

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    transcript = ""
    error = ""
    video_id = ""
    
    if request.method == 'POST':
        video_url = request.form.get('video_url')
        language = request.form.get('language', 'es')
        video_id = extract_video_id(video_url)

        if not video_id:
            error = "Invalid YouTube URL"
        else:
            cache_file = f"cache/{video_id}_{language}.txt"
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as file:
                    transcript = file.read()
                    error = f"Transcript loaded from cache."
            else:
                try:
                    transcript_lines = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
                except Exception:
                    try:
                        transcript_lines = YouTubeTranscriptApi.get_transcript(video_id)
                        error = f"No transcript found in '{language}'. Showing available transcript instead."
                    except Exception as e2:
                        import traceback
                        traceback.print_exc()
                        if "429" in str(e2):
                            error = "Too many requests from this IP. Please try again later."
                        else:
                            error = f"No transcripts available. Reason: {str(e2)}"
                        transcript_lines = []

                transcript = "\n".join([line['text'] for line in transcript_lines])
                # Save to cache if we have a valid transcript
                if transcript.strip():
                    os.makedirs("cache", exist_ok=True)
                    with open(cache_file, "w", encoding="utf-8") as file:
                        file.write(transcript)

    return render_template('index.html', transcript=transcript, error=error, video_id=video_id)


@app.route('/download/<video_id>')
def download_transcript(video_id):
    try:
        transcript_lines = YouTubeTranscriptApi.get_transcript(video_id, languages=['es'])
        transcript = "\n".join([line['text'] for line in transcript_lines])
        
        buffer = io.BytesIO()
        buffer.write(transcript.encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{video_id}_transcript.txt",
            mimetype='text/plain'
        )
    except Exception as e:
        traceback.print_exc()
        return f"Error downloading transcript: {str(e)}"

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
