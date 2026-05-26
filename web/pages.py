import logging
from flask import redirect, make_response

logger = logging.getLogger(__name__)


def register_routes(app):
    @app.route("/")
    def index():
        return redirect("/app/")

    @app.route("/dashboard")
    def dashboard_redirect():
        return redirect("/app/")

    @app.route("/tickets")
    def tickets_redirect():
        return redirect("/app/tickets")

    @app.route("/tickets/<int:ticket_id>")
    def ticket_detail_redirect(ticket_id):
        return redirect(f"/app/tickets/{ticket_id}")

    @app.route("/tickets/new")
    def ticket_create_redirect():
        return redirect("/app/tickets/new")

    @app.route("/clients")
    def clients_redirect():
        return redirect("/app/clients")

    @app.route("/clients/<path:client_name>")
    def client_detail_redirect(client_name):
        return redirect(f"/app/clients/{client_name}")

    @app.route("/equipment")
    def equipment_redirect():
        return redirect("/app/equipment")

    @app.route("/equipment/<int:equip_id>")
    def equipment_detail_redirect(equip_id):
        return redirect(f"/app/equipment/{equip_id}")

    @app.route("/service-fees")
    def service_fees_redirect():
        return redirect("/app/service-fees")

    @app.route("/staff")
    def staff_redirect():
        return redirect("/app/staff")

    @app.route("/suppliers")
    def suppliers_redirect():
        return redirect("/app/suppliers")

    @app.route("/sales")
    def sales_redirect():
        return redirect("/app/sales")

    @app.route("/finance")
    def finance_redirect():
        return redirect("/app/finance")

    @app.route("/stats")
    def stats_redirect():
        return redirect("/app/stats")

    @app.route("/todos")
    def todos_redirect():
        return redirect("/app/todos")

    @app.route("/settings")
    def settings_redirect():
        return redirect("/app/settings")

    @app.route("/warehouses")
    def warehouses_redirect():
        return redirect("/app/warehouses")

    @app.route("/notifications")
    def notifications_redirect():
        return redirect("/app/notifications")

    @app.route("/inventory")
    def inventory_redirect():
        return redirect("/app/inventory")

    @app.route("/design-system")
    def design_system_redirect():
        return redirect("/app/design-system")

    @app.route("/products")
    def products_redirect():
        return redirect("/app/service-fees")

    @app.route("/goods")
    def goods_redirect():
        return redirect("/app/inventory")

    @app.route("/inventory-management")
    def inventory_mgmt_redirect():
        return redirect("/app/inventory")

    @app.route("/api-docs")
    def api_docs_page():
        return redirect("/app/")

    logger.info("Web 页面路由已注册（全部重定向到 Vue SPA /app/）")
