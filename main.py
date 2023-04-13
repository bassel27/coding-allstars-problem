from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
from tester import Tester

tester = Tester()
app = FastAPI()
templates = Jinja2Templates(directory="templates")


async def test_selenium(url):
    tester.run_tests(url)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/test_urls", response_class=HTMLResponse)
async def test_urls(request: Request):
    form_data = await request.form()
    urls = form_data["urls"].split("\n")
    results = []
    for url in urls:
        if url.strip():
            await test_selenium(url.strip())
            results.append(tester.result.__str__())
    return templates.TemplateResponse(
        "results.html", {"request": request, "results": results}
    )
