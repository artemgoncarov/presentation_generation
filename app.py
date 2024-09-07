from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import json
from io import BytesIO
from iteract import interact
import os
from generate import generate_presentation_maket, generate_presentation_yourself
from graphics import hist, plot, pie
import pandas as pd
import time
import translators as ts
from api import Text2ImageAPI
import base64

api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '8742BF0A3C13A23CF6483A9A8E719A2B', '7030159A30D5170FDA7F2DBEACBAC498')
model_id = api.get_model()
app = Flask(__name__)

UPLOAD_FOLDER = 'static'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/api/genImg', methods=['POST'])
def genImg():
    data = request.json
    name = data.get('name')

    t = time.time()
    prompt = ts.translate_text(str(name), translator='google', to_language='en')

    uuid = api.generate(prompt, model_id)
    images = api.check_generation(uuid)
    with open(f"static/{t}.jpg", "wb") as file:
        file.write(base64.b64decode(images[0]))

    return f"static/{t}.jpg"

@app.route('/upload_template', methods=['POST'])
def upload_template():
    if 'file' not in request.files:
        return jsonify({'error': 'Нет файла для загрузки'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    # Сохранение файла
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    
    return jsonify({'message': 'Файл успешно загружен', 'file_path': file_path}), 200

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/graphics')
def graphics():
    return render_template('graphics.html')

@app.route('/api/getGraphic', methods=['POST'])
def get_graphic():
    # Проверяем, был ли загружен файл
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']

    # Проверяем, выбран ли файл
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Получаем тип графика и названия колонок из запроса
    graphic_type = request.form.get('type')
    columns = request.form.get('columns').split(',')

    # Сохраняем файл
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Генерируем уникальное имя для изображения с временной меткой
    output_image_filename = f'generated_graphic.png'
    output_image_path = os.path.join('static', 'images', output_image_filename)

    if '.csv' in str(file.filename):
        data = pd.read_csv(file_path)
    elif '.xlsx' in str(file.filename):
        data = pd.read_excel(file_path)
    else:
        return 0
    

    if graphic_type == 'pie':
        pie(data[columns[0]], output_path=output_image_path)  # Сохраняем график в файл
    elif graphic_type == 'hist':
        hist(data[columns[0]], output_path=output_image_path)
    else:
        if len(columns) == 1:
            plot(data[columns[0]], output_path=output_image_path)
        else:
            plot(data[columns[0]], data[columns[1]], output_path=output_image_path)

    # Возвращаем путь к сгенерированному изображению
    return jsonify({
        'message': 'File uploaded successfully',
        'imageUrl': url_for('static', filename=f'images/{output_image_filename}')
    }), 200



@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        return jsonify({"message": "Image uploaded successfully", "file_path": filepath}), 200
    else:
        return jsonify({"error": "Invalid file type"}), 400


def allowed_file(filename):
    # Разрешаем только файлы изображений
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg', 'gif']

@app.route('/save_presentation', methods=['POST'])
def save_presentation():
    data = request.json
    name = data.get('name')
    data['slides'] = data['slides'][1:]

    # Путь для сохранения JSON
    json_path = os.path.join('static', f'{secure_filename(name)}.json')

    # Сохраняем JSON-данные в файл
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    name = data['name']
    plan = data['plan']
    slides = data['slides']

    print(slides)
    try:
        design = data['design']
        if design == "1":
            generate_presentation_maket(slides, plan, design, name, 'static/presentations/123.pptx', maket='1.pptx')
        elif design == "2":
            generate_presentation_maket(slides, plan, design, name, 'static/presentations/123.pptx', maket='2.pptx')
    except:
        try:
            font_name = data['font']
            font_color = data['font_color']
            bg_color = data['color']
            generate_presentation_yourself(slides, plan, name, 'static/presentations/123.pptx', font_name, 14, bg_color, font_color)
        except KeyError as err:
            print(err)
            path = 'static/' + data['file_path']
            print(path)
            generate_presentation_maket(slides, plan, "0", name, 'static/presentations/123.pptx', maket=path)


    return redirect('/')

@app.route('/api/download', methods=['GET'])
def download_file():
    name = "123.pptx"  # Название презентации
    if not name:
        return jsonify({"error": "Missing 'name' parameter"}), 400

    # Путь к файлу
    filepath = os.path.join('static', 'presentations', secure_filename(name))

    # Проверяем, существует ли файл
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404

# Эндпоинт для главной страницы
@app.route('/')
def index():
    return render_template('index.html')

# Эндпоинт для получения плана презентации
@app.route('/api/getDescription', methods=['GET'])
def get_description():
    name = request.args.get('name')  # Получаем параметр name из URL
    n_slides = request.args.get('n_slides')
    description = request.args.get('description')


    if n_slides:
        res = interact(messages=[{"role": "system", "content": f"Ты - помощник для генерации презентаций на основе текста. Пользователь будет вводить тебе название презентации, ее описание(что он хочет в ней видеть), а ты должен выдавать ее план, соблюдая описание(пожелание) пользователя. В плане презентации обязательно должно быть: {description}, это очень важно. Должно быть {n_slides} слайда. Шаблон для ответа, которого ты всегда должен строго придерживаться, без лишних символов и слов, просто подставляй названия слайдов в форму: - Название слайда 1(без подробного описания)\n- Название слайда 2(без подробного описания)\n- ...\n- Название слайда n(без подробного описания)"}, {"role": "user", "content": name}])
    else:
        res = interact(messages=[{"role": "system", "content": f"Ты - помощник для генерации презентаций на основе текста. Пользователь будет вводить тебе название презентации, ее описание(что он хочет в ней видеть), а ты должен выдавать ее план, соблюдая описание(пожелание) пользователя. В плане презентации обязательно должно быть: {description}, это очень важно. Должно быть 4 слайда. Шаблон для ответа, которого ты всегда должен строго придерживаться, без лишних символов и слов, просто подставляй названия слайдов в форму: - Название слайда 1(без подробного описания)\n- Название слайда 2(без подробного описания)\n- ...\n- Название слайда n(без подробного описания)"}, {"role": "user", "content": name}])

    return jsonify(list(map(lambda x: x[2:], res.split('\n'))))


# Эндпоинт для получения текста слайда
@app.route('/api/getSlideText', methods=['POST'])
def get_slide_text():
    data = request.json
    text = data.get('text')
    name = data.get('name')
    n = data.get('n')
    template = data.get('template')
    description = data.get('description')

    print(template)

    if int(n) == 3 and template == "2":
        res = interact(messages=[{"role": "system", "content": "Ты - помощник для генерации презентаций на основе текста. Пользователь будет вводить тебе название слайда, описание и тему презентации, а ты ему текст для этого слайда от 5 до 6 предложений на твое усмотрение и до 300 символов. В своем ответе ты должен выдать только содержимое слайда, без лишних символов, отступов и слов. Раздели текст на 6 частей, где разделительным символом будет [r], не [р], а именно [r]. И в самое начало текста ставить этот тег не нужно. Всего должно быть 5 таких тегов. Только это слово, никакое другое. Этот символ должен делить текст на 6 частей"}, {"role": "user", "content": f"Название презентации: {name}. Описание презентации: {description}. Название слайда: {text}"}])
    elif int(n) == 1 and template == "1" or int(n) == 3 and template == "1":
        res = interact(messages=[{"role": "system", "content": "Ты - помощник для генерации презентаций на основе текста. Пользователь будет вводить тебе название слайда, описание и тему презентации, а ты ему текст для этого слайда от 5 до 6 предложений на твое усмотрение и до 300 символов. В своем ответе ты должен выдать только содержимое слайда, без лишних символов, отступов и слов. Раздели текст на 4 части, где разделительным символом будет [r], не [р], а именно [r]. И в самое начало текста ставить этот тег не нужно. Всего должно быть 3 таких тега. Только это слово, никакое другое. Этот символ должен делить текст на 4 части"}, {"role": "user", "content": f"Название презентации: {name}. Описание презентации: {description}. Название слайда: {text}"}])
    elif int(n) == 2 and template == "1":
        res = interact(messages=[{"role": "system", "content": "Ты - помощник для генерации презентаций на основе текста. Пользователь будет вводить тебе название слайда, описание и тему презентации, а ты ему текст для этого слайда от 3 до 4 предложений на твое усмотрение и до 300 символов. В своем ответе ты должен выдать только содержимое слайда, без лишних символов, отступов и слов. Раздели текст на 3 части, где разделительным символом будет [r], не [р], а именно [r]. И в самое начало текста ставить этот тег не нужно. Всего должно быть 2 таких тега. Только это слово, никакое другое. Этот символ должен делить текст на 3 части"}, {"role": "user", "content": f"Название презентации: {name}. Описание презентации: {description}. Название слайда: {text}"}])
    else:
        res = interact(messages=[{"role": "system", "content": "Ты - помощник для генерации презентаций на основе текста. Пользователь будет вводить тебе название слайда, описание и тему презентации, а ты ему текст для этого слайда от 5 до 6 предложений на твое усмотрение и до 300 символов. В своем ответе ты должен выдать только содержимое слайда, без лишних символов, отступов и слов."}, {"role": "user", "content": f"Название презентации: {name}. Описание презентации: {description}. Название слайда: {text}"}])

    # Возвращаем модифицированный текст слайда
    return jsonify(res)

# Эндпоинт для генерации файла
@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    name = data['name']
    design = data['design']
    slides = data['data']
    
    # Генерация файла (например, текстовый файл с презентацией)
    presentation = f"Презентация: {name}\nДизайн: {design}\n\n"
    for slide_num, slide_text in slides.items():
        presentation += f"{slide_num}: {slide_text}\n"
    
    # Отправка файла
    file_data = BytesIO(presentation.encode('utf-8'))
    file_data.seek(0)
    return send_file(file_data, as_attachment=True, download_name=f'{name}.txt')


if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0", debug=False)
