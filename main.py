import uvicorn                                          # ASGI сервер (Asynchronous Server Gateway Interface)
import os
import logging
from fastapi import HTTPException, FastAPI, Request     # для работы с HTTP запросами
from fastapi.responses import HTMLResponse              # для возврата HTML страниц и работы Jinja2
from fastapi.templating import Jinja2Templates          # шаблонизатор Jinja2 для рендеринга HTML с переменными
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel                          # для валидации входных данных POST запросов

from gigachat import GigaChat   # официальный СБЕР SDK

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()     # Создаем экземпляр FastAPI — наше приложение

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")  # Указываем папку с HTML-шаблонами

latest_message = {"text": "Жду данных...", "answer": ""}  # Переменная для хранения последнего сообщения, отображаемого на сайте


class Message(BaseModel):  # Класс модели для валидации данных, приходящих в POST /send
    text: str              # Поле text — текст сообщения


@app.get("/", response_class=HTMLResponse)  # Роут для главной страницы, возвращает HTML
async def index(request: Request):          # Асинхронная функция-обработчик GET "/"
    return templates.TemplateResponse("index.html", {"request": request, "latest_message": latest_message})
    # Возвращаем с рендерингом шаблон index.html, передаем объект request (обязателен для Jinja2)
    # (Иначе не будет главной страницы, пользователь не увидит сайт)


@app.post("/send")                                 # Роут для получения сообщений по POST запросу
async def send(request: Request, msg: Message):    # Асинхронный обработчик POST "/send", принимает объект msg класса Message

    # header_password = request.headers.get("x-api-key")
    # expected_password = os.environ.get("SP_PASSWORD")
    #
    # if not expected_password:
    #     raise HTTPException(status_code=500, detail="Server config error: SP_PASSWORD is not set.")
    #
    # if header_password != expected_password:
    #     raise HTTPException(status_code=403, detail="Forbidden: invalid API key")


    global latest_message                           # Объявляем, что будем менять глобальную переменную latest_message
    latest_message["text"] = msg.text
    latest_message["answer"] = "Обрабатывается..."


    answer_text = ""  # дефолтно пустой ответ
    try:
        auth_key = os.environ.get("GIGACHAT_AUTH_KEY")  # сюда кладём ключ авторизации (токен)
        if not auth_key:
            raise RuntimeError("GIGACHAT_AUTH_KEY is not set")

        # giga = GigaChat(credentials=auth_key, model="GigaChat", verify_ssl_certs=False)  # модель 1
        giga = GigaChat(credentials=auth_key, model="GigaChat-Pro", verify_ssl_certs=False)  # модель 2
        # giga = GigaChat(credentials=auth_key, model="GigaChat-Max", verify_ssl_certs=False)  # модель 3

        answer = giga.chat(msg.text)
        answer_text = answer.choices[0].message.content
        latest_message["answer"] = answer_text


    except Exception as e:
        logger.error(f"Ошибка при запросе к GigaChat: {e}", exc_info=True)
        error_msg = f"Ошибка при запросе GigaChat: {str(e)}"
        latest_message["answer"] = error_msg
        answer_text = error_msg


    # Сохраняем в файл
    with open("history.log", "a", encoding="utf-8") as f:
        f.write(f"Вопрос: {msg.text.strip()}\n")
        f.write(f"Ответ: {answer_text.strip()}\n")
        f.write("-" * 40 + "\n")


    return {
        "status": "ok",
        "question": latest_message["text"],
        "answer": latest_message["answer"]
    }

@app.get("/stream")        # Роут для отдачи текущего сообщения в JSON
async def stream():        # Асинхронный обработчик GET "/stream"
    return latest_message  # Возвращаем последнее сообщение (FastAPI сам сериализует в JSON)
    # (Иначе нет API для получения данных на клиент для динамического обновления)

# можно запускать main.py напрямую, необязательно через uvicorn (python main.py)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, log_level="info", reload=True)