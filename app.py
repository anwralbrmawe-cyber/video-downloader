import os
import re
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

# مجلد التحميلات المؤقتة
UPLOAD_FOLDER = 'downloads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch-info', methods=['POST'])
def fetch_info():
    """جلب معلومات الفيديو (العنوان، المعاينة) قبل التحميل"""
    data = request.get_json()
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'الرجاء إدخال رابط صحيح!'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            return jsonify({
                'title': info.get('title', 'فيديو بدون عنوان'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration_string', ''),
                'uploader': info.get('uploader', 'غير معروف'),
                'url': video_url
            })
    except Exception as e:
        return jsonify({'error': f'تعذر جلب بيانات الرابط: {str(e)}'}), 500

@app.route('/download-media', methods=['POST'])
def download_media():
    """تحميل الفيديو بناءً على الخيار المحدد دون معالجة معقدة لتجنب الأخطاء"""
    data = request.get_json()
    video_url = data.get('url')
    quality_option = data.get('quality', 'best')

    if not video_url:
        return jsonify({'error': 'رابط غير صالح!'}), 400

    # تحديد صيغة التحميل المباشرة
    if quality_option == 'mp3':
        format_opt = 'bestaudio/best'
    elif quality_option == '720p':
        format_opt = 'best[height<=720]/best'
    else:
        format_opt = 'best'

    output_template = os.path.join(UPLOAD_FOLDER, '%(title).100s.%(ext)s')

    ydl_opts = {
        'format': format_opt,
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)

            filename_only = os.path.basename(filename)
            return jsonify({'download_link': f'/get-file/{filename_only}'})

    except Exception as e:
        return jsonify({'error': f'فشل التحميل: {str(e)}'}), 500

@app.route('/get-file/<filename>')
def get_file(filename):
    """إرسال الملف النهائي للمستخدم ليتم تنزيله على جهازه"""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "الملف غير موجود!", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
