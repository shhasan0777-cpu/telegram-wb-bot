"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users", sa.Column("user_id", sa.Integer, primary_key=True), sa.Column("username", sa.Text), sa.Column("current_lesson", sa.Integer, server_default="0"), sa.Column("stage", sa.Text, server_default="start"), sa.Column("funnel_started", sa.Integer, server_default="0"), sa.Column("segment", sa.Text, server_default="cold"), sa.Column("access_deadline", sa.Text))
    op.create_table("analytics", sa.Column("id", sa.Integer, primary_key=True, autoincrement=True), sa.Column("user_id", sa.Integer), sa.Column("event", sa.Text), sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_table("crm_leads", sa.Column("id", sa.Integer, primary_key=True, autoincrement=True), sa.Column("user_id", sa.Integer), sa.Column("username", sa.Text), sa.Column("name", sa.Text), sa.Column("phone", sa.Text), sa.Column("interest", sa.Text), sa.Column("budget", sa.Text), sa.Column("status", sa.Text, server_default="new"), sa.Column("pain", sa.Text), sa.Column("next_action", sa.Text), sa.Column("next_action_at", sa.Text), sa.Column("manager_note", sa.Text), sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_table("wb_unit_sessions", sa.Column("id", sa.Integer, primary_key=True, autoincrement=True), sa.Column("user_id", sa.Integer), sa.Column("api_key", sa.Text), sa.Column("nm_id", sa.Text), sa.Column("vendor_code", sa.Text), sa.Column("product_name", sa.Text), sa.Column("work_model", sa.Text), sa.Column("warehouse_name", sa.Text), sa.Column("purchase_price", sa.REAL), sa.Column("fulfilment_price", sa.REAL), sa.Column("tax_percent", sa.REAL), sa.Column("other_expenses", sa.REAL), sa.Column("salary_expenses", sa.REAL), sa.Column("price", sa.REAL), sa.Column("spp_percent", sa.REAL), sa.Column("price_with_spp", sa.REAL), sa.Column("buyout_percent", sa.REAL), sa.Column("ads_percent", sa.REAL), sa.Column("ads_rub", sa.REAL), sa.Column("commission_percent", sa.REAL), sa.Column("commission_rub", sa.REAL), sa.Column("logistics_rub", sa.REAL), sa.Column("reverse_logistics_rub", sa.REAL), sa.Column("storage_rub", sa.REAL), sa.Column("acceptance_rub", sa.REAL), sa.Column("transit_rub", sa.REAL), sa.Column("width", sa.REAL), sa.Column("height", sa.REAL), sa.Column("length", sa.REAL), sa.Column("weight", sa.REAL), sa.Column("profit_per_unit", sa.REAL), sa.Column("margin_percent", sa.REAL), sa.Column("roi_percent", sa.REAL), sa.Column("stage", sa.Text, server_default="api_key"), sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_table("products_cache", sa.Column("user_id", sa.Integer, primary_key=True), sa.Column("payload", sa.Text, nullable=False), sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_table("scheduled_tasks", sa.Column("id", sa.Integer, primary_key=True, autoincrement=True), sa.Column("user_id", sa.Integer, nullable=False), sa.Column("task_type", sa.Text, nullable=False), sa.Column("run_at", sa.Text, nullable=False), sa.Column("payload", sa.Text), sa.Column("status", sa.Text, server_default="pending"), sa.Column("last_error", sa.Text), sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("idx_scheduled_tasks_due", "scheduled_tasks", ["status", "run_at"])


def downgrade():
    op.drop_table("scheduled_tasks")
    op.drop_table("products_cache")
    op.drop_table("wb_unit_sessions")
    op.drop_table("crm_leads")
    op.drop_table("analytics")
    op.drop_table("users")
