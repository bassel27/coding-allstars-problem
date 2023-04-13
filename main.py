from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.templating import Jinja2Templates
import asyncio
from tester import Tester

tester = Tester()
app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/test_urls")
async def test_urls(request: Request):
    form_data = await request.form()
    urls = form_data["urls"].split("\n")

    async def event_generator():
        for url in urls:
            if url.strip():
                tester.run_tests(url)
                result = tester.result.__str__()
                yield {"data": result}

    return EventSourceResponse(event_generator())
