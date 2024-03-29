import os
import time
from flask import Flask, request, jsonify, render_template
import subprocess
import threading

app = Flask(__name__)
base_path = os.path.dirname(os.path.abspath(__file__))
stream_key_file = os.path.join(base_path, "stream_key.txt")
stream_process = None

def start_stream(stream_key):
    global stream_process
    # Stop the existing stream process, if there is one
    stop_stream()
    # Start the new stream process with the given stream key
    command = "raspivid -o - -t 0 -n -w 1080 -h 720 -fps 25 -b 1000000 | ffmpeg -re -ar 44100 -ac 2 -acodec pcm_s16le -f s16le -ac 2 -i /dev/zero -f h264 -i - -vcodec copy -acodec aac -ab 128k -g 50 -strict experimental -f flv rtmp://a.rtmp.youtube.com/live2/" + stream_key
    stream_process = subprocess.Popen(command, shell=True)
    print("Stream started successfully.")

def stop_stream():
    global stream_process
    if stream_process:
        # Stop the existing stream process
        stream_process.kill()
        stream_process = None
        print("Stream stopped successfully.")

def monitor_stream():
    while True:
        # Check if the stream process is still running
        if stream_process and stream_process.poll() is not None:
            print("Stream process exited with status code %d" % stream_process.returncode)
            # Restart the stream process with the same stream key
            with open(stream_key_file, "r") as fp:
                stream_key = fp.read().strip()
            start_stream(stream_key)
        time.sleep(15)

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/start_stream', methods=['POST'])
def start():
    stream_key = request.form.get('stream_key')
    if not stream_key:
        with open(stream_key_file, "r") as fp:
            stream_key = fp.read().strip()
        if not stream_key:
            return jsonify({'error': 'Stream key not provided and could not be read from file.'})
    else:
        with open(stream_key_file, "w") as fp:
            fp.write(stream_key)
    start_stream(stream_key)
    return jsonify({'message': 'Stream started successfully.'})

if __name__ == '__main__':
    # Check if a valid stream key is present in the file
    try:
        with open(stream_key_file, "r") as fp:
            stream_key = fp.read().strip()
    except FileNotFoundError:
        with open(stream_key_file, "w") as fp:
            pass
        stream_key = ""
    if stream_key:
        # Start the stream automatically
        start_stream(stream_key)
    # Start the monitoring thread
    monitor_thread = threading.Thread(target=monitor_stream)
    monitor_thread.daemon = True
    monitor_thread.start()
    # Run the Flask app
    app.run(host='0.0.0.0', port=8080)