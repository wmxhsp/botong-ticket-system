-- add is_deleted to tables that require soft-delete
ALTER TABLE audit_log ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE equipment ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE equipment_components ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE equipment_photos ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE inventory_items ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE maintenance_records ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE purchase_items ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE ticket_equipment ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE tickets ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE warehouses ADD COLUMN is_deleted INTEGER DEFAULT 0;
