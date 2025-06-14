from fastapi import FastAPI, Request            # для работы с HTTP запросами
from fastapi.responses import HTMLResponse      # для возврата HTML страниц и работы Jinja2
from fastapi.templating import Jinja2Templates  # шаблонизатор Jinja2 для рендеринга HTML с переменными
from pydantic import BaseModel                  # для валидации входных данных POST запросов

app = FastAPI()  # Создаем экземпляр FastAPI — наше приложение

templates = Jinja2Templates(directory="templates")  # Указываем папку с HTML-шаблонами

latest_message = {"text": "Жду данных..."}  # Переменная для хранения последнего сообщения, отображаемого на сайте


class Message(BaseModel):  # Класс модели для валидации данных, приходящих в POST /send
    text: str              # Поле text — текст сообщения


@app.get("/", response_class=HTMLResponse)  # Роут для главной страницы, возвращает HTML
async def index(request: Request):          # Асинхронная функция-обработчик GET "/"
    return templates.TemplateResponse("index.html", {"request": request})
    # Возвращаем с рендерингом шаблон index.html, передаем объект request (обязателен для Jinja2)
    # (Иначе не будет главной страницы, пользователь не увидит сайт)


@app.post("/send")               # Роут для получения сообщений по POST запросу
async def send(msg: Message):    # Асинхронный обработчик POST "/send", принимает объект msg класса Message
    global latest_message        # Объявляем, что будем менять глобальную переменную latest_message
    latest_message = msg.dict()  # Обновляем последнее сообщение новыми данными из запроса
    return {"status": "ok"}      # Возвращаем JSON с результатом успешной операции
    # (Иначе не сможем обновлять сообщение, нет API для отправки данных)


@app.get("/stream")        # Роут для отдачи текущего сообщения в JSON
async def stream():        # Асинхронный обработчик GET "/stream"
    return latest_message  # Возвращаем последнее сообщение (FastAPI сам сериализует в JSON)
    # (Иначе нет API для получения данных на клиент для динамического обновления)