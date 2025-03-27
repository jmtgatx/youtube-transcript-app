from flask import Flask, request, render_template, send_file
from youtube_transcript_api import YouTubeTranscriptApi
import io
import re

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
            try:
                # Try the selected language first
                transcript_lines = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            except:
                try:
                    # Fallback to any available transcript
                    transcript_lines = YouTubeTranscriptApi.get_transcript(video_id)
                    error = f"No transcript found in '{language}'. Showing available transcript instead."
                except Exception as e:
                    error = f"No transcripts available: {str(e)}"
                    transcript_lines = []

            transcript = "\n".join([line['text'] for line in transcript_lines])

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
        return f"Error downloading transcript: {str(e)}"

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

if __name__ == '__main__':
    app.run(debug=True)
