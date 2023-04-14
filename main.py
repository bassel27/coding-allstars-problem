from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.templating import Jinja2Templates
from tester import Tester
import os

tester = Tester()
app = FastAPI()
templates = Jinja2Templates(directory="templates")
SECRET = os.getenv("SECRET")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/test_urls")
async def test_urls(
    request: Request,
):  # receives the request object as an argument from the FastAPI framework.
    form_data = (
        await request.form()
    )  # returns a dictionary containing the form data submitted with the request
    urls = form_data["urls"].split("\n")

    async def event_generator():
        for url in urls:
            if url.strip():
                tester.run_tests(url)
                result = tester.result.__str__()
                result = result.replace(": ", "")
                yield result  # dictionary containing a single key-value pair
                # When the yield statement is executed, the generator function is paused and the event object is sent back to the caller as part of an HTTP response.

    return EventSourceResponse(event_generator())
