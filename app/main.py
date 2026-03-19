from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import init_db
from app.api import accounts, journal_entries, reports
from app.i18n import TRANSLATIONS, get_translations
from config import settings

LANG_COOKIE = "lang"
DEFAULT_LANG = "vi"


class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        response: Response = await call_next(request)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Double-Entry Accounting System with PostgreSQL ORM",
    version="1.0.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory="app/templates")
templates.env.globals['t'] = lambda key, lang="en", **kwargs: get_translations(lang).get(key, key)
templates.env.globals['translations'] = TRANSLATIONS

app.add_middleware(LanguageMiddleware)

app.include_router(accounts.router)
app.include_router(journal_entries.router)
app.include_router(reports.router)


def get_lang(request: Request) -> str:
    return request.cookies.get(LANG_COOKIE, DEFAULT_LANG)


def render_template(request: Request, template_name: str, **kwargs):
    lang = get_lang(request)
    kwargs.update({
        "request": request,
        "config": settings,
        "lang": lang,
        "trans": TRANSLATIONS[lang],
        "all_translations": TRANSLATIONS,
    })
    return templates.TemplateResponse(template_name, kwargs)


@app.get("/set-lang/{lang}")
async def set_language(request: Request, lang: str):
    if lang not in TRANSLATIONS:
        lang = DEFAULT_LANG
    
    response = RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)
    response.set_cookie(key=LANG_COOKIE, value=lang, max_age=60*60*24*365, httponly=True)
    return response


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return render_template(request, "dashboard.html", today=date.today().isoformat())


@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    return render_template(request, "accounts.html", today=date.today().isoformat())


@app.get("/journal", response_class=HTMLResponse)
async def journal_page(request: Request):
    return render_template(request, "journal.html")


@app.get("/journal/new", response_class=HTMLResponse)
async def new_journal_page(request: Request):
    return render_template(
        request, "journal_form.html",
        today=date.today().isoformat(),
        entry_id=None,
        entry_date=date.today().isoformat()
    )


@app.get("/journal/{entry_id}/edit", response_class=HTMLResponse)
async def edit_journal_page(request: Request, entry_id: str):
    return render_template(
        request, "journal_form.html",
        today=date.today().isoformat(),
        entry_id=f"'{entry_id}'",
        entry_date=None
    )


@app.get("/journal/{entry_id}", response_class=HTMLResponse)
async def journal_detail_page(request: Request, entry_id: str):
    return RedirectResponse(url="/journal")


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    return render_template(request, "reports.html", today=date.today().isoformat())


@app.get("/reports/account/{account_id}", response_class=HTMLResponse)
async def account_ledger_page(request: Request, account_id: str):
    return RedirectResponse(url="/reports")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
