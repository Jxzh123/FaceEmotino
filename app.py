# app.py
from flask import Flask, request, render_template, redirect, url_for
import cv2
from fer import FER # 导入 FER
import os
from werkzeug.utils import secure_filename # 用于生成安全的文件名
import traceback # 用于打印详细的错误堆栈

# --- 从这里开始是您文件已有的内容，保持不变 ---
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

try:
    print("正在初始化 FER(mtcnn=True)...")
    emotion_detector = FER(mtcnn=True) 
    print("FER(mtcnn=True) 初始化成功。")
except Exception as e:
    print(f"初始化 FER 时出错: {e}")
    print("请确保已正确安装 FER 及其所有依赖 (如 TensorFlow, facenet-pytorch, Keras等)。") # 更新了依赖提示
    traceback.print_exc()
    emotion_detector = None 

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', error="没有选择文件。")
        
        file = request.files['file']
        
        if file.filename == '':
            return render_template('index.html', error="文件名为空。")
        
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename) 
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
            
            try:
                file.save(filepath)
            except Exception as e:
                print(f"保存文件 {original_filename} 失败: {e}")
                return render_template('index.html', error=f"保存文件失败: {str(e)}")

            try:
                print(f"开始处理图片: {filepath}")
                img = cv2.imread(filepath)
                if img is None:
                    print(f"无法加载图片: {filepath}")
                    if os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                        except Exception as remove_err:
                             print(f"删除无效图片 {filepath} 失败: {remove_err}")
                    return render_template('index.html', error="无法加载图片，请确保是有效的图片格式。")

                if emotion_detector is None:
                    print("错误: emotion_detector 未能初始化。")
                    return render_template('index.html', error="情绪识别器未能初始化，请检查服务器日志。")

                print(f"调用 emotion_detector.detect_emotions() 处理图片: {original_filename}")
                detected_faces_data = emotion_detector.detect_emotions(img)
                
                results = []
                img_copy = img.copy() 
                processed_filename = None 

                if not detected_faces_data:
                     message = "未能在此图片中检测到人脸 (使用MTCNN)。"
                     print(message + f" 文件: {original_filename}")
                     return render_template('results.html', 
                                       original_image=original_filename, 
                                       processed_image=None, 
                                       results=results, 
                                       message=message)
                else:
                    print(f"FER(mtcnn=True) 在 {original_filename} 中检测到 {len(detected_faces_data)} 张人脸。")
                    for i, face_data in enumerate(detected_faces_data):
                        box = face_data['box']
                        emotions = face_data['emotions']
                        
                        print(f"  人脸 {i+1} @ {box}: 情绪原始数据: {emotions}")

                        dominant_emotion = "处理中..."
                        if emotions and isinstance(emotions, dict):
                            valid_emotions = {k: v for k, v in emotions.items() if isinstance(v, (int, float))}
                            if not valid_emotions: # 如果所有情绪值都是0或者无效
                                dominant_emotion = "情绪数据无效"
                            else:
                                dominant_emotion = max(valid_emotions, key=valid_emotions.get)
                        elif emotions is None:
                            dominant_emotion = "未返回情绪数据"
                        else:
                            dominant_emotion = "无法识别情绪"
                        
                        print(f"  人脸 {i+1}: 主要情绪: {dominant_emotion}")
                        results.append({'emotion': dominant_emotion, 'box': box})
                        
                        (x, y, w, h) = box
                        cv2.rectangle(img_copy, (x, y), (x+w, y+h), (0, 0, 255), 2) 
                        cv2.putText(img_copy, dominant_emotion, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                    
                    processed_filename = 'processed_' + original_filename
                    processed_image_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
                    cv2.imwrite(processed_image_path, img_copy)
                    print(f"已保存处理后的图片: {processed_image_path}")

                return render_template('results.html', 
                                       original_image=original_filename, 
                                       processed_image=processed_filename,
                                       results=results)
            
            except Exception as e:
                print(f"处理图片 {original_filename} 时发生严重错误: {e}")
                traceback.print_exc()
                
                if os.path.exists(filepath): 
                    try:
                        os.remove(filepath)
                        print(f"已删除原始文件: {filepath}")
                    except Exception as remove_err:
                        print(f"删除原始文件 {filepath} 失败: {remove_err}")
                
                temp_processed_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + original_filename)
                if os.path.exists(temp_processed_path): 
                     try:
                        os.remove(temp_processed_path)
                        print(f"已删除处理中的文件: {temp_processed_path}")
                     except Exception as remove_err:
                        print(f"删除处理中文件 {temp_processed_path} 失败: {remove_err}")
                
                return render_template('index.html', error=f"处理图片时发生内部错误。详情请查看服务器日志。")
        else:
            return render_template('index.html', error="文件类型不支持，请上传 'png', 'jpg', 'jpeg', 'gif' 格式的图片。")
            
    return render_template('index.html')

# --- 从这里开始是修改的部分 ---
if __name__ == '__main__':
    # 导入 waitress
    from waitress import serve

    if emotion_detector:
        print("FER 情绪检测器 (mtcnn=True) 已成功加载。")
        # 预热模型的代码可以放在这里 (如果需要)
        # import numpy as np
        # print("尝试预热 FER(mtcnn=True) 模型...")
        # try:
        #    dummy_img = np.zeros((200,200,3), dtype=np.uint8)
        #    _ = emotion_detector.detect_emotions(dummy_img)
        #    print("FER(mtcnn=True) 模型已预热。")
        # except Exception as e:
        #    print(f"预热 FER(mtcnn=True) 模型时出错: {e}")
        #    traceback.print_exc()
    else:
        print("警告: FER 情绪检测器未能初始化。应用的情绪识别功能将不可用。")
    
    # 定义主机和端口
    # 对于打包后的 .exe，通常不需要 debug=True
    # host='0.0.0.0' 使应用可以从局域网内其他机器访问
    # port=5000 是常用的开发端口
    host = '0.0.0.0' 
    port = 5000      

    print(f"使用 Waitress 启动服务器，监听地址 http://{host}:{port}")
    print("如果从本机访问，请使用 http://127.0.0.1:5000 或 http://localhost:5000")
    print("按 Ctrl+C 关闭服务器。")
    
    # 使用 waitress.serve() 来运行 Flask 应用
    # threads 参数可以根据您的 CPU核心数调整，例如 4 或 8
    # 对于打包的 .exe，移除 debug=True，因为 waitress 不直接使用它，
    # Flask 的 debug 模式也不应在生产型服务器中开启。
    serve(app, host=host, port=port, threads=8)