import os
import pandas as pd
import yt_dlp
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import openpyxl

app = Flask(__name__)
app.secret_key = 'downloadmp3'  # Required for flashing messages

# Path where your downloaded mp3s are stored
DOWNLOAD_FOLDER = './downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def download_video_as_mp3(youtube_url, output_path=DOWNLOAD_FOLDER):
    # Ensure the output directory exists
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Define options for yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
    }

    try:
        # Download and convert the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as e:
        print(f"An error occurred while downloading {youtube_url}: {e}")
        return None

    # Find the downloaded mp3 file
    for file in os.listdir(output_path):
        if file.endswith(".mp3"):
            return os.path.join(output_path, file)
    return None


@app.route('/', methods=['POST', 'GET'])
def single_track():
    file_path = None
    if request.method == 'POST':
        youtube_url = request.form.get('videoLink')  # Get the YouTube URL from the form
        if youtube_url:
            try:
                # Call the function to download the video as mp3
                file_path = download_video_as_mp3(youtube_url)
                if file_path:
                    flash("MP3 Downloaded Successfully!", "success")  # Flash success message
                else:
                    flash("Error: MP3 file not found after download.", "danger")  # Handle file not found
            except Exception as e:
                flash(f"Error occurred: {str(e)}", "danger")  # Flash error message
        else:
            flash("Error: URL is missing!", "danger")  # Flash error message if URL is missing
        return render_template('index.html', file_path=file_path)  # Pass file path to template

    return render_template('index.html', file_path=file_path)


@app.route('/bulkurl', methods=['POST', 'GET'])
def multiple_track():
    file = None
    if request.method == 'POST':
        # Handle file upload (Excel)
        if 'excelFile' not in request.files:
            flash("Error: No file part", "danger")
            return redirect(request.url)

        file = request.files['excelFile']

        if file.filename == '':
            flash('Error: No selected file', 'danger')
            return redirect(request.url)

        # Process the uploaded Excel file
        if file and file.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(file)
            except Exception as e:
                flash(f"Failed to load the Excel file: {e}", "danger")
                return redirect(request.url)

            # Assume the column containing the URLs is named 'LINKS'
            if 'LINKS' not in df.columns:
                flash("Error: 'LINKS' column not found in the Excel file.", "danger")
                return redirect(request.url)

            urls = df['LINKS'].dropna().tolist()

            # Check if there are URLs to process
            if not urls:
                flash("Error: No URLs found in the 'LINKS' column.", "danger")
                return redirect(request.url)

            # Loop through the list of URLs and download each as MP3
            downloaded_files = []
            for url in urls:
                mp3_file = download_video_as_mp3(url)
                if mp3_file:
                    downloaded_files.append(mp3_file)

            if downloaded_files:
                flash(f"Successfully downloaded {len(downloaded_files)} MP3 files!", "success")
            else:
                flash("Error: No files were downloaded.", "danger")

            return render_template('index.html', file_path=None)  # Update the template
        else:
            flash("Error: Please upload a valid .xlsx file!", "danger")
            return redirect(request.url)

    return render_template('index.html', file_path=None)


# Route to open the file
@app.route('/open/<path:filename>', methods=['GET'])
def open_file(filename):
    return send_file(filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
