"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('force_password_change', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Clients table
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('client_type', sa.String(50), nullable=False),
        sa.Column('hostname', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('platform_info', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_seen', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('employee_consent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('consent_date', sa.DateTime(), nullable=True),
        sa.Column('consent_ip', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_clients_client_id', 'clients', ['client_id'])
    op.create_index('ix_clients_last_seen', 'clients', ['last_seen'])
    op.create_index('ix_clients_type_active', 'clients', ['client_type', 'is_active'])
    
    # Activities table with foreign key
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('active_window', sa.Text(), nullable=True),
        sa.Column('active_application', sa.String(255), nullable=True),
        sa.Column('active_url', sa.Text(), nullable=True),
        sa.Column('processes', sa.Text(), nullable=True),
        sa.Column('process_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('system_metrics', sa.Text(), nullable=True),
        sa.Column('cpu_percent', sa.Float(), nullable=True),
        sa.Column('memory_percent', sa.Float(), nullable=True),
        sa.Column('disk_percent', sa.Float(), nullable=True),
        sa.Column('activity_category', sa.String(50), nullable=True),
        sa.Column('productivity_score', sa.Integer(), nullable=True),
        sa.Column('additional_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE')
    )
    op.create_index('ix_activities_client_id', 'activities', ['client_id'])
    op.create_index('ix_activities_timestamp', 'activities', ['timestamp'])
    op.create_index('ix_activities_client_timestamp', 'activities', ['client_id', 'timestamp'])
    op.create_index('ix_activities_category', 'activities', ['activity_category'])
    
    # API Keys table with foreign key
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('allowed_ips', sa.Text(), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'])


def downgrade() -> None:
    op.drop_table('api_keys')
    op.drop_table('activities')
    op.drop_table('clients')
    op.drop_table('users')