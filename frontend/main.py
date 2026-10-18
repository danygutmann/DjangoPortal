import json
import os
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from nicegui import app, ui

API = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/") + "/api/v1"


class APIError(Exception):
    def __init__(self, message, status_code=0):
        self.status_code = status_code
        super().__init__(message)


def api_request(path, *, token=None, method="GET", payload=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + str(token)
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode()
    request = Request(f"{API}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read()) if response.status != 204 else None
    except HTTPError as exc:
        message = "The request was denied." if exc.code in (401, 403) else "The backend could not complete the request."
        try:
            detail = json.loads(exc.read()).get("detail")
            if exc.code in (400, 401, 403) and detail:
                message = detail
        except (ValueError, AttributeError):
            pass
        raise APIError(message, exc.code) from exc
    except (URLError, TimeoutError) as exc:
        raise APIError("The backend is unavailable.") from exc


def logout():
    token = app.storage.user.get("token")
    if token:
        try:
            api_request("/auth/logout/", token=token, method="POST")
        except APIError:
            pass
    app.storage.user.pop("token", None)
    ui.navigate.to("/login")


def apply_preferences():
    theme = app.storage.user.get("theme", "auto")
    dark = ui.dark_mode(value={"light": False, "dark": True, "auto": None}.get(theme))
    density = "p-3" if app.storage.user.get("density") == "compact" else "p-6"
    return density


def render_header(token):
    with ui.header().classes("items-center justify-between bg-slate-900 text-white"):
        ui.label("DjangoPortal").classes("text-lg font-semibold")
        with ui.row().classes("items-center"):
            try:
                modules = api_request("/modules/", token=token)
                for module in modules:
                    for item in module["manifest"].get("navigation", []):
                        ui.link(item["label"], item["path"]).classes("text-white")
            except (APIError, KeyError, TypeError):
                pass
            with ui.button(icon="account_circle").props("flat color=white"):
                with ui.menu():
                    ui.menu_item("Profile", on_click=lambda: ui.navigate.to("/profile"))
                    ui.menu_item("Permissions", on_click=lambda: ui.navigate.to("/permissions"))
                    ui.menu_item("Settings", on_click=lambda: ui.navigate.to("/settings"))
                    ui.separator()
                    ui.menu_item("Sign out", on_click=logout)


@ui.page("/login")
def login_page():
    if app.storage.user.get("token"):
        ui.navigate.to("/tasks")
        return
    with ui.column().classes("absolute-center w-80"):
        ui.label("DjangoPortal").classes("text-2xl font-bold")
        username = ui.input("Username").props("autocomplete=username").classes("w-full")
        password = ui.input("Password").props("type=password autocomplete=current-password").classes("w-full")
        message = ui.label().classes("text-red-700")

        def submit():
            try:
                result = api_request("/auth/login/", method="POST",
                                     payload={"username": username.value, "password": password.value})
                app.storage.user["token"] = result["token"]
                ui.navigate.to("/tasks")
            except APIError as exc:
                message.set_text(str(exc))

        ui.button("Sign in", on_click=submit).classes("w-full")
        password.on("keydown.enter", submit)


@ui.page("/")
def index_page():
    ui.navigate.to("/tasks" if app.storage.user.get("token") else "/login")


@ui.page("/tasks")
def tasks_page():
    token = app.storage.user.get("token")
    if not token:
        ui.navigate.to("/login")
        return
    density = apply_preferences()
    render_header(token)
    with ui.column().classes(f"mx-auto w-full max-w-5xl {density}"):
        ui.label("Tasks").classes("text-2xl font-semibold")
        error = ui.label().classes("text-red-700")
        create_form = ui.row().classes("w-full")
        with create_form:
            title = ui.input("Title").classes("grow")
            description = ui.input("Description").classes("grow")
            priority = ui.select(["low", "normal", "high", "critical"], value="normal", label="Priority")
            due_date = ui.input("Due date (YYYY-MM-DD)")
            create = ui.button("Create")
        query = ui.input("Search tasks").classes("w-full")
        status_filter = ui.select(
            ["all", "open", "in_progress", "done"], value="all", label="Status"
        )
        priority_filter = ui.select(
            ["all", "low", "normal", "high", "critical"], value="all", label="Priority"
        )
        try:
            permission_result = api_request("/me/permissions/", token=token)
            permissions = set(permission_result["permissions"])
        except APIError as exc:
            error.set_text(str(exc))
            permissions = set()
        is_admin = "task_manager.administer_task_manager" in permissions
        if "task_manager.create_task" not in permissions and not is_admin:
            create_form.set_visibility(False)
        scope_filter = None
        if "task_manager.view_all_tasks" in permissions or is_admin:
            scope_filter = ui.select(["mine", "all"], value="mine", label="Scope")
        table = ui.column().classes("w-full")

        def refresh():
            try:
                filters = {"scope": scope_filter.value if scope_filter else "mine"}
                if query.value:
                    filters["search"] = query.value
                if status_filter.value != "all":
                    filters["status"] = status_filter.value
                if priority_filter.value != "all":
                    filters["priority"] = priority_filter.value
                result = api_request("/tasks/?" + urlencode(filters), token=token)
                rows = result.get("results", result) if isinstance(result, dict) else result
                table.clear()
                with table:
                    for task in rows:
                        with ui.card().classes("w-full"):
                            ui.label(f"{task['title']} · {task['status']} · {task['priority']}").classes(
                                "font-semibold"
                            )
                            if task["description"]:
                                ui.label(task["description"])
                            ui.label(f"Assigned to: {task['assigned_to'] or 'Unassigned'}")
                            if task["due_date"]:
                                ui.label(f"Due: {task['due_date']}")
                            if "task_manager.edit_task" in permissions or is_admin:
                                with ui.row():
                                    new_status = ui.select(
                                        ["open", "in_progress", "done"], value=task["status"], label="Status"
                                    )
                                    new_priority = ui.select(
                                        ["low", "normal", "high", "critical"], value=task["priority"],
                                        label="Priority"
                                    )
                                    def save_task(task_id=task["id"], status_input=new_status,
                                                  priority_input=new_priority):
                                        try:
                                            api_request(f"/tasks/{task_id}/", token=token, method="PATCH",
                                                        payload={"status": status_input.value,
                                                                 "priority": priority_input.value})
                                            refresh()
                                        except APIError as exc:
                                            error.set_text(str(exc))
                                    ui.button("Save", on_click=save_task)
                            if "task_manager.delete_task" in permissions or is_admin:
                                def remove_task(task_id=task["id"]):
                                    try:
                                        api_request(f"/tasks/{task_id}/", token=token, method="DELETE")
                                        refresh()
                                    except APIError as exc:
                                        error.set_text(str(exc))
                                ui.button("Delete", on_click=remove_task, color="negative")
                            if "task_manager.view_task" in permissions or is_admin:
                                with ui.expansion("Comments"):
                                    try:
                                        comments = api_request(f"/tasks/{task['id']}/comments/", token=token)
                                        for comment in comments:
                                            ui.label(f"{comment['author']}: {comment['body']}")
                                    except APIError as exc:
                                        ui.label(str(exc)).classes("text-red-700")
                                    if "task_manager.comment_task" in permissions or is_admin:
                                        comment_input = ui.input("Add a comment").classes("w-full")
                                        def add_task_comment(task_id=task["id"], field=comment_input):
                                            try:
                                                api_request(f"/tasks/{task_id}/comments/", token=token, method="POST",
                                                            payload={"body": field.value})
                                                refresh()
                                            except APIError as exc:
                                                error.set_text(str(exc))
                                        ui.button("Comment", on_click=add_task_comment)
            except APIError as exc:
                error.set_text(str(exc))
                if exc.status_code == 401:
                    app.storage.user.pop("token", None)
                    ui.navigate.to("/login")

        if "task_manager.create_task" in permissions or is_admin:
            def create_task():
                try:
                    api_request("/tasks/", token=token, method="POST",
                                payload={"title": title.value, "description": description.value or "",
                                         "priority": priority.value, "due_date": due_date.value or None})
                    title.value = ""
                    error.set_text("")
                    refresh()
                except APIError as exc:
                    error.set_text(str(exc))

            create.on_click(create_task)
        query.on("update:model-value", lambda _: refresh())
        status_filter.on("update:model-value", lambda _: refresh())
        priority_filter.on("update:model-value", lambda _: refresh())
        if scope_filter:
            scope_filter.on("update:model-value", lambda _: refresh())
        refresh()


@ui.page("/profile")
def profile_page():
    token = app.storage.user.get("token")
    if not token:
        ui.navigate.to("/login")
        return
    apply_preferences()
    render_header(token)
    try:
        profile = api_request("/me/permissions/", token=token)
        ui.label("Profile").classes("text-2xl font-semibold")
        ui.label(f"Username: {profile['username']}")
    except APIError as exc:
        ui.label(str(exc)).classes("text-red-700")


@ui.page("/permissions")
def permissions_page():
    token = app.storage.user.get("token")
    if not token:
        ui.navigate.to("/login")
        return
    apply_preferences()
    render_header(token)
    ui.label("Effective permissions").classes("text-2xl font-semibold")
    try:
        permissions = api_request("/me/permissions/", token=token)
        ui.label(f"User: {permissions['username']}")
        for permission in permissions["permissions"]:
            ui.label(permission)
    except APIError as exc:
        ui.label(str(exc)).classes("text-red-700")


@ui.page("/settings")
def settings_page():
    token = app.storage.user.get("token")
    if not token:
        ui.navigate.to("/login")
        return
    apply_preferences()
    render_header(token)
    ui.label("Personal settings").classes("text-2xl font-semibold")
    theme = ui.select(["auto", "light", "dark"], value=app.storage.user.get("theme", "auto"), label="Theme")
    density = ui.select(
        ["comfortable", "compact"], value=app.storage.user.get("density", "comfortable"), label="Density"
    )

    def save_settings():
        app.storage.user["theme"] = theme.value
        app.storage.user["density"] = density.value
        ui.navigate.to("/settings")

    ui.button("Save settings", on_click=save_settings)


def run():
    secret = os.environ.get("FRONTEND_STORAGE_SECRET")
    if not secret or secret.startswith("replace-") or len(secret) < 50:
        raise RuntimeError("Set FRONTEND_STORAGE_SECRET to a unique secret of at least 50 characters.")
    ui.run(host="0.0.0.0", port=8080, title="DjangoPortal", storage_secret=secret, reload=False)


if __name__ in {"__main__", "__mp_main__"}:
    run()
